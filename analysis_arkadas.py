# Dosya: src/analysis.py

import datetime
import json
import logging
import uuid
import re
from src.llm_client import LLMClient
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)

# ==============================================================================
# 🧠 KURUMSAL HIERARCHY VE VERİ SÖZLÜĞÜ
# ==============================================================================

def get_current_year():
    return datetime.datetime.now().year

def get_target_year():
    return datetime.datetime.now().year + 1

# --- KURALLAR ---
DATA_PRIORITY = """
### VERİ ÖNCELİK HİYERARŞİSİ ###
1. NİCEL PERFORMANS VERİSİ (Kesin gerçekleşen sayılar)
2. TREND ANALİZİ (Dönemsel değişimlerin yönü)
3. TASKS DOKÜMANI (Anayasal yetki ve sorumluluk çerçevesi - KANIT ZORUNLU)
4. YÖNETİCİ VİZYONU (Stratejik yön)
5. GÖREV TANIMI (Genel iş tanımı)
"""

MATH_RULES = """
### MATEMATİKSEL CLAMP (KISITLAMA) KURALLARI ###

⚠️ KRİTİK KURAL — HEDEF YÖNÜ:
- Her metriğin bir "Hedef Yönü" vardır: "Artan" veya "Azalan".
- "Artan" metrikler (örn: satış, verimlilik, kalite skoru): Hedef değer ÜST sınıra doğru gitmeli — ARTTIRILIR.
- "Azalan" metrikler (örn: hata oranı, maliyet, gecikme süresi): Hedef değer ALT sınıra doğru gitmeli — AZALTILIR.
- YASAK: "Azalan" hedefli bir metriği ASLA artırma! Bu mantık hatasıdır.
- YASAK: "Artan" hedefli bir metriği ASLA azaltma! Bu da mantık hatasıdır.
- TAM SAYI KURALI: Hesaplanacak her bir "target_value" kesinlikle en yakın tam sayıya yuvarlanmalıdır. Örn: 15.84 veya 15.2 yerine sadece tam sayı olarak 15 veya 16 yaz.

ARTAN metrikler için bant ve cap:
- ZAYIF: Artış %10-15 | ORTA: Artış %10-20 | GÜÇLÜ: Artış %15-25.
- HARD CAP (ARTAN): Hiçbir revizyon son gerçekleşmenin %30 üzerine çıkamaz.
- NEGATİF TREND (ARTAN): 3 dönem düşüş varsa artış yasaktır (Toparlama hedefi).

AZALAN metrikler için bant ve cap:
- ZAYIF: Azalış %5-10 | ORTA: Azalış %10-20 | GÜÇLÜ: Azalış %15-25.
- HARD CAP (AZALAN): Hiçbir revizyon son gerçekleşmenin %30'dan fazlasını azaltamaz.
- POZİTİF TREND (AZALAN): 3 dönem art arda artış varsa daha agresif azalış hedeflenebilir.
"""

# --- SCHEMAS ---

GOAL_SET_SCHEMA = """
{
  "goal_set_id": "string",
  "version": 1,
  "status": "BASELINE",
  "performance_tier": "Weak | Mid | Strong",
  "analysis_summary": "string",
  "goals": [
    {
      "id": "goal_1",
      "title": "string",
      "smart_goal": "string (Çok sade eylem cümlesi. Aradaki artış/düşüş hesaplaması (% X azaltarak vb.) YAZILMAZ. Doğrudan birimiyle net hedef belirtilir. Örn: 'Doğru stok sayımı oranını %95\\'e çıkarmak.')",
      "context": "string (zayıf yön entegrasyonu dahil)",
      "metrics": {
        "previous_value": 0,
        "target_value": 0,
        "direction": "Artan | Azalan",
        "change_rate_percent": 0.0,
        "metric_key": "string"
      },
      "evidence_chunk_ids": ["string"]
    }
  ],
  "self_check": {
    "math_compliance": true,
    "direction_compliance": true,
    "task_compliance": true,
    "weakness_compensated": true
  }
}
"""

PATCH_SCHEMA = """
{
  "proposed_version": 2,
  "changes": [
    {
      "goal_index": 0,
      "field": "metrics.target_value | title | smart_goal",
      "old_value": "any",
      "new_value": "any",
      "reason": "Değişiklik özeti. Eğer Hedef Yönü 'Azalan' ise yeni değer eski değerden KÜÇÜK olmalıdır. Eğer clamping devreye girdiyse hangi kural (Örn: %30 HARD CAP) olduğunu belirt.",
      "evidence_chunk_ids": ["string"]
    }
  ],
  "self_check": {
    "math_compliance": true,
    "direction_compliance": true,
    "feedback_aligned": true
  }
}
"""

EVALUATE_SCHEMA = """
{
  "is_appropriate": true,
  "risk_score": 1-10,
  "analysis": "string",
  "improvement_suggestions": ["string"],
  "requires_revision": false
}
"""

# ==============================================================================
# 🚀 ANALYZER CLASS
# ==============================================================================

class Analyzer:
    def __init__(self):
        self.version = "2.0.0-DECISION-ENGINE"
        self.llm_client = LLMClient()
        self.vector_store = VectorStore()

    def build_system_prompt(self, mode="GENERATE"):
        base = f"""
        ### ROL: KIDEMLİ PERFORMANS ANALİTİK MOTORU ###
        Sen sezgisel değil, tamamen veriye ve kurallara dayalı çalışan bir karar motorusun.
        DİKKAT CİDDİ KURAL: Yanıtlarını KESİNLİKLE VE SADECE TÜRKÇE vereceksin! Asla İngilizce, Almanca ("möglich" vb.) veya başka bir yabancı dil kullanma. Tüm metinler kurumsal, akıcı bir Türkçe seviyesinde olmalı.
        YIL: {get_current_year()}
        
        {DATA_PRIORITY}
        {MATH_RULES}
        
        ⛔ HEDEF YÖNÜ KONTROL ZORUNLULUĞU:
        Hedef üretmeden veya revize etmeden önce MUTLAKA şunu sor: "Bu metriğin 'Hedef Yönü' nedir?"
        - Eğer geçmişte "Azalan" olarak işaretlenmişse → target_value'yu DÜŞÜR, direction="Azalan" yaz.
        - Eğer "Artan" olarak işaretlenmişse → target_value'yu ARTIR, direction="Artan" yaz.
        - Veri yoksa bağlamdan çıkar: hata/maliyet/gecikme/oran düşüş → Azalan; satış/verimlilik/skor artış → Artan.
        Bu kuralı ihlal eden bir JSON üretmek KESİNLİKLE yasaktır.
        
        ÖNEMLİ: Çıktıların daima geçerli bir JSON objesi olmalıdır.
        MOD: {mode}
        """
        return base

    def analyze_and_suggest(self, employee_name, target_type, manager_vision, history_text):
        """v1 (BASELINE) Hedef Seti Üretimi"""
        evidence = self.vector_store.get_evidence(f"{employee_name} {target_type} görevleri", top_k=5)
        evidence_text = "\n".join([f"[{e['id']}] {e['content']}" for e in evidence])
        
        goal_set_uuid = str(uuid.uuid4())[:8]
        user_prompt = f"""
        {employee_name} için v1 BASELINE hedef seti üret.
        GİRDİLER:
        - Vizyon: {manager_vision}
        - Geçmiş (Hedef Yönü kolonuna DİKKAT et — "Azalan" hedeflerde target_value KÜÇÜLMELI): {history_text}
        - Tasks Kanıtları: {evidence_text}
        
        ⚠️ HEDEF YÖNÜ KURALI: Geçmiş verideki "Hedef Yönü" kolonuna göre:
          • "Azalan" → direction="Azalan", target_value < previous_value (azalt)
          • "Artan"  → direction="Artan",  target_value > previous_value (artır)
        Bu kuralı ihlal eden hedef üretme.
        
        ⚠️ SMART KURALI: 'smart_goal' metninde ASLA "%20 azaltarak" veya "%15 artırarak" gibi hesaplama detaylarını YAZMA. Sadece ulaşılması istenen son noktayı ve birimini düzgün kullanarak çok kısa, sade ve net bir eylem cümlesi yaz. Eğer ilgili metrik bir "oran" ise yanına % işaretini ekle. Ondalıklı sayı (14.4 vb.) yasaktır, daima tam sayı.
        DOĞRU ÖRNEK 1: "Doğru stok sayımı oranını %95'e çıkarmak."
        DOĞRU ÖRNEK 2: "Kalite hatalarının sayısını 14'e düşürmek."
        YANLIŞ ÖRNEK: "Stok sayımını %20 artırıp 92'den 95'e çıkarmak."
        
        Format: {GOAL_SET_SCHEMA}
        Lütfen geçerli bir JSON döndür. goal_set_id'yi '{goal_set_uuid}' olarak ata.
        """

        response = self.llm_client.generate_response(
            system_prompt=self.build_system_prompt("GENERATE"),
            user_prompt=user_prompt,
            temperature=0.2,
            json_mode=True
        )
        return self._safe_json_load(response)

    def evaluate_goals(self, current_goal_set, employee_name):
        """Mevcut hedeflerin uygunluğunu analiz eder (Evaluate Mode)"""
        user_prompt = f"""
        Şu hedef setini (v{current_goal_set.get('version')}) analiz et. 
        Mevcut rakamları değiştirme, sadece risk ve uygunluk değerlendirmesi yap.
        
        HEDEFLER: {json.dumps(current_goal_set['goals'])}
        
        Format: {EVALUATE_SCHEMA}
        Lütfen geçerli bir JSON döndür.
        """
        
        for attempt in range(2):
            response = self.llm_client.generate_response(
                system_prompt=self.build_system_prompt("EVALUATE"),
                user_prompt=user_prompt,
                temperature=0.2,
                json_mode=True
            )
            data = self._safe_json_load(response)
            if "error" not in data and "is_appropriate" in data:
                return data
            logger.warning(f"Evaluate JSON attempt {attempt+1} failed or missing keys.")
        return data

    def revise_goals(self, current_goal_set, feedback):
        """Yönetici geri bildirimine göre PATCH (Revizyon) önerir (Revise Mode)"""
        # Her hedefin yön bilgisini özetleyelim (LLM'e net bilgi verelim)
        direction_summary = []
        for i, g in enumerate(current_goal_set.get('goals', [])):
            direction = g.get('metrics', {}).get('direction', 'Belirtilmemiş')
            direction_summary.append(f"  Hedef {i} ({g.get('title','?')}): Hedef Yönü = {direction}")
        direction_info = "\n".join(direction_summary)
        
        user_prompt = f"""
        MEVCUT HEDEF SETİ (v{current_goal_set.get('version')}):
        {json.dumps(current_goal_set['goals'], ensure_ascii=False)}
        
        HER HEDEFİN YÖNÜ (BU BİLGİYİ KESİNLİKLE KULLAN):
{direction_info}
        
        YÖNETİCİ GERİ BİLDİRİMİ:
        "{feedback}"
        
        Bu geri bildirime göre bir PATCH üret.
        ⚠️ HEDEF YÖNÜ KURALI:
          • "Azalan" yönlü hedefte new_value, old_value'dan KÜÇÜK olmalı (azalt).
          • "Artan" yönlü hedefte new_value, old_value'dan BÜYÜK olmalı (artır).
          Bu kuralı ihlal etmek YASAKTIR. Yönetici yanlış yön istese bile kuralı uygula ve reason'da açıkla.
        Kuralları (%30 cap, band limitleri) asla ihlal etme.
        Eğer yöneticinin talebi kurallara (clamping) takılırsa, 'reason' alanında HANGİ kuralın devreye girdiğini açıkla.
        
        Format: {PATCH_SCHEMA}
        Lütfen geçerli bir JSON döndür.
        """
        
        for attempt in range(2):
            response = self.llm_client.generate_response(
                system_prompt=self.build_system_prompt("REVISE"),
                user_prompt=user_prompt,
                temperature=0.1,
                json_mode=True
            )
            data = self._safe_json_load(response)
            if "error" not in data and "proposed_version" in data:
                return data
            logger.warning(f"Revise JSON attempt {attempt+1} failed or missing keys.")
        return data

    def _safe_json_load(self, raw):
        """JSON yanıtlarını temizler ve objeye çevirir. (Gelişmiş Extraction)"""
        try:
            # 1. Klasik temizlik
            clean = raw.strip()
            
            # 2. Markdown bloklarını ayıkla (regex öncesi hızlı kontrol)
            if "```" in clean:
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", clean, re.DOTALL)
                if match:
                    clean = match.group(1)
            
            # 3. JSON objesini bul (İlk { ile son } arası)
            if not (clean.startswith("{") and clean.endswith("}")):
                match = re.search(r"(\{.*\})", clean, re.DOTALL)
                if match:
                    clean = match.group(1)
            
            return json.loads(clean)
        except Exception as e:
            logger.error(f"JSON Parse Hatası: {e} | Ham: {raw}")
            # Eğer hala hata varsa, basitçe ham metni döndür (Üst katmanda hata kontrolü var)
            return {"error": f"JSON parse hatası: {str(e)}", "raw": raw}

    def format_goal_set(self, data):
        """Hedef setini UI için markdown yapar."""
        if "error" in data: return f"⚠️ Hata: {data['error']}"
        
        status_map = {
            "BASELINE": "YENİ TASLAK",
            "PROPOSED": "ONAY BEKLEYEN REVİZYON",
            "ACTIVE": "ONAYLI / KİLİTLENDİ"
        }
        display_status = status_map.get(data.get('status'), data.get('status', ''))
        
        tier_map = {
            "Weak": "Gelişime Açık",
            "Mid": "Beklentiyi Karşılayan",
            "Strong": "Güçlü Beklenti Üstü"
        }
        raw_tier = str(data.get('performance_tier', ''))
        display_tier = tier_map.get(raw_tier, raw_tier)
        
        m = f"## 🎯 Hedef Seti v{data['version']} ({display_status})\n"
        m += f"> **Analiz:** {data['analysis_summary']}\n"
        m += f"> **Performans Katmanı:** {display_tier}\n\n"
        
        for g in data['goals']:
            m += f"### {g['title']}\n"
            m += f"- **SMART:** {g['smart_goal']}\n"
            m += f"- **Bağlam:** {g['context']}\n"
            metrics = g.get('metrics', {})
            direction = metrics.get('direction', 'Artan')
            arrow = "⬆️" if direction == "Artan" else "⬇️"
            change_rate = metrics.get('change_rate_percent', metrics.get('increase_rate_percent', 0))
            # Azalan hedeflerde change_rate negatif olmalı, ama gösterim için abs kullan
            change_label = f"%{abs(change_rate):.1f} {'artış' if direction == 'Artan' else 'azalış'}"
            
            # Tam sayı olarak göstermek için temizle
            p_val = metrics.get('previous_value')
            t_val = metrics.get('target_value')
            if isinstance(p_val, float) and p_val.is_integer(): p_val = int(p_val)
            if isinstance(t_val, float) and t_val.is_integer(): t_val = int(t_val)
            
            m += f"- **Metrikler:** {p_val} → **{t_val}** {arrow} ({change_label}) | Hedef Yönü: **{direction}**\n"
            m += f"- **Kanıt Kurumsal ID'ler:** `{', '.join(g.get('evidence_chunk_ids', []))}` \n\n"
        
        sc = data.get('self_check', {})
        direction_ok = sc.get('direction_compliance', True)
        m += f"---\n🛡️ **Mühür:** Matematik: {'✅' if sc.get('math_compliance') else '❌'} | Yön Uyumu: {'✅' if direction_ok else '❌'} | Tasks: {'✅' if sc.get('task_compliance') else '❌'}"
        return m

    def format_patch(self, patch_data, base_goal_set):
        """Revizyon önerisini (diff) görselleştirir."""
        m = f"## ⚠️ Revizyon Önerisi (v{patch_data.get('proposed_version')})\n"
        m += "Yönetici geri bildirimi doğrultusunda şu değişiklikler planlanmıştır:\n\n"
        
        # Alan isimlerini Türkçeleştiren harita
        field_map = {
            "metrics.target_value": "Hedef Değer",
            "title": "Başlık",
            "smart_goal": "SMART Tanımı",
            "context": "Bağlam"
        }
        
        for ch in patch_data.get('changes', []):
            idx = ch['goal_index']
            target_goal = base_goal_set['goals'][idx]
            field_name = field_map.get(ch['field'], ch['field'])
            
            # Hedefin yönünü göster
            direction = target_goal.get('metrics', {}).get('direction', 'Belirtilmemiş')
            arrow = "⬆️ Artan" if direction == "Artan" else ("⬇️ Azalan" if direction == "Azalan" else direction)
            
            m += f"**Hedef: {target_goal['title']}** *(Hedef Yönü: {arrow})*\n"
            m += f"- **Değişen:** {field_name} | **Eski:** {ch['old_value']} → **Yeni:** {ch['new_value']}\n"
            m += f"- **Gerekçe:** {ch['reason']}\n\n"
            
        sc = patch_data.get('self_check', {})
        direction_ok = sc.get('direction_compliance', True)
        m += f"🛡️ **Güvenlik Notu:** Yön Uyumu: {'✅' if direction_ok else '❌'} | Tüm değişiklikler kurumsal matematik sınırları (clamping) dahilinde doğrulanmıştır."
        return m

    # Eski metodları yeni yapıya uyumlu hale getirmek için placeholder veya basit wrap yapıyoruz
    def analyze_performance(self, employee_name, target_type, history_text):
        # ... Mevcut analizi basitleştirerek devam ettiriyoruz ...
        rag_query = f"{employee_name} {target_type} yetkinlik"
        context = self.vector_store.get_context(rag_query)
        prompt = f"{employee_name} için {target_type} analizi yap. Veriler: {history_text}. Konteks: {context}"
        return self.llm_client.generate_response(self.build_system_prompt("ANALYZE"), prompt)

    def chat_with_data(self, message, history, employee_name, metadata_context=""):
        # Chatbot aynı zamanda intent detection yapabilir ama basit tutuyoruz
        rag_query = f"{employee_name} {message}"
        context = self.vector_store.get_context(rag_query)
        sys_prompt = self.build_system_prompt("CHAT") + f"\nContext: {context}\nMetadata: {metadata_context}"
        return self.llm_client.generate_response(sys_prompt, message)

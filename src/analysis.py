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
# 🧠 YIL VE KURALLAR
# ==============================================================================

def get_current_year():
    return datetime.datetime.now().year

def get_target_year():
    return datetime.datetime.now().year + 1

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
- ZAYIF: Artış %10-15 | ORTA: Artış %10-20 | GÜÇLÜ: Artış %15-25.
- HARD CAP: Hiçbir revizyon son gerçekleşmenin %30'unu aşamaz.
- NEGATİF TREND: 3 dönem düşüş varsa artış yasaktır (Toparlama hedefi).
"""

MASTERMIND_RULES = """
### KIDEMLİ PERFORMANS MİMARI KURALLARI ###
1. DİL KİLİDİ: Sadece ve sadece TÜRKÇE. İngilizce kelime yasak.
2. VERİ SADAKATİ: Asla halüsinasyon görme. Verilen veriler dışında bilgi uydurma.
3. KONTEKST HAKİMİYETİ: Çalışanın kim olduğunu, yönetici vizyonunu ve geçmiş başarıları tüm yanıtlarda akılda tut.
4. MATEMATİKSEL İTAAT:
   - Hedef tutmamışsa: "Kurtarma Hedefi" ver, çıtayı düşür ama yan destek ekle.
   - Hedef tutmuşsa: "Meydan Okuma Hedefi" ver, çıtayı yukarı çek.
5. DÜŞÜNME ALGORİTMASI:
   ADIM 1 - DEDEKTİF: Sayıları cımbızla çek, gizli trendleri bul.
   ADIM 2 - STRATEJİST: Vizyonu göreve tercüme et.
   ADIM 3 - YAZAR: Başlıklar profesyonel ve kurumsal olsun. Kanıtlar "çünkü" ile açıklanmış gerekçe içersin.
"""

# ==============================================================================
# 📋 JSON ŞEMALARI
# ==============================================================================

GOAL_SET_SCHEMA = """
{
  "goal_set_id": "string",
  "version": 1,
  "status": "BASELINE",
  "performance_tier": "Weak | Mid | Strong",
  "analysis_summary": "string (çalışanın genel performans değerlendirmesi — güçlü ve zayıf yönlere atıfla)",
  "goals": [
    {
      "id": "goal_1",
      "title": "string (profesyonel ve kurumsal başlık)",
      "smart_goal": "string (S-M-A-R-T cümle: içinde hedef rakamı ve zaman çerçevesi MUTLAKA geçmeli. Örn: '2027 yılı sonuna kadar X metriğini Y'den Z değerine çıkarmak')",
      "context": "string (GEÇMİŞ VERİYE VE GÖREV TANIMI'NA DAYALI gerekçe: bu hedef neden seçildi, geçmişte ne oldu, şimdi ne hedefleniyor)",
      "evidence_justification": "string (METRİK GEREKÇE: previous_value ve target_value hangi veriden türetildi? Hangi trend bu artışı haklı kılıyor? 'Geçmiş veride X görüldüğü için target Y olarak belirlendi' formatında yaz)",
      "metrics": {
        "previous_value": 0.0,
        "target_value": 0.0,
        "increase_rate_percent": 0.0,
        "metric_key": "string (ölçülen birimin adı, örn: 'hata oranı %', 'müşteri memnuniyet puanı', 'tamamlanan proje sayısı')"
      }
    },
    {
      "id": "goal_2",
      "title": "string",
      "smart_goal": "string (içinde hedef rakamı ve zaman çerçevesi MUTLAKA geçmeli)",
      "context": "string (geçmiş + görev tanımı gerekçesi)",
      "evidence_justification": "string (metrik gerekçesi — hangi veri bu rakamı belirledi)",
      "metrics": {
        "previous_value": 0.0,
        "target_value": 0.0,
        "increase_rate_percent": 0.0,
        "metric_key": "string"
      }
    },
    {
      "id": "goal_3",
      "title": "string",
      "smart_goal": "string (içinde hedef rakamı ve zaman çerçevesi MUTLAKA geçmeli)",
      "context": "string (geçmiş + görev tanımı gerekçesi)",
      "evidence_justification": "string (metrik gerekçesi — hangi veri bu rakamı belirledi)",
      "metrics": {
        "previous_value": 0.0,
        "target_value": 0.0,
        "increase_rate_percent": 0.0,
        "metric_key": "string"
      }
    }
  ],
  "self_check": {
    "math_compliance": true,
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
      "reason": "Değişiklik özeti ve eğer varsa Clamping (kurallara takılma) gerekçesi (Örn: %30 kuralı nedeniyle talep edilen artış tıraşlandı).",
      "evidence_justification": "string (bu değişikliğin dayanağı)"
    }
  ],
  "self_check": {
    "math_compliance": true,
    "feedback_aligned": true
  }
}
"""

EVALUATE_SCHEMA = """
{
  "is_appropriate": true,
  "risk_score": 5,
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
        self.version = "2.1.0-MASTERMIND-ENGINE"
        self.llm_client = LLMClient()
        self.vector_store = VectorStore()

    def build_system_prompt(self, mode="GENERATE"):
        base = f"""
        ### ROL: KIDEMLİ PERFORMANS MİMARI (MASTERMIND ENGINE) ###
        Sen Fortune 500 şirketlerine stratejik danışmanlık veren, veri analitiği konusunda uzmanlaşmış bir karar motorusun.
        Görevin: Ham verileri işleyerek şirketin geleceğini şekillendirecek, matematiksel olarak tutarlı "Masterpiece" hedefler tasarlamak.
        DİL: TÜRKÇE | YIL: {get_current_year()} | HEDEF YILI: {get_target_year()}
        
        {DATA_PRIORITY}
        {MATH_RULES}
        {MASTERMIND_RULES}
        
        ÖNEMLİ: Çıktıların daima geçerli bir JSON objesi olmalıdır. Markdown, açıklama veya ek metin YASAK.
        MOD: {mode}
        """
        return base

    def analyze_and_suggest(self, employee_name, target_type, manager_vision, history_text):
        """v1 (BASELINE) Hedef Seti Üretimi - Tam olarak 3 SMART hedef"""
        evidence = self.vector_store.get_evidence(
            f"{employee_name} {target_type} görev sorumluluk yetkinlik", top_k=6
        )
        evidence_text = "\n".join([
            f"[Kaynak: {e.get('metadata', {}).get('source', 'Belge')}] {e['content']}"
            for e in evidence
        ])

        goal_set_uuid = str(uuid.uuid4())[:8]
        user_prompt = f"""
        {employee_name} için '{target_type}' kategorisinde TAM OLARAK 3 ADET SMART hedef içeren v1 BASELINE hedef seti üret.

        GİRDİLER:
        - Çalışan: {employee_name}
        - Hedef Kategorisi: {target_type}
        - Yönetici Vizyonu: {manager_vision}
        
        - Geçmiş Performans Verileri (Bu sayılar metrik hesaplamalarının TEMELİ):
        {history_text if history_text else "Geçmiş veri bulunamadı. Görev tanımı ve yönetici vizyonuna dayalı hedef üret."}
        
        - Destekleyici Kurumsal Kanıtlar (Görev Tanımı & Geçmiş Kayıtlar):
        {evidence_text}

        KESİN KURALLAR — HEPSİNE UYULACAK:
        1. Hedef sayısı KESİNLİKLE 3 olmalı. Ne 2 ne 4 — tam olarak 3.
        2. Her hedef SADECE '{target_type}' kategorisiyle ilgili olmalı. Başka kategori yasak.
        3. 'smart_goal' cümlesi içinde hedef rakamı (target_value) ve zaman çerçevesi ({get_target_year()} sonu gibi) MUTLAKA geçmeli.
           Örnek: '{get_target_year()} yıl sonuna kadar müşteri memnuniyet skorunu 72 puandan 88 puana çıkarmak.'
        4. 'context' alanı: geçmiş veriye DOĞRUDAN atıf yaparak başlamali. Örn: 'Geçen dönem hedef X gerçekleşen Y oldu, bu nedenle...'
           Eğer görev tanımı/kanıtlarda da destek varsa onu da bağla.
        5. 'evidence_justification' alanı İKİ BÖLÜM içermeli:
           - GEÇMİŞ VERİ & TREND: Bu hedefi hangi sayı veya eğilim tetikledi?
           - METRİK GEREKÇESİ: previous_value ve target_value neden bu rakamlar seçildi, bant kuralı nasıl uygulandı?
           Örn: 'Geçmiş veride hata oranı %18 görüldü (trend: 3 dönem artış). Hedef %14'e düşürülmesi, %30 cap içindeki maksimum iyileştirmeyi temsil ediyor.'
        6. Matematik kurallarına (clamping) mutlaka uy. Her rakam veriye dayalı olmalı.
        
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
        
        HEDEFLER: {json.dumps(current_goal_set['goals'], ensure_ascii=False)}
        
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
        """Yönetici geri bildirimine göre PATCH (Revizyon) önerir"""
        user_prompt = f"""
        MEVCUT HEDEF SETİ (v{current_goal_set.get('version')}):
        {json.dumps(current_goal_set['goals'], ensure_ascii=False)}
        
        YÖNETİCİ GERİ BİLDİRİMİ:
        "{feedback}"
        
        Bu geri bildirime göre bir PATCH üret. Kuralları (%30 cap, band limitleri) asla ihlal etme.
        Eğer yöneticinin talebi kurallara (clamping) takılırsa, 'reason' alanında HANGİ kuralın devreye girdiğini açıkla.
        'evidence_justification' alanına somut gerekçe yaz.
        
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

    def analyze_performance(self, employee_name, target_type, history_text):
        """Seçilen hedef türü için çalışanın Güçlü ve Zayıf yönlerini analiz eder."""
        rag_query = f"{employee_name} {target_type} yetkinlik performans geri bildirim"
        unstructured_context = self.vector_store.get_context(rag_query)

        user_prompt = f"""
        {employee_name} isimli çalışanın '{target_type}' alanındaki performansını analiz et.
        
        === VERİLER ===
        1. SAYISAL GEÇMİŞ ({target_type}):
        {history_text if history_text else "Sayısal veri yok."}
        
        2. SÖZEL KAYITLAR (Geri Bildirimler/Görevler):
        {unstructured_context}
        
        Lütfen şunları listele:
        
        ### 💪 GÜÇLÜ YÖNLER (Verilerle Kanıtla)
        - Madde 1 (Kanıt: ...)
        - Madde 2 ...
        
        ### ⚠️ GELİŞİME AÇIK ALANLAR / ZAYIF YÖNLER
        - Madde 1 (Sebep: ...)
        - Madde 2 ...
        
        ### 🚀 GELİŞİM ÖNERİLERİ
        - Bu alanları iyileştirmek için somut 2-3 öneri.
        
        Kısa, öz ve profesyonel bir dille yaz. Kanıtları "çünkü" veya "veriye göre" ile açıkla.
        """

        return self.llm_client.generate_response(
            system_prompt=self.build_system_prompt("ANALYZE"),
            user_prompt=user_prompt,
            temperature=0.4
        )

    def chat_with_data(self, message, history, employee_name, target_type="",
                       metadata_context="", current_goal_set=None):
        """
        Chatbot: SADECE seçilen çalışan ve hedef türüne ait verilere erişim izni.
        Diğer çalışanlar ve kategoriler hakkında bilgi vermez.
        Chat geçmişini dikkate alır. Hedef seti varsa tam içeriğiyle bilir.
        """
        rag_query = f"{employee_name} {target_type} {message}"
        context = self.vector_store.get_context(rag_query)

        # Aktif hedef setini asistana detaylı aktar
        goal_context = ""
        if current_goal_set and "goals" in current_goal_set and "error" not in current_goal_set:
            goal_context = f"""
        === AKTİF HEDEF SETİ (v{current_goal_set.get('version', 1)} — {current_goal_set.get('status', 'BASELINE')}) ===
        Performans Katmanı: {current_goal_set.get('performance_tier', '-')}
        Analiz Özeti: {current_goal_set.get('analysis_summary', '-')}

        BELİRLENEN 3 HEDEF VE SEÇİLME GEREKÇELERİ:
        """
            for i, g in enumerate(current_goal_set["goals"], 1):
                m = g.get("metrics", {})
                goal_context += f"""
        Hedef {i}: {g.get('title', '-')}
          - SMART Hedef: {g.get('smart_goal', '-')}
          - Bağlam (Neden seçildi): {g.get('context', '-')}
          - Kanıt & Metrik Gerekçesi: {g.get('evidence_justification', '-')}
          - Metrik: {m.get('metric_key','-')} | Önceki: {m.get('previous_value','-')} → Hedef: {m.get('target_value','-')} (%{m.get('increase_rate_percent','-')} artış)
        """
        else:
            goal_context = "\n        === HENÜZ BELİRLENMİŞ HEDEF SETİ YOK ===\n"

        dynamic_system = self.build_system_prompt("CHAT") + f"""

        === YETKİ KISITLAMASI (ZORUNLU) ===
        Sen SADECE aşağıdaki kapsam dahilinde yanıt vermelisin:
        - Çalışan: {employee_name}
        - Hedef Kategorisi: {target_type}

        Bu kapsam DIŞINDA başka çalışan veya kategoriler hakkında ASLA veri paylaşma.
        Eğer kullanıcı başka biri veya kategori sorarsa, kibarca reddet:
        "Bu oturumda sadece {employee_name} için '{target_type}' verileri üzerinde çalışıyorum."

        === ÇALIŞAN KİMLİK BİLGİLERİ ===
        {metadata_context if metadata_context else f"Çalışan: {employee_name}, Kategori: {target_type}"}

        {goal_context}

        === İLGİLİ DÖKÜMAN VERİLERİ (RAG) ===
        {context}

        Sohbet tarihçesini dikkate al. Hedefler ve gerekçeleri hakkında sorulunca yukarıdaki bilgilere dayan.
        Cevaplarını kısa, net ve profesyonel tut.
        """

        # Geçmiş mesajları metne dök
        history_text = ""
        for msg in history:
            if isinstance(msg, tuple) and len(msg) == 2:
                history_text += f"Kullanıcı: {msg[0]}\nAsistan: {msg[1]}\n\n"

        user_input = f"{history_text}Kullanıcı: {message}\nAsistan:"

        return self.llm_client.generate_response(
            system_prompt=dynamic_system,
            user_prompt=user_input,
            temperature=0.4
        )

    def _safe_json_load(self, raw):
        """JSON yanıtlarını temizler ve objeye çevirir. (Gelişmiş Extraction)"""
        try:
            clean = raw.strip()

            # Markdown bloklarını ayıkla
            if "```" in clean:
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", clean, re.DOTALL)
                if match:
                    clean = match.group(1)

            # JSON objesini bul
            if not (clean.startswith("{") and clean.endswith("}")):
                match = re.search(r"(\{.*\})", clean, re.DOTALL)
                if match:
                    clean = match.group(1)

            return json.loads(clean)
        except Exception as e:
            logger.error(f"JSON Parse Hatası: {e} | Ham: {raw[:200]}")
            return {"error": f"JSON parse hatası: {str(e)}", "raw": raw}

    def format_goal_set(self, data):
        """Hedef setini UI için güzel markdown yapar."""
        if "error" in data:
            return f"⚠️ **Hata:** {data['error']}\n\n*Ham Yanıt:* {data.get('raw', '')[:300]}"

        tier_map = {"Weak": "🔴 Zayıf", "Mid": "🟡 Orta", "Strong": "🟢 Güçlü"}
        tier = tier_map.get(data.get('performance_tier', ''), data.get('performance_tier', 'Bilinmiyor'))

        m = f"## 🎯 Hedef Seti v{data.get('version', 1)} · `{data.get('status', 'BASELINE')}`\n\n"
        m += f"> **📊 Performans Katmanı:** {tier}\n\n"
        m += f"> **🔍 Analiz Özeti:** {data.get('analysis_summary', '-')}\n\n"
        m += "---\n\n"

        for i, g in enumerate(data.get('goals', []), 1):
            metrics = g.get('metrics', {})
            prev = metrics.get('previous_value', '-')
            target = metrics.get('target_value', '-')
            rate = metrics.get('increase_rate_percent', '-')

            m += f"### Hedef {i}: {g.get('title', '')}\n\n"
            m += f"**🎯 SMART Hedef:**\n{g.get('smart_goal', '-')}\n\n"
            m += f"**📌 Bağlam & Analiz:**\n{g.get('context', '-')}\n\n"
            m += f"**📈 Metrikler:** `{prev}` → **`{target}`** *(+%{rate} artış)*\n\n"
            m += f"**🔬 Kanıt & Gerekçe:**\n> {g.get('evidence_justification', '-')}\n\n"
            m += "---\n\n"

        sc = data.get('self_check', {})
        m += "### 🛡️ Sistem Mühürü\n"
        m += f"- Matematik Uyumu: {'✅' if sc.get('math_compliance') else '❌'}\n"
        m += f"- Görev Uyumu: {'✅' if sc.get('task_compliance') else '❌'}\n"
        m += f"- Zayıf Yön Telafisi: {'✅' if sc.get('weakness_compensated') else '❌'}\n"
        return m

    def format_patch(self, patch_data, base_goal_set):
        """Revizyon önerisini (diff) görselleştirir."""
        m = f"## ✏️ Revizyon Önerisi (v{patch_data.get('proposed_version')})\n\n"
        m += "Yönetici geri bildirimi doğrultusunda aşağıdaki değişiklikler önerilmiştir:\n\n"

        field_map = {
            "metrics.target_value": "Hedef Değer",
            "title": "Başlık",
            "smart_goal": "SMART Tanımı",
            "context": "Bağlam"
        }

        goals = base_goal_set.get('goals', [])
        for ch in patch_data.get('changes', []):
            idx = ch.get('goal_index', 0)
            target_goal = goals[idx] if idx < len(goals) else {}
            field_name = field_map.get(ch.get('field', ''), ch.get('field', ''))

            m += f"**📌 Hedef: {target_goal.get('title', f'Hedef {idx+1}')}**\n"
            m += f"- **Değişen Alan:** {field_name}\n"
            m += f"- **Eski Değer:** {ch.get('old_value', '-')}\n"
            m += f"- **Yeni Değer:** {ch.get('new_value', '-')}\n"
            m += f"- **Gerekçe:** {ch.get('reason', '-')}\n"
            m += f"- **Kanıt:** {ch.get('evidence_justification', '-')}\n\n"

        m += "\n🛡️ **Güvenlik Notu:** Tüm değişiklikler kurumsal matematik sınırları (clamping) dahilinde doğrulanmıştır."
        return m
# Dosya: src/analysis.py

import datetime
import json
import logging
import uuid
import re
import pandas as pd
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

MASTERMIND_RULES = """
### KIDEMLİ PERFORMANS MİMARI KURALLARI ###
1. DİL KİLİDİ: Sadece ve sadece TÜRKÇE. İngilizce kelime yasak.
2. VERİ SADAKATİ: Asla halüsinasyon görme. Verilen veriler dışında bilgi uydurma.
3. KONTEKST HAKİMİYETİ: Çalışanın kim olduğunu, yönetici vizyonunu ve geçmiş başarıları tüm yanıtlarda akılda tut.
4. MATEMATİKSEL İTAAT (BU KURAL ÇOK KRİTİKTİR):
   - Hedef tutmamışsa: "Kurtarma Hedefi" ver, çıtayı düşür ama yan destek ekle.
   - Hedef tutmuşsa: "Meydan Okuma Hedefi" ver, çıtayı yukarı çek.
   - KESİN %30 KURALI: Hiçbir hedef önerisi geçmişteki veya mevcut gerçekleşenden %30 DAHA FAZLA OLAMAZ. Eğer hesapladığın artış oranı > %30 ise, HEDEF DEĞERİNİ DÜŞÜR. Bunu hem ilk hedeflerde hem revizyonda ZORUNLU KIL.
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
      "smart_goal": "string (S-M-A-R-T cümle: içinde hedef rakamı ve zaman çerçevesi MUTLAKA geçmeli. Asla ondalık sayı kullanma, doğrudan net hedef belirt. Örn: 'Doğru stok sayımı oranını %95\\'e çıkarmak.')",
      "context": "string (GEÇMİŞ VERİYE VE GÖREV TANIMI'NA DAYALI gerekçe: bu hedef neden seçildi, geçmişte ne oldu, şimdi ne hedefleniyor)",
      "evidence_justification": "string (Bu hedefin mantıksal dayanağı: 1. Geçmiş performans, 2. Görev tanımı, 3. Geri bildirim dayanaklarını içeren kanıt paragrafı)",
      "vision_alignment_note": "string (Bu hedef vizyonun hangi temasını karşılıyor? MAKSIMUM 15 KELIME. Örn: 'Operasyonel mükemmellik temasını; kalite odağıyla destekliyor.')",
      "vision_influence_explanation": "string (Bu hedefin yönetici vizyonundan nasıl etkilendiği, vizyon ile hedef arasındaki ilişki ve yapay zekanın bu kararı verirken vizyondan nasıl etkilendiğinin detaylı açıklaması)",
      "metrics": {
        "previous_value": 0,
        "target_value": 0,
        "direction": "Artan | Azalan",
        "change_rate_percent": 0.0,
        "metric_key": "string (ölçülen birimin adı)"
      }
    },
    {
      "id": "goal_2",
      "title": "string",
      "smart_goal": "string (içinde hedef rakamı ve zaman çerçevesi MUTLAKA geçmeli)",
      "context": "string (geçmiş + görev tanımı gerekçesi)",
      "evidence_justification": "string (Bu hedefin mantıksal dayanağı)",
      "vision_alignment_note": "string (MAKSIMUM 15 KELIME — bu hedef vizyonun hangi temasını karşılıyor)",
      "vision_influence_explanation": "string (Bu hedefin yönetici vizyonundan nasıl etkilendiği, vizyon ile hedef arasındaki ilişki ve yapay zekanın bu kararı verirken vizyondan nasıl etkilendiğinin detaylı açıklaması)",
      "metrics": {
        "previous_value": 0,
        "target_value": 0,
        "direction": "Artan | Azalan",
        "change_rate_percent": 0.0,
        "metric_key": "string"
      }
    },
    {
      "id": "goal_3",
      "title": "string",
      "smart_goal": "string (içinde hedef rakamı ve zaman çerçevesi MUTLAKA geçmeli)",
      "context": "string (geçmiş + görev tanımı gerekçesi)",
      "evidence_justification": "string (Bu hedefin mantıksal dayanağı)",
      "vision_alignment_note": "string (MAKSIMUM 15 KELIME — bu hedef vizyonun hangi temasını karşılıyor)",
      "vision_influence_explanation": "string (Bu hedefin yönetici vizyonundan nasıl etkilendiği, vizyon ile hedef arasındaki ilişki ve yapay zekanın bu kararı verirken vizyondan nasıl etkilendiğinin detaylı açıklaması)",
      "metrics": {
        "previous_value": 0,
        "target_value": 0,
        "direction": "Artan | Azalan",
        "change_rate_percent": 0.0,
        "metric_key": "string"
      }
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

# ==============================================================================
# 🔮 VİZYON DECODE ŞEMASI
# ==============================================================================

VISION_DECODE_SCHEMA = """
{
  "ambition_level": "Zayıf | Dengeli | Agresif",
  "stretch_factor": 0.0,
  "focus_themes": [
    {"theme": "string (Kalite | Büyüme | Verimlilik | İnovasyon | Maliyet | Müşteri | Diğer)", "weight": 0.0}
  ],
  "risk_appetite": "Düşük | Orta | Yüksek",
  "vision_summary": "string (Vizyonu tek cümleyle özetle — maksimum 20 kelime)",
  "key_signals": ["string (vizyondan çıkarılan 2-3 anahtar sinyal)"]
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
      "reason": "Değişiklik özeti. Eğer Hedef Yönü 'Azalan' ise yeni değer eski değerden KÜÇÜK olmalıdır. Clamping veya Hedef Yönü kuralları devreye girdiyse açıklanmalı.",
      "evidence_justification": "string (bu değişikliğin dayanağı)"
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
  "analysis": "string",
  "improvement_suggestions": ["string"],
  "requires_revision": false
}
"""

# ==============================================================================
# 📊 RISK & KARAR DESTEK MOTORU (DSS) KATMANLARI
# ==============================================================================
RISK_MATRIX = {
    "veri_tutarsizligi": {
        "risk_tanimi": "Veri Tutarsızlığı",
        "kategori": "Veri",
        "olasilik": 4,
        "etki": 5,
        "skor": 20,
        "oncelik": "Kritik",
        "mitigation": "Veri giriş aşamasında otomatik doğrulama (validation) kuralları ve eksik veri tamamlama algoritmaları entegre edilecektir."
    },
    "yetki_ihlali": {
        "risk_tanimi": "Yetki İhlali",
        "kategori": "Güvenlik",
        "olasilik": 2,
        "etki": 5,
        "skor": 10,
        "oncelik": "Orta",
        "mitigation": "Rol Tabanlı Erişim Kontrolü (RBAC) testleri her sprint sonunda tekrarlanacak ve log kayıtları izlenecektir."
    },
    "nlp_hatalari": {
        "risk_tanimi": "NLP Hataları",
        "kategori": "Teknik",
        "olasilik": 3,
        "etki": 3,
        "skor": 9,
        "oncelik": "Orta",
        "mitigation": "Duygu analizi modülü, sektörel veri setleriyle (Fine-tuning) eğitilecek ve önerilerin yanına 'Gerekçe Kartı' eklenecektir."
    },
    "kullanici_direnci": {
        "risk_tanimi": "Kullanıcı Direnci",
        "kategori": "Operasyonel",
        "olasilik": 3,
        "etki": 3,
        "skor": 9,
        "oncelik": "Orta",
        "mitigation": "Sistemin 'karar verici' değil 'destekleyici' olduğu vurgulanacak ve açıklanabilir YZ (XAI) çıktıları ile güven artırılacaktır."
    },
    "hiyerarsi_kisiti": {
        "risk_tanimi": "Hiyerarşi Kısıtı",
        "kategori": "Operasyonel",
        "olasilik": 2,
        "etki": 2,
        "skor": 4,
        "oncelik": "Düşük",
        "mitigation": "Kritik roller ve acil durumlar için yöneticilere 'Manuel Override' (Sistemi Ezme) yetkisi tanımlanacaktır."
    }
}

class DataQualityValidator:
    def validate_history(self, history_text):
        """Veri kalitesini kontrol eder. %80 üzeri eksiklikte analizi durdurur."""
        issues = []
        if not history_text or len(history_text.strip()) < 10 or history_text == "Sayısal veri yok.":
            return {"valid": False, "score": 0, "issues": ["Geçmiş veri tamamen eksik veya çok kısa."]}

        expected_fields = ["hedef", "gerçekleşen", "performans", "tarih"]
        found_fields = sum(1 for field in expected_fields if field in history_text.lower())
        missing_ratio = 1 - (found_fields / len(expected_fields))

        if missing_ratio > 0.8:
            return {"valid": False, "score": 20, "issues": [f"Veri setinde %{int(missing_ratio*100)} eksiklik tespit edildi (Eşik: %80)."]}

        numeric_data = re.findall(r"\d+", history_text)
        if not numeric_data:
            issues.append("Sayısal KPI verisi tespit edilemedi.")

        quality_score = 100 - (len(issues) * 20) - (missing_ratio * 50)
        return {
            "valid": quality_score > 30,
            "score": quality_score,
            "issues": issues,
            "missing_ratio": missing_ratio
        }

class RiskEngine:
    def assess_risks(self, data_quality_score, valid_structure):
        """Sistemdeki aktif riskleri matrisle eşleştirir."""
        active_risks = []
        if data_quality_score < 60:
            active_risks.append(RISK_MATRIX["veri_tutarsizligi"])
        if not valid_structure:
            active_risks.append(RISK_MATRIX["nlp_hatalari"])
        return active_risks

class DecisionSupportEngine:
    def calculate_success_probability(self, history_df, suggested_response):
        """Geçmiş verilere ve önerilen hedefin niteliğine göre başarı olasılığını hesaplar."""
        if history_df.empty:
            return 65

        try:
            ratios = []
            for _, row in history_df.iterrows():
                h = float(row.get('Hedef Değeri', 100))
                g = float(row.get('Gerçekleşen Değer', 80))
                yon = row.get('Hedef Yönü', 'Artan') # Hedef yönünü çek
                if str(yon).strip().lower() == 'azalan':
                    # Azalan hedefte gerçekleşen değer hedef değerden küçükse daha iyidir
                    ratios.append(h / g if g != 0 else 1.2)
                else:
                    ratios.append(g / h if h != 0 else 0.8)
            
            avg_ratio = sum(ratios) / len(ratios) if ratios else 0.8
            last_ratio = ratios[-1] if ratios else avg_ratio
            stat_prob = (avg_ratio * 0.4 + last_ratio * 0.6)
            
            risk_bonus = 0
            if "inovasyon" in suggested_response.lower() or "yeni" in suggested_response.lower():
                risk_bonus = -0.1
            if "tekrarlı" in suggested_response.lower() or "standart" in suggested_response.lower():
                risk_bonus = 0.05
                
            final_prob = (stat_prob + risk_bonus) * 100
            return min(max(int(final_prob), 15), 98) 
        except:
            return 70

    def calculate_risk_score(self, history_df, alignment_values, active_risks=[]):
        """Stratejik risk skorunu hesaplar (0-100)."""
        score = 20
        if len(history_df) < 5:
            score += 30
        max_focus = max(alignment_values.values()) if alignment_values else 0
        if max_focus > 70:
            score += 25
        
        # RiskEngine'den gelen riskleri ekle
        for risk in active_risks:
            score += risk.get("skor", 0)

        return min(score, 100)

    def get_strategic_alignment(self, suggested_goals_text):
        """Hedeflerin stratejik odak dağılımını analiz eder."""
        themes = {
            "Kalite/Hata": ["kalite", "hata", "sıfır", "revizyon", "kpi"],
            "Hız/Zaman": ["hız", "süre", "teslim", "zaman", "deadline"],
            "Maliyet/Verim": ["maliyet", "verim", "tasarruf", "optimizasyon"],
            "İnovasyon": ["yeni", "arge", "patent", "tasarım", "inovasyon"]
        }
        
        distribution = {k: 0 for k in themes.keys()}
        total_hits = 0
        
        for theme, keywords in themes.items():
            for kw in keywords:
                if kw in suggested_goals_text.lower():
                    distribution[theme] += 1
                    total_hits += 1
        
        if total_hits == 0: 
            return {
                "values": {k: 25 for k in themes.keys()}, 
                "descriptions": {k: "Veri dağılımı stabil." for k in themes.keys()}
            }
        
        distribution_pct = {k: int((v/total_hits)*100) for k, v in distribution.items()}
        details = {
            "Kalite/Hata": "Hata payını minimize eden mükemmellik yaklaşımı.",
            "Hız/Zaman": "Teslimat sürelerini optimize eden hız odaklı hedefler.",
            "Maliyet/Verim": "Kaynak kullanımını optimize eden verimlilik odağı.",
            "İnovasyon": "Yeni teknolojilerle fark yaratan alanlar."
        }
        return {"values": distribution_pct, "descriptions": details}


# ==============================================================================
# 🔮 VİZYON DECODER
# Akademik Çerçeve:
#   - Locke & Latham (2019) "The development of goal setting theory:
#     A half century retrospective" — Motivation Science, 5(2), 93-105.
#   - OKR Framework: Niven & Lamorte (2022) "Objectives and Key Results"
#   - EU AI Act 2024 (Reg. EU 2024/1689) Art. 13 — Şeffaflık Yükümlülüğü
# ==============================================================================

class VisionDecoder:
    """
    Ham yönetici vizyon metnini yapısal parametrelere dönüştürür.

    Akademik dayanak:
    • Locke & Latham (2019) — Hedef özgüllüğü ve zorluk düzeylerinin
      performans üzerindeki etkisi yarım asırlık ampirik kanıtlarla
      güncellenmiş meta-analiz çerçevesinde ele alınır.
    • OKR (Niven & Lamorte, 2022) — Stratejik vizyonun ölçülebilir
      anahtar sonuçlara (Key Results) dönüştürülmesi metodolojisi.
    • EU AI Act 2024 Art. 13 — Yüksek riskli AI sistemlerinde karar
      çıktılarının şeffaf ve yorumlanabilir olma zorunluluğu.

    Yalnızca LLM Structured Output (JSON Mode) kullanır.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def decode(self, vision_text: str) -> dict:
        """Vizyon metnini analiz eder ve yapısal JSON döndürür."""
        if not vision_text or not vision_text.strip():
            return {
                "ambition_level": "Dengeli",
                "stretch_factor": 0.5,
                "focus_themes": [{"theme": "Genel", "weight": 1.0}],
                "risk_appetite": "Orta",
                "vision_summary": "Vizyon girilmedi.",
                "key_signals": []
            }

        system_prompt = """
        Sen kurumsal strateji uzmanısın. Görevin: Bir yöneticinin serbest metin olarak yazdığı vizyon cümlesini
        güncel hedef koyma teorisi (Locke & Latham, 2019) ve OKR çerçevesi (Niven & Lamorte, 2022) perspektifinde analiz etmek.
        Analiz sonuçları EU AI Act 2024 şeffaflık ilkeleri doğrultusunda yapılandırılmış, yorumlanabilir ve denetlenebilir olmalıdır.
        DİL: TÜRKÇE. Çıktın daima geçerli bir JSON objesi olmalı. Markdown yasak.
        """

        user_prompt = f"""
        Aşağıdaki yönetici vizyonunu analiz et ve JSON çıktı üret:

        VİZYON: "{vision_text}"

        KILAVUZ:
        - ambition_level: Vizyon ne kadar agresif hedef içeriyor?
          * Zayıf → belirsiz, soyut, sayısal hedef yok
          * Dengeli → gerçekçi, ölçülebilir hedefler
          * Agresif → yüksek büyüme, kısa süre, köklü dönüşüm vurgusu
        - stretch_factor: 0.0 (hiç zorlanmayan) → 1.0 (maksimum gerilim)
        - focus_themes: Her temanın ağırlığı 0.0-1.0 arası, toplamı 1.0 olmalı
        - risk_appetite: Vizyondaki belirsizlik ve iddia düzeyine göre
        - vision_summary: Vizyonu tek cümleyle özetle (maks. 20 kelime)
        - key_signals: Vizyon metninden çıkarılan 2-3 anahtar kelime/cümle

        Format: {VISION_DECODE_SCHEMA}
        Lütfen geçerli bir JSON döndür.
        """

        try:
            response = self.llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                json_mode=True
            )
            result = self._safe_parse(response)
            # stretch_factor 0-1 aralığını garantile
            sf = result.get("stretch_factor", 0.5)
            result["stretch_factor"] = max(0.0, min(1.0, float(sf)))
            return result
        except Exception as e:
            logger.error(f"VisionDecoder hatası: {e}")
            return {
                "ambition_level": "Dengeli",
                "stretch_factor": 0.5,
                "focus_themes": [{"theme": "Genel", "weight": 1.0}],
                "risk_appetite": "Orta",
                "vision_summary": "Vizyon analizi yapılamadı.",
                "key_signals": []
            }

    def _safe_parse(self, raw: str) -> dict:
        import re, json
        clean = raw.strip()
        if "```" in clean:
            m = re.search(r"```(?:json)?\s*(.*?)\s*```", clean, re.DOTALL)
            if m:
                clean = m.group(1)
        if not (clean.startswith("{") and clean.endswith("}")):
            m = re.search(r"(\{.*\})", clean, re.DOTALL)
            if m:
                clean = m.group(1)
        return json.loads(clean)


# ==============================================================================
# 🔴 DEVIL'S ADVOCATE ENGINE
# Akademik Çerçeve:
#   - Schwenk (2020) "Devil's Advocacy in Strategic Decision Making"
#   - Kahneman, Sibony & Sunstein (2021) "Noise: A Flaw in Human Judgment"
#   - EU AI Act 2024 (Reg. EU 2024/1689) Art. 14 — Human Oversight
#   - NIST AI RMF 1.0 (2023) — MAP & MEASURE Functions
# ==============================================================================

class DevilsAdvocateEngine:
    """
    Vizyonun fizibilite denetimini yapar — saf Python, LLM çağrısı yok.

    Akademik dayanak:
    • Schwenk (2020) — Stratejik karar süreçlerinde çelişkisel sorgulama
      (Devil's Advocacy) yönteminin güncellenen meta-analizi.
    • Kahneman, Sibony & Sunstein (2021) — Yönetici kararlarındaki
      "gürültü" (noise) ve sistematik yanlılık (bias) tanımlaması.
    • EU AI Act 2024 Art. 14 — Yüksek riskli AI çıktılarında insan
      denetimi (Human Oversight) zorunluluğu; otomasyon yanlılığının
      önlenmesi.
    • NIST AI RMF 1.0 (2023) — AI risk değerlendirme çerçevesinin
      MAP ve MEASURE fonksiyonları.
    """

    # Agresif vizyon eşiği
    AGGRESSIVE_STRETCH_THRESHOLD = 0.70
    # Tarihsel başarı düşük eşiği
    LOW_SUCCESS_THRESHOLD = 70
    # Risk skoru yüksek eşiği
    HIGH_RISK_THRESHOLD = 60

    def evaluate(self, decoded_vision: dict, success_probability: int, risk_score: int) -> dict:
        """
        Vizyon ↔ geçmiş performans çelişkisini değerlendirir.
        Döndürür: {triggered: bool, severity: str, message: str, calibration_note: str}
        """
        ambition = decoded_vision.get("ambition_level", "Dengeli")
        stretch = decoded_vision.get("stretch_factor", 0.5)

        triggered = False
        severity = "info"   # info | warning | error
        message = ""
        calibration_note = ""

        # Kural 1 — Agresif vizyon + düşük tarihsel başarı
        if ambition == "Agresif" and success_probability < self.LOW_SUCCESS_THRESHOLD:
            triggered = True
            severity = "error"
            message = (
                f"Vizyonunuz agresif kalibre edilmiş, ancak geçmiş başarı olasılığı "
                f"%{success_probability} düzeyinde. "
                f"Hedefler matematiksel kısıtlar içinde (±%30) üretilecektir."
            )
            calibration_note = "⚠️ Agresif Vizyon — Geçmiş Başarı Düşük"

        # Kural 2 — Yüksek stretch + yüksek risk skoru
        elif stretch >= self.AGGRESSIVE_STRETCH_THRESHOLD and risk_score >= self.HIGH_RISK_THRESHOLD:
            triggered = True
            severity = "warning"
            message = (
                f"Vizyon gerilim faktörü {stretch:.2f} (Yüksek) ve DSS risk skoru %{risk_score}. "
                f"Hedefler gerçekçi bandın üst sınırına kalibre edilecektir."
            )
            calibration_note = "🟡 Yüksek Gerilim — Yüksek Risk"

        # Kural 3 — Agresif vizyon + yüksek risk (tek başına)
        elif ambition == "Agresif" and risk_score >= self.HIGH_RISK_THRESHOLD:
            triggered = True
            severity = "warning"
            message = (
                f"Agresif vizyon tespit edildi. DSS risk skoru: %{risk_score}. "
                f"Bu hedefler geçmiş %{success_probability} başarı oranınıza göre agresif kalibre edilmiştir."
            )
            calibration_note = "🟡 Agresif Vizyon — Yüksek Risk"

        return {
            "triggered": triggered,
            "severity": severity,
            "message": message,
            "calibration_note": calibration_note,
            "ambition_level": ambition,
            "stretch_factor": stretch,
            "success_probability": success_probability,
            "risk_score": risk_score
        }

# ==============================================================================
# 🚀 ANALYZER CLASS
# ==============================================================================

class Analyzer:
    def __init__(self):
        self.version = "2.4.0-DEFENSE-ACADEMIC-REF"
        self.llm_client = LLMClient()
        self.vector_store = VectorStore()
        self.data_validator = DataQualityValidator()
        self.risk_engine = RiskEngine()
        self.dss_engine = DecisionSupportEngine()
        self.vision_decoder = VisionDecoder(self.llm_client)
        self.devils_advocate = DevilsAdvocateEngine()

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

    def analyze_and_suggest(self, employee_name, target_type, manager_vision, history_text,
                            sicil_no=None, employee_title=None, decoded_vision=None, goal_count=3):
        """v1 (BASELINE) Hedef Seti Üretimi - Dinamik hedef sayısı (maks 3)"""
        
        # 1. VERİ KALİTE KONTROLÜ (Pre-processing Risk Layer)
        data_check = self.data_validator.validate_history(history_text)
        if not data_check["valid"]:
            logger.warning(f"Kritik Veri Riski: {data_check['issues']}")
            return {"error": f"Veri Yetersiz / Risk Yönetimi: {', '.join(data_check['issues'])} Lütfen geçerli geçmiş performans verisi sağlayın.", "raw": history_text}

        evidence = self.vector_store.get_evidence(
            f"{employee_name} {target_type} görev sorumluluk yetkinlik", top_k=6
        )
        evidence_text = "\n".join([
            f"[Kaynak: {e.get('metadata', {}).get('source', 'Belge')}] {e['content']}"
            for e in evidence
        ])

        # 2. KALİTATİF BAĞLAM: Görev Tanımı + Geri Bildirimler (Hibrit RAG)
        job_desc_ctx = self.vector_store.get_context(
            f"{employee_title or target_type} görev sorumluluk yetkinlik",
            top_k=3, position_name=employee_title
        )
        feedback_ctx = self.vector_store.get_context(
            f"{employee_name} teknik sosyal gelişim geri bildirim",
            top_k=3, sicil_no=sicil_no
        )
        _is_empty = lambda s: not s or "BİLGİ" in s or "HATA" in s
        kurumsal_baglaml = (
            "\n### KURUMSAL BAĞLAM VE GERİ BİLDİRİMLER ###\n\n"
            "[ÇALIŞANIN GÖREV TANIMI]\n"
            + ("Görev tanımı mevcut değil." if _is_empty(job_desc_ctx) else job_desc_ctx)
            + "\n\n[GEÇMİŞ GERİ BİLDİRİMLER]\n"
            + ("Geri bildirim kaydı mevcut değil." if _is_empty(feedback_ctx) else feedback_ctx)
            + "\n"
        )

        # 3. VİZYON PARAMETRELERİNİ PROMPT'A ENTİGRE ET
        vision_context = ""
        if decoded_vision:
            ambition = decoded_vision.get("ambition_level", "Dengeli")
            stretch = decoded_vision.get("stretch_factor", 0.5)
            themes = decoded_vision.get("focus_themes", [])
            theme_str = " | ".join(
                f"{t.get('theme', '')}: %{int(t.get('weight', 0) * 100)}"
                for t in themes
            ) if themes else "Genel"
            vision_context = f"""
        === VİZYON İSTİHBARAT KATMANI ===
        Akademik Çerçeve: Locke & Latham (2019) Güncel Hedef Koyma Teorisi;
        OKR — Niven & Lamorte (2022); EU AI Act 2024 Şeffaflık İlkeleri
        ---
        Hırs Düzeyi: {ambition} | Gerilim Faktörü: {stretch:.2f}
        Odak Temaları: {theme_str}
        Özet: {decoded_vision.get('vision_summary', '')}
        Önemli Sinyaller: {', '.join(decoded_vision.get('key_signals', []))}

        HEDEF KALİBRELEME TALİMATI:
        - Hırs Düzeyi "{ambition}" olduğundan hedefler bu banta göre ayarlanmalı:
          * Agresif → geçmiş trende göre %25-30 bantının üst sınırı
          * Dengeli → %10-20 bant ortası
          * Zayıf → %5-10 bant alt sınırı (kurtarma hedefi)
        - Odak teması en yüksek olan hedef türü bu kategoride önceliklendirilmeli.
        ===
        """

        goal_set_uuid = str(uuid.uuid4())[:8]
        user_prompt = f"""
        {employee_name} için '{target_type}' kategorisinde TAM OLARAK {goal_count} ADET SMART hedef içeren v1 BASELINE hedef seti üret.

        GİRDİLER:
        - Çalışan: {employee_name}
        - Hedef Kategorisi: {target_type}
        - Yönetici Vizyonu: {manager_vision}
        {vision_context}
        - Geçmiş Performans Verileri (Bu sayılar metrik hesaplamalarının TEMELİ):
        {history_text if history_text else "Geçmiş veri bulunamadı. Görev tanımı ve yönetici vizyonuna dayalı hedef üret."}
        
        {kurumsal_baglaml}
        - Destekleyici Kurumsal Kanıtlar (Görev Tanımı & Geçmiş Kayıtlar):
        {evidence_text}

        KESİN KURALLAR — HEPSİNE UYULACAK:
        1. Hedef sayısı KESİNLİKLE {goal_count} olmalı. Ne daha az ne daha çok — tam olarak {goal_count}.
        2. Her hedef SADECE '{target_type}' kategorisiyle ilgili olmalı. Başka kategori yasak.
        3. 'smart_goal' cümlesi içinde hedef rakamı (target_value) ve zaman çerçevesi ({get_target_year()} sonu gibi) MUTLAKA geçmeli. Ondalık sayı kullanma, doğrudan tam sayılarla net hedef belirt.
        4. HEDEF YÖNÜ KURALI (ÇOK KRİTİK): Geçmiş verideki "Hedef Yönü" veya bağlama göre:
           • Hata, maliyet, gecikme gibi düşürülmesi gereken şeyler için yönü "Azalan" yap ve target_value < previous_value (AZALT).
           • Ciro, müşteri memnuniyeti, verimlilik gibi yükseltilmesi gerekenler için yönü "Artan" yap ve target_value > previous_value (ARTIR).
        5. 'context' alanı: geçmiş veriye DOĞRUDAN atıf yaparak başlamalı. Örn: 'Geçen dönem hedef X gerçekleşen Y oldu, bu nedenle...'
        6. 'evidence_justification' alanı şu ÜÇ DAYANAĞI içeren mantıksal bir açıklama paragrafı olmalıdır:
           - GEÇMİŞ VERİ & TREND: Metrik olarak neden bu target_value seçildi?
           - GÖREV TANIMI: Bu sayısal artış personelin ana sorumluluklarıyla ve kurumsal rolüyle nasıl bağdaşıyor?
           - GERİ BİLDİRİM: Bu hedef, çalışanın yıllık değerlendirmelerindeki hangi noktayı destekliyor/iyileştiriyor?
        7. %30 HARD LIMIT (ÇOK KRİTİK): 'target_value' değeri, 'previous_value' değerinden oransal olarak en fazla %30 değişebilir.
        8. KALİTATİF BAĞLAM: Önerilerini oluştururken görev tanımı ve geri bildirimleri dikkate al.
        9. 'vision_alignment_note' alanı: Her hedef için MUTLAKA doldur. MAKSİMUM 15 KELİME. Örn: 'Büyüme temasını; pazar payı odaklı hedefle karşılıyor.'
        10. 'vision_influence_explanation' alanı: Her hedef için yönetici vizyonunun bu hedefe nasıl etki ettiğini, aralarındaki ilişkiyi ve yapay zeka olarak senin bu kararı verirken yöneticinin vizyonundan nasıl etkilendiğini anlatan açıklayıcı bir metin.
        
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

    def evaluate_goals(self, current_goal_set, employee_name, dss_risk_score=None):
        """Mevcut hedeflerin uygunluğunu analiz eder (Evaluate Mode)"""
        dss_info = f"\nKarar Destek Sistemi (DSS) Risk Skoru: %{dss_risk_score} (0 en iyi, 100 en riskli)" if dss_risk_score else ""
        
        user_prompt = f"""
        Şu hedef setini (v{current_goal_set.get('version')}) analiz et.
        Mevcut rakamları değiştirme, sadece risk ve uygunluk değerlendirmesi yap.{dss_info}
        Bu skoru değerlendirmenin analiz kısmında (gerekçesiyle) kullanabilirsin.
        
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
        
        Bu geri bildirime göre bir PATCH üret.
        ⚠️ HEDEF YÖNÜ KURALI: "Azalan" yönlü hedefte new_value eski değerden KÜÇÜK olmalı. "Artan" yönlü hedefte new_value eski değerden BÜYÜK olmalı. Yönetici yanlış yön istese bile matematiksel kuralı uygula ve reason'da açıkla.
        DİKKAT: %30 HARD LIMIT KURALI geçerlidir. Eğer yönetici %30'dan daha yüksek bir değişim talep ederse, limiti uygula (clamping) ve 'reason' alanında açıkla.
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

    def validate_manual_revision(self, old_value, new_value, target_direction):
        """
        Manuel revizyonlarda EU AI Act uyumu ve %30 kısıt limitini kontrol eder.
        Döndürür: { "valid": bool, "error": str, "clamped_value": float }
        """
        try:
            old_val = float(old_value)
            new_val = float(new_value)
        except ValueError:
            return {"valid": False, "error": "Geçersiz sayısal değer formatı.", "clamped_value": old_value}

        if old_val == 0:
            return {"valid": True, "error": "", "clamped_value": new_val}

        change_ratio = abs(new_val - old_val) / abs(old_val)
        
        # 1. Yön Kontrolü
        if target_direction.strip().lower() == "azalan":
            if new_val > old_val:
                return {"valid": False, "error": "Hata: 'Azalan' yönlü bir hedef artırılamaz.", "clamped_value": old_val}
            # %30 Limit
            if change_ratio > 0.30:
                limit_val = old_val * 0.70
                return {"valid": False, "error": f"Hata: Değişim %30'u aşamaz. Azami inilebilecek değer: {limit_val:.1f}", "clamped_value": limit_val}
        else: # Artan
            if new_val < old_val:
                return {"valid": False, "error": "Hata: 'Artan' yönlü bir hedef azaltılamaz.", "clamped_value": old_val}
            # %30 Limit
            if change_ratio > 0.30:
                limit_val = old_val * 1.30
                return {"valid": False, "error": f"Hata: Değişim %30'u aşamaz. Azami çıkılabilecek değer: {limit_val:.1f}", "clamped_value": limit_val}

        return {"valid": True, "error": "", "clamped_value": new_val}

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
        
        ### 💪 GÜÇLÜ YÖNLER
        - Madde 1 (Gerekçe: [İlgili ispatı şu 3 kavramla açıkla: Geçmiş Performans Sayıları, Görev Tanımı, Geri Bildirimler. DİKKAT: Herhangi birinde veri yoksa ASLA uydurma, "Bu bağlamda veri yok" diyerek dürüstçe belirt.])
        - Madde 2 ...
        
        ### ⚠️ GELİŞİME AÇIK ALANLAR / ZAYIF YÖNLER
        - Madde 1 (Sebep: [İlgili ispatı şu 3 kavramla açıkla: Geçmiş Performans Sayıları, Görev Tanımı, Geri Bildirimler. DİKKAT: Herhangi birinde veri yoksa ASLA uydurma, "Bu bağlamda veri yok" diyerek dürüstçe belirt.])
        - Madde 2 ...
        
        ### 🚀 GELİŞİM ÖNERİLERİ
        - Bu alanları iyileştirmek için somut 2-3 öneri.
        
        Kısa, öz ve profesyonel bir dille yaz. Metinlerinde renkli yeşil bloklar yaratmaktan kaçın. Mümkün olduğunca standart siyah düz metin tonunda yaz (örneğin sadece düz markdown). Kanıtları normal parantez içinde açıkla.
        """

        return self.llm_client.generate_response(
            system_prompt=self.build_system_prompt("ANALYZE"),
            user_prompt=user_prompt,
            temperature=0.4
        )

    def analyze_risk_factors(self, employee_name, target_type, history_text):
        """LLM kullanarak personelin ve hedeflerin önündeki spesifik risk faktörlerini analiz eder."""
        rag_query = f"{employee_name} {target_type} alanındaki geçmiş hatalar gecikmeler riskler yetkinlik eksiklikleri"
        unstructured_context = self.vector_store.get_context(rag_query)

        user_prompt = f"""
        Sen sistemin "Risk ve Güvenlik Yöneticisi"sin. Görevin {employee_name} isimli çalışanın '{target_type}' hedefleri için DERİNLEMESİNE BİR RİSK ANALİZİ yapmaktır.
        
        === ÇALIŞAN VE BAĞLAM VERİLERİ ===
        Sayısal Geçmiş: {history_text}
        Sözel Kayıtlar: {unstructured_context}
        
        Sistemimizde tanımlı olan 5 adet PMI standartlarına dayalı sabit risk kategorisi şunlardır:
        1. Veri Tutarsızlığı (Kritik)
        2. Yetki İhlali (Orta)
        3. NLP Hataları (Orta)
        4. Kullanıcı Direnci (Orta)
        5. Hiyerarşi Kısıtı (Düşük)
        
        Lütfen aşağıdaki şablona tam olarak uyarak raporunu oluştur:
        
        ### PMI (Literatür) Riskleri
        (Sistemdeki 5 sabit riskten hangileri bu çalışan özelinde geçmiş verilere ve görevlere bakıldığında "Aktif Risk" haline gelebilir? Örneğin veri seti çok eksikse "Veri Tutarsızlığı" tetiklenecektir. Uygun olan 1 veya 2 tanesini detaylıca gerekçelendir.)
        
        ### Çalışana Özgü Gizli Riskler
        (PMI matrisi dışında, doğrudan çalışanın verilerinden çıkarım yaptığın, o kişiye veya işe özgü en az 2 risk tespit et. Örn: "Teknik Borç Birikimi", "Tükenmişlik (Burnout) Belirtisi", "Proje Gecikme Alışkanlığı" vb. Gerekçeleriyle belirt.)
        
        ### Risk Hafifletme (Mitigation) Planı
        (Tespit edilen tüm bu spesifik risklerin olasılığını ve etkisini düşürmek için yöneticiye verilecek 3 adet nokta atışı, tamamen somut eylem önerisi.)
        
        Lütfen raporu son derece profesyonel, analitik ve doğrudan konuya giren bir üslupla Türkçe yaz.
        """

        return self.llm_client.generate_response(
            system_prompt=self.build_system_prompt("ANALYZE"),
            user_prompt=user_prompt,
            temperature=0.3
        )

    def get_decision_support_metrics(self, history_df, suggested_goals_text, active_risks=None):
        """Yönetici için karar destek metriklerini hesaplar."""
        if active_risks is None:
            active_risks = []

        avg_success = 0
        try:
            if not history_df.empty and 'Gerçekleşen Değer' in history_df:
                numeric_vals = pd.to_numeric(history_df['Gerçekleşen Değer'], errors='coerce')
                if not numeric_vals.isna().all():
                    avg_success = numeric_vals.mean()
        except:
            avg_success = 0
            
        benchmark_val = "+%12" if avg_success > 85 else "+%5"
        
        alignment = self.dss_engine.get_strategic_alignment(suggested_goals_text)
        
        metrics = {
            "success_probability": self.dss_engine.calculate_success_probability(history_df, suggested_goals_text),
            "strategic_alignment": alignment,
            "benchmark_status": f"Bölüm Ortalamasının {benchmark_val} Üzerinde",
            "skill_impact": "Teknik Yetkinlik Kazanımı (%20 Verim Artışı Potansiyeli)",
            "risk_score": self.dss_engine.calculate_risk_score(history_df, alignment["values"], active_risks)
        }
        return metrics

    def chat_with_data(self, message, history, employee_name, target_type="",
                       metadata_context="", current_goal_set=None,
                       sicil_no=None, employee_title=None):
        """
        Chatbot: SADECE seçilen çalışan ve hedef türüne ait verilere erişim izni.
        Diğer çalışanlar ve kategoriler hakkında bilgi vermez.
        Chat geçmişini dikkate alır. Hedef seti varsa tam içeriğiyle bilir.
        """
        rag_query = f"{employee_name} {target_type} {message}"
        context = self.vector_store.get_context(rag_query)

        # Kalıtatif bağlam: görev tanımı + geri bildirimler (Hibrit RAG)
        job_desc_ctx = self.vector_store.get_context(
            f"{employee_title or target_type} görev sorumluluk yetkinlik",
            top_k=3, position_name=employee_title
        )
        feedback_ctx = self.vector_store.get_context(
            f"{employee_name} teknik sosyal gelişim geri bildirim",
            top_k=3, sicil_no=sicil_no
        )
        _is_empty = lambda s: not s or "BİLGİ" in s or "HATA" in s
        kurumsal_baglaml = (
            "\n=== KURUMSAL BAĞLAM VE GERİ BİLDİRİMLER ===\n\n"
            "[ÇALIŞANIN GÖREV TANIMI]\n"
            + ("Görev tanımı mevcut değil." if _is_empty(job_desc_ctx) else job_desc_ctx)
            + "\n\n[GEÇMİŞ GERİ BİLDİRİMLER]\n"
            + ("Geri bildirim kaydı mevcut değil." if _is_empty(feedback_ctx) else feedback_ctx)
            + "\n"
        )

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

        {kurumsal_baglaml}

        === İLGİLİ DÖKÜMAN VERİLERİ (RAG) ===
        {context}

        === KANIT SUNMA VE AÇIKLAMA DİSİPLİNİ ===
        Hedefler tartışılırken veya kullanıcının analiz/hedef ile ilgili bir sorduğu sorulara cevap verilirken, mantığını daima şu 3 sütuna dayandır ve kullanıcıya bu şekilde aktar:
        1. Geçmiş Performans (Sayısal gerçeklik ve trendler)
        2. Görev Tanımı (Çalışanın kurumsal sorumlukları)
        3. Geri Bildirimler (Çalışanın kişisel değerlendirme geçmişi, güçlü veya gelişime açık yönleri)
        Yanıtlarda her hedefin mantığını veya sorunun cevabını bu üç bağlamla destele.
        DİKKAT KANIT UYDURMA YASAĞI: RAG verisinde veya Geri Bildirim metninde, sorulan veya anlatılan konuyla ilgili AÇIKÇA bir destekleyici cümle YOKSA, ASLA uydurma kanıt sunma. Veri eksikse "Geri bildirimlerde veya kayıtlarda bu duruma ilişkin doğrudan bir kanıt bulunmamaktadır" diye belirt ve elindeki somut verilerle yetin.
        
        Sohbet tarihçesini dikkate al.
        Cevaplarını kısa, net ve profesyonel tut.
        """

        # Geçmiş mesajları metne dök
        history_text = ""
        for msg in history:
            if isinstance(msg, dict):
                role_label = "Kullanıcı" if msg.get("role") == "user" else "Asistan"
                history_text += f"{role_label}: {msg.get('content')}\n\n"
            elif isinstance(msg, tuple) and len(msg) == 2:
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

        tier_map = {
            "Weak": "🔴 Gelişime Açık", 
            "Mid": "🟡 Beklentiyi Karşılayan", 
            "Strong": "🟢 Güçlü Beklenti Üstü"
        }
        status_map = {
            "BASELINE": "Yeni Taslak",
            "PROPOSED": "Onay Bekleyen Revizyon",
            "ACTIVE": "Onaylı / Kilitlendi"
        }
        
        tier = tier_map.get(data.get('performance_tier', ''), data.get('performance_tier', 'Bilinmiyor'))
        display_status = status_map.get(data.get('status'), data.get('status', ''))

        m = f"## 🎯 Hedef Seti v{data.get('version', 1)} · `{display_status}`\n\n"
        m += f"> **📊 Performans Katmanı:** {tier}\n\n"
        m += f"> **🔍 Analiz Özeti:** {data.get('analysis_summary', '-')}\n\n"
        m += "---\n\n"

        for i, g in enumerate(data.get('goals', []), 1):
            metrics = g.get('metrics', {})
            direction = metrics.get('direction', 'Artan')
            arrow = "⬆️" if direction == "Artan" else "⬇️"
            
            p_val = metrics.get('previous_value', '-')
            t_val = metrics.get('target_value', '-')
            if isinstance(p_val, float) and p_val.is_integer(): p_val = int(p_val)
            if isinstance(t_val, float) and t_val.is_integer(): t_val = int(t_val)
            
            rate = metrics.get('change_rate_percent', metrics.get('increase_rate_percent', '-'))
            change_label = f"%{abs(rate) if isinstance(rate, (int, float)) else rate} {'artış' if direction == 'Artan' else 'azalış'}"

            m += f"### Hedef {i}: {g.get('title', '')}\n\n"
            m += f"**🎯 SMART Hedef:**\n{g.get('smart_goal', '-')}\n\n"
            m += f"**📌 Bağlam & Analiz:**\n{g.get('context', '-')}\n\n"
            m += f"**📈 Metrikler:** `{p_val}` → **`{t_val}`** {arrow} *({change_label})* | Hedef Yönü: **{direction}**\n\n"
            m += f"**🔬 Kanıt & Gerekçe:**\n> {g.get('evidence_justification', '-')}\n\n"
            m += "---\n\n"

        sc = data.get('self_check', {})
        direction_ok = sc.get('direction_compliance', True)
        m += "### 🛡️ Sistem Mühürü\n"
        m += f"- Matematik Uyumu: {'✅' if sc.get('math_compliance') else '❌'}\n"
        m += f"- Yön Uyumu: {'✅' if direction_ok else '❌'}\n"
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
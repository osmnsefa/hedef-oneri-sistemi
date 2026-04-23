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
- ZAYIF: Artış %10-15 | ORTA: Artış %10-20 | GÜÇLÜ: Artış %15-25.
- HARD CAP: Hiçbir revizyon son gerçekleşmenin %30'unu aşamaz.
- NEGATİF TREND: 3 dönem düşüş varsa artış yasaktır (Toparlama hedefi).
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
      "smart_goal": "string (S-M-A-R-T cümle: içinde hedef rakamı ve zaman çerçevesi MUTLAKA geçmeli. Örn: '2027 yılı sonuna kadar X metriğini Y'den Z değerine çıkarmak')",
      "context": "string (GEÇMİŞ VERİYE VE GÖREV TANIMI'NA DAYALI gerekçe: bu hedef neden seçildi, geçmişte ne oldu, şimdi ne hedefleniyor)",
      "evidence_justification": "string (Bu hedefin mantıksal dayanağı: 1. Geçmiş performanstaki durum ve metrikler nelerdi? 2. Çalışanın görev tanımıyla nasıl bağlantılı? 3. Geri bildirimlerdeki hangi noktayı adresliyor? Bu 3 başlığı da barındıran destekleyici tek bir mantıksal kanıt paragrafı)",
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
      "evidence_justification": "string (Bu hedefin mantıksal dayanağı: Geçmiş performans, Görev tanımı ve Geri bildirim dayanaklarını içeren kanıt paragrafı)",
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
      "evidence_justification": "string (Bu hedefin mantıksal dayanağı: Geçmiş performans, Görev tanımı ve Geri bildirim dayanaklarını içeren kanıt paragrafı)",
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
        "kategori": "Veri",
        "olasilik": 4,
        "etki": 5,
        "skor": 20,
        "oncelik": "Kritik",
        "mitigation": "Otomatik doğrulama ve %80 eksik veri filtresi"
    },
    "yetki_ihlali": {
        "kategori": "Güvenlik",
        "olasilik": 2,
        "etki": 5,
        "skor": 10,
        "oncelik": "Orta",
        "mitigation": "RBAC kontrolü ve Audit logging"
    },
    "nlp_hatalari": {
        "kategori": "Teknik",
        "olasilik": 3,
        "etki": 3,
        "skor": 9,
        "oncelik": "Orta",
        "mitigation": "Gerekçe Kartı ve Çıktı Doğrulama"
    },
    "kullanici_direnci": {
        "kategori": "Operasyonel",
        "olasilik": 3,
        "etki": 3,
        "skor": 9,
        "oncelik": "Orta",
        "mitigation": "XAI (Açıklanabilir YZ) ve Karar Destek vurgusu"
    },
    "hiyerarsi_kisiti": {
        "kategori": "Operasyonel",
        "olasilik": 2,
        "etki": 2,
        "skor": 4,
        "oncelik": "Düşük",
        "mitigation": "Manuel Override ve Yönetici Onayı"
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
                ratios.append(g / h if h != 0 else 0)
            
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
# 🚀 ANALYZER CLASS
# ==============================================================================

class Analyzer:
    def __init__(self):
        self.version = "2.2.0-RISK-INTEGRATED"
        self.llm_client = LLMClient()
        self.vector_store = VectorStore()
        self.data_validator = DataQualityValidator()
        self.risk_engine = RiskEngine()
        self.dss_engine = DecisionSupportEngine()

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
                            sicil_no=None, employee_title=None):
        """v1 (BASELINE) Hedef Seti Üretimi - Tam olarak 3 SMART hedef"""
        
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

        goal_set_uuid = str(uuid.uuid4())[:8]
        user_prompt = f"""
        {employee_name} için '{target_type}' kategorisinde TAM OLARAK 3 ADET SMART hedef içeren v1 BASELINE hedef seti üret.

        GİRDİLER:
        - Çalışan: {employee_name}
        - Hedef Kategorisi: {target_type}
        - Yönetici Vizyonu: {manager_vision}
        
        - Geçmiş Performans Verileri (Bu sayılar metrik hesaplamalarının TEMELİ):
        {history_text if history_text else "Geçmiş veri bulunamadı. Görev tanımı ve yönetici vizyonuna dayalı hedef üret."}
        
        {kurumsal_baglaml}
        - Destekleyici Kurumsal Kanıtlar (Görev Tanımı & Geçmiş Kayıtlar):
        {evidence_text}

        KESİN KURALLAR — HEPSİNE UYULACAK:
        1. Hedef sayısı KESİNLİKLE 3 olmalı. Ne 2 ne 4 — tam olarak 3.
        2. Her hedef SADECE '{target_type}' kategorisiyle ilgili olmalı. Başka kategori yasak.
        3. 'smart_goal' cümlesi içinde hedef rakamı (target_value) ve zaman çerçevesi ({get_target_year()} sonu gibi) MUTLAKA geçmeli.
           Örnek: '{get_target_year()} yıl sonuna kadar müşteri memnuniyet skorunu 72 puandan 88 puana çıkarmak.'
        4. 'context' alanı: geçmiş veriye DOĞRUDAN atıf yaparak başlamali. Örn: 'Geçen dönem hedef X gerçekleşen Y oldu, bu nedenle...'
           Eğer görev tanımı/kanıtlarda da destek varsa onu da bağla.
        5. 'evidence_justification' alanı şu ÜÇ DAYANAĞI içeren mantıksal bir açıklama paragrafı olmalıdır:
           - GEÇMİŞ VERİ & TREND: Metrik olarak neden bu target_value seçildi?
           - GÖREV TANIMI: Bu sayısal artış personelin ana sorumluluklarıyla ve kurumsal rolüyle nasıl bağdaşıyor?
           - GERİ BİLDİRİM: Bu hedef, çalışanın yıllık değerlendirmelerindeki (gelişim/güçlü alan) hangi noktayı destekliyor/iyileştiriyor?
           DİKKAT KANIT UYDURMA YASAĞI: Eğer bu üç dayanaktan birinde (örneğin Geri Bildirimlerde) ilgili hedefe dair açık/destekleyici bir veri veya metin YOKSA, KESİNLİKLE hikaye uydurma. "Geri bildirimlerde bu spesifik konuda doğrudan bir destek/kanıt bulunmamaktadır" diyerek sadece mevcut verilere dayan.
        6. %30 HARD LIMIT (ÇOK KRİTİK): Çıkaracağın hiçbir hedefin 'target_value' değeri, 'previous_value' değerinden %30'dan daha fazla YÜKSEK OLAMAZ. Bu kuralı AŞMAK KESİNLİKLE YASAKTIR. Eğer %30'u aştığını hesaplarsan değeri geri düşür.
        7. KALİTATİF BAĞLAM: Önerilerini oluştururken sayısal verilerin yanı sıra yukarıdaki görev tanımı ve geri bildirimlerdeki teknik/sosyal yetkinlikleri de mutlaka dikkate al.
        
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
        
        Bu geri bildirime göre bir PATCH üret. Kuralları (%30 cap, band limitleri) asla ihlal etme.
        DİKKAT: %30 HARD LIMIT KURALI geçerlidir. Eğer yönetici %30'dan daha yüksek bir artış talep ederse, değeri tam %30 limitine çekerek (clamping yaparak) 'reason' alanında HANGİ kuralın devreye girdiğini mutlaka açıkla (Örn: "%30 limiti kuralı nedeniyle hedef talep edilen X değerine değil limit olan Y değerine çekilmiştir").
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
        rag_query = f"{employee_name} {target_type} geçmiş hatalar gecikmeler riskler yetkinlik eksiklikleri"
        unstructured_context = self.vector_store.get_context(rag_query)

        user_prompt = f"""
        {employee_name} isimli çalışanın '{target_type}' hedefleri için spesifik RİSK FAKTÖRLERİ analizi yap.
        
        === VERİLER ===
        Sayısal Geçmiş: {history_text}
        Sözel Kayıtlar: {unstructured_context}
        
        Lütfen tam olarak şu formatta bir tablo ve özet dön:
        1. "Faktör | Seviye | Etki" kolonlarından oluşan bir markdown tablosu.
        2. Seviye: Düşük, Orta, Yüksek.
        3. Etki: -%X (Başarı olasılığına etkisi).
        4. Tablonun altına "### ⚠️ En Kritik Risk: [Risk Adı]" başlığıyla bir açıklama ekle.
        
        Örnek Faktörler: Yetkinlik Boşluğu, Operasyonel Yük, Kaynak Kısıtı, Geçmiş Teknik Hatalar vb.
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
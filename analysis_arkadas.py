# Dosya: src/analysis.py

import datetime
import re
from llm_client import LLMClient
from vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# 📊 RISK DEĞERLENDİRME MATRİSİ (Tablo 6)
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

# ==============================================================================
# 🛡️ KONTROL VE DOĞRULAMA KATMANLARI
# ==============================================================================

class DataQualityValidator:
    def validate_history(self, history_text):
        """Veri kalitesini kontrol eder. %80 üzeri eksiklikte analizi durdurur."""
        issues = []
        if not history_text or len(history_text.strip()) < 10:
            return {"valid": False, "score": 0, "issues": ["Geçmiş veri tamamen eksik veya çok kısa."]}

        # Eksik veri oranı tahmini (Kritik Alan Kontrolü)
        expected_fields = ["hedef", "gerçekleşen", "performans", "tarih"]
        found_fields = sum(1 for field in expected_fields if field in history_text.lower())
        missing_ratio = 1 - (found_fields / len(expected_fields))

        if missing_ratio > 0.8:
            return {"valid": False, "score": 20, "issues": [f"Veri setinde %{int(missing_ratio*100)} eksiklik tespit edildi (Eşik: %80)."]}

        # Sayısal veri kontrolü
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

class ResponseValidator:
    def validate_structure(self, response_text):
        """Üretilen yanıtın kurumsal şablona uygunluğunu denetler."""
        checks = {
            "HEDEF 1": "HEDEF 1:" in response_text,
            "HEDEF 2": "HEDEF 2:" in response_text,
            "HEDEF 3": "HEDEF 3:" in response_text,
            "Gerekçe Kartı": "Gerekçe Kartı" in response_text,
            "SMART İŞ HEDEFİ": "SMART İŞ HEDEFİ" in response_text,
            "ZORUNLU GELİŞİM HEDEFİ": "ZORUNLU GELİŞİM HEDEFİ" in response_text
        }
        
        missing = [k for k, v in checks.items() if not v]
        return {"valid": len(missing) == 0, "missing": missing}

class RiskEngine:
    def assess_risks(self, data_quality, validation_result):
        """Sistemdeki aktif riskleri matrisle eşleştirir."""
        active_risks = []
        
        if data_quality["score"] < 60:
            active_risks.append(RISK_MATRIX["veri_tutarsizligi"])
        
        if not validation_result["valid"]:
            active_risks.append(RISK_MATRIX["nlp_hatalari"])
            
        return active_risks


# ==============================================================================
# 🧠 MEGA-SYSTEM PROMPT (YAPAY ZEKA ANAYASASI)
# ==============================================================================
def get_current_year():
    return datetime.datetime.now().year

def get_target_year():
    return datetime.datetime.now().year + 1

MASTERMIND_PROMPT = f"""
### ROL TANIMI ###
Sen, TUSAŞ ve Savunma Sanayii standartlarında stratejik performans yönetimi (Hoshin Kanri) ve veri analitiği konusunda uzmanlaşmış "Kıdemli Performans Mimarı"sın.
Görevin, önüne gelen ham verileri DİREKT sübjektif yargılardan arındırarak işleyip, şirketin gelecekteki ana stratejilerini (örneğin: "Milli Muharip Uçak Seri Üretim Fazı") destekleyecek, matematiksel olarak tutarlı "Masterpiece" (Şaheser) hedefler tasarlamaktır.

### ANAYASA VE KIRMIZI ÇİZGİLER ###
1. DİL KİLİDİ: Sadece ve sadece TÜRKÇE konuş. İngilizce düşünmen bile yasak.
2. VERİ SADAKATİ (OBJEKTİFLİK): Asla halüsinasyon görme ve tamamen sübjektif yargılardan arın. Sana verilen "Geçmiş Veri" ve "Görev Tanımı" dışında bilgi uydurma.
3. KONTEKST HAKİMİYETİ: Sohbetin başından sonuna kadar çalışanın kim olduğunu, yöneticinin vizyonunu ve geçmiş başarılarını hafızanda canlı tut.
4. MATEMATİKSEL İTAAT:
   - Eğer Hedef: 100, Gerçekleşen: 80 ise (Başarısızlık): Yeni hedefi asla 120 yapma. "Kurtarma Hedefi" ver. (Örn: 90 yap ama yanına eğitim ekle).
   - Eğer Hedef: 100, Gerçekleşen: 110 ise (Başarı): Yeni hedefi asla 100 veya 110 yapma. "Meydan Okuma Hedefi" ver. (Örn: 125 yap).

### DÜŞÜNME ALGORİTMASI (BU ADIMLARI İZLE) ###
ADIM 1: DEDEKTİF MODU (Veriye Dayalı Analiz)
   - Metinlerin içindeki sayıları (%, adet, puan) cımbızla çek ve sübjektif yorumları filtrele.
   - Gizli trendleri bul (Örn: "Hedef tutmuş ama kalite düşmüş mü?").

ADIM 2: STRATEJİST MODU (Hoshin Kanri Hizalaması)
   - Yönetici "Hata Azaltma" diyorsa ve çalışanın görevi "Kod Yazmak" ise, hedef "Daha az satır kod" değil, şirketin üst stratejisindeki "Kalite ve Güvenilirlik" temasına uygun "Sıfır Hata ve Yüksek Güvenilirlik" odaklı olmalıdır. Vizyonu kurumsal hedeflere (Cascading) bağla.

ADIM 3: YETKİNLİK BOŞLUĞU (SKILL-GAP) ANALİZİ
   - Çalışanın sadece ne üreteceğine ("iş sonucu") değil, bunu nasıl başaracağına ("yetkinlik kazanımı") da odaklan. Zayıf yönleri tespit edip her iş hedefinin yanına onu destekleyecek ve zayıf yönleri kapatacak bir "Gelişim Hedefi / Yol Haritası" ekle.

ADIM 4: YAZAR MODU
   - Hedef başlıkları "Rapor Hazırlamak" gibi sıkıcı olmamalı. TUSAŞ standartlarına uygun, kurumsal ve vizyoner olmalı. 
   - Gerekçeler, "Yaptım oldu" değil, "Verilere göre X olduğu için, TUSAŞ'ın Z vizyonuna ve stratejisine hizmet etmesi için Y hedefini koydum" şeklinde kanıta dayalı (Sübjektif olmayan) olmalı.

### RİSK FARKINDALIĞI VE GÜVENLİK (Tablo 6 Uyum) ###
1. VERİ TUTARSIZLIĞI: Eğer veride %80 eksiklik varsa analizi reddet (Sistem katmanında kontrol edilir).
2. NLP HATALARI: Halüsinasyon görme. Sadece "Gerekçe Kartı" ile kanıtlanmış hedefler ver.
3. KULLANICI DİRENCİ: Çıktıların "Karar Destek" amaçlı olduğunu unutma. "Açıklanabilir YZ" prensibiyle gerekçeleri teknik değil, vizyoner ve mantıksal sun.
4. HİYERARŞİ KISITI: Önerilerin yönetici tarafından her zaman "Override" edilebileceğini bildiğin için esnek ama tutarlı ol.

### KARAR DESTEK VE SENARYOLAR (DSS) ###
Analiz sonunda sadece tek bir yol değil, yöneticiye karar verebileceği 3 ALTERNATİF SENARYO sun:
1. SENARYO A (KONSERVATİF): %85+ başarı olasılığı, düşük risk, standart gelişim.
2. SENARYO B (DENGELİ): %70+ başarı olasılığı, makul risk, kurumsal beklenti.
3. SENARYO C (STRATEJİK SIÇRAMA): %45+ başarı olasılığı, yüksek risk, yüksek ödül/vizyon.

ŞU ANKİ YIL: {get_current_year()} | HEDEF YILI: {get_target_year()}
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

class Analyzer:
    def __init__(self):
        self.llm_client = LLMClient()
        self.vector_store = VectorStore() # Singleton
        self.data_validator = DataQualityValidator()
        self.response_validator = ResponseValidator()
        self.risk_engine = RiskEngine()

    def _apply_deterministic_constraints(self, llm_response, history_text, risk_report=None):
        """
        LLM tarafından üretilen hedef değerlerini denetler ve risk notları ekler.
        """
        disclaimer = "\n\n--- 🛡️ GÜVENLİK VE RİSK ANALİZİ ---\n"
        disclaimer += "> **⚖️ Karar Destek Notu:** *Bu rapor yapay zeka tarafından üretilmiş bir 'Öneri' setidir. Karar verici mekanizma insandır (Human-in-the-loop).* \n"
        
        if risk_report:
            risk_details = ", ".join([f"{r['kategori']}: {r['oncelik']}" for r in risk_report])
            disclaimer += f"> **⚠️ Tespit Edilen Riskler:** {risk_details}\n"
        
        validation_note = "> ⚙️ **Sistem Doğrulaması:** *Verilen hedefler TUSAŞ Hoshin Kanri standartlarında matematiksel denetime tabi tutulmuştur.*"
        
        return llm_response + disclaimer + validation_note

    def analyze_and_suggest(self, employee_name, target_type, manager_vision, history_text, user_role="manager"):
        """
        Risk analizi ve veri doğrulama içeren hedef öneri akışı.
        """
        # 0. YETKİ KONTROLÜ (RBAC Placeholder)
        if user_role not in ["admin", "manager"]:
            return "⛔ **Erişim Engellendi:** Bu analizi yapmak için yönetici yetkisine sahip olmanız gerekmektedir."

        if not employee_name or not target_type:
            return "⚠️ Lütfen çalışan ve hedef türü seçiniz."

        # 1. VERİ KALİTE KONTROLÜ (Pre-processing Risk Layer)
        data_check = self.data_validator.validate_history(history_text)
        if not data_check["valid"]:
            logger.warning(f"Kritik Veri Riski: {data_check['issues']}")
            return f"❌ **Analiz Durduruldu (Veri Riski):** {', '.join(data_check['issues'])} \n\nLütfen verileri tamamlayıp tekrar deneyiniz."

        # 2. RAG İŞLEMİ
        rag_query = f"{employee_name} görev tanımı sorumlulukları {target_type}"
        try:
            unstructured_context = self.vector_store.get_context(rag_query)
        except Exception as e:
            logger.error(f"RAG Hatası: {str(e)}")
            unstructured_context = "Ek sözel veri bulunamadı."

        # 3. LLM ÜRETİMİ
        user_prompt = f"""
        Aşağıdaki verileri kullanarak {employee_name} için '{target_type}' kategorisinde 3 adet NOKTA ATIŞI ve KUSURSUZ SMART HEDEF oluştur.
        
        === BAĞLAM DOSYASI ===
        1. YÖNETİCİ VİZYONU: "{manager_vision}"
        2. PERFORMANS VERİLERİ: {history_text}
        3. DESTEKLEYİCİ VERİLER: {unstructured_context}
        
        === KRİTİK KURALLAR ===
        - Her hedef için mutlaka bir 'Gerekçe Kartı' oluştur.
        - Gerekçede 'Veri Sadakati' ve 'Hoshin Kanri Uyumunu' göster.
        - Her iş hedefinin yanına zorunlu bir 'Gelişim Hedefi (Skill-Gap)' ekle.
        """

        response = self.llm_client.generate_response(
            system_prompt=MASTERMIND_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1
        )

        # 4. POST-PROCESSING (Validation & Risk Assessment)
        val_result = self.response_validator.validate_structure(response)
        active_risks = self.risk_engine.assess_risks(data_check, val_result)
        
        # 5. DETERMINISTIK KISIT VE RİSK RAPORU
        final_response = self._apply_deterministic_constraints(response, history_text, risk_report=active_risks)
        
        # Karar destek veya ekstra raporlama eklenebilir, şu an sadece final_response dönülüyor.
        return final_response

    def analyze_risk_factors(self, employee_name, target_type, history_text):
        """
        LLM kullanarak personelin ve hedeflerin önündeki spesifik risk faktörlerini analiz eder.
        PMI Standartları RISK_MATRIX kullanılarak analiz genişletilir.
        """
        rag_query = f"{employee_name} {target_type} alanındaki geçmiş hatalar gecikmeler riskler yetkinlik eksiklikleri"
        unstructured_context = self.vector_store.get_context(rag_query)

        user_prompt = f"""
        Sen sistemin "Risk ve Güvenlik Yöneticisi"sin. Görevin {employee_name} isimli çalışanın '{target_type}' hedefleri için DERİNLEMESİNE BİR RİSK ANALİZİ yapmaktır.
        
        === ÇALIŞAN VE BAĞLAM VERİLERİ ===
        Sayısal Geçmiş: {history_text}
        Sözel Kayıtlar/Performans Detayları: {unstructured_context}
        
        Sistemimizde tanımlı olan 5 adet PMI standartlarına dayalı sabit risk kategorisi şunlardır:
        1. Veri Tutarsızlığı (Kritik)
        2. Yetki İhlali (Orta)
        3. NLP Hataları (Orta)
        4. Kullanıcı Direnci (Orta)
        5. Hiyerarşi Kısıtı (Düşük)
        
        Lütfen aşağıdaki şablona tam olarak uyarak raporunu oluştur:
        
        ### 1. LİTERATÜR (PMI) RİSKLERİ UYUM ANALİZİ
        (Sistemdeki 5 sabit riskten hangileri bu çalışan özelinde geçmiş verilere ve görevlere bakıldığında "Aktif Risk" haline gelebilir? Örneğin veri seti çok eksikse "Veri Tutarsızlığı" tetiklenecektir. Uygun olan 1 veya 2 tanesini detaylıca gerekçelendir.)
        
        ### 2. ÇALIŞANA ÖZGÜ GİZLİ RİSKLER (YAPAY ZEKA TESPİTİ)
        (PMI matrisi dışında, doğrudan çalışanın verilerinden çıkarım yaptığın, o kişiye veya işe özgü en az 2 risk tespit et. Örn: "Teknik Borç Birikimi", "Tükenmişlik (Burnout) Belirtisi", "Proje Gecikme Alışkanlığı" vb. Gerekçeleriyle belirt.)
        
        ### 3. RİSK HAFİFLETME (MITIGATION) VE AKSİYON PLANI
        (Tespit edilen tüm bu spesifik risklerin olasılığını ve etkisini düşürmek için yöneticiye verilecek 3 adet nokta atışı, tamamen somut eylem önerisi.)
        
        Lütfen raporu son derece profesyonel, analitik ve doğrudan konuya giren bir üslupla Türkçe yaz.
        """

        return self.llm_client.generate_response(
            system_prompt=MASTERMIND_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3
        )

    def analyze_performance(self, employee_name, target_type, history_text):
        """
        Seçilen hedef türü için çalışanın Güçlü ve Zayıf yönlerini analiz eder.
        """
        # Sözel verileri de çekelim
        rag_query = f"{employee_name} {target_type} alanındaki yetkinlikleri performansı geri bildirimler"
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
        
        Kısa, öz ve profesyonel bir dille yaz.
        """
        
        return self.llm_client.generate_response(
            system_prompt=MASTERMIND_PROMPT,
            user_prompt=user_prompt,
            temperature=0.4
        )

    def chat_with_data(self, message, history, employee_name, metadata_context=""):
        """
        Sohbet botu fonksiyonu.
        """
        context = self.vector_store.get_context(message)
        
        dynamic_system = MASTERMIND_PROMPT + f"""
        HATIRLATMA:
        Şu an {employee_name} isimli çalışan hakkında konuşuyorsun.
        
        {metadata_context}
        
        Kullanıcı sana soru soruyor. RAG ile çektiğimiz şu verilere bakarak cevap ver:
        
        {context}
        """
        
        # History'i metne dök
        history_text = ""
        for human, ai in history:
            history_text += f"Kullanıcı: {human}\nAsistan: {ai}\n"
        
        user_input = f"{history_text}\nKullanıcı: {message}\nAsistan:"
        
        response = self.llm_client.generate_response(
            system_prompt=dynamic_system,
            user_prompt=user_input
        )
        
        return response
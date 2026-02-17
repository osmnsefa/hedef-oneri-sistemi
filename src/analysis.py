# Dosya: src/analysis.py

import datetime
from src.llm_client import LLMClient
from src.vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# 🧠 MEGA-SYSTEM PROMPT (YAPAY ZEKA ANAYASASI)
# ==============================================================================
def get_current_year():
    return datetime.datetime.now().year

def get_target_year():
    return datetime.datetime.now().year + 1

MASTERMIND_PROMPT = f"""
### ROL TANIMI ###
Sen, Fortune 500 şirketlerine stratejik danışmanlık veren, veri analitiği ve insan psikolojisi konusunda uzmanlaşmış "Kıdemli Performans Mimarı"sın.
Görevin, önüne gelen ham verileri işleyerek, şirketin geleceğini şekillendirecek, çalışanları motive edecek ve matematiksel olarak tutarlı "Masterpiece" (Şaheser) hedefler tasarlamaktır.

### ANAYASA VE KIRMIZI ÇİZGİLER ###
1. DİL KİLİDİ: Sadece ve sadece TÜRKÇE konuş. İngilizce düşünmen bile yasak.
2. VERİ SADAKATİ: Asla halüsinasyon görme. Sana verilen "Geçmiş Veri" ve "Görev Tanımı" dışında bilgi uydurma.
3. KONTEKST HAKİMİYETİ: Sohbetin başından sonuna kadar çalışanın kim olduğunu, yöneticinin vizyonunu ve geçmiş başarılarını hafızanda canlı tut.
4. MATEMATİKSEL İTAAT:
   - Eğer Hedef: 100, Gerçekleşen: 80 ise (Başarısızlık): Yeni hedefi asla 120 yapma. "Kurtarma Hedefi" ver. (Örn: 90 yap ama yanına eğitim ekle).
   - Eğer Hedef: 100, Gerçekleşen: 110 ise (Başarı): Yeni hedefi asla 100 veya 110 yapma. "Meydan Okuma Hedefi" ver. (Örn: 125 yap).

### DÜŞÜNME ALGORİTMASI (BU ADIMLARI İZLE) ###
ADIM 1: DEDEKTİF MODU
   - Metinlerin içindeki sayıları (%, adet, puan) cımbızla çek.
   - Gizli trendleri bul (Örn: "Hedef tutmuş ama kalite düşmüş mü?").

ADIM 2: STRATEJİST MODU
   - Yönetici "Hata Azaltma" diyorsa ve çalışanın görevi "Kod Yazmak" ise, hedef "Daha az satır kod" değil, "Bug oranı düşük kod" olmalıdır. Vizyonu göreve tercüme et.

ADIM 3: YAZAR MODU
   - Hedef başlıkları "Rapor Hazırlamak" gibi sıkıcı olmamalı. "Stratejik Karar Destek Raporlaması ile Verimliliği Artırmak" gibi kurumsal ve havalı olmalı.
   - Gerekçeler, "Yaptım oldu" değil, "Verilere göre X olduğu için, Vizyon Y olduğu için, Z hedefini koydum" şeklinde kanıta dayalı olmalı.

ŞU ANKİ YIL: {get_current_year()} | HEDEF YILI: {get_target_year()}
"""

class Analyzer:
    def __init__(self):
        self.llm_client = LLMClient()
        self.vector_store = VectorStore() # Singleton

    def analyze_and_suggest(self, employee_name, target_type, manager_vision, history_text):
        """
        RAG yapar, Prompt'u hazırlar ve Hedef Önerileri üretir.
        history_text: DataLoader'dan gelen yapılandırılmış geçmiş verisi.
        """
        if not employee_name or not target_type:
            return "⚠️ Lütfen çalışan ve hedef türü seçiniz."

        # 1. RAG İŞLEMİ: Sadece Görev Tanımı ve Geri Bildirimleri Vektör DB'den çek
        # Geçmiş sayısal verileri zaten history_text olarak veriyoruz, bu yüzden RAG'a "sözel" verileri soruyoruz.
        rag_query = f"{employee_name} görev tanımı sorumlulukları yetkinlikleri geri bildirimleri {target_type} hakkında yorumlar"
        
        try:
            unstructured_context = self.vector_store.get_context(rag_query)
        except Exception as e:
            logger.error(f"RAG Hatası: {str(e)}")
            unstructured_context = "Ek sözel veri bulunamadı."

        # 2. İŞLEM PROMPTU (EXECUTION PROMPT)
        user_prompt = f"""
        Aşağıdaki verileri kullanarak {employee_name} için '{target_type}' kategorisinde 3 adet NOKTA ATIŞI ve KUSURSUZ SMART HEDEF oluştur.
        
        === BAĞLAM DOSYASI ===
        1. YÖNETİCİ VİZYONU (KUZEY YILDIZI): "{manager_vision}"
        
        2. KESİN GEÇMİŞ PERFORMANS VERİLERİ (Sadece bu kategoriye ait):
        {history_text if history_text else "Bu kategori için geçmiş veri bulunamadı. Sıfırdan bir başlangıç yapılıyor."}
        
        3. DESTEKLEYİCİ SÖZEL VERİLER (Görev Tanımı & Geri Bildirimler):
        {unstructured_context}
        
        === KURALLAR ===
        - EĞER GEÇMİŞ VERİ VARSA: Mutlaka geçmişteki başarı/başarısızlık durumuna atıfta bulun. Geçen sene hedefi tuttuysa çıtayı yükselt, tutmadıysa onarıcı hedef ver.
        - SADECE SEÇİLEN HEDEF TÜRÜNE ODAKLAN: '{target_type}' dışında (örneğin eğitim veya sosyal kulüp gibi) alakasız hedefler önerme.
        - GÖREV TANIMINA UYGUNLUK: Çalışanın görev tanımında olmayan bir şeyi hedef olarak verme.
        
        === HEDEF TASARIM ŞABLONU ===
        **HEDEF 1:** [Profesyonel Başlık]
        * **BAĞLAM ve ANALİZ:** (Geçmiş veriye dayalı gerekçe: "Geçen yıl X hedefini %Y oranında gerçekleştirdiği için...")
        * **SMART HEDEF:** {get_target_year()} yılı içinde...
        
        **HEDEF 2:** ...
        **HEDEF 3:** ...
        """

        # 3. LLM İSTEĞİ
        response = self.llm_client.generate_response(
            system_prompt=MASTERMIND_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3
        )
        
        return response

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
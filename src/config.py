import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Dosya Yolları
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'guncel_veriler')
    CHROMA_DB_PATH = os.environ.get('CHROMA_DB_PATH', os.path.join(BASE_DIR, 'chroma_db'))
    
    # Groq Ayarları
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    MODEL_NAME = "llama-3.3-70b-versatile"
    
    # Model Ayarları
    # Türkçe için daha iyi olabilecek multilingual modeller tercih edilebilir ama varsayılan olarak bunu tutuyoruz
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    
    # Veritabanı Ayarları
    # Eski Yerel SQLite Bağlantısı
    #DATABASE_URL = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'pms_sql.db')}")
    
    # Yeni Bulut PostgreSQL Bağlantısı (Supabase)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("Kritik Hata: DATABASE_URL bulunamadı! Lütfen .env dosyanıza Supabase bağlantı linkini ekleyin.")
    
    # UI Ayarları
    PAGE_TITLE = "Stratejik PMS - Yönetim Paneli"
    PAGE_ICON = "🚀"
    LAYOUT = "wide"
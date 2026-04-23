import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import Config
from src.models import EmployeeFeedback
from seed import parse_feedbacks, parse_job_descriptions

def quick_update():
    engine = create_engine(Config.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("Sadece yeni veriler güncelleniyor...")
    try:
        # Sadece bu iki fonksiyonu çalıştır (seed.py'deki yeni versiyonlar)
        parse_job_descriptions(session, Config.DATA_DIR)
        parse_feedbacks(session, Config.DATA_DIR)
        print("Bitti!")
    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    quick_update()

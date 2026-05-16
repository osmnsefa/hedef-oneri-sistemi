import os
from sqlalchemy import create_engine

db_url = "postgresql://postgres:Osc1453database@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
print(f"Connecting to: {db_url}")

try:
    engine = create_engine(db_url, connect_args={'connect_timeout': 5})
    with engine.connect() as conn:
        print("Bağlantı başarılı (postgres formatı)!")
except Exception as e:
    print(f"Hata: {e}")

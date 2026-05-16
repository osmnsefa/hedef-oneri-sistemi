import os
from sqlalchemy import create_engine
import urllib.parse

db_url = "postgresql://postgres:Osc1453database@db.zhjakqvtixhttnzxlzyq.supabase.co:5432/postgres"
print(f"Connecting to: {db_url}")

try:
    engine = create_engine(db_url, connect_args={'connect_timeout': 5})
    with engine.connect() as conn:
        print("Bağlantı başarılı (port 5432)!")
except Exception as e:
    print(f"Hata: {e}")

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL')
print("Connecting to:", db_url)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cur.fetchall()
    print("Tables:")
    for t in tables:
        print(" -", t[0])
    
    # Check if there is data in any table
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
        count = cur.fetchone()[0]
        print(f"   {t[0]} count: {count}")
        
    conn.close()
except Exception as e:
    print("Error:", e)

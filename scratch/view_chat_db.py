import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL')
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Schema of chat_history
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='chat_history'")
    print("chat_history columns:")
    for col in cur.fetchall():
        print(f" - {col[0]} ({col[1]})")
        
    # Schema of chat_sessions
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='chat_sessions'")
    print("\nchat_sessions columns:")
    for col in cur.fetchall():
        print(f" - {col[0]} ({col[1]})")
        
    # Sample data from chat_history
    cur.execute("SELECT * FROM chat_history LIMIT 5")
    print("\nchat_history sample:")
    for row in cur.fetchall():
        print(" ", row)
        
    # Sample data from chat_sessions
    cur.execute("SELECT * FROM chat_sessions LIMIT 5")
    print("\nchat_sessions sample:")
    for row in cur.fetchall():
        print(" ", row)
        
    conn.close()
except Exception as e:
    print("Error:", e)

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import Config
from src.models import User, Employee

engine = create_engine(Config.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("--- USERS ---")
    users = session.query(User).all()
    for u in users:
        print(f"User: {u.sicil_no}, role: {u.role}, manager_sicil: {u.manager_sicil}")

    print("\n--- EMPLOYEES ---")
    employees = session.query(Employee).all()
    for e in employees:
        print(f"Employee ID: {e.id}, user_sicil: {e.user_sicil}, Name: {e.first_name} {e.last_name}, Title: {e.title}, Dept: {e.department}")
        
except Exception as err:
    print("Error:", err)
finally:
    session.close()

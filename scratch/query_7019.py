from src.auth import get_db_session
from src.models import Employee, PerformanceHistory

session = get_db_session()
try:
    emp = session.query(Employee).filter(Employee.user_sicil == '7019').first()
    if emp:
        print(f"Employee table - Name: {emp.first_name} {emp.last_name}, Title: {emp.title}, Dept: {emp.department}")
    ph = session.query(PerformanceHistory).filter(PerformanceHistory.sicil_no == '7019').first()
    if ph:
        print(f"PerformanceHistory table - Name: {ph.isim}, Title: {ph.unvan}, Dept: {ph.bolum}")
finally:
    session.close()

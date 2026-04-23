import pandas as pd
import logging
from sqlalchemy.orm import Session
from src.auth import get_db_session
from src.models import Employee, PerformanceHistory

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        pass
        
    def get_dropdown_options(self):
        """SQL'den benzersiz Çalışan isimlerini ve Hedef Türlerini çeker."""
        session = get_db_session()
        try:
            # Çalışan adlarını PerformanceHistory üzerinden çekiyoruz ki null değerler olmasın
            employees = session.query(PerformanceHistory.isim).distinct().all()
            target_types = session.query(PerformanceHistory.hedef_turu).distinct().all()
            
            employees_list = sorted([e[0] for e in employees if e[0]])
            target_list = sorted([t[0] for t in target_types if t[0]])
            return employees_list, target_list
        except Exception as e:
            logger.error(f"Seçenekleri SQL'den çekerken hata: {e}")
            return [], []
        finally:
            session.close()

    def get_employee_history(self, employee_name, target_type=None):
        """Seçilen çalışan ve hedef türü için SQL üzerinden geçmiş verileri tablo (DataFrame) olarak döner."""
        session = get_db_session()
        try:
            query = session.query(
                PerformanceHistory.sicil_no.label('Sicil'),
                PerformanceHistory.isim.label('İsim'),
                PerformanceHistory.bolum.label('Bölüm Ana Sorumluluk Alanı'),
                PerformanceHistory.unvan.label('Unvan'),
                PerformanceHistory.yil.label('Yıl'),
                PerformanceHistory.hedef_turu.label('Hedef Türü'),
                PerformanceHistory.yetkinlik.label('Yetkinlik'),
                PerformanceHistory.stratejik_hedef.label('Stratejik Hedef Tanımı'),
                PerformanceHistory.smart_hedef.label('SMART Hedef Tanımı'),
                PerformanceHistory.hedef_degeri.label('Hedef Değeri'),
                PerformanceHistory.birim.label('Birim'),
                PerformanceHistory.hedef_yonu.label('Hedef Yönü'),
                PerformanceHistory.gerceklesen_deger.label('Gerçekleşen Değer'),
                PerformanceHistory.sonuc.label('Gerçekleşen Değere Göre Sonuç')
            ).filter(PerformanceHistory.isim == employee_name)
            
            if target_type:
                query = query.filter(PerformanceHistory.hedef_turu == target_type)
                
            df = pd.read_sql(query.statement, session.bind)
            return df
        except Exception as e:
            logger.error(f"Geçmiş verileri çekerken hata: {e}")
            return pd.DataFrame()
        finally:
             session.close()

    def get_employee_metadata(self, employee_name):
        """Çalışanın kimlik bilgilerini (Unvan, Bölüm, Sicil) döner."""
        session = get_db_session()
        try:
            emp = session.query(PerformanceHistory).filter(PerformanceHistory.isim == employee_name).first()
            if emp:
                return {
                    "Sicil": emp.sicil_no,
                    "Unvan": emp.unvan,
                    "Bölüm Ana Sorumluluk Alanı": emp.bolum
                }
            return {}
        except Exception as e:
            logger.error(f"Metadata çekerken hata: {e}")
            return {}
        finally:
            session.close()

    def get_chunked_documents(self):
        """SQL'deki tüm performans kayıtlarını RAG için flat (düz) metin dokümanlarına (chunk) çevirir."""
        session = get_db_session()
        docs = []
        try:
            records = session.query(PerformanceHistory).all()
            for record in records:
                content = (
                    f"Çalışan: {record.isim} | Bölüm: {record.bolum} | Unvan: {record.unvan} | Yıl: {record.yil} | "
                    f"Hedef Türü: {record.hedef_turu} | ŞART Hedef (SMART): {record.smart_hedef} | "
                    f"Stratejik Hedef: {record.stratejik_hedef} | "
                    f"Hedeflenen: {record.hedef_degeri} {record.birim} | Gerçekleşen: {record.gerceklesen_deger} | "
                    f"Sonuç: {record.sonuc}"
                )
                docs.append({
                    "page_content": content,
                    "metadata": {
                        "source": "SQL_PerformanceHistory",
                        "employee": record.isim
                    }
                })
            return docs
        except Exception as e:
            logger.error(f"SQL verileri RAG için çekilemedi: {e}")
            return []
        finally:
            session.close()
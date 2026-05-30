import pandas as pd
import logging
import uuid
from sqlalchemy.orm import Session
import streamlit as st
from src.auth import get_db_session
from src.models import Employee, PerformanceHistory, ChatHistory, ChatSession, JobDescriptions

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        pass
        
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_dropdown_options():
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

    def get_exact_job_description(self, employee_title):
        """Çalışanın unvanına göre görev tanımını doğrudan SQL veritabanından çeker. Bulamazsa boş döner."""
        if not employee_title:
            return ""
            
        session = get_db_session()
        try:
            # Önce tam eşleşme ara
            jd = session.query(JobDescriptions).filter(JobDescriptions.position_name == employee_title).first()
            
            # Tam eşleşme yoksa, içerisinde kelime geçen ilk kaydı bul
            if not jd:
                jd = session.query(JobDescriptions).filter(JobDescriptions.position_name.ilike(f"%{employee_title}%")).first()
                
            # Genellenebilir Esnek Arama: İlk ve Son kelimeyi içerenleri bul (Örn: "Montaj Hattı Teknisyen" -> "Montaj" ve "Teknisyen")
            if not jd:
                words = employee_title.split()
                if len(words) >= 2:
                    ilk_kelime = words[0]
                    son_kelime = words[-1]
                    jd = session.query(JobDescriptions).filter(
                        JobDescriptions.position_name.ilike(f"%{ilk_kelime}%"),
                        JobDescriptions.position_name.ilike(f"%{son_kelime}%")
                    ).first()
                
            if jd:
                parts = []
                if jd.responsibilities: parts.append(f"Ana Sorumluluklar:\n{jd.responsibilities}")
                if jd.technical_requirements: parts.append(f"Teknik Gereksinimler:\n{jd.technical_requirements}")
                if jd.competencies: parts.append(f"Yetkinlikler:\n{jd.competencies}")
                return "\n\n".join(parts)
            return ""
        except Exception as e:
            logger.error(f"SQL Görev Tanımı çekerken hata: {e}")
            return ""
        finally:
            session.close()

    def get_logged_in_user_info(self, user_sicil):
        """Giriş yapan kullanıcının kimlik bilgilerini (İsim, Unvan, Bölüm, Sicil) döner."""
        session = get_db_session()
        try:
            # Önce Employee tablosunda ara
            emp = session.query(Employee).filter(Employee.user_sicil == user_sicil).first()
            if emp:
                return {
                    "Name": f"{emp.first_name} {emp.last_name}",
                    "Sicil": emp.user_sicil,
                    "Unvan": emp.title if emp.title else "Yönetici",
                    "Bölüm Ana Sorumluluk Alanı": emp.department if emp.department else "Yönetim"
                }
            
            # Yoksa PerformanceHistory tablosunda ara
            ph = session.query(PerformanceHistory).filter(PerformanceHistory.sicil_no == user_sicil).first()
            if ph:
                return {
                    "Name": ph.isim,
                    "Sicil": ph.sicil_no,
                    "Unvan": ph.unvan if ph.unvan else "Yönetici",
                    "Bölüm Ana Sorumluluk Alanı": ph.bolum if ph.bolum else "Yönetim"
                }
                
            return {
                "Name": "Yönetici",
                "Sicil": user_sicil,
                "Unvan": "Yönetici",
                "Bölüm Ana Sorumluluk Alanı": "Yönetim"
            }
        except Exception as e:
            logger.error(f"Giriş yapan kullanıcı bilgileri çekerken hata: {e}")
            return {
                "Name": "Yönetici",
                "Sicil": user_sicil,
                "Unvan": "Yönetici",
                "Bölüm Ana Sorumluluk Alanı": "Yönetim"
            }
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

    def create_chat_session(self, user_sicil, employee_sicil, target_type, title):
        """Yeni bir sohbet oturumu oluşturur ve ID'sini döner."""
        session = get_db_session()
        try:
            session_id = str(uuid.uuid4())
            new_session = ChatSession(
                id=session_id,
                user_sicil=user_sicil,
                employee_sicil=employee_sicil,
                target_type=target_type,
                title=title
            )
            session.add(new_session)
            session.commit()
            return session_id
        except Exception as e:
            logger.error(f"Sohbet oturumu oluşturulurken hata: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_chat_sessions(self, user_sicil, employee_sicil, target_type):
        """Seçili bağlamdaki geçmiş sohbet oturumlarını liste olarak döner."""
        session = get_db_session()
        try:
            records = session.query(ChatSession).filter(
                ChatSession.user_sicil == user_sicil,
                ChatSession.employee_sicil == employee_sicil,
                ChatSession.target_type == target_type
            ).order_by(ChatSession.updated_at.desc()).all()
            
            sessions = []
            for r in records:
                sessions.append({
                    "id": r.id,
                    "title": r.title,
                    "updated_at": r.updated_at
                })
            return sessions
        except Exception as e:
            logger.error(f"Sohbet oturumları çekilirken hata: {e}")
            return []
        finally:
            session.close()

    def save_chat_message(self, user_sicil, employee_sicil, target_type, role, content, session_id=None):
        """Yeni sohbet mesajını veritabanına kaydeder."""
        session = get_db_session()
        try:
            msg = ChatHistory(
                session_id=session_id,
                user_sicil=user_sicil,
                employee_sicil=employee_sicil,
                target_type=target_type,
                role=role,
                content=content
            )
            session.add(msg)
            
            # Oturumun güncellenme tarihini de yenile
            if session_id:
                chat_session = session.query(ChatSession).filter_by(id=session_id).first()
                if chat_session:
                    import datetime
                    chat_session.updated_at = datetime.datetime.now()
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Sohbet mesajı kaydedilirken hata: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_chat_history(self, session_id, limit=50):
        """Spesifik bir oturumdaki mesajları kronolojik sırada döner."""
        if not session_id:
            return []
            
        session = get_db_session()
        try:
            records = session.query(ChatHistory).filter(
                ChatHistory.session_id == session_id
            ).order_by(ChatHistory.created_at.desc()).limit(limit).all()
            
            # Kronolojik sıralama için (eskiden yeniye)
            records = reversed(records)
            
            history = []
            for r in records:
                history.append({
                    "role": r.role,
                    "content": r.content,
                    "timestamp": r.created_at
                })
            return history
        except Exception as e:
            logger.error(f"Sohbet geçmişi çekilirken hata: {e}")
            return []
        finally:
            session.close()

    def rename_chat_session(self, session_id, new_title):
        """Mevcut bir sohbet oturumunun başlığını (ismini) günceller."""
        if not session_id or not new_title:
            return False
            
        session = get_db_session()
        try:
            chat_session = session.query(ChatSession).filter_by(id=session_id).first()
            if chat_session:
                chat_session.title = new_title
                import datetime
                chat_session.updated_at = datetime.datetime.now()
                session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Sohbet oturumu adlandırılırken hata: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_chat_session(self, session_id):
        """Bir sohbet oturumunu ve o oturuma ait tüm mesajları kalıcı olarak siler."""
        if not session_id:
            return False
            
        session = get_db_session()
        try:
            session.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete(synchronize_session=False)
            session.query(ChatSession).filter(ChatSession.id == session_id).delete(synchronize_session=False)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Sohbet oturumu silinirken hata: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_team_performance_summary(self, allowed_sicils):
        """Yöneticinin ekibindeki çalışanların geçmiş performans skorlarını/risk durumlarını döner."""
        if not allowed_sicils:
            return pd.DataFrame()
            
        session = get_db_session()
        try:
            from src.models import PerformanceHistory, Employee
            emps = session.query(Employee).filter(Employee.user_sicil.in_(allowed_sicils)).all()
            
            data = []
            for emp in emps:
                records = session.query(PerformanceHistory.sonuc).filter(PerformanceHistory.sicil_no == emp.user_sicil).all()
                total = len(records)
                beklenen = 0
                ustunde = 0
                altinda = 0
                for r in records:
                    s = str(r[0]).strip().lower() if r[0] else ''
                    if s == 'beklenen': beklenen += 1
                    elif s == 'beklenenin üstünde': ustunde += 1
                    elif s == 'beklenenin altında': altinda += 1
                
                if total == 0:
                    status = "Beklemede"
                    score = 0.0
                else:
                    altinda_ratio = altinda / total
                    if altinda_ratio >= 0.33: # %33 ve daha fazla "altında" ise riskli
                        status = "Riskli"
                    else:
                        status = "İyi"
                    score = ((beklenen * 75) + (ustunde * 100) + (altinda * 25)) / total
                
                data.append({
                    "Sicil": emp.user_sicil,
                    "İsim": f"{emp.first_name} {emp.last_name}",
                    "Bölüm": emp.department,
                    "Unvan": emp.title,
                    "Performans Durumu": status,
                    "Performans Skoru": round(score, 1),
                    "Toplam Geçmiş Hedef": total
                })
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Ekip performans özeti çekerken hata: {e}")
            return pd.DataFrame()
        finally:
            session.close()

    def get_team_goal_assignment_stats(self, allowed_sicils):
        """Ekipteki hangi çalışanlara hedef atanmış verilerini döner."""
        if not allowed_sicils:
            return pd.DataFrame()
            
        session = get_db_session()
        try:
            from src.models import AnnualGoals, Employee
            emps = session.query(Employee).filter(Employee.user_sicil.in_(allowed_sicils)).all()
            
            data = []
            for emp in emps:
                # Kilitli aktif hedefler
                locked_goals = session.query(AnnualGoals).filter(
                    AnnualGoals.employee_sicil == emp.user_sicil,
                    AnnualGoals.is_locked == True,
                    AnnualGoals.approval_status != 'Passive'
                ).count()
                
                # Taslak hedefler
                draft_goals = session.query(AnnualGoals).filter(
                    AnnualGoals.employee_sicil == emp.user_sicil,
                    AnnualGoals.is_locked == False,
                    AnnualGoals.admin_approval_status != 'Reddedildi',
                    AnnualGoals.approval_status != 'Passive'
                ).count()
                
                data.append({
                    "Sicil": emp.user_sicil,
                    "Atanan Hedef Sayısı": locked_goals,
                    "Taslak Hedef Sayısı": draft_goals
                })
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Ekip hedef atama istatistikleri çekerken hata: {e}")
            return pd.DataFrame()
        finally:
            session.close()

    def get_approved_annual_goals(self, employee_sicil, target_type):
        """Çalışanın onaylanmış ve kilitli yeni yıl hedeflerini metin olarak döner."""
        if not employee_sicil:
            return "Çalışan kimliği bulunamadı."
            
        session = get_db_session()
        try:
            from src.models import AnnualGoals
            
            goals = session.query(AnnualGoals).filter(
                AnnualGoals.employee_sicil == employee_sicil,
                AnnualGoals.hedef_turu == target_type,
                AnnualGoals.approval_status != 'Passive',
                AnnualGoals.admin_approval_status.in_(['Onaylandı', 'Onay Bekliyor'])
            ).all()
            
            if not goals:
                return "Henüz onaylanmış veya kilitlenmiş bir yeni yıl hedefi bulunmuyor."
                
            result_text = "### ONAYLANAN YENİ YIL HEDEFLERİ:\n"
            for i, g in enumerate(goals, 1):
                status_str = "🔒 Kilitli" if g.is_locked else "⏳ Taslak"
                result_text += f"\nHedef {i} ({status_str}):\n"
                result_text += f"- SMART Hedef: {g.smart_hedef}\n"
                result_text += f"- Değer: {g.hedef_degeri} {g.birim} (Yön: {g.hedef_yonu})\n"
                result_text += f"- Gerekçe: {g.evidence_justification}\n"
            
            return result_text
        except Exception as e:
            logger.error(f"Onaylı hedefleri çekerken hata: {e}")
            return "Hedefler çekilirken bir veritabanı hatası oluştu."
        finally:
            session.close()
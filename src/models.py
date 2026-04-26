from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    """
    Kullanıcı hesapları ve hiyerarşik yönetici yapısını tutan tablo.
    """
    __tablename__ = 'users'
    
    sicil_no = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # Admin, Manager, Employee vb.
    is_active = Column(Boolean, default=True)
    force_password_change = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    
    # Hiyerarşik yapı için Manager Sicil bağlamı
    manager_sicil = Column(String, ForeignKey('users.sicil_no'), nullable=True)
    
    # Kendine bağlı ilişki (Self-referential)
    manager = relationship('User', remote_side=[sicil_no], backref='subordinates')
    
    # Bu kullanıcıya bağlı çalışan kayıtları (varsa)
    employees = relationship('Employee', back_populates='user')


class Employee(Base):
    """
    Çalışanların temel bilgilerini tutan tablo.
    """
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_sicil = Column(String, ForeignKey('users.sicil_no'), unique=True, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    title = Column(String)
    department = Column(String)
    email = Column(String, unique=True)
    
    # İlişkiler
    user = relationship('User', back_populates='employees')
    performance_history = relationship('PerformanceHistory', back_populates='employee')
    feedbacks = relationship('EmployeeFeedback', back_populates='employee')
    annual_goals = relationship('AnnualGoals', back_populates='employee')

class AnnualGoals(Base):
    """
    Gelecek yıl hedeflerinin kilitlendiği, AI tarafından üretilen yeni kayıtları tutar.
    """
    __tablename__ = 'annual_goals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_sicil = Column(String, ForeignKey('employees.user_sicil'), nullable=False)
    
    yil = Column(Integer, nullable=False)
    hedef_turu = Column(String, nullable=False)
    smart_hedef = Column(Text, nullable=False)
    hedef_degeri = Column(Float, nullable=True)
    birim = Column(String, nullable=True)
    evidence_justification = Column(Text, nullable=True)
    hedef_yonu = Column(String, default="Artan")
    
    is_locked = Column(Boolean, default=False)
    locked_by_sicil = Column(String, nullable=True)
    version_no = Column(Integer, default=1)
    
    # Yönetici Davranış Analizi (Telemetri)
    ai_status = Column(String, default="Kabul") # Kabul, Revize, Manuel
    decision_duration = Column(Integer, default=0) # saniye (max 3600)
    revision_depth = Column(Float, default=0.0) # 0.0 ile 100.0 arası yüzde
    regen_count = Column(Integer, default=0)
    chat_interaction_count = Column(Integer, default=0)
    
    # İlişki
    employee = relationship('Employee', back_populates='annual_goals')


class PerformanceHistory(Base):
    """
    Çalışanların performans hedeflerini ve geçmişini tutan tablo.
    """
    __tablename__ = 'performance_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    
    # Orijinal Excel Kolonları (Birebir Eşitlik İçin)
    sicil_no = Column(String)
    isim = Column(String)
    bolum = Column(String)
    unvan = Column(String)
    yil = Column(String)
    hedef_turu = Column(String)
    yetkinlik = Column(String)
    stratejik_hedef = Column(String)
    smart_hedef = Column(String)
    hedef_degeri = Column(String)
    birim = Column(String)
    hedef_yonu = Column(String)
    gerceklesen_deger = Column(String)
    sonuc = Column(String)
    
    # İlişkiler
    employee = relationship('Employee', back_populates='performance_history')


class JobDescriptions(Base):
    """
    Organizasyon şemasındaki rolleri ve gereksinimlerini tutan tablo.
    Yapay zeka bağlamını (context) zenginleştirmek amacıyla kullanılır.
    """
    __tablename__ = 'job_descriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_name = Column(String, unique=True, nullable=False)  # Örn: 'Kalite Mühendisi'
    responsibilities = Column(Text, nullable=True)               # Ana sorumluluklar
    technical_requirements = Column(Text, nullable=True)         # Aranan teknik yetkinlikler
    competencies = Column(Text, nullable=True)                   # Aranan sosyal/genel yetkinlikler


class EmployeeFeedback(Base):
    """
    Çalışanlara ait bireysel geri bildirimleri tutan tablo.
    Her çalışan ve her yıl için tek bir geniş satır (Wide Row) olarak derlenir.
    """
    __tablename__ = 'employee_feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_sicil = Column(String, ForeignKey('employees.user_sicil'), nullable=False)
    yil = Column(Integer, nullable=True)
    harf_notu = Column(String, nullable=True)
    genel_degerlendirme = Column(Text, nullable=True)
    guclu_alanlar = Column(Text, nullable=True)
    gelisim_alanlari = Column(Text, nullable=True)
    gelecek_beklentileri = Column(Text, nullable=True)

    # İlişkiler
    employee = relationship('Employee', back_populates='feedbacks')

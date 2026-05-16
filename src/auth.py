import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from src.config import Config
from src.models import User, Employee

@st.cache_resource
def get_engine():
    return create_engine(Config.DATABASE_URL)

def get_db_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

@st.cache_data(ttl=3600)
def get_allowed_sicil_list(current_user_sicil, current_user_role):
    """
    Rol (Admin/Manager/Employee) bazlı özyineli yetki listesi döndürür (Sicil dizisi).
    Her saat başı veya yetki değiştiğinde güncellenir.
    """
    if current_user_role == 'Employee':
        return [current_user_sicil]
        
    session = get_db_session()
    try:
        if current_user_role == 'Admin':
            all_users = session.query(User).all()
            return [u.sicil_no for u in all_users]
            
        elif current_user_role == 'Manager':
            allowed_sicils = set()
            to_check = [current_user_sicil]
            
            while to_check:
                cur = to_check.pop(0)
                if cur not in allowed_sicils:
                    allowed_sicils.add(cur)
                    subs = session.query(User).filter(User.manager_sicil == cur).all()
                    for sub_user in subs:
                        if sub_user.sicil_no not in allowed_sicils:
                            to_check.append(sub_user.sicil_no)
                            
            return list(allowed_sicils)
    finally:
        session.close()
        
    return []

def create_new_user(session, sicil_no, isim, role, manager_sicil=None):
    existing = session.query(User).filter(User.sicil_no == sicil_no).first()
    if existing:
        return False, "Bu sicil numarası zaten kullanımda."
        
    pwd_hash = generate_password_hash(f"{sicil_no}Pms2026!")
    new_user = User(
        sicil_no=sicil_no,
        password_hash=pwd_hash,
        role=role,
        manager_sicil=manager_sicil if manager_sicil else None,
        is_active=True,
        force_password_change=True
    )
    session.add(new_user)
    
    emp = session.query(Employee).filter(Employee.user_sicil == sicil_no).first()
    if not emp:
        parts = isim.strip().split()
        first_name = " ".join(parts[:-1]) if len(parts) > 1 else isim.strip()
        last_name = parts[-1] if len(parts) > 1 else ""
        new_emp = Employee(
            user_sicil=sicil_no,
            first_name=first_name,
            last_name=last_name
        )
        session.add(new_emp)
        
    session.commit()
    return True, "Kullanıcı başarıyla oluşturuldu."

def render_login_screen():
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>Stratejik PMS'e Hoş Geldiniz</h2>", unsafe_allow_html=True)
    
    if st.session_state.get('pending_password_change'):
        sicil = st.session_state['pending_password_change']
        st.markdown("<p style='text-align: center; color:red;'>Güvenliğiniz için lütfen yeni bir şifre belirleyin.</p>", unsafe_allow_html=True)
        with st.form("reset_pwd_form"):
            new_pwd1 = st.text_input("Yeni Şifre", type="password")
            new_pwd2 = st.text_input("Yeni Şifre (Tekrar)", type="password")
            submitted = st.form_submit_button("Şifreyi Güncelle")
            if submitted:
                if len(new_pwd1) < 6:
                    st.error("Şifre en az 6 karakter olmalıdır.")
                elif new_pwd1 != new_pwd2:
                    st.error("Şifreler eşleşmiyor.")
                else:
                    session = get_db_session()
                    user = session.query(User).filter(User.sicil_no == sicil).first()
                    if user:
                        user.password_hash = generate_password_hash(new_pwd1)
                        user.force_password_change = False
                        session.commit()
                        st.success("Şifreniz başarıyla güncellendi! Lütfen giriş yapın.")
                        del st.session_state['pending_password_change']
                    session.close()
                    st.rerun()
        return False

    st.markdown("<p style='text-align: center;'>Devam etmek için Sicil numaranız ve Şifreniz ile giriş yapın.</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Sicil No", placeholder="Örn: 99120")
        password = st.text_input("Şifre", type="password", placeholder="Şifrenizi girin")
        submitted = st.form_submit_button("Giriş Yap")
        
        if submitted:
            if not username or not password:
                st.error("Lütfen sicil numaranızı ve şifrenizi giriniz.")
                return False
                
            session = get_db_session()
            user = session.query(User).filter(User.sicil_no == username.strip()).first()
            
            if user and check_password_hash(user.password_hash, password):
                if hasattr(user, 'is_active') and getattr(user, 'is_active', True) is False:
                    st.error("Hesabınız pasif duruma getirilmiştir. Lütfen yönetici ile iletişime geçin.")
                    session.close()
                    return False
                    
                user.last_login = datetime.now()
                session.commit()

                if getattr(user, 'force_password_change', False):
                    st.session_state['pending_password_change'] = user.sicil_no
                    st.warning("Güvenliğiniz için şifrenizi yenilemeniz gerekmektedir.")
                    session.close()
                    st.rerun()
                    return False

                st.success("Giriş Başarılı! Hoş Geldiniz, yetkileriniz ayarlanıyor...")
                
                # Yetki hesaplaması
                allowed_sicils = get_allowed_sicil_list(user.sicil_no, user.role)
                
                st.session_state['user_id'] = user.sicil_no
                st.session_state['username'] = user.sicil_no
                st.session_state['role'] = user.role
                st.session_state['allowed_employees'] = allowed_sicils
                
                session.close()
                st.rerun()
            else:
                session.close()
                st.error("Hatalı Sicil No veya Şifre.")
                
    return 'user_id' in st.session_state

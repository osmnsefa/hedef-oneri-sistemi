import streamlit as st
import pandas as pd
from src.config import Config
from src.ui_components import load_custom_css, render_header, display_chat_message, render_dss_metrics, render_vision_card, render_devils_advocate_warning, render_vision_traceability
from src.analysis import Analyzer
from src.data_loader import DataLoader
from src.admin_panel import render_admin_dashboard

# Sayfa Ayarları (En başta olmalı)
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

load_custom_css()

# ==============================================================================
# CACHING
# ==============================================================================

@st.cache_resource(show_spinner="⚙️ Sistem başlatılıyor...")
def get_analyzer():
    return Analyzer()

@st.cache_data(ttl=600)
def load_metadata_cached():
    loader = DataLoader()
    return loader.get_dropdown_options()

@st.cache_data(ttl=600)
def load_history_cached(name, target):
    loader = DataLoader()
    return loader.get_employee_history(name, target)

@st.cache_data(ttl=600)
def load_employee_metadata_cached(name):
    loader = DataLoader()
    return loader.get_employee_metadata(name)

# ==============================================================================
# UYGULAMA BAŞLATMA
# ==============================================================================

analyzer = get_analyzer()

# Session State
def init_session():
    defaults = {
        "chat_history": [],      # [(user_msg, bot_msg), ...]
        "last_analysis": None,
        "current_goal_set": None,
        "proposed_patch": None,
        "eval_result": None,
        "perf_res": None,
        "active_employee": "",
        "active_target": "",
        "decoded_vision": None,
        "active_session_id": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

from src.auth import render_login_screen

init_session()

# ==============================================================================
# VERİTABANI BAŞLATMA (DB BOŞSA SEED + OTOMATİK MİGRASYON)
# ==============================================================================
from src.auth import get_db_session, get_engine
from src.models import User
import logging
from sqlalchemy import text

try:
    _sys_sess = get_db_session()
    
    # Tablo var mı ve dolu mu kontrolü
    needs_seed = False
    try:
        if not _sys_sess.query(User).first():
            needs_seed = True
    except Exception:
        # Tablo yoksa 'no such table' hatası fırlatır, seed gerekir.
        needs_seed = True
        
    if needs_seed:
        logging.info("Veritabanı boş veya tablolar eksik, ilk kurulum (seed) yapılıyor...")
        from seed import run_seed
        run_seed()

    # ── OTOMATİK KOLON MİGRASYONU ──────────────────────────────────────────
    # Supabase'deki annual_goals tablosuna yeni eklenen kolonları kontrol et.
    # Kolon yoksa ekle (idempotent — defalarca çalışsa sorun olmaz).
    try:
        _engine = get_engine()
        with _engine.connect() as _conn:
            # PostgreSQL: information_schema ile kolon varlığını kontrol et
            _result = _conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'annual_goals' 
                  AND column_name = 'hedef_yonu'
            """))
            if _result.fetchone() is None:
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN hedef_yonu VARCHAR DEFAULT 'Artan'"))
                _conn.commit()
                logging.info("✅ Migration: 'hedef_yonu' kolonu annual_goals tablosuna eklendi.")
                
            _result_vision = _conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'annual_goals' 
                  AND column_name = 'vision_text'
            """))
            if _result_vision.fetchone() is None:
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN vision_text TEXT"))
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN vision_ambition_level VARCHAR"))
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN vision_stretch_factor FLOAT"))
                _conn.commit()
                logging.info("✅ Migration: Vizyon kolonları (vision_text, vision_ambition_level, vision_stretch_factor) annual_goals tablosuna eklendi.")
                
            _result_rev = _conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'annual_goals' 
                  AND column_name = 'employee_note'
            """))
            if _result_rev.fetchone() is None:
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN employee_note TEXT"))
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN approval_status VARCHAR DEFAULT 'Locked'"))
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN parent_goal_id INTEGER"))
                _conn.commit()
                logging.info("✅ Migration: Revizyon kolonları (employee_note, approval_status, parent_goal_id) annual_goals tablosuna eklendi.")
                
            _result_admin = _conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'annual_goals' 
                  AND column_name = 'admin_approval_status'
            """))
            if _result_admin.fetchone() is None:
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN admin_approval_status VARCHAR DEFAULT 'Onay Bekliyor'"))
                _conn.execute(text("ALTER TABLE annual_goals ADD COLUMN denetim_loglari JSON"))
                _conn.commit()
                logging.info("✅ Migration: Admin denetim kolonları (admin_approval_status, denetim_loglari) annual_goals tablosuna eklendi.")
                
    except Exception as _mig_err:
        logging.warning(f"Migration kontrolü sırasında uyarı (büyük ihtimalle kolon zaten var): {_mig_err}")
        
    try:
        from src.models import ChatHistory, ChatSession
        ChatSession.__table__.create(_engine, checkfirst=True)
        ChatHistory.__table__.create(_engine, checkfirst=True)
        
        with _engine.connect() as _conn:
            _result_ch = _conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'chat_history' AND column_name = 'session_id'"))
            if _result_ch.fetchone() is None:
                _conn.execute(text("ALTER TABLE chat_history ADD COLUMN session_id VARCHAR"))
                _conn.commit()
                logging.info("✅ Migration: 'session_id' kolonu chat_history tablosuna eklendi.")
                
        logging.info("✅ Migration: 'chat_history' ve 'chat_sessions' tabloları kontrol edildi/oluşturuldu.")
    except Exception as _mig_err2:
        logging.warning(f"Migration kontrolü sırasında uyarı (chat_history/sessions): {_mig_err2}")
    # ────────────────────────────────────────────────────────────────────────

    _sys_sess.close()
except Exception as e:
    logging.error(f"Veritabanı başlatma hatası: {e}")


# ==============================================================================
# LOGIN KONTROLÜ
# ==============================================================================
if 'user_id' not in st.session_state:
    is_logged_in = render_login_screen()
    if not is_logged_in:
        st.stop()

# Veri Yükle
employees_list, target_types_list = load_metadata_cached()

if 'allowed_employees' in st.session_state:
    allowed_sicils = st.session_state['allowed_employees']
    from src.auth import get_db_session
    from src.models import Employee
    
    session = get_db_session()
    allowed_emps = session.query(Employee).filter(Employee.user_sicil.in_(allowed_sicils)).all()
    allowed_names = [f"{e.first_name} {e.last_name}".strip() for e in allowed_emps]
    session.close()

    employees_list = [emp for emp in employees_list if emp in allowed_names]

# ==============================================================================
# SIDEBAR
# ==============================================================================

with st.sidebar:
    current_role = st.session_state.get('role', '')
    
    if current_role == 'Admin':
        st.markdown("""
        <div style="padding: 0.5rem 0 1rem 0;">
            <h2 style="font-size:1.3rem; font-weight:800; margin:0; color:white;">🛡️ Admin Paneli</h2>
            <p style="font-size:0.78rem; color:rgba(255,255,255,0.5); margin:0.2rem 0 0 0;">Sistem yönetimi</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("🚪 Çıkış Yap", width='stretch', type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        st.markdown("""
        <div style="padding: 0.5rem 0 1rem 0;">
            <h2 style="font-size:1.3rem; font-weight:800; margin:0; color:white;">🎛️ Kontrol Paneli</h2>
            <p style="font-size:0.78rem; color:rgba(255,255,255,0.5); margin:0.2rem 0 0 0;">Parametreleri seçin</p>
        </div>
        """, unsafe_allow_html=True)

        # Çalışan Seçimi
        if employees_list:
            emp_index = 0
            if st.session_state.get('active_employee') in employees_list:
                emp_index = employees_list.index(st.session_state.get('active_employee'))
            employee_name = st.selectbox("Çalışan", employees_list, index=emp_index)
        else:
            employee_name = st.text_input("Çalışan Adı Soyadı", value=st.session_state.get('active_employee', ''), placeholder="Örn: Ahmet Yılmaz")
            st.warning("Çalışan listesi çekilemedi.")

        # Hedef Kategorisi
        default_targets = ["Satış & Pazarlama", "Yazılım Geliştirme", "Operasyonel Verimlilik"]
        options = target_types_list if target_types_list else default_targets
        t_index = 0
        if st.session_state.get('active_target') in options:
            t_index = options.index(st.session_state.get('active_target'))
        target_type = st.selectbox("Hedef Kategorisi", options, index=t_index)

        # Chat kısıtlaması için aktif oturumu senkronize et
        if (st.session_state.active_employee != employee_name or
                st.session_state.active_target != target_type):
            st.session_state.active_employee = employee_name
            st.session_state.active_target = target_type
            
            # Geçmişi DB'den yükle
            st.session_state.chat_history = []
            st.session_state.active_session_id = None
            if employee_name and target_type:
                emp_meta = load_employee_metadata_cached(employee_name)
                e_sicil = emp_meta.get("Sicil") if emp_meta else None
                u_sicil = st.session_state.get('user_id')
                if e_sicil and u_sicil:
                    from src.data_loader import DataLoader
                    loader = DataLoader()
                    sessions = loader.get_chat_sessions(u_sicil, e_sicil, target_type)
                    if sessions:
                        st.session_state.active_session_id = sessions[0]['id']
                        st.session_state.chat_history = loader.get_chat_history(st.session_state.active_session_id)

            st.session_state.current_goal_set = None
            st.session_state.proposed_patch = None
            st.session_state.eval_result = None
            st.session_state.perf_res = None
            st.session_state.regen_count = 0
            st.session_state.chat_interaction_count = 0
            st.session_state.ai_start_time = None
            st.session_state.original_goal_set = None
            st.session_state.decoded_vision = None

        st.markdown("---")
        st.markdown("### 💬 Sohbet Oturumları")
        
        u_sicil = st.session_state.get('user_id')
        emp_meta = load_employee_metadata_cached(employee_name) if employee_name else None
        e_sicil = emp_meta.get("Sicil") if emp_meta else None
        
        from src.data_loader import DataLoader
        loader = DataLoader()
        
        sessions = []
        if u_sicil and e_sicil and target_type:
            sessions = loader.get_chat_sessions(u_sicil, e_sicil, target_type)
            
        if st.button("➕ Yeni Sohbet"):
            st.session_state.active_session_id = None
            st.session_state.chat_history = []
            st.session_state.current_goal_set = None
            st.rerun()
            
        if sessions:
            for s in sessions:
                btn_label = f"📝 {s['title']} ({s['updated_at'].strftime('%d.%m %H:%M')})"
                if st.session_state.get('active_session_id') == s['id']:
                    btn_label = f"🟢 {s['title']}"
                    
                if st.button(btn_label, key=f"sess_{s['id']}", use_container_width=True):
                    st.session_state.active_session_id = s['id']
                    st.session_state.chat_history = loader.get_chat_history(s['id'])
                    st.session_state.current_goal_set = None
                    st.rerun()
        else:
            st.info("Henüz geçmiş sohbet yok.")

        manager_vision = st.text_area(
            "Yönetici Vizyonu",
            placeholder="Örn: Global pazarda %15 büyüme hedeflerken çalışan memnuniyetini de en üst düzeyde tutmak...",
            height=140
        )

        st.markdown("---")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("♻️ Oturumu Temizle"):
                for key in ["chat_history", "current_goal_set", "proposed_patch",
                            "eval_result", "perf_res", "last_analysis", "decoded_vision"]:
                    st.session_state[key] = None if key != "chat_history" else []
                st.rerun()
        with col_s2:
            if st.button("🔄 Veri İndeksle"):
                with st.spinner("İndeksleniyor..."):
                    try:
                        analyzer.vector_store.refresh_data()
                        load_metadata_cached.clear()
                        load_history_cached.clear()
                        load_employee_metadata_cached.clear()
                        st.success("✅ Veriler güncellendi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")

        st.markdown("---")
        if st.button("🚪 Çıkış Yap", width='stretch', type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        if st.button("🧹 Önbellek & Sistem Sıfırla", width='stretch'):
            st.cache_resource.clear()
            st.cache_data.clear()
            for key in ["chat_history", "current_goal_set", "proposed_patch",
                        "eval_result", "perf_res", "last_analysis", "decoded_vision"]:
                st.session_state[key] = None if key != "chat_history" else []
            st.success("Sistem sıfırlandı!")
            st.rerun()

        st.markdown(f"""
        <p style='text-align:center; color:rgba(255,255,255,0.3); font-size:0.72rem; margin-top:1rem;'>
            Engine v{getattr(analyzer, 'version', '—')}
        </p>
        """, unsafe_allow_html=True)

# Admin değilse değişkenlerin tanımlı olduğundan emin ol
if current_role != 'Admin':
    pass  # employee_name, target_type, manager_vision sidebar bloğunda tanımlandı
else:
    employee_name = ""
    target_type = ""
    manager_vision = ""

# ==============================================================================
# ANA SAYFA — ROLE GÖRE AYRIŞIM
# ==============================================================================

current_role = st.session_state.get('role', '')

# ---- ADMIN: Sadece Admin Dashboard ----
if current_role == 'Admin' and not st.session_state.get('force_chat_view', False):
    render_admin_dashboard()
    st.stop()

# ---- DİĞER ROLLER: Normal Çalışan/Yönetici Arayüzü ----

# Çalışan metadata'sını yükle
employee_metadata = {}
if employee_name:
    employee_metadata = load_employee_metadata_cached(employee_name)

render_header(
    employee_name=employee_name,
    target_type=target_type,
    metadata=employee_metadata
)

metadata_ctx_parts = [f"Çalışan: {employee_name}"]
if employee_metadata:
    for k, v in employee_metadata.items():
        if v:
            metadata_ctx_parts.append(f"{k}: {v}")
metadata_ctx_parts.append(f"Hedef Kategorisi: {target_type}")
metadata_context_str = " | ".join(metadata_ctx_parts)

is_employee_locked = False
emp_sicil_for_lock = employee_metadata.get('Sicil') if employee_metadata else None

if emp_sicil_for_lock and target_type:
    
    if st.session_state.get('force_chat_view', False):
        if st.button("🔙 Admin Paneline Dön"):
            st.session_state.force_chat_view = False
            st.rerun()

    try:
        from src.auth import get_db_session
        from src.models import AnnualGoals
        _lsess = get_db_session()
        _locked_rec = _lsess.query(AnnualGoals).filter(
            AnnualGoals.employee_sicil == emp_sicil_for_lock,
            AnnualGoals.hedef_turu == target_type,
            AnnualGoals.is_locked == True
        ).first()
        if _locked_rec:
            is_employee_locked = True
        _lsess.close()
    except Exception:
        pass

is_disabled_by_lock = is_employee_locked if current_role != 'Admin' else False

tab1, tab2, tab3, tab4 = st.tabs(["💬 Asistan", "📌 Hedef Süreci", "🔍 Performans Analizi", "📁 Atanan Hedefler"])

# ====================== TAB 1: CHAT ASISTAN ======================
with tab1:
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        border: 1px solid #bae6fd;
        border-radius: 12px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 1rem;
    ">
        <p style="margin:0; font-size:1rem; color:#0369a1; font-weight:600;">
            🔒 <b>Kısıtlı Oturum:</b> Bu asistan yalnızca
            <b>{employee_name}</b> çalışanına ait <b>{target_type}</b>
            verilerine erişebilir. Diğer çalışan ve kategoriler hakkında bilgi paylaşmaz.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Geçmiş mesajları göster (silinmez, kalıcı)
    chat_placeholder = st.container()
    with chat_placeholder:
        for msg in st.session_state.chat_history:
            if isinstance(msg, dict):
                display_chat_message(msg.get("role"), msg.get("content"), msg.get("timestamp"))
            elif isinstance(msg, tuple) and len(msg) == 2:
                display_chat_message("user", msg[0])
                display_chat_message("bot", msg[1])

    # Yeni mesaj girişi
    if prompt := st.chat_input(f"{employee_name} hakkında soru sorun..."):
        # Kullanıcı mesajını hemen göster
        display_chat_message("user", prompt)

        with st.spinner("Yanıt üretiliyor..."):
            response = analyzer.chat_with_data(
                message=prompt,
                history=st.session_state.chat_history,
                employee_name=employee_name,
                target_type=target_type,
                metadata_context=metadata_context_str,
                current_goal_set=st.session_state.current_goal_set
            )
            
            # Telemetry: Chat etkileşimi artır. (Sistem AI hakkında chat ederse)
            if st.session_state.get('current_goal_set'):
                st.session_state.chat_interaction_count += 1

        # Bot yanıtını göster
        display_chat_message("bot", response)

        # DB'ye kaydet ve Geçmişe ekle (dict olarak)
        u_sicil = st.session_state.get('user_id')
        e_sicil = employee_metadata.get('Sicil') if employee_metadata else None
        
        import datetime
        now = datetime.datetime.now()
        
        st.session_state.chat_history.append({"role": "user", "content": prompt, "timestamp": now})
        st.session_state.chat_history.append({"role": "bot", "content": response, "timestamp": now})
        
        if u_sicil and e_sicil:
            from src.data_loader import DataLoader
            loader = DataLoader()
            
            if not st.session_state.get('active_session_id'):
                title = prompt[:25] + "..." if len(prompt) > 25 else prompt
                new_session_id = loader.create_chat_session(u_sicil, e_sicil, target_type, title)
                st.session_state.active_session_id = new_session_id
                
            sess_id = st.session_state.get('active_session_id')
            loader.save_chat_message(u_sicil, e_sicil, target_type, "user", prompt, session_id=sess_id)
            loader.save_chat_message(u_sicil, e_sicil, target_type, "bot", response, session_id=sess_id)

        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Sohbeti Temizle", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()

# ====================== TAB 2: HEDEF SÜRECİ ======================
with tab2:

    # 1. BASELINE OLUŞTURMA
    if not st.session_state.current_goal_set:
        if is_employee_locked:
            st.error("🔒 Bu çalışanın bu kategorideki hedefleri KESİNLEŞTİRİLMİŞ(Kilitli)'tir. (Değişiklik yapamazsınız)")
        
        st.info("Henüz aktif bir hedef seti yok. Yönetici vizyonunu girin ve **'✨ Hedef Setini Başlat'** butonuna basın.")

        if not manager_vision:
            st.warning("⚠️ Soldan yönetici vizyonunu doldurun.")

        if st.button("✨ Hedef Öner", use_container_width=True,
                     disabled=is_disabled_by_lock or not (employee_name and manager_vision)):
            with st.spinner(f"🤖 {employee_name} için 3 SMART hedef oluşturuluyor..."):
                history_df = load_history_cached(employee_name, target_type)
                history_text = history_df.to_markdown(index=False) if not history_df.empty else "Sayısal veri yok."
                
                # --- NEW LOGIC: VİZYON ÇÖZÜMLEME ---
                decoded_vision = analyzer.vision_decoder.decode(manager_vision)
                st.session_state.decoded_vision = decoded_vision
                
                goal_set = analyzer.analyze_and_suggest(employee_name, target_type, manager_vision, history_text, decoded_vision=decoded_vision)
                
                # Telemetry Initialize
                import time, copy
                st.session_state.ai_start_time = time.time()
                st.session_state.regen_count += 1
                st.session_state.chat_interaction_count = 0
                st.session_state.original_goal_set = copy.deepcopy(goal_set)
                
                st.session_state.current_goal_set = goal_set
                
                # Uretilen hedefleri asistan sekmesine de düşür
                if goal_set and "error" not in goal_set:
                    bot_msg = f"Sizin için **{target_type}** kategorisinde hedefler ürettim:\n\n"
                    bot_msg += analyzer.format_goal_set(goal_set)
                    bot_msg += "\n\nBu hedefler hakkında konuşmak veya revizyon istemek için bana sorular sorabilirsiniz."
                    
                    user_prompt_txt = "Bu çalışan için hedef önerir misin?"
                    u_sicil = st.session_state.get('user_id')
                    e_sicil = employee_metadata.get('Sicil') if employee_metadata else None
                    import datetime
                    now = datetime.datetime.now()
                    st.session_state.chat_history.append({"role": "user", "content": user_prompt_txt, "timestamp": now})
                    st.session_state.chat_history.append({"role": "bot", "content": bot_msg, "timestamp": now})
                    
                    if u_sicil and e_sicil:
                        from src.data_loader import DataLoader
                        loader = DataLoader()
                        
                        if not st.session_state.get('active_session_id'):
                            title = f"{target_type} Hedefleri"
                            new_session_id = loader.create_chat_session(u_sicil, e_sicil, target_type, title)
                            st.session_state.active_session_id = new_session_id
                            
                        sess_id = st.session_state.get('active_session_id')
                        loader.save_chat_message(u_sicil, e_sicil, target_type, "user", user_prompt_txt, session_id=sess_id)
                        loader.save_chat_message(u_sicil, e_sicil, target_type, "bot", bot_msg, session_id=sess_id)
                    
                st.rerun()

    else:
        gs = st.session_state.current_goal_set

        if "error" in gs:
            st.error(f"Hedef seti üretilemedi: {gs.get('error')}")
            if st.button("🔁 Tekrar Dene"):
                st.session_state.current_goal_set = None
                st.rerun()
        else:
            # Karar Destek Sistemi (DSS) ve Risk Metrikleri
            history_df = load_history_cached(employee_name, target_type)
            suggested_goals_text = " ".join([g.get('smart_goal', '') for g in gs.get('goals', [])])
            dss_metrics = analyzer.get_decision_support_metrics(history_df, suggested_goals_text)
            
            # --- VİZYON KARTI VE DEVIL'S ADVOCATE UYARISI ---
            decoded_vision = st.session_state.get('decoded_vision')
            if decoded_vision:
                with st.sidebar:
                    render_vision_card(decoded_vision)
                
                da_result = analyzer.devils_advocate.evaluate(
                    decoded_vision,
                    dss_metrics.get("success_probability", 65),
                    dss_metrics.get("risk_score", 50)
                )
                render_devils_advocate_warning(da_result)

            st.markdown(analyzer.format_goal_set(gs))

            if decoded_vision:
                render_vision_traceability(gs, decoded_vision)

            with st.expander("📊 Karar Destek Sistemi (Açıklanabilir YZ)", expanded=True):
                render_dss_metrics(dss_metrics, employee_name)

            st.markdown("---")
            col_act1, col_act2, col_act3 = st.columns(3)

            with col_act1:
                if st.button("🔍 Uygunluk Değerlendir", type="secondary"):
                    with st.spinner("Analiz ediliyor..."):
                        eval_res = analyzer.evaluate_goals(gs, employee_name, dss_metrics.get("risk_score"))
                        st.session_state.eval_result = eval_res

            with col_act2:
                if st.button("✏️ Revizyon İste", use_container_width=True, disabled=is_disabled_by_lock):
                    st.session_state.show_revision_input = True

            with col_act3:
                if st.button("✅ Onayla & Kilitle", type="primary", use_container_width=True):
                    st.session_state.current_goal_set["status"] = "ACTIVE"
                    
                    # AI Telemetri: Onaylanan hedefleri DB'ye işaretle
                    try:
                        from src.auth import get_db_session
                        from src.models import PerformanceHistory
                        _sess = get_db_session()
                        _records = _sess.query(PerformanceHistory).filter(
                            PerformanceHistory.isim == employee_name
                        ).all()
                        for _r in _records:
                            _r.is_ai_suggested = 'True'
                            _r.ai_status = 'TAM_KABUL'
                        _sess.commit()
                        _sess.close()
                    except Exception as _e:
                        pass  # Telemetri hatası ana akışı durdurmasın
                    
                    st.success("✅ Hedef Seti onaylandı ve ACTIVE olarak işaretlendi.")

            # Değerlendirme Sonucu
            if st.session_state.eval_result:
                er = st.session_state.eval_result
                if "error" in er:
                    st.error(f"Değerlendirme üretilemedi: {er.get('error')}")
                    if st.button("Tekrar Dene"):
                        st.session_state.eval_result = None
                        st.rerun()
                else:
                    with st.expander("📊 Sistem Değerlendirmesi", expanded=True):
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            st.metric("Uygunluk", "✅ Uygun" if er.get("is_appropriate") else "⚠️ Riskli")
                        with col_e2:
                            st.metric("Risk Skoru (DSS)", f"%{dss_metrics.get('risk_score', '?')}")
                        st.write(f"**Analiz:** {er.get('analysis', '-')}")
                        for s in er.get("improvement_suggestions", []):
                            st.write(f"- {s}")
                        if st.button("Kapat"):
                            st.session_state.eval_result = None
                            st.rerun()

            # Revizyon Girişi
            if st.session_state.get("show_revision_input"):
                st.markdown("---")
                feedback = st.text_area(
                    "Yönetici Geri Bildirimi",
                    placeholder="Örn: Hedef 1'deki rakam çok agresif, %15'e çekelim."
                )
                col_rev1, col_rev2 = st.columns(2)
                with col_rev1:
                    if st.button("🚀 Revizyon Önerisi Üret", type="primary"):
                        if not feedback.strip():
                            st.error("Lütfen revizyon için bir geri bildirim girin.")
                        else:
                            with st.spinner("Patch hazırlanıyor..."):
                                patch = analyzer.revise_goals(gs, feedback)
                                st.session_state.proposed_patch = patch
                                del st.session_state.show_revision_input
                                st.rerun()
                with col_rev2:
                    if st.button("İptal Et"):
                        del st.session_state.show_revision_input
                        st.rerun()

            # Patch Onay / Red
            if st.session_state.proposed_patch:
                st.info("Sistem bir revizyon (PATCH) önerdi. Lütfen aşağıdan inceleyip onaylayın.")
                st.markdown(analyzer.format_patch(st.session_state.proposed_patch, gs))
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    if st.button("✔️ Revizyonu Onayla"):
                        patch = st.session_state.proposed_patch
                        for ch in patch.get("changes", []):
                            idx = ch.get("goal_index", 0)
                            field = ch.get("field", "")
                            new_val = ch.get("new_value")
                            if idx < len(gs["goals"]):
                                if field == "title":
                                    gs["goals"][idx]["title"] = new_val
                                elif field == "smart_goal":
                                    gs["goals"][idx]["smart_goal"] = new_val
                                elif "metrics.target_value" in field:
                                    gs["goals"][idx]["metrics"]["target_value"] = new_val
                        gs["version"] = patch.get("proposed_version", gs.get("version", 1) + 1)
                        gs["status"] = "ÖNERİLEN"
                        st.session_state.current_goal_set = gs
                        st.session_state.proposed_patch = None
                        
                        # AI Telemetri: (Tarihi verilere değil, memory'de tutulacak çünkü AnnualGoals'da kaydedilecek)

                        
                        # Revize edilen hedefi chat'e at
                        bot_msg = f"Hedefleriniz geri bildiriminiz doğrultusunda revize edildi (v{gs['version']}).\n\n"
                        bot_msg += analyzer.format_goal_set(gs)
                        
                        user_prompt_txt = "Verdiğim geri bildirimi uygulayarak hedefleri revize et."
                        u_sicil = st.session_state.get('user_id')
                        e_sicil = employee_metadata.get('Sicil') if employee_metadata else None
                        import datetime
                        now = datetime.datetime.now()
                        st.session_state.chat_history.append({"role": "user", "content": user_prompt_txt, "timestamp": now})
                        st.session_state.chat_history.append({"role": "bot", "content": bot_msg, "timestamp": now})
                        
                        if u_sicil and e_sicil:
                            from src.data_loader import DataLoader
                            loader = DataLoader()
                            
                            if not st.session_state.get('active_session_id'):
                                title = f"{target_type} Revizyonu"
                                new_session_id = loader.create_chat_session(u_sicil, e_sicil, target_type, title)
                                st.session_state.active_session_id = new_session_id
                                
                            sess_id = st.session_state.get('active_session_id')
                            loader.save_chat_message(u_sicil, e_sicil, target_type, "user", user_prompt_txt, session_id=sess_id)
                            loader.save_chat_message(u_sicil, e_sicil, target_type, "bot", bot_msg, session_id=sess_id)
                        
                        st.success("✅ Versiyon güncellendi!")
                        st.rerun()
                with col_p2:
                    if st.button("❌ Revizyonu Reddet"):
                        st.session_state.proposed_patch = None
                        st.rerun()

        # Kesinleştir Button
        if current_role in ['Manager', 'Admin'] and not is_employee_locked:
            st.markdown("---")
            if emp_sicil_for_lock and st.session_state['user_id'] == emp_sicil_for_lock:
                st.warning("⚠️ Kendi hedeflerinizi kesinleştiremezsiniz. Sadece yöneticiniz onaylayabilir.")
            else:
                if st.button("🔒 Tüm Hedefleri Kesinleştir (Kilitle)", type="primary"):
                    try:
                        from src.auth import get_db_session
                        from src.models import AnnualGoals
                        import datetime
                        _lsess = get_db_session()
                        
                        # --- TELEMETRY CALCULATIONS ---
                        import time
                        import difflib
                        
                        duration = 0
                        if st.session_state.get('ai_start_time'):
                            duration = int(time.time() - st.session_state.ai_start_time)
                            duration = min(duration, 3600)  # Max 1 hour outlier clamp
                            
                        # 1. Eski AnnualGoals kayıtlarını pasife çek (aynı sicil+kategori için)
                        old_goals = _lsess.query(AnnualGoals).filter(
                            AnnualGoals.employee_sicil == emp_sicil_for_lock,
                            AnnualGoals.hedef_turu == target_type,
                            AnnualGoals.approval_status != 'Passive'
                        ).all()
                        for og in old_goals:
                            og.approval_status = 'Passive'
                            og.is_locked = False
                        
                        # 2. Yeni hedefleri insert et
                        gs_data = st.session_state.current_goal_set
                        current_year = datetime.datetime.now().year + 1
                        
                        for idx, g in enumerate(gs_data.get("goals", [])):
                            metric_val = str(g.get('metrics', {}).get('target_value', '0')).replace(',', '.')
                            try:
                                metric_float = float(metric_val)
                            except:
                                metric_float = 0.0
                                
                            # Text diff
                            orig_text = ""
                            if st.session_state.get('original_goal_set') and len(st.session_state.original_goal_set.get("goals", [])) > idx:
                                orig_text = st.session_state.original_goal_set["goals"][idx].get("smart_goal", "")
                                
                            final_text = g.get('smart_goal', '')
                            
                            diff_pct = 0.0
                            if orig_text and final_text:
                                similarity = difflib.SequenceMatcher(None, orig_text, final_text).ratio()
                                diff_pct = (1.0 - similarity) * 100.0
                                
                            ai_status = "Manuel"
                            if st.session_state.get('original_goal_set'):
                                ai_status = "Kabul" if diff_pct == 0.0 else "Revize"
                                
                            decoded_v = st.session_state.get('decoded_vision', {})
                                
                            new_goal = AnnualGoals(
                                employee_sicil=emp_sicil_for_lock,
                                yil=current_year,
                                hedef_turu=target_type,
                                smart_hedef=final_text,
                                hedef_degeri=metric_float,
                                birim=g.get('metrics', {}).get('unit', ''),
                                evidence_justification=g.get('evidence_justification', 'Gerekçe Yok'),
                                hedef_yonu=g.get('metrics', {}).get('direction', 'Artan'),
                                is_locked=True,
                                approval_status='Locked',
                                parent_goal_id=st.session_state.get('revision_parent_goal_id'),
                                locked_by_sicil=st.session_state.get('user_id'),
                                version_no=gs_data.get("version", 1),
                                ai_status=ai_status,
                                decision_duration=duration,
                                revision_depth=diff_pct,
                                regen_count=st.session_state.get('regen_count', 0),
                                chat_interaction_count=st.session_state.get('chat_interaction_count', 0),
                                vision_text=manager_vision,
                                vision_ambition_level=decoded_v.get("ambition_level"),
                                vision_stretch_factor=decoded_v.get("stretch_factor")
                            )
                            _lsess.add(new_goal)
                            
                        _lsess.commit()
                        _lsess.close()
                        
                        st.cache_data.clear() # Cache invalidation
                        
                        # Revizyon durumunu temizle
                        st.session_state.revision_parent_goal_id = None
                        
                        st.success(f"✅ {employee_name} için {target_type} hedefleri KİLİTLENDİ.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Kilit uygulanamadı: {e}")
        elif current_role == 'Admin' and is_employee_locked:
            st.markdown("---")
            if st.button("🔓 Kilidi Aç (Sadece Admin)"):
                try:
                    from src.auth import get_db_session
                    from src.models import AnnualGoals
                    _lsess = get_db_session()
                    _records = _lsess.query(AnnualGoals).filter(
                        AnnualGoals.employee_sicil == emp_sicil_for_lock,
                        AnnualGoals.hedef_turu == target_type
                    ).all()
                    for _r in _records:
                        _r.is_locked = False
                    _lsess.commit()
                    _lsess.close()
                    st.cache_data.clear() # Cache invalidation
                    st.success(f"🔓 {employee_name} için {target_type} hedefleri açıldı.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Kilit Açılamadı: {e}")

# ====================== TAB 3: PERFORMANS ANALİZİ ======================
with tab3:
    st.write(f"**{employee_name}** için `{target_type}` kategorisinde derinlemesine performans ve yetkinlik analizi.")

    if st.button("📊 Analizi Başlat", use_container_width=True):
        with st.spinner("🔍 Analiz ediliyor..."):
            history_df = load_history_cached(employee_name, target_type)
            history_text = history_df.to_markdown(index=False) if not history_df.empty else ""
            res = analyzer.analyze_performance(employee_name, target_type, history_text)
            st.session_state.perf_res = res

    if st.session_state.perf_res:
        st.markdown("---")
        st.markdown(st.session_state.perf_res)

        st.markdown("---")
        if st.button("⚠️ Risk Faktörleri Analizi (Gelişmiş)"):
            with st.spinner("Risk senaryoları analiz ediliyor..."):
                history_df = load_history_cached(employee_name, target_type)
                history_text = history_df.to_markdown(index=False) if not history_df.empty else "Sayısal veri yok."
                risk_res = analyzer.analyze_risk_factors(employee_name, target_type, history_text)
                st.markdown("### ⚠️ Risk Analiz Sonuçları")
                st.markdown(risk_res)

    with st.expander("💾 Ham Performans Verileri", expanded=False):
        if employee_name:
            history_df = load_history_cached(employee_name, target_type)
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True)
            else:
                st.info("Bu çalışan ve kategori için geçmiş veri bulunamadı.")

# ====================== TAB 4: ATANAN HEDEFLER ======================
with tab4:
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border: 1px solid #86efac;
        border-radius: 12px;
        padding: 0.9rem 1.4rem;
        margin-bottom: 1.2rem;
    ">
        <p style="margin:0; font-size:1rem; color:#15803d; font-weight:700;">
            📁 <b>Atanan & Kesinleşmiş Hedefler</b> — {employee_name if employee_name else '—'}
        </p>
        <p style="margin:0.2rem 0 0 0; font-size:0.82rem; color:#166534;">
            Aşağıdaki hedefler yönetici tarafından onaylanmış ve sisteme kalıcı olarak kaydedilmiştir.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not emp_sicil_for_lock:
        st.warning("⚠️ Hedefleri görüntülemek için önce sol menüden geçerli bir çalışan seçin.")
    else:
        try:
            from src.auth import get_db_session
            from src.models import AnnualGoals, Employee
            import datetime as _dt
            import pandas as _pd

            _asess = get_db_session()
            _all_locked = _asess.query(AnnualGoals).filter(
                AnnualGoals.employee_sicil == emp_sicil_for_lock,
                AnnualGoals.is_locked == True,
                AnnualGoals.approval_status != 'Passive'
            ).order_by(AnnualGoals.yil.desc(), AnnualGoals.hedef_turu).all()

            if not _all_locked:
                st.info("Bu çalışana ait kesinleştirilmiş hedef bulunmamaktadır. Hedef Süreci sekmesinden yeni hedef oluşturup onaylayabilirsiniz.")
            else:
                def has_chat_history(g):
                    logs = getattr(g, 'denetim_loglari', [])
                    if isinstance(logs, str):
                        import json
                        try: logs = json.loads(logs)
                        except: logs = []
                    return bool(logs)

                _onaylananlar = [g for g in _all_locked if g.admin_approval_status == 'Onaylandı']
                _onay_bekleyenler = [g for g in _all_locked if g.admin_approval_status != 'Onaylandı' and not has_chat_history(g)]
                _sohbet_edilenler = [g for g in _all_locked if g.admin_approval_status != 'Onaylandı' and has_chat_history(g)]
                
                # ── Özet metrik kartları ──────────────────────────────────────
                _total = len(_all_locked)
                _artan = sum(1 for g in _all_locked if getattr(g, 'hedef_yonu', 'Artan') == 'Artan')
                _azalan = _total - _artan
                _mc1, _mc2, _mc3 = st.columns(3)
                _mc1.metric("📌 Toplam Kilitli Hedef", _total)
                _mc2.metric("⬆️ Artan Hedefler", _artan)
                _mc3.metric("⬇️ Azalan Hedefler", _azalan)
                st.markdown("---")

                tab_onay_bekleyen, tab_sohbet, tab_onay = st.tabs([
                    f"Onay Bekleyenler ({len(_onay_bekleyenler)})", 
                    f"Revizyon Bekleyenler ({len(_sohbet_edilenler)})", 
                    f"Onaylanan Hedefler ({len(_onaylananlar)})"
                ])
                
                _export_rows = []
                
                def render_goals_table(goals_list, is_approved_tab):
                    if not goals_list:
                        st.info("Bu sekmede gösterilecek hedef bulunmuyor.")
                        return
                        
                    # ── Excel görünümlü tablo ─────────────────────────────────────
                    # Başlık satırı
                    _hc = st.columns([0.4, 1.2, 0.8, 2.8, 0.7, 0.7, 0.5, 0.5])
                    _headers = ["Yıl", "Tür", "Yön", "SMART Hedef", "Önceki", "Hedef", "Değişim", "İşlem"]
                    for _h, _col in zip(_headers, _hc):
                        _col.markdown(f'<div class="excel-table-header">{_h}</div>', unsafe_allow_html=True)
    
                    for _goal in goals_list:
                        _yil = _goal.yil
                        _tur = _goal.hedef_turu
                        _yon = getattr(_goal, 'hedef_yonu', 'Artan')
                        _arrow = "⬆️" if _yon == "Artan" else "⬇️"
                        _smart = _goal.smart_hedef or "—"
                        _hedef_val = _goal.hedef_degeri
    
                        # Önceki değeri geçmiş tablosundan çek
                        _prev_val = "—"
                        try:
                            _hist = load_history_cached(employee_name, _tur)
                            if not _hist.empty:
                                _prev_col = next((c for c in _hist.columns if 'gerçekleşen' in c.lower() or 'gerceklesen' in c.lower()), None)
                                if _prev_col:
                                    _prev_val = _hist[_prev_col].dropna().iloc[-1] if not _hist[_prev_col].dropna().empty else "—"
                        except Exception:
                            pass
    
                        # Değişim oranı hesapla
                        _change_str = "—"
                        try:
                            _p = float(str(_prev_val).replace(',', '.'))
                            _t = float(str(_hedef_val).replace(',', '.'))
                            if _p != 0:
                                _chg = ((_t - _p) / abs(_p)) * 100
                                _sign = "▲" if _chg >= 0 else "▼"
                                _change_str = f"{_sign} %{abs(_chg):.1f}"
                        except Exception:
                            pass
    
                        _rc = st.columns([0.4, 1.2, 0.8, 2.8, 0.7, 0.7, 0.5, 0.5])
                        _rc[0].markdown(f'<div class="excel-table-row">{_yil}</div>', unsafe_allow_html=True)
                        _rc[1].markdown(f'<div class="excel-table-row">{_tur}</div>', unsafe_allow_html=True)
                        _rc[2].markdown(f'<div class="excel-table-row">{_arrow} {_yon}</div>', unsafe_allow_html=True)
                        _rc[3].markdown(f'<div class="excel-table-row">{_smart}</div>', unsafe_allow_html=True)
                        _rc[4].markdown(f'<div class="excel-table-row">{_prev_val}</div>', unsafe_allow_html=True)
                        _rc[5].markdown(f'<div class="excel-table-row"><b>{_hedef_val}</b></div>', unsafe_allow_html=True)
                        _rc[6].markdown(f'<div class="excel-table-row">{_change_str}</div>', unsafe_allow_html=True)
                        with _rc[7]:
                            if current_role != 'Employee':
                                if st.button("🗑️", key=f"tab4_del_{_goal.id}", help="Bu hedefi kalıcı olarak sil"):
                                    _asess.delete(_goal)
                                    _asess.commit()
                                    st.success(f"✅ Hedef silindi.")
                                    st.rerun()
    
                        # Çalışan Notu & İtiraz Bloğu
                        if current_role == 'Employee':
                            if getattr(_goal, 'approval_status', 'Locked') == 'Locked':
                                with st.expander(f"💬 {_tur} Hedefine Görüş Bildir"):
                                    with st.form(f"feedback_form_{_goal.id}"):
                                        f_note = st.text_area("İtiraz / Geri Bildiriminiz", placeholder="Örn: Bu hedef değeri piyasa koşullarında ulaşılabilir değil...")
                                        f_submit = st.form_submit_button("Gönder")
                                        if f_submit and f_note:
                                            _goal.employee_note = f_note
                                            _goal.approval_status = 'Feedback_Received'
                                            _asess.commit()
                                            st.success("Geri bildiriminiz yöneticiye iletildi!")
                                            st.rerun()
                            elif getattr(_goal, 'approval_status', 'Locked') == 'Feedback_Received':
                                st.info(f"⏳ İtirazınız yönetici onayında: {_goal.employee_note}")
                        else: # Manager or Admin
                            if getattr(_goal, 'approval_status', 'Locked') == 'Feedback_Received':
                                st.warning(f"💬 Çalışan İtirazı: {_goal.employee_note}")
                                    
                        # Admin Stratejik Denetim Bloğu (Yöneticiler için)
                        if current_role in ['Manager', 'Admin']:
                            admin_status = getattr(_goal, 'admin_approval_status', 'Onay Bekliyor')
                            if not is_approved_tab or admin_status == 'Onaylandı':
                                st.markdown("---")
                                with st.expander(f"🛡️ Admin Denetim Durumu: {admin_status}"):
                                    logs = getattr(_goal, 'denetim_loglari', [])
                                    if isinstance(logs, str):
                                        import json
                                        try: logs = json.loads(logs)
                                        except: logs = []
                                    if not logs: logs = []
                                    
                                    if logs:
                                        for log in logs:
                                            role_icon = "🛡️ Admin" if log.get('role') == 'Admin' else "👔 Yönetici"
                                            ts = log.get('timestamp', '')
                                            if ts:
                                                try: ts = ts.split('.')[0]
                                                except: pass
                                            st.markdown(f"**{role_icon}** 🕒 `{ts}`\n> {log.get('content')}")
                                    else:
                                        st.caption("Henüz bir iletişim kaydı yok.")
                                        
                                    if current_role == 'Manager' and not is_approved_tab:
                                        with st.form(f"manager_audit_form_{_goal.id}"):
                                            mgr_msg = st.text_area("Admin'e Yanıt Yaz", placeholder="Örn: Bu hedef revizyon isteğine istinaden düzenlendi.")
                                            if st.form_submit_button("Gönder"):
                                                if mgr_msg.strip():
                                                    import datetime
                                                    now_str = datetime.datetime.now().isoformat()
                                                    new_log = {"role": "Manager", "content": mgr_msg.strip(), "timestamp": now_str}
                                                    if isinstance(logs, list):
                                                        logs.append(new_log)
                                                    else:
                                                        logs = [new_log]
                                                    _goal.denetim_loglari = list(logs)
                                                    from sqlalchemy.orm.attributes import flag_modified
                                                    flag_modified(_goal, "denetim_loglari")
                                                    _goal.admin_approval_status = 'Onay Bekliyor'
                                                    _asess.commit()
                                                    st.success("Mesajınız Admin'e iletildi.")
                                                    st.rerun()
    
                        _export_rows.append({
                            "Yıl": _yil, "Hedef Türü": _tur, "Yön": _yon,
                            "SMART Hedef": _smart, "Önceki Değer": _prev_val,
                            "Hedef Değeri": _hedef_val, "Değişim": _change_str,
                            "Kilitleyen": _goal.locked_by_sicil
                        })

                with tab_onay_bekleyen:
                    render_goals_table(_onay_bekleyenler, is_approved_tab=False)
                    
                with tab_sohbet:
                    render_goals_table(_sohbet_edilenler, is_approved_tab=False)
                    
                with tab_onay:
                    render_goals_table(_onaylananlar, is_approved_tab=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── CSV İndirme ───────────────────────────────────────────────
                _df_exp = _pd.DataFrame(_export_rows)
                _csv_exp = _df_exp.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📄 Tüm Hedefleri Dışa Aktar (CSV)",
                    data=_csv_exp,
                    file_name=f"{_dt.datetime.now().strftime('%Y%m%d')}_{emp_sicil_for_lock}_atanan_hedefler.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            _asess.close()
        except Exception as _tab4_err:
            st.error(f"Hedefler yüklenirken hata oluştu: {_tab4_err}")
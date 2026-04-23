import streamlit as st

def load_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ===== ANA ARKA PLAN ===== */
        .stApp {
            background-color: #f0f4f9;
        }

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e3a5f 0%, #162d4a 100%);
            border-right: none;
        }
        section[data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stTextArea label,
        section[data-testid="stSidebar"] .stTextInput label {
            color: #94a3b8 !important;
            font-size: 0.82rem;
            font-weight: 500;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        /* Sidebar Input Alanları */
        section[data-testid="stSidebar"] .stSelectbox > div > div,
        section[data-testid="stSidebar"] .stTextArea textarea,
        section[data-testid="stSidebar"] .stTextInput input {
            background-color: #1a2f4a !important;
            border: 1px solid rgba(255,255,255,0.4) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        /* Focus durumu için */
        section[data-testid="stSidebar"] .stTextArea textarea:focus,
        section[data-testid="stSidebar"] .stTextInput input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 1px #3b82f6 !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.12) !important;
        }

        /* ===== BUTONLAR ===== */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.6rem 1.2rem;
            border: none;
            transition: all 0.25s ease;
            box-shadow: 0 2px 8px rgba(37,99,235,0.3);
            width: 100%;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(135deg, #1d4ed8, #1e40af);
            box-shadow: 0 4px 16px rgba(37,99,235,0.45);
            transform: translateY(-1px);
        }
        div.stButton > button:first-child:active {
            transform: translateY(0px);
        }

        /* ===== SEKMELEr ===== */
        .stTabs [data-baseweb="tab-list"] {
            background-color: transparent;
            border-bottom: 2px solid #e2e8f0;
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            font-weight: 600;
            color: #64748b;
            padding: 0.6rem 1.2rem;
            transition: all 0.2s;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
        }

        /* ===== CHAT ===== */
        .chat-container {
            background-color: #ffffff;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            padding: 1.5rem;
            margin-top: 1rem;
        }
        .user-message {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: #ffffff;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            margin: 8px 0 8px auto;
            max-width: 80%;
            font-size: 0.93rem;
            line-height: 1.5;
            box-shadow: 0 2px 8px rgba(37,99,235,0.25);
        }
        .bot-message {
            background-color: #f8fafc;
            color: #334155;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            margin: 8px auto 8px 0;
            border: 1px solid #e2e8f0;
            max-width: 85%;
            font-size: 0.93rem;
            line-height: 1.5;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }

        /* ===== METRİK KARTLARI ===== */
        [data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: box-shadow 0.2s;
        }
        [data-testid="metric-container"]:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }

        /* ===== INFO / WARNING / SUCCESS ===== */
        .stAlert {
            border-radius: 12px;
        }

        /* ===== EXPANDER ===== */
        .streamlit-expanderHeader {
            background-color: #f8fafc;
            border-radius: 10px;
            font-weight: 600;
            color: #334155;
        }

        /* ===== DATAFRAME ===== */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }

        /* ===== CHAT INPUT ===== */
        .stChatInput > div {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            transition: border-color 0.2s;
        }
        .stChatInput > div:focus-within {
            border-color: #2563eb;
        }

        /* ===== GENEL DÜZEN ===== */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* ===== BAŞLIKLAR ===== */
        h1, h2, h3 {
            color: #0f172a;
            font-weight: 700;
        }
        h3 {
            margin-top: 1.2rem;
        }

        /* ===== SEPARATOR ===== */
        hr {
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 1.5rem 0;
        }

        /* ===== SPINNER ===== */
        .stSpinner > div {
            border-top-color: #2563eb !important;
        }
    </style>
    """, unsafe_allow_html=True)


def render_header(employee_name="", target_type="", metadata=None):
    """Uygulamanın üst banner'ını render eder."""
    subtitle = "Yapay Zeka Destekli Yeni Nesil Performans Yönetim Sistemi"

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 60%, #3b82f6 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 24px rgba(37,99,235,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <h1 style="color:#ffffff; font-size:2rem; margin:0; font-weight:800; letter-spacing:-0.5px;">
                🚀 Stratejik PMS
            </h1>
            <p style="color:rgba(255,255,255,0.75); font-size:0.95rem; margin:0.3rem 0 0 0; font-weight:400;">
                {subtitle}
            </p>
        </div>
        <div style="text-align:right;">
            <div style="
                background: rgba(255,255,255,0.15);
                border-radius: 12px;
                padding: 0.8rem 1.4rem;
                backdrop-filter: blur(10px);
                border: 2px solid rgba(255,255,255,0.4);
            ">
                <p style="color:rgba(255,255,255,0.8); font-size:0.8rem; margin:0; font-weight:600; text-transform:uppercase; letter-spacing:0.06em;">Aktif Oturum</p>
                <p style="color:#ffffff; font-size:1.3rem; margin:0.2rem 0 0.1rem 0; font-weight:900; display:flex; align-items:center; justify-content:flex-end; gap:8px;">
                    <span>{employee_name if employee_name else "—"}</span>
                    {f'<span style="background-color: #3b82f6; color: #ffffff; font-size: 0.65rem; padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2);">{metadata.get("Bölüm Ana Sorumluluk Alanı")}</span>' if metadata and metadata.get("Bölüm Ana Sorumluluk Alanı") else ''}
                </p>
                <p style="color:rgba(255,255,255,0.8); font-size:0.85rem; margin:0; font-weight:500;">
                    {target_type if target_type else "Hedef seçilmedi"}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metadata bilgileri (varsa) kartlar halinde göster
    if metadata and isinstance(metadata, dict) and len(metadata) > 0:
        meta_cols = st.columns(len(metadata))
        labels = {
            "Sicil": "🪪 Sicil No",
            "Unvan": "👔 Unvan",
            "Bölüm Ana Sorumluluk Alanı": "🏢 Bölüm",
        }
        for col, (key, val) in zip(meta_cols, metadata.items()):
            with col:
                st.metric(label=labels.get(key, key), value=str(val) if val else "—")


def display_chat_message(role, message):
    if role == "user":
        st.markdown(f'<div class="user-message">👤 <b>Siz:</b><br>{message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-message">🤖 <b>Asistan:</b><br>{message}</div>', unsafe_allow_html=True)

def render_dss_metrics(metrics, employee_name=""):
    """Karar Destek Sistemi (DSS) metriklerini görselleştirir."""
    if not metrics:
        return

    title_name = f"{employee_name} için " if employee_name else ""
    st.markdown(f"### 🧠 {title_name}Stratejik Karar Desteği\n", unsafe_allow_html=True)
    
    # --- 1. SATIR: DÖRT KOLONLU METRİKLER ---
    c1, c2, c3, c4 = st.columns(4)
    
    # Başarı Olasılığı
    with c1:
        prob = metrics.get('success_probability', 65)
        color = "#16a34a" if prob >= 70 else ("#f59e0b" if prob >= 40 else "#dc2626")
        label = "Yüksek Güven" if prob >= 70 else ("Orta Güven" if prob >= 40 else "Düşük Güven")
        st.markdown(f"""
        <div style="padding:0;">
            <p style="color:#475569; font-size:0.8rem; font-weight:700; margin:0;">🎯 BAŞARI</p>
            <h2 style="color:#0f172a; margin:0; font-size:1.8rem; font-weight:800;">%{prob}</h2>
            <p style="color:{color}; font-size:0.75rem; font-weight:600; margin:0;">Güven: %{prob}</p>
        </div>
        """, unsafe_allow_html=True)

    # Bölüm Uyumu (Benchmark)
    with c2:
        bench = metrics.get('benchmark_status', '')
        # Basit ayrıştırma (Örn: "Bölüm Ortalamasının +%5 Üzerinde")
        st.markdown(f"""
        <div style="padding:0;">
            <p style="color:#475569; font-size:0.8rem; font-weight:700; margin:0;">📈 BÖLÜM UYUMU</p>
            <p style="color:#475569; font-size:0.85rem; font-weight:500; margin:0.2rem 0; line-height:1.2;">{bench}</p>
            <p style="color:#16a34a; font-size:0.75rem; font-weight:600; margin:0;">Üst Segment</p>
        </div>
        """, unsafe_allow_html=True)

    # Risk Skoru
    with c3:
        risk = metrics.get('risk_score', 50)
        r_level = "Düşük" if risk < 40 else ("Orta/Yüksek" if risk < 75 else "Kritik")
        st.markdown(f"""
        <div style="padding:0;">
            <p style="color:#475569; font-size:0.8rem; font-weight:700; margin:0;">⚠️ RİSK SKORU</p>
            <h2 style="color:#0f172a; margin:0; font-size:1.8rem; font-weight:800;">%{risk}</h2>
            <p style="color:#64748b; font-size:0.75rem; font-weight:600; margin:0;">Seviye: {r_level}</p>
        </div>
        """, unsafe_allow_html=True)

    # Gelişim / Yetkinlik
    with c4:
        st.markdown(f"""
        <div style="padding:0;">
            <p style="color:#475569; font-size:0.8rem; font-weight:700; margin:0;">🚀 GELİŞİM</p>
            <p style="color:#475569; font-size:0.75rem; font-weight:500; margin:0.2rem 0; line-height:1.2;">{metrics.get('skill_impact', 'Belirlenemedi.')}</p>
            <p style="color:#16a34a; font-size:0.75rem; font-weight:600; margin:0;">Pozitif Katkı</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:1.5rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # --- 2. SATIR: STRATEJİK ODAK ---
    st.markdown("### 🎯 Stratejik Odak ve Detay Analizi\n", unsafe_allow_html=True)
    
    align = metrics.get('strategic_alignment', {})
    values = align.get("values", {})
    descriptions = align.get("descriptions", {})
    
    col_str1, col_str2 = st.columns(2)
    
    keys = list(values.keys())
    if len(keys) >= 4:
        with col_str1:
            st.markdown(f"**{keys[0]} %{values[keys[0]]}**")
            st.markdown(f"<p style='color:#64748b; font-size:0.85rem;'>💡 {descriptions.get(keys[0], '')}</p>", unsafe_allow_html=True)
            st.markdown(f"**{keys[2]} %{values[keys[2]]}**")
            st.markdown(f"<p style='color:#64748b; font-size:0.85rem;'>💡 {descriptions.get(keys[2], '')}</p>", unsafe_allow_html=True)

        with col_str2:
            st.markdown(f"**{keys[1]} %{values[keys[1]]}**")
            st.markdown(f"<p style='color:#64748b; font-size:0.85rem;'>💡 {descriptions.get(keys[1], '')}</p>", unsafe_allow_html=True)
            st.markdown(f"**{keys[3]} %{values[keys[3]]}**")
            st.markdown(f"<p style='color:#64748b; font-size:0.85rem;'>💡 {descriptions.get(keys[3], '')}</p>", unsafe_allow_html=True)

def render_locked_goals(employee_sicil):
    """Kilitlenmiş hedefleri Streamlit üzerinde kart yapısı ile listeler ve indirme butonu sunar."""
    from src.auth import get_db_session
    from src.models import AnnualGoals, Employee
    import datetime
    import pandas as pd

    st.markdown("### 🔒 Kesinleşmiş (Kilitli) Hedefler", unsafe_allow_html=True)
    
    session = get_db_session()
    try:
        locked_goals = session.query(AnnualGoals).filter(
            AnnualGoals.employee_sicil == employee_sicil,
            AnnualGoals.is_locked == True
        ).all()
        
        emp = session.query(Employee).filter(Employee.user_sicil == employee_sicil).first()
        employee_name = f"{emp.first_name} {emp.last_name}" if emp else employee_sicil
        
        if not locked_goals:
            st.info(f"Kilitlenmiş herhangi bir hedef bulunmamaktadır.")
            return

        # Listeleme
        report_data = []
        for goal in locked_goals:
            with st.expander(f"📌 {goal.yil} | {goal.hedef_turu} - {goal.smart_hedef[:40]}...", expanded=False):
                st.markdown(f"**Hedef Türü:** {goal.hedef_turu}")
                st.markdown(f"**SMART Hedef:** {goal.smart_hedef}")
                justify_text = goal.evidence_justification if goal.evidence_justification else "Gerekçe belirtilmedi."
                st.markdown(f"**Kanıt/Gerekçe:** {justify_text}")
                
                locked_by_str = goal.locked_by_sicil if goal.locked_by_sicil else "Belirtilmemiş"
                st.markdown(f"**Kesinleştiren Yönetici (Sicil):** {locked_by_str}")
                
            report_data.append({
                "Tarih": datetime.datetime.now().strftime("%Y-%m-%d"),
                "İsim": employee_name,
                "Sicil No": employee_sicil,
                "Yıl": goal.yil,
                "Hedef Türü": goal.hedef_turu,
                "SMART Hedef": goal.smart_hedef,
                "Gerekçe": justify_text,
                "Kesinleştiren": locked_by_str
            })
            
        # Rapor İndirme
        df = pd.DataFrame(report_data)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📄 Yıllık Hedef Raporu Üret (CSV)",
            data=csv,
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_{employee_sicil}_Kesinlesmis_Hedefler.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Kilitli hedefler yüklenirken hata oluştu: {e}")
    finally:
        session.close()

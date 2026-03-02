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
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
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
                padding: 0.6rem 1.2rem;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.25);
            ">
                <p style="color:rgba(255,255,255,0.7); font-size:0.75rem; margin:0; font-weight:500; text-transform:uppercase; letter-spacing:0.06em;">Aktif Oturum</p>
                <p style="color:#ffffff; font-size:1rem; margin:0.2rem 0 0 0; font-weight:700;">
                    {employee_name if employee_name else "—"}
                </p>
                <p style="color:rgba(255,255,255,0.65); font-size:0.8rem; margin:0;">
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

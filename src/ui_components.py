import streamlit as st

def load_custom_css():
    st.markdown("""
    <style>
        /* Ana Arka Plan ve Fontlar */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar Tasarımı */
        section[data-testid="stSidebar"] {
            background-color: #f8fafc;
            border-right: 1px solid #e2e8f0;
        }
        
        /* Başlıklar */
        h1, h2, h3 {
            color: #0f172a;
            font-weight: 700;
        }
        
        /* Kart Tasarımları */
        div.stButton > button:first-child {
            background-color: #2563eb;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.75rem 1rem;
            border: none;
            transition: all 0.2s;
            width: 100%;
        }
        
        div.stButton > button:first-child:hover {
            background-color: #1d4ed8;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        div.stButton > button:active {
            background-color: #1e40af;
        }

        /* İkincil Buton (Verileri Yenile vs.) */
        button[type="secondary"] {
            background-color: #ffffff;
            color: #475569;
            border: 1px solid #cbd5e1;
        }

        /* Chat Mesajları */
        .user-message {
            background-color: #eff6ff;
            color: #1e3a8a;
            padding: 15px;
            border-radius: 12px 12px 0 12px;
            margin: 10px 0 10px auto;
            text-align: right;
            border: 1px solid #bfdbfe;
            max-width: 85%;
        }
        
        .bot-message {
            background-color: white;
            color: #334155;
            padding: 15px;
            border-radius: 12px 12px 12px 0;
            margin: 10px auto 10px 0;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            max-width: 90%;
        }

        /* Genel Düzen İyileştirmeleri */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Input Alanları */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border-color: #e2e8f0;
        }
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border-color: #e2e8f0;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem; padding: 2rem; background: linear-gradient(to right, #eff6ff, #ffffff); border-radius: 16px; border: 1px solid #e0f2fe;">
        <h1 style="color: #1e40af; font-size: 2.5rem; margin-bottom: 0.5rem;">🚀 Stratejik PMS</h1>
        <p style="color: #64748b; font-size: 1.1rem; font-weight: 500;">Yapay Zeka Destekli Yeni Nesil Performans Yönetimi</p>
    </div>
    """, unsafe_allow_html=True)

def display_chat_message(role, message):
    if role == "user":
        st.markdown(f'<div class="user-message">👤 <b>Siz:</b><br>{message}</div>', unsafe_allow_html=True)
    else:
        # Markdown içeriğini desteklemek için st.markdown içinde HTML kullanımı bazen sorun olabilir
        # Ama basit metinler için sorun yok. Karmaşık markdown için st.chat_message daha iyi olabilir.
        # Biz burada HTML container içinde markdown render edemeyiz kolayca.
        # O yüzden hibrit bir yapı kullanacağız.
        st.markdown(f'<div class="bot-message">🤖 <b>Asistan:</b><br>{message}</div>', unsafe_allow_html=True)

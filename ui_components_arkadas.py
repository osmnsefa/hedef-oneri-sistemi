import streamlit as st

def load_custom_css():
    st.markdown("""
    <style>
        /* Ana Arka Plan ve Fontlar */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            background-color: #fcfcfd;
        }
        
        /* Sidebar Tasarımı */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #f1f5f9;
        }
        
        /* Başlıklar */
        h1, h2, h3 {
            color: #1e293b;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        
        /* Kart Tasarımları */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.8rem 1.2rem;
            border: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            width: 100%;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
            text-transform: none;
        }
        
        div.stButton > button:first-child:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3);
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        }
        
        div.stButton > button:active {
            transform: translateY(0);
        }

        /* Chat Mesajları */
        .user-message {
            background: linear-gradient(135deg, #f0f7ff 0%, #e0effe 100%);
            color: #1e40af;
            padding: 1.25rem;
            border-radius: 16px 16px 4px 16px;
            margin: 1rem 0 1rem auto;
            border: 1px solid #dbeafe;
            max-width: 85%;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.05);
        }
        
        .bot-message {
            background-color: #ffffff;
            color: #334155;
            padding: 1.25rem;
            border-radius: 16px 16px 16px 4px;
            margin: 1rem auto 1rem 0;
            border: 1px solid #f1f5f9;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
            max-width: 90%;
        }

        /* Tabs Tasarımı */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px;
            white-space: pre-wrap;
            background-color: #f1f5f9;
            border-radius: 8px;
            color: #64748b;
            font-weight: 500;
            border: none;
            padding: 0 20px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #2563eb !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown("""
    <div style="margin: 0 0 1.5rem 0; text-align: center; padding: 0.5rem 2rem; background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%); border-radius: 12px; border: 1px solid #e0f2fe; box-shadow: 0 4px 12px rgba(30, 64, 175, 0.05);">
        <h1 style="color: #1e40af; font-size: 1.5rem; margin: 0; display: inline-block; vertical-align: middle;">🚀 Stratejik PMS</h1>
        <span style="color: #94a3b8; margin: 0 15px; font-weight: 300;">|</span>
        <span style="color: #64748b; font-size: 0.9rem; font-weight: 500; vertical-align: middle;">AI Destekli Performans Analiz ve Karar Motoru</span>
    </div>
    """, unsafe_allow_html=True)

def display_chat_message(role, message):
    if role == "user":
        st.markdown(f'<div class="user-message">👤 <b>Siz:</b><br>{message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-message">🤖 <b>Asistan:</b><br>{message}</div>', unsafe_allow_html=True)

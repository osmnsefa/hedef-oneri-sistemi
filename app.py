import streamlit as st
import pandas as pd
from src.config import Config
from src.ui_components import load_custom_css, render_header
from src.analysis import Analyzer
from src.data_loader import DataLoader
import os

# Sayfa Ayarları (En başta olmalı)
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS'i yükle
load_custom_css()

# --- OPTİMİZASYON VE CACHING ---

@st.cache_resource(show_spinner="Sistem Başlatılıyor...")
def get_analyzer():
    """Analyzer sınıfını önbelleğe alır. (VectorStore ve LLM bağlantısı tek sefer yapılır)"""
    return Analyzer()

@st.cache_data(ttl=600)  # 10 dakika önbellekte tut
def load_metadata_cached():
    """Dropdown verilerini önbelleğe alır."""
    loader = DataLoader()
    return loader.get_dropdown_options()

@st.cache_data(ttl=600)
def load_history_cached(name, target):
    """Geçmiş verileri önbelleğe alır."""
    loader = DataLoader() # DataLoader hafif olduğu için burada tekrar instance alınabilir
    return loader.get_employee_history(name, target)

# --- UYGULAMA MANTIĞI ---

# Analyzer'ı al (Cached Resource)
analyzer = get_analyzer()

# Session State Başlatma
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_analysis" not in st.session_state: # Hata almamak için opsiyonel başlatma
    st.session_state.last_analysis = None

# Metadata Yükle (Cached Data)
employees_list, target_types_list = load_metadata_cached()

# Yan Menü (Sidebar)
with st.sidebar:
    st.title("🎛️ Kontrol Paneli")
    st.markdown("---")
    
    # Çalışan Seçimi
    if employees_list:
        employee_name = st.selectbox("Çalışan Adı Soyadı", employees_list)
    else:
        employee_name = st.text_input("Çalışan Adı Soyadı", placeholder="Örn: Ahmet Yılmaz")
        if not employees_list:
            st.warning("Excel dosyasından çalışan listesi çekilemedi.")
    
    # Hedef Kategorisi
    default_targets = ["Satış & Pazarlama", "Yazılım Geliştirme", "Operasyonel Verimlilik"]
    options = target_types_list if target_types_list else default_targets
    target_type = st.selectbox("Hedef Kategorisi", options)
    
    manager_vision = st.text_area(
        "Yönetici Vizyonu (Kuzey Yıldızı)",
        placeholder="Örn: Global pazarda %15 büyüme hedeflerken, çalışan memnuniyetini de maksimum seviyede tutmak...",
        height=150
    )
    
    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("♻️ Temizle"):
             st.session_state.chat_history = []
             st.session_state.last_analysis = None
             st.rerun()
    with col_s2:
        if st.button("🔄 Veri İndeksle"):
            with st.spinner("İndeksleniyor..."):
                try:
                    analyzer.vector_store.refresh_data()
                    load_metadata_cached.clear() # Cache temizle
                    st.success("Tamamlandı!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")

# Ana Sayfa Düzeni
render_header()

# İki Kolonlu Yapı
main_col1, main_col2 = st.columns([4, 6], gap="medium")

with main_col1:
    st.markdown("### 🎯 Stratejik Hedef Sihirbazı")
    st.info("Çalışan verilerini ve vizyonunuzu analiz ederek saniyeler içinde 'Kusursuz Hedefler' oluşturun.")
    
    # URL parametreleri veya Session State ile Sekme Yönetimi
    tab1, tab2 = st.tabs(["📌 Hedef Önerisi Oluştur", "🔍 Güçlü/Zayıf Yön Analizi"])
    
    # --- SEKME 1: HEDEF ÖNERİSİ ---
    with tab1:
        if st.button("✨ Hedefleri Oluştur", use_container_width=True):
            if not employee_name or not manager_vision:
                st.error("Lütfen çalışan adı ve yönetici vizyonunu eksiksiz doldurunuz.")
            else:
                with st.spinner("🤖 Geçmiş veriler ve görev tanımları taranıyor..."):
                    try:
                        # Geçmiş veriyi çek ve metne çevir (Markdown tablosu olarak)
                        history_df = load_history_cached(employee_name, target_type)
                        history_text = history_df.to_markdown(index=False) if not history_df.empty else ""
                        
                        suggestion = analyzer.analyze_and_suggest(
                            employee_name, target_type, manager_vision, history_text
                        )
                        
                        st.session_state.last_analysis = suggestion
                        st.session_state.chat_history.append(("Asistan", suggestion))
                        st.success("Hedef Seti Hazırlandı!")
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")

        # Son Analiz Sonucunu Göster (Varsa)
        if st.session_state.last_analysis:
            with st.expander("📝 Oluşturulan Hedefler", expanded=True):
                st.markdown(st.session_state.last_analysis)
    
    # --- SEKME 2: PERFORMANS ANALİZİ ---
    with tab2:
        st.write(f"**{employee_name}** için **{target_type}** alanında detaylı performans analizi.")
        
        if st.button("📊 Analiz Et (Güçlü/Zayıf Yönler)", use_container_width=True):
             if not employee_name:
                st.error("Lütfen çalışan seçin.")
             else:
                with st.spinner("🕵️‍♂️ Detektif modunda analiz yapılıyor..."):
                    try:
                        history_df = load_history_cached(employee_name, target_type)
                        history_text = history_df.to_markdown(index=False) if not history_df.empty else ""
                        
                        analysis_result = analyzer.analyze_performance(
                            employee_name, target_type, history_text
                        )
                        st.session_state.performance_analysis = analysis_result
                    except Exception as e:
                        st.error(f"Analiz Hatası: {e}")
        
        if "performance_analysis" in st.session_state:
             st.markdown(st.session_state.performance_analysis)

    # GEÇMİŞ VERİ TABLOSU
    st.markdown("---")
    st.markdown(f"#### 📊 {employee_name} - {target_type} Verileri")
    
    if employee_name:
        history_df = load_history_cached(employee_name, target_type)
        if not history_df.empty:
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.info("Bu kriterlere uygun geçmiş sayısal veri bulunamadı.")
    else:
        st.info("Lütfen bir çalışan seçin.")

with main_col2:
    st.markdown("### 💬 Asistan ile Sohbet")
    
    # Sohbet Geçmişi Konteynerı
    chat_container = st.container(height=600, border=True)
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align: center; color: #94a3b8; padding: 20px;">
                Henüz bir sohbet başlamadı.<br>
                Sol taraftan analiz başlatabilir veya aşağıdan soru sorabilirsiniz.
            </div>
            """, unsafe_allow_html=True)
            
        for role, msg in st.session_state.chat_history:
            with st.chat_message("user" if role == "Kullanıcı" else "ai", avatar="👤" if role == "Kullanıcı" else "🤖"):
                st.markdown(msg)

    # Yeni Mesaj Girişi
    if prompt := st.chat_input("Örn: Bu hedefleri daha agresif hale getirebilir miyiz?"):
        st.session_state.chat_history.append(("Kullanıcı", prompt))
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
            
        with st.spinner("Yanıtlanıyor..."):
            try:
                response = analyzer.chat_with_data(
                    prompt, 
                    st.session_state.chat_history[:-1], 
                    employee_name if employee_name else "Genel"
                )
                
                st.session_state.chat_history.append(("Asistan", response))
                with chat_container:
                    with st.chat_message("ai", avatar="🤖"):
                        st.markdown(response)
            except Exception as e:
                st.error(f"Hata: {e}")

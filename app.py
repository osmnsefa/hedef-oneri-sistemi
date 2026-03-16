import streamlit as st
import pandas as pd
from src.config import Config
from src.ui_components import load_custom_css, render_header, display_chat_message, render_dss_metrics
from src.analysis import Analyzer
from src.data_loader import DataLoader

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
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# Veri Yükle
employees_list, target_types_list = load_metadata_cached()

# ==============================================================================
# SIDEBAR
# ==============================================================================

with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <h2 style="font-size:1.3rem; font-weight:800; margin:0; color:white;">🎛️ Kontrol Paneli</h2>
        <p style="font-size:0.78rem; color:rgba(255,255,255,0.5); margin:0.2rem 0 0 0;">Parametreleri seçin</p>
    </div>
    """, unsafe_allow_html=True)

    # Çalışan Seçimi
    if employees_list:
        employee_name = st.selectbox("Çalışan", employees_list)
    else:
        employee_name = st.text_input("Çalışan Adı Soyadı", placeholder="Örn: Ahmet Yılmaz")
        st.warning("Excel'den çalışan listesi çekilemedi.")

    # Hedef Kategorisi
    default_targets = ["Satış & Pazarlama", "Yazılım Geliştirme", "Operasyonel Verimlilik"]
    options = target_types_list if target_types_list else default_targets
    target_type = st.selectbox("Hedef Kategorisi", options)

    # Chat kısıtlaması için aktif oturumu senkronize et
    if (st.session_state.active_employee != employee_name or
            st.session_state.active_target != target_type):
        st.session_state.active_employee = employee_name
        st.session_state.active_target = target_type
        # Çalışan/kategori değişince chat geçmişini sıfırla
        st.session_state.chat_history = []
        st.session_state.current_goal_set = None
        st.session_state.proposed_patch = None
        st.session_state.eval_result = None
        st.session_state.perf_res = None

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
                        "eval_result", "perf_res", "last_analysis"]:
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

    if st.button("🧹 Önbellek & Sistem Sıfırla", use_container_width=True):
        st.cache_resource.clear()
        st.cache_data.clear()
        for key in ["chat_history", "current_goal_set", "proposed_patch",
                    "eval_result", "perf_res", "last_analysis"]:
            st.session_state[key] = None if key != "chat_history" else []
        st.success("Sistem sıfırlandı!")
        st.rerun()

    st.markdown(f"""
    <p style='text-align:center; color:rgba(255,255,255,0.3); font-size:0.72rem; margin-top:1rem;'>
        Engine v{getattr(analyzer, 'version', '—')}
    </p>
    """, unsafe_allow_html=True)

# ==============================================================================
# ANA SAYFA
# ==============================================================================

# Çalışan metadata'sını yükle (Unvan, Bölüm, Sicil)
employee_metadata = {}
if employee_name:
    employee_metadata = load_employee_metadata_cached(employee_name)

# Header (metadata bilgileri ile)
render_header(
    employee_name=employee_name,
    target_type=target_type,
    metadata=employee_metadata
)

# Metadata context string'i (chat için)
metadata_ctx_parts = [f"Çalışan: {employee_name}"]
if employee_metadata:
    for k, v in employee_metadata.items():
        if v:
            metadata_ctx_parts.append(f"{k}: {v}")
metadata_ctx_parts.append(f"Hedef Kategorisi: {target_type}")
metadata_context_str = " | ".join(metadata_ctx_parts)

# ==============================================================================
# SEKMELER
# ==============================================================================

tab1, tab2, tab3 = st.tabs(["💬 Asistan", "📌 Hedef Süreci", "🔍 Performans Analizi"])

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
        for user_msg, bot_msg in st.session_state.chat_history:
            display_chat_message("user", user_msg)
            display_chat_message("bot", bot_msg)

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

        # Bot yanıtını göster
        display_chat_message("bot", response)

        # Geçmişe ekle (tuple olarak)
        st.session_state.chat_history.append((prompt, response))
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Sohbeti Temizle", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()

# ====================== TAB 2: HEDEF SÜRECİ ======================
with tab2:

    # 1. BASELINE OLUŞTURMA
    if not st.session_state.current_goal_set:
        st.info("Henüz aktif bir hedef seti yok. Yönetici vizyonunu girin ve **'✨ Hedef Setini Başlat'** butonuna basın.")

        if not manager_vision:
            st.warning("⚠️ Soldan yönetici vizyonunu doldurun.")

        if st.button("✨ Hedef Öner", use_container_width=True,
                     disabled=not (employee_name and manager_vision)):
            with st.spinner(f"🤖 {employee_name} için 3 SMART hedef oluşturuluyor..."):
                history_df = load_history_cached(employee_name, target_type)
                history_text = history_df.to_markdown(index=False) if not history_df.empty else "Sayısal veri yok."
                goal_set = analyzer.analyze_and_suggest(employee_name, target_type, manager_vision, history_text)
                st.session_state.current_goal_set = goal_set
                
                # Uretilen hedefleri asistan sekmesine de düşür
                if goal_set and "error" not in goal_set:
                    bot_msg = f"Sizin için **{target_type}** kategorisinde hedefler ürettim:\n\n"
                    bot_msg += analyzer.format_goal_set(goal_set)
                    bot_msg += "\n\nBu hedefler hakkında konuşmak veya revizyon istemek için bana sorular sorabilirsiniz."
                    st.session_state.chat_history.append(("Bu çalışan için hedef önerir misin?", bot_msg))
                    
                st.rerun()

    # 2. AKTİF HEDEF SETİ
    else:
        gs = st.session_state.current_goal_set

        if "error" in gs:
            st.error(f"Hedef seti üretilemedi: {gs.get('error')}")
            if st.button("🔁 Tekrar Dene"):
                st.session_state.current_goal_set = None
                st.rerun()
        else:
            st.markdown(analyzer.format_goal_set(gs))

            # Karar Destek Sistemi (DSS) ve Risk Metrikleri
            history_df = load_history_cached(employee_name, target_type)
            suggested_goals_text = " ".join([g.get('smart_goal', '') for g in gs.get('goals', [])])
            dss_metrics = analyzer.get_decision_support_metrics(history_df, suggested_goals_text)
            
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
                if st.button("✏️ Revizyon İste", use_container_width=True):
                    st.session_state.show_revision_input = True

            with col_act3:
                if st.button("✅ Onayla & Kilitle", type="primary", use_container_width=True):
                    st.session_state.current_goal_set["status"] = "ACTIVE"
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
                        
                        # Revize edilen hedefi chat'e at
                        bot_msg = f"Hedefleriniz geri bildiriminiz doğrultusunda revize edildi (v{gs['version']}).\n\n"
                        bot_msg += analyzer.format_goal_set(gs)
                        st.session_state.chat_history.append(("Verdiğim geri bildirimi uygulayarak hedefleri revize et.", bot_msg))
                        
                        st.success("✅ Versiyon güncellendi!")
                        st.rerun()
                with col_p2:
                    if st.button("❌ Revizyonu Reddet"):
                        st.session_state.proposed_patch = None
                        st.rerun()

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
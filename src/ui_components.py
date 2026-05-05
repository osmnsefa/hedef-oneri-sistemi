import streamlit as st

def load_custom_css():
    st.markdown("""
    <style>
        /* Ana Arka Plan ve Fontlar */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            background-color: #f0f4f9;
        }
        
        /* ===== SIDEBAR — Koyu Lacivert (app.py'deki beyaz metinler için şart) ===== */
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
        section[data-testid="stSidebar"] .stSelectbox > div > div,
        section[data-testid="stSidebar"] .stTextArea textarea,
        section[data-testid="stSidebar"] .stTextInput input {
            background-color: #1a2f4a !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.12) !important;
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
        
        /* Excel Table Mimic CSS */
        .excel-table-header {
            background-color: #f1f5f9;
            font-weight: 600;
            color: #475569;
            padding: 10px;
            border-bottom: 2px solid #cbd5e1;
            font-size: 0.9rem;
        }
        .excel-table-row {
            padding: 10px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 0.85rem;
            color: #334155;
            display: flex;
            align-items: center;
        }
        .excel-table-row:hover {
            background-color: #f8fafc;
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
    """Kilitlenmiş hedefleri Streamlit üzerinde Excel benzeri tablo ile listeler ve silme imkanı sunar."""
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

        # Excel-like Header
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns([0.5, 1.5, 3, 1, 1, 0.5])
        with h_col1: st.markdown('<div class="excel-table-header">Yıl</div>', unsafe_allow_html=True)
        with h_col2: st.markdown('<div class="excel-table-header">Tür</div>', unsafe_allow_html=True)
        with h_col3: st.markdown('<div class="excel-table-header">SMART Hedef</div>', unsafe_allow_html=True)
        with h_col4: st.markdown('<div class="excel-table-header">Değer</div>', unsafe_allow_html=True)
        with h_col5: st.markdown('<div class="excel-table-header">Yön</div>', unsafe_allow_html=True)
        with h_col6: st.markdown('<div class="excel-table-header">İşlem</div>', unsafe_allow_html=True)

        report_data = []
        for goal in locked_goals:
            c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1.5, 3, 1, 1, 0.5])
            with c1: st.markdown(f'<div class="excel-table-row">{goal.yil}</div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="excel-table-row">{goal.hedef_turu}</div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="excel-table-row">{goal.smart_hedef}</div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="excel-table-row">{goal.hedef_degeri}</div>', unsafe_allow_html=True)
            with c5: st.markdown(f'<div class="excel-table-row">{getattr(goal, "hedef_yonu", "Artan")}</div>', unsafe_allow_html=True)
            with c6:
                if st.button("🗑️ Sil", key=f"del_goal_{goal.id}"):
                    session.delete(goal)
                    session.commit()
                    st.success("Hedef kalıcı olarak silindi.")
                    st.rerun()
            
            justify_text = goal.evidence_justification if goal.evidence_justification else "Gerekçe belirtilmedi."
            locked_by_str = goal.locked_by_sicil if goal.locked_by_sicil else "Belirtilmemiş"
            report_data.append({
                "Tarih": datetime.datetime.now().strftime("%Y-%m-%d"),
                "İsim": employee_name,
                "Sicil No": employee_sicil,
                "Yıl": goal.yil,
                "Hedef Türü": goal.hedef_turu,
                "SMART Hedef": goal.smart_hedef,
                "Hedef Yönü": getattr(goal, "hedef_yonu", "Artan"),
                "Gerekçe": justify_text,
                "Kesinleştiren": locked_by_str
            })
            
        st.markdown("<br>", unsafe_allow_html=True)
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
        session.rollback()
        st.error(f"Kilitli hedefler yüklenirken hata oluştu: {e}")
    finally:
        session.close()

# ==============================================================================
# 📡 VİZYON İSTİHBARAT KARTI
# Akademik Çerçeve:
#   - Wickens (2021) "Attention: Theory and Practice" — Çoklu kaynak
#     dikkat teorisi ile yönetici arayüzü bilişsel yükü optimize edilir.
#   - ISO 9241-210:2019 — İnsan Merkezli Tasarım (Human-Centred Design)
#     etkileşimli sistemler için uluslararası standart.
# ==============================================================================

def render_vision_card(decoded_vision: dict):
    """
    Sidebar için sade Vizyon İstihbarat Kartı.

    Akademik dayanak:
    • Wickens (2021) — Çoklu Kaynak Dikkat Teorisi (Multiple Resource
      Theory); yönetici arayüzünde bilişsel yük minimize edilmeli,
      arka plan hesaplamaları net sinyallere çevrilmelidir.
    • ISO 9241-210:2019 — Etkileşimli sistemlerde insan merkezli
      tasarım prensipleri; kullanıcının ihtiyaç ve bağlamı ön planda.
    """
    if not decoded_vision or decoded_vision.get("vision_summary") in ("", "Vizyon girilmedi.", "Vizyon analizi yapılamadı.", None):
        return

    ambition = decoded_vision.get("ambition_level", "Dengeli")
    stretch = decoded_vision.get("stretch_factor", 0.5)
    risk = decoded_vision.get("risk_appetite", "Orta")
    summary = decoded_vision.get("vision_summary", "")
    themes = decoded_vision.get("focus_themes", [])

    # Renk ve ikon kodlaması
    ambition_style = {
        "Agresif": ("#dc2626", "🔴"),
        "Dengeli": ("#16a34a", "🟢"),
        "Zayıf":   ("#f59e0b", "🟡"),
    }
    color, icon = ambition_style.get(ambition, ("#64748b", "⚪"))

    # Tema satırı
    theme_html = ""
    for t in themes[:3]:
        w = int(t.get("weight", 0) * 100)
        th = t.get("theme", "")
        if w > 0:
            theme_html += f'<span style="background:rgba(255,255,255,0.15);border-radius:4px;padding:2px 6px;font-size:0.72rem;margin-right:4px;">{th} %{w}</span>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e3a5f 0%, #162d4a 100%);
        border: 1px solid {color};
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-top: 0.5rem;
    ">
        <p style="color:rgba(255,255,255,0.6); font-size:0.7rem; font-weight:700;
                  letter-spacing:0.08em; margin:0; text-transform:uppercase;">📡 Vizyon Analizi</p>
        <p style="color:#ffffff; font-size:0.85rem; margin:0.3rem 0; line-height:1.3;">{summary}</p>
        <div style="display:flex; align-items:center; gap:12px; margin-top:0.4rem; flex-wrap:wrap;">
            <span style="color:{color}; font-size:0.78rem; font-weight:700;">{icon} {ambition}</span>
            <span style="color:rgba(255,255,255,0.6); font-size:0.75rem;">Gerilim: {stretch:.2f}</span>
            <span style="color:rgba(255,255,255,0.6); font-size:0.75rem;">Risk: {risk}</span>
        </div>
        <div style="margin-top:0.4rem;">{theme_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 🔴 DEVIL'S ADVOCATE UYARI BİLEŞENİ
# Akademik Çerçeve:
#   - Schwenk (2020) Devil's Advocacy in Strategic Decision Making
#   - EU AI Act 2024 Art. 14 — Human Oversight (insan denetimi) zorunluluğu
#   - Proaktif UI uyarısı — Streamlit'in yukarıdan-aşağı execution modeliyle uyumlu.
# ==============================================================================

def render_devils_advocate_warning(da_result: dict):
    """
    Vizyon fizibilite uyarısını hedef setinin üzerinde proaktif olarak gösterir.

    Akademik dayanak:
    • Schwenk (2020) — Stratejik karar destek sistemlerinde çelişkisel
      sorgulama mekanizması.
    • EU AI Act 2024 Art. 14 — Yüksek riskli AI sistemlerinde insan
      denetimi; otomasyon yanlılığını önleyen proaktif uyarı mekanizmaları.
    """
    if not da_result or not da_result.get("triggered"):
        return

    severity = da_result.get("severity", "info")
    message = da_result.get("message", "")
    note = da_result.get("calibration_note", "")

    if severity == "error":
        bg, border, icon = "#fef2f2", "#dc2626", "⚠️"
        text_color = "#991b1b"
    elif severity == "warning":
        bg, border, icon = "#fffbeb", "#f59e0b", "🟡"
        text_color = "#92400e"
    else:
        bg, border, icon = "#eff6ff", "#3b82f6", "ℹ️"
        text_color = "#1e40af"

    st.markdown(f"""
    <div style="
        background:{bg};
        border-left: 4px solid {border};
        border-radius: 8px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 1rem;
    ">
        <p style="margin:0; font-weight:700; color:{text_color}; font-size:0.9rem;">
            {icon} Devil's Advocate — Vizyon Fizibilite Denetimi
        </p>
        <p style="margin:0.3rem 0 0 0; color:{text_color}; font-size:0.83rem; line-height:1.5;">
            {message}
        </p>
        {f'<p style="margin:0.2rem 0 0 0; color:{text_color}; font-size:0.78rem; font-style:italic;">{note}</p>' if note else ''}
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 🔗 VİZYON İZLENEBİLİRLİK PANELİ
# Akademik Çerçeve:
#   - ISO 56002:2019 — İnovasyon Yönetim Sistemi; stratejik hedeflerin
#     organizasyonel yenilik süreçleriyle izlenebilir hizalanması.
#   - NIST AI RMF 1.0 (2023) — GOVERN fonksiyonu; AI karar çıktılarının
#     stratejik kaynaklarla denetlenebilir bağlantısı.
# ==============================================================================

def render_vision_traceability(goal_set: dict, decoded_vision: dict):
    """
    Hedef seti ile vizyon arasındaki izlenebilirlik zincirini görselleştirir.
    Expander içinde gösterilir — bilişsel yük minimize edilir.

    Akademik dayanak:
    • ISO 56002:2019 — İnovasyon yönetim sistemi stratejik hizalanma modeli.
    • NIST AI RMF 1.0 (2023) — GOVERN fonksiyonu; AI çıktılarının
      kurumsal stratejiye izlenebilir bağlantısının sağlanması.
    """
    if not goal_set or not decoded_vision:
        return
    if "error" in goal_set:
        return

    goals = goal_set.get("goals", [])
    if not goals:
        return

    has_alignment = any(g.get("vision_alignment_note") for g in goals)
    if not has_alignment:
        return

    ambition = decoded_vision.get("ambition_level", "Dengeli")
    summary = decoded_vision.get("vision_summary", "")
    themes = decoded_vision.get("focus_themes", [])
    top_theme = themes[0].get("theme", "—") if themes else "—"

    ambition_colors = {"Agresif": "#dc2626", "Dengeli": "#16a34a", "Zayıf": "#f59e0b"}
    color = ambition_colors.get(ambition, "#64748b")

    with st.expander("🔗 Vizyon ↔ Hedef İzlenebilirlik Zinciri (ISO 56002 / NIST AI RMF)", expanded=False):
        st.markdown(
            f"<p style='font-size:0.8rem;color:#64748b;margin-bottom:0.5rem;'>"
            f"Akademik dayanak: <em>ISO 56002:2019</em> İnovasyon Yönetim Sistemi · "
            f"<em>NIST AI RMF 1.0 (2023)</em> İzlenebilirlik Çerçevesi</p>",
            unsafe_allow_html=True
        )

        # Vizyon özeti
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                    padding:0.6rem 1rem;margin-bottom:0.8rem;">
            <span style="font-size:0.72rem;color:#94a3b8;font-weight:700;
                         text-transform:uppercase;letter-spacing:0.06em;">Yönetici Vizyonu</span>
            <p style="margin:0.2rem 0 0;font-size:0.87rem;color:#1e293b;">{summary}</p>
            <span style="font-size:0.75rem;color:{color};font-weight:700;">
                {ambition} · Baskın Tema: {top_theme}
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Her hedef için izlenebilirlik satırı
        for i, g in enumerate(goals, 1):
            note = g.get("vision_alignment_note", "")
            title = g.get("title", f"Hedef {i}")
            if not note:
                continue
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:10px;
                        padding:0.5rem 0.75rem;border-left:3px solid {color};
                        background:#fafafa;border-radius:0 6px 6px 0;margin-bottom:0.4rem;">
                <span style="font-size:0.85rem;font-weight:700;color:{color};
                             min-width:22px;">H{i}</span>
                <div>
                    <span style="font-size:0.82rem;font-weight:600;color:#1e293b;">{title}</span>
                    <br/>
                    <span style="font-size:0.78rem;color:#475569;font-style:italic;">
                        🔗 {note}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

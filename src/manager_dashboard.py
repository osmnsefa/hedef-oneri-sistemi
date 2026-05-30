"""
Manager Executive Summary Dashboard
Sadece 'Manager' rolüne açıktır. RBAC izolasyonu auth.py üzerinden sağlanır.
"""

import streamlit as st
import textwrap
import pandas as pd
from src.data_loader import DataLoader


# ─────────────────────────────────────────────────────────────────────────────
# PREMIUM CSS
# ─────────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

.mgr-header {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 24px;
    color: #1e293b;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.mgr-header h1 { font-family:'Outfit',sans-serif; font-size:1.6rem; font-weight:800; margin:0; color:#1e293b; }
.mgr-header p  { font-family:'Outfit',sans-serif; font-size:0.9rem; color:#64748b; margin:6px 0 0 0; }

.kpi-card {
    background: white;
    border-radius: 8px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border: 1px solid #e2e8f0;
    border-left: 4px solid #3b82f6;
}
.kpi-label { font-size:0.75rem; color:#64748b; font-weight:600; letter-spacing:.5px; text-transform:uppercase; }
.kpi-value { font-size:2rem; font-weight:800; color:#1e293b; margin:4px 0; line-height:1; }
.kpi-sub   { font-size:0.8rem; color:#94a3b8; }

.kpi-card.green { border-left-color: #16a34a; }
.kpi-card.orange { border-left-color: #d97706; }
.kpi-card.red { border-left-color: #dc2626; }
.kpi-card.blue { border-left-color: #2563eb; }


.emp-row {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: all .2s ease;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.emp-row:hover { box-shadow: 0 4px 12px rgba(37,99,235,0.08); border-color: #cbd5e1; }

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing:.3px;
}
.badge-iyi       { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
.badge-riskli    { background:#fee2e2; color:#b91c1c; border:1px solid #fecaca; }
.badge-beklemede { background:#f1f5f9; color:#475569; border:1px solid #e2e8f0; }

.section-title {
    font-family:'Outfit',sans-serif;
    font-size:1.1rem;
    font-weight:700;
    color:#1e293b;
    margin: 24px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.mini-divider { border:none; border-top:1px solid #e2e8f0; margin: 6px 0 10px 0; }
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# YARDIMCI: KPI HTML KARTI
# ─────────────────────────────────────────────────────────────────────────────
def _kpi_html(label: str, value: str, sub: str, color: str = "") -> str:
    return f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# ANA FONKSİYON
# ─────────────────────────────────────────────────────────────────────────────
def render_manager_dashboard():
    """Manager rolü için Ekip Genel Bakış ekranı."""

    # RBAC Kontrolü
    current_role = st.session_state.get('role', '')
    if current_role not in ('Manager', 'Admin'):
        st.warning("⛔ Bu ekran yalnızca Yönetici rolüne sahip kullanıcılara açıktır.")
        return

    allowed_sicils = st.session_state.get('allowed_employees', [])
    if not allowed_sicils:
        st.warning("Size bağlı herhangi bir çalışan bulunamadı.")
        return

    # CSS Uygula
    st.markdown(_CSS, unsafe_allow_html=True)

    loader = DataLoader()

    # HEADER
    from src.ui_components import render_header
    mgr_sicil = st.session_state.get('user_id')
    mgr_info = loader.get_logged_in_user_info(mgr_sicil) if mgr_sicil else {}
    
    mgr_name = mgr_info.get("Name", "Yönetici")
    mgr_metadata = {
        "Sicil": mgr_info.get("Sicil", mgr_sicil),
        "Unvan": mgr_info.get("Unvan", "Yönetici"),
        "Bölüm Ana Sorumluluk Alanı": mgr_info.get("Bölüm Ana Sorumluluk Alanı", "Yönetim")
    }
    
    render_header(
        employee_name=mgr_name,
        target_type="Ekip Genel Bakış",
        metadata=mgr_metadata
    )

    # VERİ YÜKLEMESİ
    with st.spinner("Ekip verileri analiz ediliyor…"):
        df_perf  = loader.get_team_performance_summary(allowed_sicils)
        df_goals = loader.get_team_goal_assignment_stats(allowed_sicils)

    if df_perf.empty:
        st.info("Ekibe bağlı çalışan verisi bulunamadı.")
        return

    # Merge
    if not df_goals.empty:
        df = pd.merge(df_perf, df_goals, on="Sicil", how="left")
    else:
        df = df_perf.copy()
        df["Atanan Hedef Sayısı"] = 0
        df["Taslak Hedef Sayısı"] = 0

    df["Atanan Hedef Sayısı"] = df["Atanan Hedef Sayısı"].fillna(0).astype(int)
    df["Taslak Hedef Sayısı"]  = df["Taslak Hedef Sayısı"].fillna(0).astype(int)

    # ── KPI HESAPLAMA ──────────────────────────────────────────────────────────
    total_emp           = len(df)
    emp_with_goals      = int((df["Atanan Hedef Sayısı"] > 0).sum())
    assignment_rate     = (emp_with_goals / total_emp * 100) if total_emp else 0
    avg_score           = df["Performans Skoru"].mean() if not df.empty else 0
    team_ok             = avg_score >= 60
    riskli_count        = int((df["Performans Durumu"] == "Riskli").sum())
    hedefsiz_count      = total_emp - emp_with_goals

    # Active revisions query
    from src.auth import get_db_session
    from src.models import AnnualGoals
    session = get_db_session()
    try:
        active_revisions = session.query(AnnualGoals).filter(
            AnnualGoals.employee_sicil.in_(allowed_sicils),
            AnnualGoals.is_revised == True,
            AnnualGoals.approval_status != 'Passive'
        ).count()
    except Exception:
        active_revisions = 0
    finally:
        session.close()

    # ── KPI KARTLARI ───────────────────────────────────────────────────────────
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.markdown(_kpi_html(
        "Ekip Durumu",
        f"{total_emp - riskli_count} İyi / {total_emp}",
        f"{riskli_count} riskli çalışan var" if riskli_count > 0 else "Tüm ekip stabil durumda",
        "green" if riskli_count == 0 else "orange" if riskli_count == 1 else "red"
    ), unsafe_allow_html=True)
    
    kpi2.markdown(_kpi_html(
        "Hedef Atama Oranı",
        f"%{assignment_rate:.0f}",
        f"{emp_with_goals} / {total_emp} çalışan hedeflendirildi",
        "green" if assignment_rate >= 80 else "orange" if assignment_rate >= 50 else "red"
    ), unsafe_allow_html=True)
    
    kpi3.markdown(_kpi_html(
        "Aktif Revizyonlar",
        str(active_revisions),
        "Yapay Zeka veya manuel revize edilen hedefler",
        "blue" if active_revisions > 0 else "green"
    ), unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)

    # ── GRAFIKLER ─────────────────────────────────────────────────────────────
    try:
        import plotly.graph_objects as go
        import plotly.express as px

        col_pie, col_bar = st.columns(2)

        with col_pie:
            durum_counts = df["Performans Durumu"].value_counts().reset_index()
            durum_counts.columns = ["Durum", "Sayı"]
            color_map = {"İyi": "#10b981", "Riskli": "#ef4444", "Beklemede": "#94a3b8"}
            fig_pie = go.Figure(go.Pie(
                labels=durum_counts["Durum"],
                values=durum_counts["Sayı"],
                hole=0.52,
                marker=dict(colors=[color_map.get(d, "#94a3b8") for d in durum_counts["Durum"]]),
                textinfo="label+percent",
                textfont=dict(family="Outfit", size=12)
            ))
            fig_pie.update_layout(
                title=dict(text="Ekip Risk Dağılımı", font=dict(size=14, family="Outfit", color="#1e293b")),
                height=290, margin=dict(t=40, b=10, l=0, r=0),
                showlegend=True,
                legend=dict(font=dict(family="Outfit", size=11, color="#475569")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            df_sorted = df.sort_values("Performans Skoru", ascending=True)
            bar_colors = [color_map.get(s, "#94a3b8") for s in df_sorted["Performans Durumu"]]
            fig_bar = go.Figure(go.Bar(
                x=df_sorted["Performans Skoru"],
                y=df_sorted["İsim"],
                orientation="h",
                marker_color=bar_colors,
                text=[f"{v:.0f}" for v in df_sorted["Performans Skoru"]],
                textposition="outside",
                textfont=dict(family="Outfit", size=10)
            ))
            fig_bar.update_layout(
                title=dict(text="Çalışan Performans Skorları", font=dict(size=14, family="Outfit", color="#1e293b")),
                height=max(250, 55 * len(df_sorted)),
                margin=dict(t=40, b=10, l=0, r=10),
                xaxis=dict(range=[0, 110], title=dict(text="Puan (0–100)", font=dict(family="Outfit", size=11, color="#64748b")), tickfont=dict(family="Outfit", size=10, color="#64748b")),
                yaxis=dict(title="", tickfont=dict(family="Outfit", size=10, color="#475569")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    except ImportError:
        st.info("Grafik görüntülemek için `plotly` kütüphanesi gereklidir.")

    # ── ÇALIŞAN KART LİSTESİ ─────────────────────────────────────────────────
    st.markdown("<div class='section-title'>🧑‍💻 Çalışan Durum Analizi</div>", unsafe_allow_html=True)
    st.caption("Bir çalışanın üzerine tıklayarak hedef süreci ve Asistan ekranına geçiş yapabilirsiniz.")

    # Filtrele
    status_filter = st.selectbox(
        "Duruma Göre Filtrele",
        ["Tümü", "İyi", "Riskli", "Beklemede"],
        key="mgr_status_filter"
    )

    if status_filter != "Tümü":
        df_view = df[df["Performans Durumu"] == status_filter]
    else:
        df_view = df.copy()

    if df_view.empty:
        st.info(f"'{status_filter}' durumunda çalışan bulunmuyor.")
    else:
        # Tablo başlığı
        hc = st.columns([2.5, 1.5, 1.2, 1.2, 1.2, 1.5, 1.2])
        for h, c in zip(["Çalışan", "Unvan / Bölüm", "Durum", "P. Skoru", "Atanan Hedef", "Taslak", ""], hc):
            c.markdown(f"<small style='color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:.5px'>{h}</small>", unsafe_allow_html=True)
        st.markdown("<hr class='mini-divider'>", unsafe_allow_html=True)

        for _, row in df_view.iterrows():
            status = row["Performans Durumu"]
            badge_class = "badge-iyi" if status == "İyi" else "badge-riskli" if status == "Riskli" else "badge-beklemede"
            icon = "🟢" if status == "İyi" else "🔴" if status == "Riskli" else "⚪"

            rc = st.columns([2.5, 1.5, 1.2, 1.2, 1.2, 1.5, 1.2])
            rc[0].markdown(f"**{row['İsim']}**<br><small style='color:#64748b'>Sicil: {row['Sicil']}</small>", unsafe_allow_html=True)
            rc[1].markdown(f"<small>{row['Unvan']}<br>{row['Bölüm']}</small>", unsafe_allow_html=True)
            rc[2].markdown(f"<span class='badge {badge_class}'>{icon} {status}</span>", unsafe_allow_html=True)
            rc[3].markdown(f"<b style='font-size:1.1rem'>{row['Performans Skoru']:.0f}</b>", unsafe_allow_html=True)
            rc[4].markdown(f"<b>{row['Atanan Hedef Sayısı']}</b> hedef", unsafe_allow_html=True)
            rc[5].markdown(f"{row['Taslak Hedef Sayısı']} taslak", unsafe_allow_html=True)
            with rc[6]:
                if st.button("Seç ➔", key=f"go_{row['Sicil']}", use_container_width=True, type="primary"):
                    st.session_state.active_employee = row["İsim"]
                    # Sidebar selectbox'ını da senkronize et
                    st.session_state["_mgr_selected_emp"] = row["İsim"]
                    st.rerun()

            st.markdown("<hr class='mini-divider'>", unsafe_allow_html=True)

    # ── HEDEF DURUMU ÖZET TABLOSU ─────────────────────────────────────────────
    st.markdown("<div class='section-title'>📋 Hedef Atama Özeti</div>", unsafe_allow_html=True)
    df_display = df[["İsim", "Bölüm", "Atanan Hedef Sayısı", "Taslak Hedef Sayısı", "Performans Durumu"]].copy()
    df_display["Durum"] = df_display["Performans Durumu"]
    df_display = df_display.drop(columns=["Performans Durumu"])
    df_display.columns = ["Çalışan", "Bölüm", "Atanan Hedef", "Taslak Hedef", "Durum"]
    st.dataframe(
        df_display.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Atanan Hedef": st.column_config.ProgressColumn("Atanan Hedef", min_value=0, max_value=3, format="%d"),
            "Durum": st.column_config.TextColumn("Performans Durumu"),
        }
    )

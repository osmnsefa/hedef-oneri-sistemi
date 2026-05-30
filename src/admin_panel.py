"""
Admin Dashboard — Sadece 'Admin' rolündeki kullanıcılar görür.
3 sekme:
  1. Kurumsal Raporlar   → Hiyerarşik filtre + DataFrame + CSV indir
  2. AI İstatistikleri   → ai_status oranları, yönetici kıyası, Top5/Bot5
  3. Kullanıcı Yönetimi  → Rol & manager güncellemek için CRUD formu
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.auth import get_db_session
from src.models import User, Employee, PerformanceHistory


# ---------------------------------------------------------------------------
# Yardımcı: Tüm PH verisini DataFrame'e çevir
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def _load_all_ph(dept=None, emp_sicil=None) -> pd.DataFrame:
    session = get_db_session()
    try:
        allowed = st.session_state.get('allowed_employees', [])
        query = session.query(PerformanceHistory).filter(PerformanceHistory.sicil_no.in_(allowed))
        if dept:
            query = query.filter(PerformanceHistory.bolum == dept)
        if emp_sicil:
            query = query.filter(PerformanceHistory.sicil_no == emp_sicil)
            
        rows = query.limit(2000).all()
        data = []
        for r in rows:
            data.append({
                "Sicil":            r.sicil_no,
                "İsim":             r.isim,
                "Bölüm":            r.bolum,
                "Unvan":            r.unvan,
                "Yıl":              r.yil,
                "Hedef Türü":       r.hedef_turu,
                "SMART Hedef":      r.smart_hedef,
                "Hedef Değeri":     r.hedef_degeri,
                "Gerçekleşen":      r.gerceklesen_deger,
                "Sonuç":            r.sonuc,
            })
        return pd.DataFrame(data)
    finally:
        session.close()

@st.cache_data(ttl=600)
def _load_locked_goals(dept=None, emp_sicil=None) -> pd.DataFrame:
    session = get_db_session()
    try:
        from src.models import AnnualGoals, Employee
        allowed = st.session_state.get('allowed_employees', [])
        query = session.query(AnnualGoals, Employee).join(Employee, AnnualGoals.employee_sicil == Employee.user_sicil)\
            .filter(AnnualGoals.is_locked == True)\
            .filter(AnnualGoals.employee_sicil.in_(allowed))
            
        if dept:
            query = query.filter(Employee.department == dept)
        if emp_sicil:
            query = query.filter(Employee.user_sicil == emp_sicil)
            
        rows = query.limit(2000).all()
        data = []
        for g, emp in rows:
            data.append({
                "Sicil": g.employee_sicil,
                "İsim": f"{emp.first_name} {emp.last_name}",
                "Bölüm": emp.department,
                "Yıl": g.yil,
                "Hedef Türü": g.hedef_turu,
                "SMART Hedef": g.smart_hedef,
                "Hedef Değeri": g.hedef_degeri,
                "Hedef Yönü": getattr(g, "hedef_yonu", "Artan"),
                "Vizyon Hırs Düzeyi": getattr(g, "vision_ambition_level", None) or "Bilinmiyor",
                "Kesinleştiren": g.locked_by_sicil
            })
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()
    finally:
        session.close()

# ---------------------------------------------------------------------------
# YARDIMCI: PDF OLUŞTURUCU BUTON HTML/JS
# ---------------------------------------------------------------------------
# PDF Generator artık src.pdf_generator üzerinden çağrılıyor.


# ---------------------------------------------------------------------------
# SEKMELİ ANA FONKSİYON
# ---------------------------------------------------------------------------
def render_admin_dashboard():
    """Ana Admin Dashboard — app.py tarafından çağrılır."""

    current_role = st.session_state.get('role', '')
    if current_role != 'Admin':
        st.warning("⛔ Bu panel yalnızca Admin yetkisine sahip kullanıcılara açıktır.")
        return

    from src.data_loader import DataLoader
    from src.ui_components import render_header

    loader = DataLoader()
    admin_sicil = st.session_state.get('user_id')
    admin_info = loader.get_logged_in_user_info(admin_sicil) if admin_sicil else {}
    
    admin_name = admin_info.get("Name", "Sistem Yöneticisi")
    admin_metadata = {
        "Sicil": admin_info.get("Sicil", admin_sicil),
        "Unvan": admin_info.get("Unvan", "Admin"),
        "Bölüm Ana Sorumluluk Alanı": admin_info.get("Bölüm Ana Sorumluluk Alanı", "Yönetim")
    }
    
    render_header(
        employee_name=admin_name,
        target_type="Sistem Yönetim Paneli",
        metadata=admin_metadata
    )

    st.markdown("""
    <style>
    .admin-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        margin-bottom: 20px;
    }
    .admin-header {
        color: #1e293b;
        font-weight: 800;
        margin-bottom: 10px;
        font-size: 1.15rem;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.spinner("Sistem verileri yükleniyor..."):
        df_all = _load_all_ph()
        df_locked = _load_locked_goals()

    tab_overview, tab_rep, tab_beh, tab_users, tab_feedback, tab_audit = st.tabs([
        "📊 Genel Bakış",
        "📋 Kurumsal Raporlar",
        "🧠 Yönetici Davranış Analizi",
        "👤 Kullanıcı Yönetimi",
        "💬 Çalışan İtirazları",
        "🛡️ Stratejik Onay ve Denetim",
    ])

    # ==========================================================================
    # SEKME 1 — GENEL BAKIŞ
    # ==========================================================================
    with tab_overview:
        st.markdown("<h3 class='admin-header'>KPI Özetleri</h3>", unsafe_allow_html=True)
        
        allowed_emps = st.session_state.get('allowed_employees', [])
        total_employees = len(allowed_emps)
        total_goals = df_all.shape[0]
        
        def normalize_status(s):
            if pd.isna(s): return ''
            return ' '.join(str(s).strip().lower().split())

        if not df_all.empty:
            df_all['norm_status'] = df_all['Sonuç'].apply(normalize_status)
            beklenen = df_all[df_all['norm_status'] == 'beklenen'].shape[0]
            ustunde = df_all[df_all['norm_status'] == 'beklenenin üstünde'].shape[0]
            altinda = df_all[df_all['norm_status'] == 'beklenenin altında'].shape[0]
        else:
            beklenen = ustunde = altinda = 0
            
        beklenen_rate = (beklenen / total_goals) * 100 if total_goals > 0 else 0
        ustunde_rate = (ustunde / total_goals) * 100 if total_goals > 0 else 0
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Toplam Sorumlu Çalışan", total_employees)
        kpi2.metric("Toplam Hedef (Geçmiş)", total_goals)
        kpi3.metric("Beklenen Oranı", f"%{beklenen_rate:.1f}")
        kpi4.metric("Beklenenin Üstünde", f"%{ustunde_rate:.1f}")
        
        st.markdown("<hr/>", unsafe_allow_html=True)
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            if not df_all.empty:
                dept_counts = df_all['Bölüm'].value_counts().reset_index()
                dept_counts.columns = ['Departman', 'Hedef Sayısı']
                fig_bar = px.bar(dept_counts, x='Departman', y='Hedef Sayısı', title="Departmanlara Göre Hedef Dağılımı", color_discrete_sequence=['#3b82f6'])
                fig_bar.update_layout(
                    font=dict(family="Inter"),
                    title=dict(font=dict(size=14, color="#1e293b")),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title="", tickfont=dict(size=10, color="#475569")),
                    yaxis=dict(title="Hedef Sayısı", gridcolor="#e2e8f0", tickfont=dict(size=10, color="#475569"))
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
                status_counts = df_all['Sonuç'].value_counts().reset_index()
                status_counts.columns = ['Durum', 'Sayı']
                status_counts = status_counts[status_counts['Durum'].astype(str).str.strip() != '']
                fig_pie = px.pie(status_counts, names='Durum', values='Sayı', title="Hedef Sonuç Dağılımı", color_discrete_sequence=['#1e293b', '#3b82f6', '#94a3b8', '#cbd5e1'])
                fig_pie.update_layout(
                    font=dict(family="Inter"),
                    title=dict(font=dict(size=14, color="#1e293b")),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(font=dict(size=10, color="#475569"))
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Grafik oluşturulacak geçmiş veri bulunamadı.")

        with chart_col2:
            if not df_all.empty and 'Yıl' in df_all.columns:
                trend_data = df_all.groupby('Yıl').apply(
                    lambda x: pd.Series({
                        'toplamHedef': len(x),
                        'beklenen': len(x[x['norm_status'] == 'beklenen']),
                        'ustunde': len(x[x['norm_status'] == 'beklenenin üstünde']),
                        'altinda': len(x[x['norm_status'] == 'beklenenin altında'])
                    })
                ).reset_index()
                
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['toplamHedef'], mode='lines+markers', name='Toplam Hedef', line=dict(color='#1e293b', width=2.5), marker=dict(size=8)))
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['beklenen'], mode='lines+markers', name='Beklenen', line=dict(color='#3b82f6', width=2), marker=dict(size=6)))
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['ustunde'], mode='lines+markers', name='Beklenenin Üstünde', line=dict(color='#10b981', width=2), marker=dict(size=6)))
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['altinda'], mode='lines+markers', name='Beklenenin Altında', line=dict(color='#ef4444', width=2), marker=dict(size=6)))
                
                fig_line.update_layout(
                    font=dict(family="Inter"),
                    title=dict(text="Yıllık Hedef Performans Trendi", font=dict(size=14, color="#1e293b")),
                    xaxis=dict(type='category', tickfont=dict(size=10, color="#475569")),
                    yaxis=dict(gridcolor="#e2e8f0", tickfont=dict(size=10, color="#475569")),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10, color="#475569")),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Trend oluşturulacak yıllık veri bulunamadı.")

    # ==========================================================================
    # SEKME 1 — KURUMSAL RAPORLAR
    # ==========================================================================
    with tab_rep:
        st.subheader("📋 Kurumsal Raporlar")
        st.markdown("Veritabanından canlı (Lazy Load) filtrelenmiş PDF raporları oluşturun.")

        if df_all.empty and df_locked.empty:
            st.info("Veritabanında henüz performans kaydı veya kilitli hedef yok.")
            return

        import streamlit.components.v1 as components
        from src.pdf_generator import generate_report_html
        
        report_type = st.selectbox("Rapor Türü Seçiniz", ["Şirket Geneli", "Departman", "Çalışan", "Genel Performans"])
        
        # Filtre Seçenekleri
        departments = sorted(list(set(df_all['Bölüm'].dropna().unique().tolist() + df_locked['Bölüm'].dropna().unique().tolist())))
        all_emps_df = pd.concat([
            df_all[['Sicil', 'İsim']] if not df_all.empty else pd.DataFrame(columns=['Sicil', 'İsim']), 
            df_locked[['Sicil', 'İsim']] if not df_locked.empty else pd.DataFrame(columns=['Sicil', 'İsim'])
        ]).drop_duplicates(subset=['Sicil']).sort_values('İsim')
        
        selected_dept = None
        selected_emp_sicil = None
        selected_emp_name = None
        
        if report_type == "Departman":
            selected_dept = st.selectbox("Departman Seçiniz", departments)
        elif report_type == "Çalışan":
            emp_dict = {row['Sicil']: row['İsim'] for _, row in all_emps_df.iterrows()}
            selected_emp_sicil = st.selectbox("Çalışan Seçiniz", list(emp_dict.keys()), format_func=lambda x: emp_dict[x])
            selected_emp_name = emp_dict.get(selected_emp_sicil, "")
            
        if st.button("📄 Raporu Hazırla & İndir"):
            with st.spinner("Raporunuz veritabanından çekiliyor..."):
                # Lazy Loading: Sadece gerekli veriyi SQL'den çek
                df_all_lazy = _load_all_ph(dept=selected_dept, emp_sicil=selected_emp_sicil)
                df_locked_lazy = _load_locked_goals(dept=selected_dept, emp_sicil=selected_emp_sicil)
                
                if report_type == "Şirket Geneli" or report_type == "Genel Performans":
                    title = "Şirket Geneli Performans Raporu"
                    sub = "Tüm Departmanlar ve Çalışanlar Özeti"
                elif report_type == "Departman":
                    title = f"{selected_dept} Departman Raporu"
                    sub = f"Departman Bazlı Performans Özeti"
                elif report_type == "Çalışan":
                    title = f"{selected_emp_name} Raporu"
                    sub = f"Çalışan Özel Performans Özeti"
                    
                html_code = generate_report_html(
                    report_type="dinamik", 
                    df_all=df_all_lazy, 
                    df_locked=df_locked_lazy, 
                    report_title=title, 
                    report_subtitle=sub
                )
                
                # HTML Container üzerinden PDF indirmeyi tetikler
                components.html(html_code, height=600, scrolling=True)

    # ==========================================================================
    # SEKME 2 — YÖNETİCİ DAVRANIŞ ANALİZİ
    # ==========================================================================
    with tab_beh:
        st.subheader("🧠 Yönetici Davranış Analizi ve Personalar")
        
        session = get_db_session()
        try:
            from src.models import AnnualGoals
            goals = session.query(AnnualGoals).all()
            if not goals:
                st.info("Henüz kilitlenmiş hedef (davranış verisi) bulunmuyor.")
            else:
                data = []
                for g in goals:
                    data.append({
                        "Manager": g.locked_by_sicil,
                        "Status": g.ai_status,
                        "Duration": g.decision_duration,
                        "RevisionDepth": g.revision_depth,
                        "RegenCount": g.regen_count,
                        "ChatCount": g.chat_interaction_count
                    })
                
                df_beh = pd.DataFrame(data)
                
                # Sadece AI tarafindan uretilen hedefler
                df_beh = df_beh[df_beh["Status"] != "Manuel"]
                
                if df_beh.empty:
                    st.info("AI tarafından üretilmiş ve onaylanmış hedef verisi bulunmuyor.")
                else:
                    mgr_stats = df_beh.groupby("Manager").agg(
                        AvgDuration=("Duration", "mean"),
                        AvgRevision=("RevisionDepth", "mean"),
                        AvgRegen=("RegenCount", "mean"),
                        AvgChat=("ChatCount", "mean"),
                        TotalGoals=("Status", "count"),
                        KabulGoals=("Status", lambda x: (x == "Kabul").sum()),
                        RevizeGoals=("Status", lambda x: (x == "Revize").sum())
                    ).reset_index()
                    
                    def get_persona(row):
                        if row["AvgRevision"] > 50 or row["AvgRegen"] > 3:
                            return "🔬 Mikro Yönetici"
                        if row["AvgDuration"] > 30 and (5 <= row["AvgRevision"] <= 20) and row["AvgChat"] > 0:
                            return "🤝 Stratejik İş Birlikçi"
                        if row["AvgDuration"] < 10 and row["AvgRevision"] == 0.0:
                            return "🙈 Kör Onaycı"
                        return "Dengeli Yönetici"
                        
                    mgr_stats["Persona"] = mgr_stats.apply(get_persona, axis=1)
                    mgr_stats["Adaptasyon Skoru (%)"] = ((mgr_stats["KabulGoals"] * 1.0 + mgr_stats["RevizeGoals"] * 0.75) / mgr_stats["TotalGoals"] * 100).round(1)
                    
                    st.markdown("### 🎭 Yönetici Personaları")
                    st.dataframe(mgr_stats.rename(columns={
                        "Manager": "Yönetici Sicil",
                        "AvgDuration": "Ort. Süre (sn)",
                        "AvgRevision": "Ort. Değişim (%)",
                        "AvgRegen": "Yeniden Üretme",
                        "AvgChat": "Chat Etkileşimi"
                    })[["Yönetici Sicil", "Persona", "Adaptasyon Skoru (%)", "Ort. Süre (sn)", "Ort. Değişim (%)", "Yeniden Üretme", "Chat Etkileşimi"]].style.format({
                        "Ort. Süre (sn)": "{:.1f}",
                        "Ort. Değişim (%)": "{:.1f}",
                        "Yeniden Üretme": "{:.1f}",
                        "Chat Etkileşimi": "{:.1f}"
                    }), use_container_width=True)

                    # ── VİZYON HIRS DAĞILIMI — Plotly (Organizational Learning) ──
                    st.markdown("---")
                    st.markdown("### 📊 Vizyon Hırs Dağılımı")
                    st.caption(
                        "Akademik dayanak: EU AI Act 2024 Art. 12-14 — İzlenebilirlik (Traceability) "
                        "ve Denetim Gereksinimleri; NIST AI RMF 1.0 (2023) — GOVERN Fonksiyonu; "
                        "Kurumsal hafızanın oluşması için geçmiş vizyon kararları denetlenebilir "
                        "bir kayda aktarılmalıdır."
                    )
                    df_locked2 = _load_locked_goals()
                    if not df_locked2.empty and "Vizyon Hırs Düzeyi" in df_locked2.columns:
                        ambition_counts = df_locked2["Vizyon Hırs Düzeyi"].value_counts().reset_index()
                        ambition_counts.columns = ["Düzey", "Hedef Sayısı"]
                        color_map = {
                            "Agresif":   "#ef4444",
                            "Dengeli":   "#10b981",
                            "Zayıf":    "#f59e0b",
                            "Bilinmiyor": "#94a3b8",
                        }
                        colors = [color_map.get(d, "#94a3b8") for d in ambition_counts["Düzey"]]
                        try:
                            col_pie, col_bar = st.columns(2)
                            with col_pie:
                                fig_pie = go.Figure(go.Pie(
                                    labels=ambition_counts["Düzey"],
                                    values=ambition_counts["Hedef Sayısı"],
                                    marker=dict(colors=colors),
                                    hole=0.4,
                                    textinfo="label+percent",
                                    textfont=dict(family="Inter", size=11)
                                ))
                                fig_pie.update_layout(
                                    font=dict(family="Inter"),
                                    title=dict(text="Hırs Düzeyi Dağılımı", font=dict(size=14, color="#1e293b")),
                                    height=320, margin=dict(t=40, b=10),
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    legend=dict(font=dict(size=10, color="#475569"))
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)
                            with col_bar:
                                fig_bar = go.Figure(go.Bar(
                                    x=ambition_counts["Düzey"],
                                    y=ambition_counts["Hedef Sayısı"],
                                    marker_color=colors,
                                    text=ambition_counts["Hedef Sayısı"],
                                    textposition="outside",
                                    textfont=dict(family="Inter", size=10)
                                ))
                                fig_bar.update_layout(
                                    font=dict(family="Inter"),
                                    title=dict(text="Hırs Düzeyi — Hedef Adet", font=dict(size=14, color="#1e293b")),
                                    height=320, margin=dict(t=40, b=10),
                                    xaxis=dict(title=dict(text="Düzey", font=dict(size=11, color="#64748b")), tickfont=dict(size=10, color="#64748b")),
                                    yaxis=dict(title=dict(text="Adet", font=dict(size=11, color="#64748b")), tickfont=dict(size=10, color="#64748b"), gridcolor="#e2e8f0"),
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)"
                                )
                                st.plotly_chart(fig_bar, use_container_width=True)
                        except ImportError:
                            st.dataframe(ambition_counts, use_container_width=True)
                            st.caption("⚠️ Plotly yüklenmemiş. `pip install plotly` ile kurabilirsiniz.")
                    else:
                        st.info("İstihbarat katmanı verileri henüz mevcut değil. Vizyon analizi yapılmış ve kilitlenmiş hedef bulunmamaktadır.")
        finally:
            session.close()

    # ==========================================================================
    # SEKME 4 — ÇALIŞAN İTİRAZLARI (GERİ BİLDİRİMLER)
    # ==========================================================================
    with tab_feedback:
        st.subheader("💬 Bekleyen Çalışan İtirazları")
        
        session = get_db_session()
        try:
            from src.models import AnnualGoals, Employee
            feedbacks = session.query(AnnualGoals, Employee).join(Employee, AnnualGoals.employee_sicil == Employee.user_sicil).filter(
                AnnualGoals.approval_status == 'Feedback_Received'
            ).all()
            
            if not feedbacks:
                st.success("🎉 Bekleyen herhangi bir çalışan itirazı bulunmuyor.")
            else:
                st.info(f"Toplam {len(feedbacks)} adet incelenmeyi bekleyen itiraz var.")
                
                # Çalışan Filtresi
                unique_emps = sorted(list(set([f"{emp.first_name} {emp.last_name}" for g, emp in feedbacks])))
                selected_emp = st.selectbox("Çalışan Filtrele (İtirazlar)", ["Tümü"] + unique_emps)
                
                from collections import defaultdict
                grouped_feedbacks = defaultdict(list)
                for g, emp in feedbacks:
                    emp_name = f"{emp.first_name} {emp.last_name}"
                    if selected_emp != "Tümü" and emp_name != selected_emp:
                        continue
                    grouped_feedbacks[g.yil].append((g, emp))
                    
                if not grouped_feedbacks:
                    st.info("Seçili çalışana ait bekleyen itiraz bulunmuyor.")
                    
                for yil in sorted(grouped_feedbacks.keys(), reverse=True):
                    with st.expander(f"📅 {yil} Yılı İtirazları ({len(grouped_feedbacks[yil])} adet)", expanded=True):
                        for g, emp in grouped_feedbacks[yil]:
                            st.markdown(f"**Çalışan:** {emp.first_name} {emp.last_name} | **Hedef Türü:** {g.hedef_turu}")
                            st.markdown(f"**SMART Hedef:** {g.smart_hedef}")
                            st.warning(f"💬 **Çalışan Notu:** {g.employee_note}")
                            st.caption(f"Kilitliyen: {g.locked_by_sicil}")
                            st.markdown("---")
        finally:
            session.close()

    # ==========================================================================
    # SEKME 5 — STRATEJİK ONAY VE DENETİM MASASI
    # ==========================================================================
    with tab_audit:
        st.subheader("🛡️ Stratejik Onay ve Denetim Masası")
        st.markdown("Yöneticiler tarafından kesinleştirilmiş hedefleri denetleyin, revizyon isteyin veya onaylayın.")
        
        session = get_db_session()
        try:
            from src.models import AnnualGoals, Employee
            import datetime
            import json
            
            # Kilitli (kesinleşmiş) hedefleri getir (sadece aktif olanlar)
            locked_goals = session.query(AnnualGoals, Employee).join(Employee, AnnualGoals.employee_sicil == Employee.user_sicil).filter(
                AnnualGoals.is_locked == True,
                AnnualGoals.approval_status != 'Passive'
            ).order_by(AnnualGoals.yil.desc(), AnnualGoals.admin_approval_status).all()
            
            # Reddedilmiş hedefleri getir
            rejected_goals = session.query(AnnualGoals, Employee).join(Employee, AnnualGoals.employee_sicil == Employee.user_sicil).filter(
                AnnualGoals.admin_approval_status == 'Reddedildi'
            ).order_by(AnnualGoals.yil.desc()).all()
            
            all_audit_goals = locked_goals + rejected_goals
            
            if not all_audit_goals:
                st.info("Sistemde kesinleştirilmiş veya reddedilmiş herhangi bir hedef bulunmuyor.")
            else:
                # Çalışan Filtresi
                unique_audit_emps = sorted(list(set([f"{emp.first_name} {emp.last_name}" for g, emp in all_audit_goals])))
                selected_audit_emp = st.selectbox("Çalışan Filtrele (Denetim)", ["Tümü"] + unique_audit_emps)
                
                filtered_goals = []
                filtered_rejected_goals = []
                for g, emp in locked_goals:
                    emp_name = f"{emp.first_name} {emp.last_name}"
                    if selected_audit_emp != "Tümü" and emp_name != selected_audit_emp:
                        continue
                    filtered_goals.append((g, emp))
                    
                for g, emp in rejected_goals:
                    emp_name = f"{emp.first_name} {emp.last_name}"
                    if selected_audit_emp != "Tümü" and emp_name != selected_audit_emp:
                        continue
                    filtered_rejected_goals.append((g, emp))
                
                if not filtered_goals and not filtered_rejected_goals:
                    st.info("Seçili çalışana ait hedef bulunmuyor.")
                else:
                    def has_chat_history(g):
                        logs = getattr(g, 'denetim_loglari', [])
                        if isinstance(logs, str):
                            try: logs = json.loads(logs)
                            except: logs = []
                        return bool(logs)

                    onaylananlar = [(g, emp) for g, emp in filtered_goals if g.admin_approval_status == 'Onaylandı']
                    onay_bekleyenler = [(g, emp) for g, emp in filtered_goals if g.admin_approval_status != 'Onaylandı' and not has_chat_history(g)]
                    sohbet_edilenler = [(g, emp) for g, emp in filtered_goals if g.admin_approval_status != 'Onaylandı' and has_chat_history(g)]
                    reddedilenler = filtered_rejected_goals
                    
                    tab_onay_bekleyen, tab_sohbet, tab_onay, tab_reddedilen = st.tabs([
                        f"Onay Bekleyenler ({len(onay_bekleyenler)})", 
                        f"Revizyon Bekleyenler ({len(sohbet_edilenler)})", 
                        f"Onaylanan Hedefler ({len(onaylananlar)})",
                        f"Reddedilen Hedefler ({len(reddedilenler)})"
                    ])
                    
                    def render_audit_goal(g, emp, is_approved):
                        status_color = "green" if g.admin_approval_status == 'Onaylandı' else "red" if g.admin_approval_status == 'Reddedildi' else "orange" if g.admin_approval_status == 'Revizyon Bekliyor' else "blue"
                        with st.expander(f"📌 {emp.first_name} {emp.last_name} | {g.hedef_turu} | Durum: {g.admin_approval_status}"):
                            st.markdown(f"**Atayan Yönetici Sicili:** `{g.locked_by_sicil}`")
                            
                            if getattr(g, 'is_revised', False) and getattr(g, 'parent_goal_id', None):
                                # Eski hedefi bul
                                old_g = session.query(AnnualGoals).filter(AnnualGoals.id == g.parent_goal_id).first()
                                if old_g:
                                    st.markdown("##### 🔍 Revizyon Karşılaştırması (Eski vs Yeni)")
                                    rev_src = getattr(g, 'revision_source', 'Bilinmiyor')
                                    rev_dt = getattr(g, 'revised_at', None)
                                    rev_dt_str = rev_dt.strftime('%d.%m.%Y %H:%M') if rev_dt else "-"
                                    st.caption(f"**Revizyon Kaynağı:** {rev_src} | **Tarih:** {rev_dt_str}")
                                    
                                    col_old, col_new = st.columns(2)
                                    with col_old:
                                        st.error("**Eski Hedef (v{})**".format(old_g.version_no))
                                        st.info(f"**SMART Hedef:** {old_g.smart_hedef}")
                                        st.info(f"**Değer:** {old_g.hedef_degeri} {old_g.birim}")
                                    with col_new:
                                        st.success("**Yeni Hedef (v{})**".format(g.version_no))
                                        st.info(f"**SMART Hedef:** {g.smart_hedef}")
                                        st.info(f"**Değer:** {g.hedef_degeri} {g.birim}")
                                else:
                                    st.markdown(f"**SMART Hedef:** {g.smart_hedef}")
                                    st.markdown(f"**Hedef Değeri:** {g.hedef_degeri} {g.birim}")
                            else:
                                st.markdown(f"**SMART Hedef:** {g.smart_hedef}")
                                st.markdown(f"**Hedef Değeri:** {g.hedef_degeri} {g.birim}")
                                
                            st.markdown("---")
                            st.markdown("##### 📜 İletişim Geçmişi (Audit Trail)")
                            
                            logs = g.denetim_loglari
                            if isinstance(logs, str):
                                try:
                                    logs = json.loads(logs)
                                except:
                                    logs = []
                            if not logs:
                                logs = []
                                
                            if not logs:
                                st.caption("Henüz bir iletişim kaydı yok.")
                            else:
                                for log in logs:
                                    role_icon = "🛡️ Admin" if log.get('role') == 'Admin' else "👔 Yönetici"
                                    ts = log.get('timestamp', '')
                                    if ts:
                                        try:
                                            ts = ts.split('.')[0]
                                        except:
                                            pass
                                    st.markdown(f"**{role_icon}** 🕒 `{ts}`\n> {log.get('content')}")
                                    
                            st.markdown("---")
                            
                            if not is_approved and g.admin_approval_status != 'Reddedildi':
                                # Aksiyonlar
                                with st.form(f"audit_form_{g.id}"):
                                    new_msg = st.text_area("Yöneticiye Mesaj / Revizyon Notu / Red Gerekçesi (Opsiyonel)", key=f"msg_{g.id}")
                                    
                                    c1, c2, c3 = st.columns(3)
                                    with c1:
                                        btn_approve = st.form_submit_button("✅ Hedefi Onayla")
                                    with c2:
                                        btn_revise = st.form_submit_button("🔄 Revizyon İste")
                                    with c3:
                                        btn_reject = st.form_submit_button("❌ Hedefi Reddet")
                                        
                                    if btn_approve or btn_revise or btn_reject:
                                        now_str = datetime.datetime.now().isoformat()
                                        
                                        if btn_approve:
                                            if new_msg.strip():
                                                st.error("⚠️ Hedefi ONAYLARKEN mesaj bırakamazsınız. Eğer yazdığınız mesaja istinaden bir revizyon istiyorsanız lütfen '🔄 Revizyon İste' butonuna tıklayınız.")
                                            else:
                                                g.admin_approval_status = 'Onaylandı'
                                                session.commit()
                                                st.cache_data.clear() # Cache invalidation
                                                st.success("Hedef onaylandı!")
                                                st.rerun()
                                                
                                        elif btn_revise:
                                            if not new_msg.strip():
                                                st.error("Revizyon istemek için lütfen bir not giriniz.")
                                            else:
                                                new_log = {"role": "Admin", "content": new_msg.strip(), "timestamp": now_str}
                                                if isinstance(logs, list):
                                                    logs.append(new_log)
                                                else:
                                                    logs = [new_log]
                                                g.denetim_loglari = list(logs)
                                                from sqlalchemy.orm.attributes import flag_modified
                                                flag_modified(g, "denetim_loglari")
                                                
                                                g.admin_approval_status = 'Revizyon Bekliyor'
                                                session.commit()
                                                st.cache_data.clear() # Cache invalidation
                                                st.warning("Yöneticiye revizyon talebi iletildi.")
                                                st.rerun()
                                                
                                        elif btn_reject:
                                            if not new_msg.strip():
                                                st.error("Reddetmek için lütfen bir gerekçe (mesaj) giriniz.")
                                            else:
                                                new_log = {"role": "Admin", "content": f"[REDDEDİLDİ] {new_msg.strip()}", "timestamp": now_str}
                                                if isinstance(logs, list):
                                                    logs.append(new_log)
                                                else:
                                                    logs = [new_log]
                                                g.denetim_loglari = list(logs)
                                                from sqlalchemy.orm.attributes import flag_modified
                                                flag_modified(g, "denetim_loglari")
                                                
                                                g.admin_approval_status = 'Reddedildi'
                                                g.is_locked = False
                                                g.approval_status = 'Passive'
                                                session.commit()
                                                st.cache_data.clear()
                                                st.error("Hedef reddedildi ve çalışanın yeni hedef oluşturabilmesi için slot açıldı.")
                                                st.rerun()
                            elif g.admin_approval_status == 'Reddedildi':
                                st.error("Bu hedef reddedilmiştir. Çalışanın kotasından düşülmüştür.")
                            else:
                                st.success("Bu hedef onaylanmıştır. Onay süreci tamamlanmıştır.")

                    with tab_onay_bekleyen:
                        if not onay_bekleyenler:
                            st.info("Onay bekleyen hedef bulunmuyor.")
                        else:
                            for g, emp in onay_bekleyenler:
                                render_audit_goal(g, emp, is_approved=False)

                    with tab_sohbet:
                        if not sohbet_edilenler:
                            st.info("Şu an revizyon bekleyen hedef bulunmuyor.")
                        else:
                            for g, emp in sohbet_edilenler:
                                render_audit_goal(g, emp, is_approved=False)
                                
                    with tab_onay:
                        if not onaylananlar:
                            st.info("Henüz onaylanmış hedef bulunmuyor.")
                        else:
                            for g, emp in onaylananlar:
                                render_audit_goal(g, emp, is_approved=True)
                                
                    with tab_reddedilen:
                        if not reddedilenler:
                            st.info("Henüz reddedilmiş hedef bulunmuyor.")
                        else:
                            for g, emp in reddedilenler:
                                render_audit_goal(g, emp, is_approved=False)
                                
        finally:
            session.close()

    # ==========================================================================
    # SEKME 6 — KULLANICI YÖNETİMİ
    # ==========================================================================
    with tab_users:
        st.subheader("👤 Kullanıcı Yönetimi")

        session = get_db_session()
        try:
            users = session.query(User).order_by(User.sicil_no).all()
            user_data = [{
                "Sicil No":           u.sicil_no,
                "Rol":                u.role,
                "Yönetici Sicili":    u.manager_sicil or "-",
            } for u in users]
        finally:
            session.close()

        df_users = pd.DataFrame(user_data)
        
        st.markdown("#### ⚡ Hızlı Liste Görünümü")
        st.data_editor(
            df_users,
            column_config={
                "Rol": st.column_config.SelectboxColumn(
                    "Yetki Rolü",
                    help="Kullanıcının sistemdeki rolü",
                    options=["Admin", "Manager", "Employee"],
                    required=True,
                )
            },
            hide_index=True,
            use_container_width=True,
            disabled=["Sicil No"]
        )

        st.markdown("---")
        
        from src.auth import create_new_user
        with st.expander("➕ Yeni Kullanıcı Ekle", expanded=False):
            with st.form("add_user_form"):
                new_u_sicil = st.text_input("Sicil No", placeholder="Örn: 99123")
                new_u_name = st.text_input("İsim Soyisim", placeholder="Örn: Ahmet Yılmaz")
                new_u_role = st.selectbox("Rol", ["Employee", "Manager", "Admin"])
                new_u_mgr = st.selectbox("Yönetici Sicili", ["(Yönetici Yok)"] + [u["Sicil No"] for u in user_data])
                
                submitted_add = st.form_submit_button("Kullanıcı Ekle")
                if submitted_add:
                    if not new_u_sicil or not new_u_name:
                        st.error("Sicil No ve İsim alanları zorunludur.")
                    else:
                        sess_add = get_db_session()
                        mgr_val = None if new_u_mgr == "(Yönetici Yok)" else new_u_mgr
                        success, msg = create_new_user(sess_add, new_u_sicil, new_u_name, new_u_role, mgr_val)
                        sess_add.close()
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        st.markdown("#### ✏️ Kullanıcı Güncelle")

        sicil_options = [u["Sicil No"] for u in user_data]
        sel_sicil = st.selectbox("Güncellenecek Sicil", sicil_options, key="usr_edit_sicil")

        role_options = ["Admin", "Manager", "Employee"]
        new_role = st.selectbox("Yeni Rol", role_options, key="usr_new_role")

        manager_options = ["(Yönetici Yok)"] + sicil_options
        new_mgr = st.selectbox("Yeni Yönetici Sicili", manager_options, key="usr_new_mgr")

        if st.button("💾 Kaydet", key="usr_save"):
            session2 = get_db_session()
            try:
                user_to_update = session2.query(User).filter(User.sicil_no == sel_sicil).first()
                if user_to_update:
                    user_to_update.role = new_role
                    user_to_update.manager_sicil = None if new_mgr == "(Yönetici Yok)" else new_mgr
                    session2.commit()
                    st.success(f"✅ {sel_sicil} başarıyla güncellendi.")
                    st.rerun()
                else:
                    st.error("Kullanıcı bulunamadı.")
            except Exception as e:
                session2.rollback()
                st.error(f"Güncelleme hatası: {e}")
            finally:
                session2.close()

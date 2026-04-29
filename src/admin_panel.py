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
def _load_all_ph() -> pd.DataFrame:
    session = get_db_session()
    try:
        allowed = st.session_state.get('allowed_employees', [])
        rows = session.query(PerformanceHistory).filter(PerformanceHistory.sicil_no.in_(allowed)).all()
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

def _load_locked_goals() -> pd.DataFrame:
    session = get_db_session()
    try:
        from src.models import AnnualGoals, Employee
        allowed = st.session_state.get('allowed_employees', [])
        rows = session.query(AnnualGoals, Employee).join(Employee, AnnualGoals.employee_sicil == Employee.user_sicil)\
            .filter(AnnualGoals.is_locked == True)\
            .filter(AnnualGoals.employee_sicil.in_(allowed)).all()
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
def _generate_four_card_pdf_ui(df_all, df_locked):
    import datetime
    
    # CSS Styles
    css = """
    <style>
        body { font-family: 'Inter', sans-serif; color: #1e293b; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }
        .card h3 { margin-top: 10px; margin-bottom: 8px; font-size: 18px; color: #2563eb; }
        .card p { color: #64748b; font-size: 14px; margin-bottom: 16px; }
        .card select { width: 100%; padding: 8px; margin-bottom: 16px; border: 1px solid #cbd5e1; border-radius: 4px; font-family: 'Inter', sans-serif; }
        .card button { width: 100%; background: #2563eb; color: white; border: none; padding: 10px; border-radius: 6px; cursor: pointer; font-weight: 600; font-family: 'Inter', sans-serif; }
        .card button:hover { background: #1d4ed8; }
        
        .pdf-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 16px; margin-bottom: 24px; }
        .pdf-table th { background: #2563eb; color: #ffffff; padding: 6px 10px; text-align: left; font-size: 11px; font-weight: 600; }
        .pdf-table td { padding: 6px 10px; border-bottom: 1px solid #e2e8f0; color: #1e293b; }
        .pdf-table tr:nth-child(even) { background: #f8fafc; }
        
        .pdf-header { border-bottom: 3px solid #2563eb; padding-bottom: 20px; margin-bottom: 32px; display: flex; justify-content: space-between; align-items: flex-end; }
        .pdf-header-title { font-size: 24px; font-weight: 700; color: #1e293b; margin: 0; }
        .pdf-header-sub { font-size: 11px; color: #64748b; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px; }
        .pdf-badge { margin-top: 4px; background: #eff6ff; color: #2563eb; padding: 4px 12px; border-radius: 20px; font-size: 12px; display: inline-block; }
        
        .pdf-footer { border-top: 1px solid #e2e8f0; margin-top: 40px; padding-top: 16px; display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; }
    </style>
    """

    js = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script>
        async function generatePDF(elementId, filename) {
            const element = document.getElementById(elementId);
            if (!element) return;

            element.style.position = 'fixed';
            element.style.top = '0';
            element.style.left = '0';
            element.style.zIndex = '9999';
            element.style.display = 'block';

            await new Promise(resolve => setTimeout(resolve, 500));

            try {
                const canvas = await html2canvas(element, {
                    scale: 2, useCORS: true, allowTaint: true, backgroundColor: '#ffffff', width: 1300, windowWidth: 1300
                });

                const imgData = canvas.toDataURL('image/png');
                const { jsPDF } = window.jspdf;
                const pdf = new jsPDF({ orientation: 'portrait', unit: 'px', format: 'a4', hotfixes: ['px_scaling'] });

                const pageWidth = pdf.internal.pageSize.getWidth();
                const pageHeight = pdf.internal.pageSize.getHeight();
                const imgWidth = pageWidth;
                const imgHeight = (canvas.height * pageWidth) / canvas.width;

                let heightLeft = imgHeight;
                let position = 0;

                pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;

                while (heightLeft > 0) {
                    position = heightLeft - imgHeight;
                    pdf.addPage();
                    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                    heightLeft -= pageHeight;
                }

                const date = new Date().toISOString().split('T')[0];
                pdf.save(`${filename}-${date}.pdf`);

            } finally {
                element.style.display = 'none';
                element.style.position = 'absolute';
                element.style.zIndex = '-1';
            }
        }
        
        function updateDept() {
            const val = document.getElementById('dept-select').value;
            document.querySelectorAll('.dept-section').forEach(el => el.style.display = 'none');
            const target = document.getElementById('dept-' + val);
            if(target) target.style.display = 'block';
        }

        function updateEmp() {
            const val = document.getElementById('emp-select').value;
            document.querySelectorAll('.emp-section').forEach(el => el.style.display = 'none');
            const target = document.getElementById('emp-' + val);
            if(target) target.style.display = 'block';
        }
    </script>
    """

    def render_header(title, subtitle=""):
        date_str = datetime.datetime.now().strftime("%d.%m.%Y")
        return f"""
        <div class="pdf-header">
            <div>
                <div class="pdf-header-sub">Stratejik Performans Yönetim Sistemi</div>
                <h1 class="pdf-header-title">{title}</h1>
                <div style="font-size: 14px; color: #64748b; margin-top: 4px;">{subtitle}</div>
            </div>
            <div style="text-align: right; font-size: 13px; color: #64748b;">
                <div>Rapor Tarihi: {date_str}</div>
                <div class="pdf-badge">GİZLİ</div>
            </div>
        </div>
        """

    def render_footer():
        now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        return f"""
        <div class="pdf-footer">
            <span>Stratejik PMS — Kurumsal Rapor</span>
            <span>Bu rapor sistem tarafından otomatik oluşturulmuştur.</span>
            <span>{now_str}</span>
        </div>
        """

    def normalize(s):
        if pd.isna(s): return ''
        return ' '.join(str(s).strip().lower().split())

    if not df_all.empty:
        df_all['norm_status'] = df_all['Sonuç'].apply(normalize)
        beklenen = len(df_all[df_all['norm_status'] == 'beklenen'])
        ustunde = len(df_all[df_all['norm_status'] == 'beklenenin üstünde'])
        altinda = len(df_all[df_all['norm_status'] == 'beklenenin altında'])
    else:
        beklenen = ustunde = altinda = 0

    total_goals = len(df_all) + len(df_locked)
    total_emps = len(set(df_all['Sicil'].tolist() + df_locked['Sicil'].tolist())) if not (df_all.empty and df_locked.empty) else 0

    # REPORT 1: Sirket Geneli
    r1_html = f"""
    <div id="pdf-sirket-geneli" style="display:none; padding:40px; background:white; width:1300px; color:#1e293b;">
        {render_header("Şirket Geneli Performans Raporu", "Tüm Departmanlar ve Çalışanlar Özeti")}
        <h3>KPI Özeti</h3>
        <table class="pdf-table">
            <tr><th>Toplam Çalışan</th><th>Toplam Hedef (Geçmiş + Yeni)</th><th>Beklenen (Geçmiş)</th><th>Beklenenin Üstünde</th><th>Beklenenin Altında</th></tr>
            <tr><td>{total_emps}</td><td>{total_goals}</td><td>{beklenen}</td><td>{ustunde}</td><td>{altinda}</td></tr>
        </table>
        <h3>Geçmiş Performans Verileri</h3>
        {df_all.drop(columns=['norm_status']).to_html(index=False, classes='pdf-table', border=0) if not df_all.empty else '<p>Veri yok.</p>'}
        <h3>Yeni Kesinleşmiş (Kilitli) Hedefler</h3>
        {df_locked.to_html(index=False, classes='pdf-table', border=0) if not df_locked.empty else '<p>Veri yok.</p>'}
        {render_footer()}
    </div>
    """

    # REPORT 2: Departman
    dept_options = ""
    dept_sections = ""
    departments = sorted(list(set(df_all['Bölüm'].dropna().unique().tolist() + df_locked['Bölüm'].dropna().unique().tolist()))) if not (df_all.empty and df_locked.empty) else []
    
    for i, dept in enumerate(departments):
        dept_options += f'<option value="{i}">{dept}</option>'
        d_all = df_all[df_all['Bölüm'] == dept] if not df_all.empty else df_all
        d_lock = df_locked[df_locked['Bölüm'] == dept] if not df_locked.empty else df_locked
        dept_emps = len(set(d_all['Sicil'].tolist() + d_lock['Sicil'].tolist()))
        dept_goals = len(d_all) + len(d_lock)
        
        display_style = "block" if i == 0 else "none"
        dept_sections += f"""
        <div id="dept-{i}" class="dept-section" style="display:{display_style}; padding:40px; background:white; width:1300px; color:#1e293b;">
            {render_header(f"{dept} Departman Raporu", f"Çalışan sayısı: {dept_emps} | Toplam hedef: {dept_goals}")}
            <h3>Geçmiş Performans Verileri</h3>
            {d_all.drop(columns=['norm_status']).to_html(index=False, classes='pdf-table', border=0) if not d_all.empty else '<p>Veri yok.</p>'}
            <h3>Yeni Kesinleşmiş (Kilitli) Hedefler</h3>
            {d_lock.to_html(index=False, classes='pdf-table', border=0) if not d_lock.empty else '<p>Veri yok.</p>'}
            {render_footer()}
        </div>
        """

    r2_html = f"""<div id="pdf-departman" style="display:none;">{dept_sections}</div>"""

    # REPORT 3: Çalışan
    emp_options = ""
    emp_sections = ""
    if not (df_all.empty and df_locked.empty):
        all_emps_df = pd.concat([df_all[['Sicil', 'İsim', 'Bölüm', 'Unvan']] if not df_all.empty else pd.DataFrame(columns=['Sicil', 'İsim', 'Bölüm', 'Unvan']), 
                                 df_locked[['Sicil', 'İsim', 'Bölüm']] if not df_locked.empty else pd.DataFrame(columns=['Sicil', 'İsim', 'Bölüm'])]).drop_duplicates(subset=['Sicil']).sort_values('İsim')
    else:
        all_emps_df = pd.DataFrame()
        
    for i, row in all_emps_df.iterrows():
        sicil = row['Sicil']
        isim = row['İsim']
        emp_options += f'<option value="{sicil}">{isim}</option>'
        
        e_all = df_all[df_all['Sicil'] == sicil] if not df_all.empty else df_all
        e_lock = df_locked[df_locked['Sicil'] == sicil] if not df_locked.empty else df_locked
        e_unvan = row.get('Unvan', '')
        if pd.isna(e_unvan): e_unvan = ''
        e_dept = row.get('Bölüm', '')
        
        display_style = "block" if i == 0 else "none"
        emp_sections += f"""
        <div id="emp-{sicil}" class="emp-section" style="display:{display_style}; padding:40px; background:white; width:1300px; color:#1e293b;">
            {render_header(f"{isim} - Performans Raporu", f"Unvan: {e_unvan} | Departman: {e_dept} | Sicil: {sicil}")}
            <h3>Geçmiş Performans Verileri</h3>
            {e_all.drop(columns=['norm_status']).to_html(index=False, classes='pdf-table', border=0) if not e_all.empty else '<p>Veri yok.</p>'}
            <h3>Yeni Kesinleşmiş (Kilitli) Hedefler</h3>
            {e_lock.to_html(index=False, classes='pdf-table', border=0) if not e_lock.empty else '<p>Veri yok.</p>'}
            {render_footer()}
        </div>
        """

    r3_html = f"""<div id="pdf-calisan" style="display:none;">{emp_sections}</div>"""

    # REPORT 4: Genel Performans
    r4_html = f"""
    <div id="pdf-performans" style="display:none; padding:40px; background:white; width:1300px; color:#1e293b;">
        {render_header("Genel Performans Raporu", "Tüm Çalışanların Performans Özeti")}
        <table class="pdf-table">
            <tr><th>Sicil</th><th>Ad Soyad</th><th>Departman</th><th>Toplam Geçmiş Hedef</th><th>Beklenen</th><th>Üstünde</th><th>Altında</th><th>Yeni Hedef Sayısı</th></tr>
    """
    for _, row in all_emps_df.iterrows():
        sicil = row['Sicil']
        e_all = df_all[df_all['Sicil'] == sicil] if not df_all.empty else df_all
        e_lock = df_locked[df_locked['Sicil'] == sicil] if not df_locked.empty else df_locked
        e_bek = len(e_all[e_all['norm_status'] == 'beklenen']) if not e_all.empty else 0
        e_ust = len(e_all[e_all['norm_status'] == 'beklenenin üstünde']) if not e_all.empty else 0
        e_alt = len(e_all[e_all['norm_status'] == 'beklenenin altında']) if not e_all.empty else 0
        r4_html += f"<tr><td>{sicil}</td><td>{row['İsim']}</td><td>{row['Bölüm']}</td><td>{len(e_all)}</td><td>{e_bek}</td><td>{e_ust}</td><td>{e_alt}</td><td>{len(e_lock)}</td></tr>"
    r4_html += f"</table>{render_footer()}</div>"

    # UI Layout
    ui_html = f"""
    <div style="background: white; border-radius: 8px;">
        <p style="color: #64748b; margin-bottom: 24px; font-family:'Inter',sans-serif; font-size:14px;">Aşağıdaki kartlardan filtrelerinizi seçerek PDF raporları üretebilirsiniz. Tüm veriler canlı SQL kayıtlarından beslenmektedir.</p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; font-family:'Inter',sans-serif;">
            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">📊</div>
                <h3>Şirket Geneli Raporu</h3>
                <p>Tüm departmanlar, tüm geçmiş performans ve kilitli yeni hedefler.</p>
                <button onclick="generatePDF('pdf-sirket-geneli', 'sirket-geneli-raporu')">📥 PDF İndir</button>
            </div>
            
            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">🏬</div>
                <h3>Departman Raporu</h3>
                <select id="dept-select" onchange="updateDept()">{dept_options}</select>
                <button onclick="generatePDF('pdf-departman', 'departman-raporu')">📥 PDF İndir</button>
            </div>

            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">👤</div>
                <h3>Çalışan Raporu</h3>
                <select id="emp-select" onchange="updateEmp()">{emp_options}</select>
                <button onclick="generatePDF('pdf-calisan', 'calisan-raporu')">📥 PDF İndir</button>
            </div>

            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">📈</div>
                <h3>Genel Performans Raporu</h3>
                <p>Tüm çalışanların tek tablo üzerinde özet performansı.</p>
                <button onclick="generatePDF('pdf-performans', 'genel-performans-raporu')">📥 PDF İndir</button>
            </div>
        </div>
    </div>
    """

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        {css}
        {js}
    </head>
    <body>
        {ui_html}
        {r1_html}
        {r2_html}
        {r3_html}
        {r4_html}
        <script>updateDept(); updateEmp();</script>
    </body>
    </html>
    """


# ---------------------------------------------------------------------------
# SEKMELİ ANA FONKSİYON
# ---------------------------------------------------------------------------
def render_admin_dashboard():
    """Ana Admin Dashboard — app.py tarafından çağrılır."""

    current_role = st.session_state.get('role', '')
    if current_role != 'Admin':
        st.warning("⛔ Bu panel yalnızca Admin yetkisine sahip kullanıcılara açıktır.")
        return

    st.markdown("## 🛡️ Sistem Yönetim Paneli")
    st.markdown("---")

    st.markdown("""
    <style>
    .admin-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #2563eb;
        margin-bottom: 20px;
    }
    .admin-header {
        color: #2563eb;
        font-weight: 800;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.spinner("Sistem verileri yükleniyor..."):
        df_all = _load_all_ph()
        df_locked = _load_locked_goals()

    tab_overview, tab_rep, tab_beh, tab_users = st.tabs([
        "📊 Genel Bakış",
        "📋 Kurumsal Raporlar",
        "🧠 Yönetici Davranış Analizi",
        "👤 Kullanıcı Yönetimi",
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
                fig_bar = px.bar(dept_counts, x='Departman', y='Hedef Sayısı', title="Departmanlara Göre Hedef Dağılımı", color_discrete_sequence=['#2563eb'])
                st.plotly_chart(fig_bar, use_container_width=True)
                
                status_counts = df_all['Sonuç'].value_counts().reset_index()
                status_counts.columns = ['Durum', 'Sayı']
                status_counts = status_counts[status_counts['Durum'].astype(str).str.strip() != '']
                fig_pie = px.pie(status_counts, names='Durum', values='Sayı', title="Hedef Sonuç Dağılımı", color_discrete_sequence=px.colors.sequential.Blues_r)
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
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['toplamHedef'], mode='lines+markers', name='Toplam Hedef', line=dict(color='#2563eb', width=2.5), marker=dict(size=10)))
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['beklenen'], mode='lines+markers', name='Beklenen', line=dict(color='#6366f1', width=2), marker=dict(size=8)))
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['ustunde'], mode='lines+markers', name='Beklenenin Üstünde', line=dict(color='#10b981', width=2), marker=dict(size=8)))
                fig_line.add_trace(go.Scatter(x=trend_data['Yıl'], y=trend_data['altinda'], mode='lines+markers', name='Beklenenin Altında', line=dict(color='#ef4444', width=2), marker=dict(size=8)))
                
                fig_line.update_layout(
                    title="Yıllık Hedef Performans Trendi",
                    xaxis=dict(type='category'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Trend oluşturulacak yıllık veri bulunamadı.")

    # ==========================================================================
    # SEKME 1 — KURUMSAL RAPORLAR
    # ==========================================================================
    with tab_rep:
        st.subheader("📋 Kurumsal Raporlar")

        if df_all.empty and df_locked.empty:
            st.info("Veritabanında henüz performans kaydı veya kilitli hedef yok.")
            return

        import streamlit.components.v1 as components
        components.html(_generate_four_card_pdf_ui(df_all, df_locked), height=550, scrolling=True)

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
        finally:
            session.close()

    # ==========================================================================
    # SEKME 3 — KULLANICI YÖNETİMİ
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

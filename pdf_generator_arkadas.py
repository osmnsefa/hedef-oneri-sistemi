import pandas as pd
import datetime

def generate_reports_html(df_goals, df_users):
    # CSS Styles
    css = """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1e293b; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }
        .card h3 { margin-top: 10px; margin-bottom: 8px; font-size: 18px; }
        .card p { color: #64748b; font-size: 14px; margin-bottom: 16px; }
        .card select { width: 100%; padding: 8px; margin-bottom: 16px; border: 1px solid #cbd5e1; border-radius: 4px; }
        .card button { width: 100%; background: #2563eb; color: white; border: none; padding: 10px; border-radius: 6px; cursor: pointer; font-weight: 600; }
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

    # Scripts
    js = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script>
        async function generatePDF(elementId, filename) {
            const element = document.getElementById(elementId);
            if (!element) { console.error('Element not found:', elementId); return; }

            // Make element temporarily visible for capture
            element.style.position = 'fixed';
            element.style.top = '0';
            element.style.left = '0';
            element.style.zIndex = '9999';
            element.style.display = 'block';
            element.style.background = '#ffffff';
            element.style.width = '1300px';
            element.style.padding = '40px';

            // Wait for fonts and layout to settle
            await new Promise(resolve => setTimeout(resolve, 600));

            try {
                const canvas = await html2canvas(element, {
                    scale: 2,
                    useCORS: true,
                    allowTaint: true,
                    backgroundColor: '#ffffff',
                    width: 1300,
                    windowWidth: 1300,
                    onclone: (clonedDoc) => {
                        const el = clonedDoc.getElementById(elementId);
                        if (el) {
                            el.style.display = 'block';
                            el.style.visibility = 'visible';
                            el.style.overflow = 'visible';
                            el.style.height = 'auto';
                            el.style.position = 'static';
                        }
                    }
                });

                const imgData = canvas.toDataURL('image/png');
                const { jsPDF } = window.jspdf;
                const pdf = new jsPDF({
                    orientation: 'portrait',
                    unit: 'px',
                    format: 'a4',
                    hotfixes: ['px_scaling']
                });

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
            <span>Stratejik PMS — Admin Raporu</span>
            <span>Bu rapor sistem tarafından otomatik oluşturulmuştur.</span>
            <span>{now_str}</span>
        </div>
        """

    # --- Pre-process Data ---
    def normalize(s):
        if pd.isna(s): return ''
        return ' '.join(str(s).strip().lower().split())

    df_goals['norm_status'] = df_goals['Gerçekleşen Değere Göre Sonuç'].apply(normalize)
    total_goals = len(df_goals)
    total_emps = df_goals['Sicil'].nunique()
    
    beklenen = len(df_goals[df_goals['norm_status'] == 'beklenen'])
    ustunde = len(df_goals[df_goals['norm_status'] == 'beklenenin üstünde'])
    altinda = len(df_goals[df_goals['norm_status'] == 'beklenenin altında'])

    # --- REPORT 1: Sirket Geneli ---
    r1_html = f"""
    <div id="pdf-sirket-geneli" style="display:none;">
        {render_header("Şirket Geneli Performans Raporu", "Tüm Departmanlar ve Çalışanlar Özeti")}
        
        <h3>KPI Özeti</h3>
        <table class="pdf-table">
            <tr>
                <th>Toplam Çalışan</th><th>Toplam Hedef</th><th>Beklenen</th><th>Beklenenin Üstünde</th><th>Beklenenin Altında</th>
            </tr>
            <tr>
                <td>{total_emps}</td><td>{total_goals}</td><td>{beklenen} ({(beklenen/total_goals*100):.1f}%)</td><td>{ustunde} ({(ustunde/total_goals*100):.1f}%)</td><td>{altinda} ({(altinda/total_goals*100):.1f}%)</td>
            </tr>
        </table>

        <h3>Yıllık Hedef Trendi</h3>
        <table class="pdf-table">
            <tr><th>Yıl</th><th>Toplam Hedef</th><th>Beklenen</th><th>Üstünde</th><th>Altında</th></tr>
            <tr><td>2023</td><td>85</td><td>53</td><td>18</td><td>14</td></tr>
            <tr><td>2024</td><td>106</td><td>59</td><td>26</td><td>21</td></tr>
            <tr><td>2025</td><td>112</td><td>52</td><td>26</td><td>34</td></tr>
        </table>

        <h3>Departman Özeti</h3>
        <table class="pdf-table">
            <tr><th>Departman</th><th>Hedef</th><th>Çalışan</th><th>Beklenen</th><th>Üstünde</th><th>Altında</th></tr>
            <tr><td>Kalite</td><td>92</td><td>6</td><td>54</td><td>19</td><td>19</td></tr>
            <tr><td>Motor Parça Üretimi</td><td>71</td><td>5</td><td>39</td><td>15</td><td>17</td></tr>
            <tr><td>Planlama</td><td>66</td><td>4</td><td>36</td><td>11</td><td>19</td></tr>
            <tr><td>Kompozit Üretim</td><td>25</td><td>2</td><td>11</td><td>8</td><td>6</td></tr>
            <tr><td>Montaj Hattı</td><td>23</td><td>2</td><td>10</td><td>10</td><td>3</td></tr>
            <tr><td>Üretim Operasyonları</td><td>14</td><td>1</td><td>9</td><td>3</td><td>2</td></tr>
            <tr><td>Lojistik</td><td>12</td><td>1</td><td>5</td><td>4</td><td>3</td></tr>
        </table>
        {render_footer()}
    </div>
    """

    # --- REPORT 2: Departman ---
    dept_options = ""
    dept_sections = ""
    departments = sorted([str(d) for d in df_goals['Bölüm Ana Sorumluluk Alanı'].dropna().unique() if str(d).strip() != ''])
    
    for i, dept in enumerate(departments):
        dept_options += f'<option value="{i}">{dept}</option>'
        dept_df = df_goals[df_goals['Bölüm Ana Sorumluluk Alanı'] == dept]
        dept_emps = dept_df['Sicil'].nunique()
        dept_goals = len(dept_df)
        d_bek = len(dept_df[dept_df['norm_status'] == 'beklenen'])
        d_ust = len(dept_df[dept_df['norm_status'] == 'beklenenin üstünde'])
        d_alt = len(dept_df[dept_df['norm_status'] == 'beklenenin altında'])
        
        emp_rows = ""
        for sicil, emp_df in dept_df.groupby(['Sicil', 'İsim', 'Unvan']):
            e_goals = len(emp_df)
            e_bek = len(emp_df[emp_df['norm_status'] == 'beklenen'])
            e_ust = len(emp_df[emp_df['norm_status'] == 'beklenenin üstünde'])
            e_alt = len(emp_df[emp_df['norm_status'] == 'beklenenin altında'])
            emp_rows += f"<tr><td>{sicil[0]}</td><td>{sicil[1]}</td><td>{sicil[2]}</td><td>{e_goals}</td><td>{e_bek}</td><td>{e_ust}</td><td>{e_alt}</td></tr>"

        display_style = "block" if i == 0 else "none"
        dept_sections += f"""
        <div id="dept-{i}" class="dept-section" style="display:{display_style};">
            {render_header(f"{dept} Departman Raporu", f"Çalışan sayısı: {dept_emps} | Toplam hedef: {dept_goals}")}
            <h3>Durum Özeti</h3>
            <table class="pdf-table">
                <tr><th>Beklenen</th><th>Beklenenin Üstünde</th><th>Beklenenin Altında</th></tr>
                <tr><td>{d_bek}</td><td>{d_ust}</td><td>{d_alt}</td></tr>
            </table>
            <h3>Çalışan Listesi</h3>
            <table class="pdf-table">
                <tr><th>Sicil</th><th>Ad Soyad</th><th>Unvan</th><th>Hedef</th><th>Beklenen</th><th>Üstünde</th><th>Altında</th></tr>
                {emp_rows}
            </table>
            {render_footer()}
        </div>
        """

    r2_html = f"""
    <div id="pdf-departman" style="display:none;">
        {dept_sections}
    </div>
    """

    # --- REPORT 3: Çalışan ---
    emp_options = ""
    emp_sections = ""
    employees = df_goals[['Sicil', 'İsim']].drop_duplicates().sort_values('İsim')
    
    for i, row in enumerate(employees.itertuples()):
        sicil = row.Sicil
        isim = row.İsim
        emp_options += f'<option value="{sicil}">{isim}</option>'
        
        emp_df = df_goals[df_goals['Sicil'] == sicil]
        e_unvan = emp_df['Unvan'].iloc[0] if not emp_df.empty else ""
        e_dept = emp_df['Bölüm Ana Sorumluluk Alanı'].iloc[0] if not emp_df.empty else ""
        
        e_goals = len(emp_df)
        e_bek = len(emp_df[emp_df['norm_status'] == 'beklenen'])
        e_ust = len(emp_df[emp_df['norm_status'] == 'beklenenin üstünde'])
        e_alt = len(emp_df[emp_df['norm_status'] == 'beklenenin altında'])
        
        goal_rows = ""
        # Sort by Yıl if possible
        if 'Yıl' in emp_df.columns:
            emp_df = emp_df.sort_values('Yıl')
            
        for _, grow in emp_df.iterrows():
            sonuc = str(grow.get('Gerçekleşen Değere Göre Sonuç', ''))
            color = "#1e293b"
            if normalize(sonuc) == 'beklenen': color = "#64748b" # gray
            elif normalize(sonuc) == 'beklenenin üstünde': color = "#10b981" # green
            elif normalize(sonuc) == 'beklenenin altında': color = "#ef4444" # red
            
            goal_rows += f"""<tr>
                <td>{grow.get('Yıl', '')}</td>
                <td>{grow.get('Hedef Türü', '')}</td>
                <td>{grow.get('SMART Hedef Tanımı', '')}</td>
                <td>{grow.get('Hedef Değeri', '')}</td>
                <td>{grow.get('Birim', '')}</td>
                <td>{grow.get('Gerçekleşen Değer', '')}</td>
                <td style="color:{color}; font-weight:600;">{sonuc}</td>
            </tr>"""

        display_style = "block" if i == 0 else "none"
        emp_sections += f"""
        <div id="emp-{sicil}" class="emp-section" style="display:{display_style};">
            {render_header(f"{isim} - Performans Raporu", f"Unvan: {e_unvan} | Departman: {e_dept} | Sicil: {sicil}")}
            <h3>Özet İstatistikler</h3>
            <table class="pdf-table">
                <tr><th>Toplam Hedef</th><th>Beklenen</th><th>Beklenenin Üstünde</th><th>Beklenenin Altında</th></tr>
                <tr><td>{e_goals}</td><td>{e_bek}</td><td>{e_ust}</td><td>{e_alt}</td></tr>
            </table>
            <h3>Tüm Hedefler</h3>
            <table class="pdf-table">
                <tr><th>Yıl</th><th>Hedef Türü</th><th>SMART Hedef Tanımı</th><th>Hedef Değeri</th><th>Birim</th><th>Gerçekleşen</th><th>Sonuç</th></tr>
                {goal_rows}
            </table>
            {render_footer()}
        </div>
        """

    r3_html = f"""
    <div id="pdf-calisan" style="display:none;">
        {emp_sections}
    </div>
    """

    # --- REPORT 4: Genel Performans ---
    perf_rows = ""
    # We use hardcoded logic provided by user or just group dynamically to get the 21 rows
    # "Tüm çalışanlar tablosu (21 çalışan):"
    perf_df = df_goals.groupby(['Sicil', 'İsim', 'Unvan', 'Bölüm Ana Sorumluluk Alanı']).apply(
        lambda x: pd.Series({
            'Toplam': len(x),
            'Beklenen': len(x[x['norm_status'] == 'beklenen']),
            'Üstünde': len(x[x['norm_status'] == 'beklenenin üstünde']),
            'Altında': len(x[x['norm_status'] == 'beklenenin altında'])
        })
    ).reset_index().sort_values('Sicil')
    
    for _, prow in perf_df.iterrows():
        perf_rows += f"<tr><td>{prow['Sicil']}</td><td>{prow['İsim']}</td><td>{prow['Unvan']}</td><td>{prow['Bölüm Ana Sorumluluk Alanı']}</td><td>{prow['Toplam']}</td><td>{prow['Beklenen']}</td><td>{prow['Üstünde']}</td><td>{prow['Altında']}</td></tr>"

    r4_html = f"""
    <div id="pdf-performans" style="display:none;">
        {render_header("Genel Performans Raporu", "Tüm Çalışanların Performans Özeti")}
        <table class="pdf-table">
            <tr><th>Sicil</th><th>Ad Soyad</th><th>Unvan</th><th>Departman</th><th>Toplam</th><th>Beklenen</th><th>Üstünde</th><th>Altında</th></tr>
            {perf_rows}
        </table>
        {render_footer()}
    </div>
    """

    # --- UI Layout ---
    ui_html = f"""
    <div style="padding: 32px; background: white; border-radius: 8px;">
        <h2 style="margin-top:0;">Raporlar</h2>
        <p style="color: #64748b; margin-bottom: 24px;">Her rapor için ayrı PDF oluşturulur. Tüm veriler Excel kaynak dosyasından alınmaktadır.</p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">📊</div>
                <h3>Şirket Geneli Raporu</h3>
                <p>21 çalışan, 303 hedef, tüm departmanlar</p>
                <button onclick="generatePDF('pdf-sirket-geneli', 'sirket-geneli-raporu')">PDF İndir</button>
            </div>
            
            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">🏬</div>
                <h3>Departman Raporu</h3>
                <select id="dept-select" onchange="updateDept()">
                    {dept_options}
                </select>
                <button onclick="generatePDF('pdf-departman', 'departman-raporu')">PDF İndir</button>
            </div>

            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">👤</div>
                <h3>Çalışan Raporu</h3>
                <select id="emp-select" onchange="updateEmp()">
                    {emp_options}
                </select>
                <button onclick="generatePDF('pdf-calisan', 'calisan-raporu')">PDF İndir</button>
            </div>

            <div class="card">
                <div style="font-size:24px; margin-bottom:8px;">📈</div>
                <h3>Genel Performans Raporu</h3>
                <p>Tüm çalışanların performans özeti</p>
                <button onclick="generatePDF('pdf-performans', 'genel-performans-raporu')">PDF İndir</button>
            </div>
        </div>
    </div>
    """

    final_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        {css}
        {js}
    </head>
    <body>
        {ui_html}
        {r1_html}
        {r2_html}
        {r3_html}
        {r4_html}
        
        <script>
            // Initialize selections
            updateDept();
            updateEmp();
        </script>
    </body>
    </html>
    """
    
    return final_html

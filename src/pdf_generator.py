import pandas as pd
import datetime

def generate_report_html(report_type, df_all, df_locked, report_title, report_subtitle=""):
    """
    Spesifik bir rapor tipi için HTML ve PDF JS kodunu üretir.
    Veritabanından çekilen 'Lazy Loading' verisini kullanarak tek bir rapor çıktısı oluşturur.
    """
    
    css = """
    <style>
        body { font-family: 'Inter', sans-serif; color: #1e293b; background: #f8fafc; }
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

            // Arka planda tam genişlikle render alabilmek için geçici stil ayarları
            const originalStyle = element.getAttribute('style');
            element.style.position = 'fixed';
            element.style.top = '0';
            element.style.left = '0';
            element.style.zIndex = '9999';
            element.style.display = 'block';

            // Tarayıcının render edebilmesi için kısa bir süre bekle
            await new Promise(resolve => setTimeout(resolve, 300));

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
                // Stili eski haline getir
                element.setAttribute('style', originalStyle);
            }
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
            <span>Bu rapor sistem tarafından dinamik filtreleme (Lazy Load) ile otomatik oluşturulmuştur.</span>
            <span>{now_str}</span>
        </div>
        """

    def normalize(s):
        if pd.isna(s): return ''
        return ' '.join(str(s).strip().lower().split())

    if not df_all.empty:
        df_all_disp = df_all.copy()
        df_all_disp['norm_status'] = df_all_disp['Sonuç'].apply(normalize)
        beklenen = len(df_all_disp[df_all_disp['norm_status'] == 'beklenen'])
        ustunde = len(df_all_disp[df_all_disp['norm_status'] == 'beklenenin üstünde'])
        altinda = len(df_all_disp[df_all_disp['norm_status'] == 'beklenenin altında'])
        df_all_disp = df_all_disp.drop(columns=['norm_status'])
    else:
        df_all_disp = df_all.copy()
        beklenen = ustunde = altinda = 0

    total_goals = len(df_all) + len(df_locked)
    total_emps = len(set(df_all['Sicil'].tolist() + df_locked['Sicil'].tolist())) if not (df_all.empty and df_locked.empty) else 0

    table_html = f"""
        {render_header(report_title, report_subtitle)}
        <h3>KPI Özeti</h3>
        <table class="pdf-table">
            <tr><th>Toplam Çalışan</th><th>Toplam Hedef (Geçmiş + Yeni)</th><th>Beklenen (Geçmiş)</th><th>Beklenenin Üstünde</th><th>Beklenenin Altında</th></tr>
            <tr><td>{total_emps}</td><td>{total_goals}</td><td>{beklenen}</td><td>{ustunde}</td><td>{altinda}</td></tr>
        </table>
        <h3>Geçmiş Performans Verileri</h3>
        {df_all_disp.to_html(index=False, classes='pdf-table', border=0) if not df_all_disp.empty else '<p>Seçili filtreye uygun geçmiş veri bulunamadı.</p>'}
        <h3>Yeni Kesinleşmiş (Kilitli) Hedefler</h3>
        {df_locked.to_html(index=False, classes='pdf-table', border=0) if not df_locked.empty else '<p>Seçili filtreye uygun yeni kilitlenmiş hedef bulunamadı.</p>'}
        {render_footer()}
    """

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        {css}
        {js}
    </head>
    <body>
        <div style="text-align: center; padding: 20px; font-family:'Inter',sans-serif;">
            <p>Raporunuz hazırlandı! Otomatik indirme başlamazsa butona tıklayın.</p>
            <button onclick="generatePDF('pdf-container', '{report_type}')" style="padding: 10px 20px; background-color: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; font-family:'Inter',sans-serif; font-weight:600; font-size:14px;">
                ⬇️ Raporu Şimdi İndir
            </button>
        </div>
        <!-- Rapor Konteyneri -->
        <div style="width: 100%; overflow-x: auto; background: #e2e8f0; padding: 20px 0;">
            <div id="pdf-container" style="background:white; width:1300px; color:#1e293b; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding:40px;">
                {table_html}
            </div>
        </div>
        <script>
            // Otomatik indirmeyi tetikle
            setTimeout(() => {{
                generatePDF('pdf-container', '{report_type}');
            }}, 1500);
        </script>
    </body>
    </html>
    """
    return full_html

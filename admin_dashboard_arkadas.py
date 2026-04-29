import streamlit as st
import pandas as pd
import plotly.express as px
import time
from src.backend_api import BackendAPI
from src.pdf_generator import generate_reports_html

@st.cache_data(ttl=60)
def load_real_admin_data():
    api = BackendAPI()
    return api.get_employees(), api.get_goals(), api.get_departments()

def render_admin_dashboard():
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
    
    st.title("🛡️ Sistem Yönetim Paneli (Admin)")
    
    # ISSUE 1: REAL DATA INTEGRATION
    with st.spinner("Sistem verileri veritabanından yükleniyor..."):
        # Simulated API calls to /api/employees, /api/goals, /api/departments
        df_users, df_goals, departments_list = load_real_admin_data()
    
    # Alt Sekmeler (Routing benzeri)
    admin_tabs = st.tabs([
        "📊 Genel Bakış", 
        "👥 Personel ve Departmanlar", 
        "📑 Raporlar", 
        "🔒 Yetkilendirme"
    ])
    
    # ==========================
    # 1. DASHBOARD (Genel Bakış)
    # ==========================
    with admin_tabs[0]:
        st.markdown("<h3 class='admin-header'>KPI Özetleri</h3>", unsafe_allow_html=True)
        
        # Calculate KPIs
        total_employees = df_users[df_users['role'] == 'Employee'].shape[0]
        total_goals = df_goals.shape[0]
        
        # Status mapping using Bug 4 strings
        def normalize(s):
            if pd.isna(s): return ''
            return ' '.join(str(s).strip().lower().split())

        df_goals['norm_status'] = df_goals['Gerçekleşen Değere Göre Sonuç'].apply(normalize)
        beklenen = df_goals[df_goals['norm_status'] == 'beklenen'].shape[0]
        ustunde = df_goals[df_goals['norm_status'] == 'beklenenin üstünde'].shape[0]
        altinda = df_goals[df_goals['norm_status'] == 'beklenenin altında'].shape[0]
        
        beklenen_rate = (beklenen / df_goals.shape[0]) * 100 if df_goals.shape[0] > 0 else 0
        ustunde_rate = (ustunde / df_goals.shape[0]) * 100 if df_goals.shape[0] > 0 else 0
        
        # Render KPI Cards
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Toplam Çalışan", total_employees)
        kpi2.metric("Toplam Hedef (Goal)", total_goals)
        kpi3.metric("Beklenen Oranı", f"%{beklenen_rate:.1f}")
        kpi4.metric("Beklenenin Üstünde Oranı", f"%{ustunde_rate:.1f}")
        
        st.markdown("<hr/>", unsafe_allow_html=True)
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Bar chart: Goals by department (Bug 2)
            dept_counts = df_goals['Bölüm Ana Sorumluluk Alanı'].value_counts().reset_index()
            dept_counts.columns = ['Departman', 'Hedef Sayısı']
            fig_bar = px.bar(dept_counts, x='Departman', y='Hedef Sayısı', title="Departmanlara Göre Hedef Dağılımı", color_discrete_sequence=['#2563eb'])
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Pie chart: Goal status distribution (Bug 4)
            status_counts = df_goals['Gerçekleşen Değere Göre Sonuç'].value_counts().reset_index()
            status_counts.columns = ['Durum', 'Sayı']
            # Clean up empty statuses
            status_counts = status_counts[status_counts['Durum'].astype(str).str.strip() != '']
            fig_pie = px.pie(status_counts, names='Durum', values='Sayı', title="Hedef Sonuç Dağılımı", color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col2:
            # Line chart: Yıllık Hedef Performans Trendi
            trend_data = [
                {'yil': '2023', 'toplamHedef': 85, 'beklenen': 53, 'ustunde': 18, 'altinda': 14},
                {'yil': '2024', 'toplamHedef': 106, 'beklenen': 59, 'ustunde': 26, 'altinda': 21},
                {'yil': '2025', 'toplamHedef': 112, 'beklenen': 52, 'ustunde': 26, 'altinda': 34},
            ]
            trend_df = pd.DataFrame(trend_data)
            
            import plotly.graph_objects as go
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=trend_df['yil'], y=trend_df['toplamHedef'], mode='lines+markers', name='Toplam Hedef', line=dict(color='#2563eb', width=2.5), marker=dict(size=10)))
            fig_line.add_trace(go.Scatter(x=trend_df['yil'], y=trend_df['beklenen'], mode='lines+markers', name='Beklenen', line=dict(color='#6366f1', width=2), marker=dict(size=8)))
            fig_line.add_trace(go.Scatter(x=trend_df['yil'], y=trend_df['ustunde'], mode='lines+markers', name='Beklenenin Üstünde', line=dict(color='#10b981', width=2), marker=dict(size=8)))
            fig_line.add_trace(go.Scatter(x=trend_df['yil'], y=trend_df['altinda'], mode='lines+markers', name='Beklenenin Altında', line=dict(color='#ef4444', width=2), marker=dict(size=8)))
            
            fig_line.update_layout(
                title="Yıllık Hedef Performans Trendi (2023–2025)",
                xaxis=dict(tickmode='array', tickvals=['2023', '2024', '2025'], ticktext=['2023', '2024', '2025']),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # ==========================
    # 2. PERSONEL VE DEPARTMANLAR
    # ==========================
    with admin_tabs[1]:
        st.markdown("<h3 class='admin-header'>Hedef Görüntüleme ve Yönetimi</h3>", unsafe_allow_html=True)
        col_f1, col_f2, col_f3 = st.columns(3)
        depts = ["Tümü"] + departments_list
        s_dept = col_f1.selectbox("Departman Filtresi", depts)
        
        # Bug 3: Year filter
        years = ["Tümü"] + sorted([int(y) for y in df_goals['Yıl'].unique() if pd.notna(y) and str(y).strip() != '']) if 'Yıl' in df_goals.columns else ["Tümü"]
        s_year = col_f2.selectbox("Yıl Filtresi", years)
        
        s_search = col_f3.text_input("Çalışan Ara...", placeholder="Örn: İsme göre ara...")
        
        filtered_users = df_users.copy()
        filtered_goals = df_goals.copy()
        
        if s_dept != "Tümü":
            filtered_users = filtered_users[filtered_users['department'] == s_dept]
            filtered_goals = filtered_goals[filtered_goals['Bölüm Ana Sorumluluk Alanı'] == s_dept]
            
        if s_year != "Tümü":
            # integer comparison
            filtered_goals = filtered_goals[filtered_goals['Yıl'] == int(s_year)]
            
        if s_search:
            filtered_users = filtered_users[filtered_users['name'].str.contains(s_search, case=False, na=False)]
            filtered_goals = filtered_goals[filtered_goals['İsim'].str.contains(s_search, case=False, na=False)]
            
        # Bug 1 & 4: Correct Groupby Using Sicil and Exact String Matching
        if not filtered_goals.empty and not filtered_users.empty:
            filtered_goals['norm_status'] = filtered_goals['Gerçekleşen Değere Göre Sonuç'].apply(normalize)
            
            goal_counts = filtered_goals.assign(
                beklenen=lambda x: x['norm_status'] == 'beklenen',
                ustunde=lambda x: x['norm_status'] == 'beklenenin üstünde',
                altinda=lambda x: x['norm_status'] == 'beklenenin altında'
            ).groupby('Sicil').agg(
                total_g=('Sicil', 'count'),
                beklenen=('beklenen', 'sum'),
                ustunde=('ustunde', 'sum'),
                altinda=('altinda', 'sum')
            ).reset_index()
            
            merged_stats = pd.merge(filtered_users, goal_counts, left_on='id', right_on='Sicil', how='left').fillna(0)
            
            df_display = merged_stats.rename(columns={
                'id': 'Sicil No', 'name': 'Ad Soyad', 'title': 'Unvan', 'department': 'Departman',
                'total_g': 'Hedef Sayısı', 'beklenen': 'Beklenen', 'ustunde': 'Beklenenin Üstünde', 'altinda': 'Beklenenin Altında'
            })[['Sicil No', 'Ad Soyad', 'Unvan', 'Departman', 'Hedef Sayısı', 'Beklenen', 'Beklenenin Üstünde', 'Beklenenin Altında']]
            
            # Convert counts to int
            cols_to_int = ['Hedef Sayısı', 'Beklenen', 'Beklenenin Üstünde', 'Beklenenin Altında']
            df_display[cols_to_int] = df_display[cols_to_int].astype(int)
        else:
            df_display = pd.DataFrame(columns=['Sicil No', 'Ad Soyad', 'Unvan', 'Departman', 'Hedef Sayısı', 'Beklenen', 'Beklenenin Üstünde', 'Beklenenin Altında'])
            
        st.dataframe(df_display, use_container_width=True)
        
        # Row expand simulation using an expander for editing
        st.markdown("### Hedef Düzenleme (Inline Edit Simülasyonu)")
        st.info("Kullanıcı seçip ilgili hedeflerini revize edebilirsiniz.")
        target_goal_id = left_col, right_col = st.columns([1, 3])
        edit_id = left_col.selectbox("Personel Seçiniz", [""] + list(df_display['Ad Soyad'].unique()) if not df_display.empty else [])
        edit_text = right_col.text_input("Hedef İçeriği / Revizyon Notu", placeholder="Yeni hedef içeriğini girin...")
        if st.button("Kaydet ve Revize Et"):
            if edit_id and edit_text:
                st.success(f"'{edit_id}' adlı kullanıcının hedefi başarıyla güncellendi!")
            else:
                st.warning("Lütfen bir personel seçin ve hedef metni girin.")

    # ==========================
    # 3. RAPORLAR
    # ==========================
    with admin_tabs[2]:
        html_content = generate_reports_html(df_goals, df_users)
        st.components.v1.html(html_content, height=800, scrolling=True)


    # ==========================
    # 4. YETKİLENDİRME PANELİ
    # ==========================
    with admin_tabs[3]:
        st.markdown("<h3 class='admin-header'>Sistem Rol Yönetimi</h3>", unsafe_allow_html=True)
        st.write("Kullanıcıların sisteme giriş yetkilerini buradan değiştirebilirsiniz (v1 Mockup)")
        
        # Display simple table UI for permissions
        permissions_df = df_users.copy()
        
        st.data_editor(
            permissions_df,
            column_config={
                "role": st.column_config.SelectboxColumn(
                    "Yetki Rolü",
                    help="Kullanıcının sistemdeki rolü",
                    options=["Admin", "Manager", "Employee"],
                    required=True,
                )
            },
            hide_index=True,
            use_container_width=True,
        )
        if st.button("Yetenekleri Güncelle", type="primary"):
            st.success("Rol değişiklikleri başarıyla kaydedildi! (Mock)")


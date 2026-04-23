"""
Admin Dashboard — Sadece 'Admin' rolündeki kullanıcılar görür.
3 sekme:
  1. Kurumsal Raporlar   → Hiyerarşik filtre + DataFrame + CSV indir
  2. AI İstatistikleri   → ai_status oranları, yönetici kıyası, Top5/Bot5
  3. Kullanıcı Yönetimi  → Rol & manager güncellemek için CRUD formu
"""

import streamlit as st
import pandas as pd
from src.auth import get_db_session
from src.models import User, Employee, PerformanceHistory


# ---------------------------------------------------------------------------
# Yardımcı: Tüm PH verisini DataFrame'e çevir
# ---------------------------------------------------------------------------
def _load_all_ph() -> pd.DataFrame:
    session = get_db_session()
    try:
        rows = session.query(PerformanceHistory).all()
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


# ---------------------------------------------------------------------------
# SEKMELİ ANA FONKSİYON
# ---------------------------------------------------------------------------
def render_admin_dashboard():
    """Ana Admin Dashboard — app.py tarafından çağrılır."""

    if st.session_state.get('role') != 'Admin':
        st.warning("⛔ Bu panel yalnızca Admin rolündeki kullanıcılara açıktır.")
        return

    st.markdown("## 🛡️ Admin Dashboard")
    st.markdown("---")

    tab_rep, tab_beh, tab_users = st.tabs([
        "📋 Kurumsal Raporlar",
        "🧠 Yönetici Davranış Analizi",
        "👤 Kullanıcı Yönetimi",
    ])

    # ==========================================================================
    # SEKME 1 — KURUMSAL RAPORLAR
    # ==========================================================================
    with tab_rep:
        st.subheader("📋 Kurumsal Raporlar")

        df_all = _load_all_ph()

        if df_all.empty:
            st.info("Veritabanında henüz performans kaydı yok.")
            return

        # Hiyerarşik filtre: Bölüm → Çalışan
        departments = ["Tümü"] + sorted(df_all["Bölüm"].dropna().unique().tolist())
        sel_dept = st.selectbox("Bölüm", departments, key="rep_dept")

        df_filtered = df_all if sel_dept == "Tümü" else df_all[df_all["Bölüm"] == sel_dept]

        employees_in_dept = ["Tümü"] + sorted(df_filtered["İsim"].dropna().unique().tolist())
        sel_emp = st.selectbox("Çalışan", employees_in_dept, key="rep_emp")

        if sel_emp != "Tümü":
            df_filtered = df_filtered[df_filtered["İsim"] == sel_emp]

            # Sicil Numarasını df_filtered'den çekelim
            try:
                emp_sicil = str(df_filtered["Sicil No"].iloc[0])
                st.markdown("---")
                from src.ui_components import render_locked_goals
                render_locked_goals(emp_sicil)
            except Exception:
                pass

        st.markdown("---")
        st.dataframe(df_filtered, use_container_width=True)

        # İndir butonları
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            if sel_emp != "Tümü":
                csv = df_filtered.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇️ Çalışan Raporu",
                    data=csv,
                    file_name=f"{sel_emp}_rapor.csv",
                    mime="text/csv"
                )
        with col_dl2:
            if sel_dept != "Tümü":
                csv = df_filtered.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇️ Bölüm Raporu",
                    data=csv,
                    file_name=f"{sel_dept}_bolum_raporu.csv",
                    mime="text/csv"
                )
        with col_dl3:
            csv_all = df_all.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇️ Şirket Geneli Raporu",
                data=csv_all,
                file_name="sirket_geneli_raporu.csv",
                mime="text/csv"
            )

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
        st.dataframe(df_users, use_container_width=True)

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

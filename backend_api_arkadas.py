import pandas as pd
import random
from datetime import datetime, timedelta
from src.data_loader import DataLoader
import plotly.express as px
import plotly.io as pio

class BackendAPI:
    """Mock API simulating real backend calls using real data extracted from DataLoader.
    Replacing hardcoded random user data with realistic data tied to actual employees."""
    def __init__(self):
        self.loader = DataLoader()
        random.seed(42)

    def get_goals(self) -> pd.DataFrame:
        """GET /api/goals"""
        import os
        file_path = os.path.join(self.loader.data_dir, 'Verileri_SMART Hedefler ve Gerçekleşmeler.xlsx')
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]
            if 'Yıl' in df.columns:
                df['Yıl'] = pd.to_numeric(df['Yıl'], errors='coerce').fillna(0).astype(int)
            return df
        except Exception as e:
            print("Error loading excel:", e)
            return pd.DataFrame()

    def get_employees(self) -> pd.DataFrame:
        """GET /api/employees"""
        df_goals = self.get_goals()
        if df_goals.empty:
            return pd.DataFrame()
            
        df_emp = df_goals.drop_duplicates(subset=['Sicil']).copy()
        
        data = []
        for index, row in df_emp.iterrows():
            data.append({
                "id": row['Sicil'],
                "name": row['İsim'],
                "department": row.get('Bölüm Ana Sorumluluk Alanı', ''),
                "title": row.get('Unvan', ''),
                "role": 'Employee'
            })
        return pd.DataFrame(data)

    def get_departments(self):
        """GET /api/departments"""
        df_goals = self.get_goals()
        if df_goals.empty or 'Bölüm Ana Sorumluluk Alanı' not in df_goals.columns:
            return []
        depts = df_goals['Bölüm Ana Sorumluluk Alanı'].dropna().unique().tolist()
        return sorted([d for d in depts if str(d).strip() != ''])

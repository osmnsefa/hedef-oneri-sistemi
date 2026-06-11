from src.data_loader import DataLoader
import pandas as pd

loader = DataLoader()
df = loader.get_employee_history("Murat Potuklugil", "Güçlendirme Hedefi")
print("Güçlendirme Hedefi DataFrame:")
print(df)
df2 = loader.get_employee_history("Murat Potuklugil")
print("Tüm DataFrame:")
print(df2)

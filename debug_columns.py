import pandas as pd
import os

data_dir = "guncel_veriler"
file_name = "Verileri_SMART Hedefler ve Gerçekleşmeler.xlsx"
file_path = os.path.join(data_dir, file_name)

try:
    df = pd.read_excel(file_path)
    with open("columns.txt", "w", encoding="utf-8") as f:
        for col in df.columns:
            f.write(col + "\n")
    print("Columns written to columns.txt")
except Exception as e:
    print(f"Error reading excel: {e}")

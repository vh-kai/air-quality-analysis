import requests
import pandas as pd
from pathlib import Path

API_URL = "https://www.umweltbundesamt.de/api/air_data/v4/components/json"

response = requests.get(API_URL)
response.raise_for_status()

data = response.json()

print(data) # zeigt, die Zuordnung der component ids zu den Schadstoffen und deren Einheiten

"""1 --> PM10 [µg/m³]
3 --> O3 [µg/m³]
5 --> NO2 [µg/m³]"""

# ============================================================
# Abspeichern als .csv
# ============================================================

rows = []

for key, values in data.items():
    if key not in ["count", "indices"]:
        rows.append(values)

df_components = pd.DataFrame(rows, columns=data["indices"])

df_components["component id"] = df_components["component id"].astype(int)


output_path = Path("data/processed/components.csv")
df_components.to_csv(output_path, index=False, encoding="utf-8")

print(f"Datei gespeichert: {output_path}")



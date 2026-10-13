import json
import pandas as pd
from pathlib import Path


component_names = {
    1: "PM10",
    2: "CO",
    3: "O3",
    4: "SO2",
    5: "NO2",
    6: "Pb",
    7: "BaP",
    8: "CHB",
    9: "PM2.5",
    10: "As",
    11: "Cd",
    12: "Ni"
}

# ============================================================
# 1. Funktion
# ============================================================

def prepare_station_data(data, station_id):
    station_data = data["data"][str(station_id)]

    rows = []

    for timestamp, values in station_data.items():
        components = values[3:]

        for component in components:
            component_id = component[0]
            value = component[1]

            row = {
                "station_id": station_id,
                "timestamp": timestamp,
                "component_id": component_id,
                "value": value
                }

            rows.append(row)

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)


    df["component_name"] = df["component_id"].map(component_names)

    return df


# ============================================================
# 2. Ausgewählte Stationen laden
# ============================================================

stations_path = Path("data/processed/selected_stations.json")

with open(stations_path, "r", encoding="utf-8") as file:
    stations = json.load(file)


# ============================================================
# 3. Alle Stationen verarbeiten
# ============================================================

all_dfs = []

for station in stations:
    station_id = station["station_id"]

    filename = f"station_{station_id}.json"
    path = Path("data/raw") / filename
    
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    df_station = prepare_station_data(data, station_id)
    all_dfs.append(df_station)


# ============================================================
# 4. Zusammenführen und Gruppen ergänzen
# ============================================================

df_all = pd.concat(all_dfs, ignore_index=True) # pd.concat() hängt die Tabellen untereinander und ignore_index=True erstellt einen neuen fortlaufenden Index von 0 an

station_groups = {
    str(station["station_id"]): station["group"]
    for station in stations
}

df_all["group"] = df_all["station_id"].map(station_groups)


# ============================================================
# 5. Als .csv speichern
# ============================================================

output_path = Path("data/processed/airquality_2025.csv")

df_all.to_csv(output_path, index=False, encoding="utf-8")

print(f"Datei gespeichert: {output_path}")
print(f"Anzahl Zeilen: {len(df_all)}")
print(f"Anzahl Spalten: {len(df_all.columns)}")

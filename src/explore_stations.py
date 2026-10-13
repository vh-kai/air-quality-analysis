import json
import pandas as pd
from select_stations import get_available_components
from pathlib import Path

with open("data/raw/stations.json", "r", encoding="utf-8") as file:
    data = json.load(file)

df_stations = pd.DataFrame.from_dict(
    data["data"],
    orient="index",
    columns=data["indices"]
)

print(df_stations.head())
print()
print(df_stations.shape)

""" für das Projekt sollen 5 Stationen ausgewählt werden, die
    - das komplette Jahr 2025 abdecken
    - unterschiedliche Standorttypen abdecken """

# die Datumsspalten den datatype datetime zuweisen
df_stations["station active from"] = pd.to_datetime(
    df_stations["station active from"]
)

df_stations["station active to"] = pd.to_datetime(
    df_stations["station active to"]
)

active_2025 = df_stations[
    (df_stations["station active from"] <= "2025-01-01") &
    (
        df_stations["station active to"].isna() |
        (df_stations["station active to"] >= "2025-12-31")
    )
]

print()
print(f"Stationen, die 2025 aktiv waren: {len(active_2025)}")

print()
print(active_2025["station setting name"].value_counts())

print()
print(active_2025["station type name"].value_counts())

"""die 1167 Stationen weiter eingrenzen: Für das Projekt sollen 5 Stationen abgedeckt werden, die folgende Stationstypen haben:
    - urban area + traffic
    - urban area + urban
    - suburban area + background
    - rural area + background
    - industry"""

candidates = active_2025[
    (
        (active_2025["station setting name"] == "urban area") &
        (active_2025["station type name"].isin(["traffic", "background"]))
    )
    |
    (
        (active_2025["station setting name"] == "suburban area") &
        (active_2025["station type name"] == "background")
    )
    |
    (
        (active_2025["station setting name"] == "rural area") &
        (active_2025["station type name"] == "background")
    )
    |
    (
        active_2025["station type name"] == "industry" # Industriestationen sind vergleichsweise selten (103), daher wird hier nicht weiter beschränkt
    )
]

print()
print(f"Anzahl Kandidaten: {len(candidates)}")

print(
    candidates.groupby(
        ["station setting name", "station type name"]
    ).size()
)


from select_stations import get_candidate_stations
candidates = get_candidate_stations(df_stations)
print(candidates.shape)


# Welche Urban-Traffic-Stationen haben im September 2025 mindestens einmal Messwerte für PM10, O₃ und NO₂?
urban_traffic_stations = candidates[
    (candidates["station setting name"] == "urban area") & 
    (candidates["station type name"] == "traffic")
]

print(len(urban_traffic_stations)) # Erwartet: 346



pm10_o3_no2_stations = []

"""for station_id in urban_traffic_stations["station id"]:
    components = get_available_components(station_id)

    if 1 in components and 3 in components and 5 in components:
        pm10_o3_no2_stations.append(station_id)

print(len(pm10_o3_no2_stations))
print(pm10_o3_no2_stations)"""



# ============================================================
# ausgewählte Stationen als .csv abspeichern
# ============================================================

with open("data/processed/selected_stations.json", "r", encoding="utf-8") as file:
    selected_stations = json.load(file)

selected_ids = [
    station["station_id"]
    for station in selected_stations
]

df_selected_stations = df_stations[
    df_stations["station id"].astype(str).isin(selected_ids)
].copy()

print(df_selected_stations.shape)
print(df_selected_stations["station id"])

station_groups = {
    str(station["station_id"]): station["group"]
    for station in selected_stations
}

df_selected_stations["group"] = (
    df_selected_stations["station id"]
    .astype(str)
    .map(station_groups)
)



output_path = Path("data/processed/stations.csv")
df_selected_stations.to_csv(output_path, index=False, encoding="utf-8")

print(f"Datei gespeichert: {output_path}")
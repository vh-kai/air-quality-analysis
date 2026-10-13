import json
import numpy as np
import pandas as pd
import requests
from pathlib import Path


# ============================================================
# Daten laden
# ============================================================

with open("data/raw/stations.json", "r", encoding="utf-8") as file:
    data = json.load(file)

df_stations = pd.DataFrame.from_dict(
    data["data"],
    orient="index",
    columns=data["indices"]
)

# Datumsspalten in datetime umwandeln
df_stations["station active from"] = pd.to_datetime(
    df_stations["station active from"]
)

df_stations["station active to"] = pd.to_datetime(
    df_stations["station active to"]
)

# ============================================================
# Funktionen zur Stationsauswahl
# ============================================================

def get_candidate_stations(df_stations):
    #Erstellt einen DataFrame mit allen Stationen, die im gesamten Jahr 2025 aktiv waren und für die Auswahl relevanten Standorttypen besitzen.
    
    active_2025 = df_stations[
        (df_stations["station active from"] <= "2025-01-01") &
        (
            df_stations["station active to"].isna() |
            (df_stations["station active to"] >= "2025-12-31")
        )
    ]

    # Auswahl der gewünschten Standort-/Stationstypen
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
        # Industriestationen sind vergleichsweise selten.
        # Daher werden sie hier nicht weiter eingeschränkt.
        (active_2025["station type name"] == "industry")
    ]

    return candidates


def add_station_groups(candidates):
    """
    Ordnet die Kandidaten fünf Gruppen zu:

    - urban_traffic
    - urban_background
    - suburban_background
    - rural_background
    - industry
    """

    conditions = [
        (
            (candidates["station setting name"] == "urban area") &
            (candidates["station type name"] == "traffic")
        ),
        (
            (candidates["station setting name"] == "urban area") &
            (candidates["station type name"] == "background")
        ),
        (
            (candidates["station setting name"] == "suburban area") &
            (candidates["station type name"] == "background")
        ),
        (
            (candidates["station setting name"] == "rural area") &
            (candidates["station type name"] == "background")
        ),
        (
            candidates["station type name"] == "industry"
        )
    ]

    choices = [
        "urban_traffic",
        "urban_background",
        "suburban_background",
        "rural_background",
        "industry"
    ]

    candidates["group"] = np.select(
        conditions,
        choices,
        default="other"
    )

    return candidates


def select_stations_by_group(candidates, n=20):
    # Wählt zufällig n Stationen aus jeder Gruppe aus.

    selected = candidates.groupby("group").sample(
        n=n,
        random_state=42
    )

    return selected


def get_available_components(station_id):
    """
    Ermittelt, welche Komponenten für eine Station im Testzeitraum September 2025 vorhanden sind.
    Rückgabe: Menge der component_ids, z. B. {1, 3, 5}
    """
    data = check_station_data(station_id, "2025-09-01", "2025-09-30")

    if not data["data"]:
        return set()  # Falls keine Messdaten zurückgegeben wurden, wird eine leere Menge zurückgegeben.

    station_data = data["data"][str(station_id)]

    component_ids = set()

    # Alle Zeitpunkte der Station durchlaufen
    for timestamp, values in station_data.items():

        # Die Komponenten beginnen ab Index 3
        components = values[3:]

        for component in components:

            component_id = component[0]

            component_ids.add(component_id)

    return component_ids


def get_components_2025(station_id):
    """
    Ermittelt, wie viele Messwerte es für jede relevante Komponente im gesamten Jahr 2025 gibt.
    Rückgabe: Anzahl an Messwerten pro Station und Komponente.
    """
    data = check_station_data(station_id, "2025-01-01", "2025-12-31")

    if not data["data"]:
        return {}  # Falls keine Messdaten zurückgegeben wurden, wird ein leeres Dictionary zurückgegeben.

    station_data = data["data"][str(station_id)]

    count_pm10 = 0
    count_o3 = 0
    count_no2 = 0

    for timestamp, values in station_data.items():
        components = values[3:]
        for component in components:
            if component[0] == 1:
                count_pm10 += 1
            elif component[0] == 3:
                count_o3 += 1
            elif component[0] == 5:
                count_no2 += 1

    return {
        "PM10": count_pm10, 
        "O3": count_o3, 
        "NO2": count_no2
    }


def select_final_stations(df_measurements):
    measurements_95 = df_measurements[(df_measurements["PM10_%"] >= 95) & (df_measurements["O3_%"] >= 95) & (df_measurements["NO2_%"] >= 95)]

    measurements_95["mean_coverage"] = (measurements_95["PM10_%"] + measurements_95["O3_%"] + measurements_95["NO2_%"]) / 3

    measurements_95_grouped = measurements_95.groupby("group")

    best_indices = measurements_95_grouped["mean_coverage"].idxmax()

    final_stations = measurements_95.loc[best_indices]

    return final_stations


def save_selected_stations(final_stations, path):
    selected = final_stations[["station_id", "group"]].to_dict(orient="records")

    with open(path, "w", encoding="utf-8") as file:
        json.dump(selected, file, ensure_ascii=False, indent=2)


# ============================================================
# Funktionen für die API-Abfrage
# ============================================================

API_URL = "https://www.umweltbundesamt.de/api/air_data/v4/airquality/json"

def check_station_data(station_id, date_from, date_to):
    # Ruft Messdaten einer Station für den Testzeitraum ab.

    params = {
        "date_from": date_from,
        "time_from": 1,
        "date_to": date_to,
        "time_to": 24,
        "station": station_id
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()

    data = response.json()

    return data


# ============================================================
# Hauptprogramm
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # 1. Kandidaten bestimmen
    # --------------------------------------------------------

    candidates = get_candidate_stations(df_stations)

    print("Anzahl Kandidaten:", len(candidates))

    print(
        candidates.groupby(
            ["station setting name", "station type name"]
        ).size()
    )

    # --------------------------------------------------------
    # 2. Kandidaten den fünf Gruppen zuordnen
    # --------------------------------------------------------

    candidates = add_station_groups(candidates)

    # Überprüfen, ob alle Stationen einer Gruppe
    # zugeordnet werden konnten.
    print("\nStationen pro Gruppe:")
    print(candidates["group"].value_counts())

    # --------------------------------------------------------
    # 3. Zufällige Stichprobe pro Gruppe auswählen
    # --------------------------------------------------------

    selected_stations = select_stations_by_group(
        candidates,
        n=20
    )

    print("\nAusgewählte Stationen pro Gruppe:")
    print(selected_stations["group"].value_counts())

    print("\nAusgewählte Stationen:")
    print(
        selected_stations[
            [
                "station id",
                "station code",
                "station name",
                "station setting name",
                "station type name",
                "group"
            ]
        ]
    )

    # --------------------------------------------------------
    # 4. Verfügbarkeit der relevanten Komponenten prüfen
    # --------------------------------------------------------

    results = []

    for _, station in selected_stations.iterrows():

        station_id = station["station id"]
        components = get_available_components(station_id)

        result = {
            "station_id": station_id,
            "group": station["group"],
            "PM10": 1 in components,
            "O3": 3 in components,
            "NO2": 5 in components
        }

        results.append(result)

    # Ergebnisse in einen DataFrame umwandeln
    df_availability = pd.DataFrame(results)

    print("\nKomponentenverfügbarkeit:")
    print(df_availability)

    # --------------------------------------------------------
    # 5. Stationen mit allen drei relevanten Komponenten
    # --------------------------------------------------------

    suitable_stations = df_availability[
        (df_availability["PM10"]) &
        (df_availability["O3"]) &
        (df_availability["NO2"])
    ]

    print("\nGeeignete Stationen:")
    print(suitable_stations)

    print("\nGeeignete Stationen pro Gruppe:")
    print(suitable_stations["group"].value_counts())

    # --------------------------------------------------------
    # 6. Urban-traffic-Stationen vollständig prüfen (keine geeigneten Stationen in der Stichprobe enthalten)
    # --------------------------------------------------------

    urban_traffic_stations = candidates[candidates["group"] == "urban_traffic"]

    urban_traffic_results = []

    for _, station in urban_traffic_stations.iterrows():

        station_id = station["station id"]
        components = get_available_components(station_id)

        result = {
            "station_id": station_id,
            "group": station["group"],
            "PM10": 1 in components,
            "O3": 3 in components,
            "NO2": 5 in components
        }

        urban_traffic_results.append(result)

    df_urban_traffic = pd.DataFrame(urban_traffic_results)

    urban_traffic_suitable = df_urban_traffic[
        (df_urban_traffic["PM10"]) &
        (df_urban_traffic["O3"]) &
        (df_urban_traffic["NO2"])
    ]

    # --------------------------------------------------------
    # 7. Zusammenführen von suitable_stations und urban_traffic_suitable
    # --------------------------------------------------------

    suitable_stations = pd.concat(
        [suitable_stations, urban_traffic_suitable],
        ignore_index=True
    )

    print("\nAlle geeigneten Stationen:")
    print(suitable_stations)

    print("\nGeeignete Stationen pro Gruppe:")
    print(suitable_stations["group"].value_counts())

    print("\nAnzahl geeigneter Stationen insgesamt:")
    print(len(suitable_stations))

    # --------------------------------------------------------
    # 8. Zählen der Messwerte pro Station und Komponente
    # --------------------------------------------------------

    results = []

    for _, station in suitable_stations.iterrows():
        station_id = station["station_id"]

        counts = get_components_2025(station_id)

        result = {
            "station_id": station_id,
            "group": station["group"],
            "PM10": counts["PM10"],
            "O3": counts["O3"],
            "NO2": counts["NO2"] 
        }

        results.append(result)

    df_measurements = pd.DataFrame(results)

    # --------------------------------------------------------
    # 9. Prozentuale Anteile Komponenten berechnen (1 Jahr entspricht 8760 h)
    # --------------------------------------------------------

    df_measurements["PM10_%"] = df_measurements["PM10"] /8760 * 100
    df_measurements["O3_%"] = df_measurements["O3"] /8760 * 100
    df_measurements["NO2_%"] = df_measurements["NO2"] /8760 * 100

    print(df_measurements)

    # --------------------------------------------------------
    # 10. Finale Auswahl der Stationen abspeichern
    # --------------------------------------------------------

    final_stations = select_final_stations(df_measurements)

    SELECTED_STATIONS_PATH = Path("data/processed/selected_stations.json")

    save_selected_stations(final_stations, SELECTED_STATIONS_PATH)

    print(f"Ausgewählte Stationen gespeichert unter: {SELECTED_STATIONS_PATH}")

    print(final_stations)
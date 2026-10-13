import requests
import json
from pathlib import Path


API_URL = "https://www.umweltbundesamt.de/api/air_data/v4/stations/json"

RAW_DATA_PATH = Path("data/raw/stations.json") # Speicherort der heruntergeladenen Rohdaten

def download_stations():
    response = requests.get(API_URL)
    response.raise_for_status() # wenn die API einen Fehler zurückgibt, gibt Python an dieser Stelle eine Fehlermeldung zurück, bei '200' läuft das Programm weiter
    return response.json()

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2) # schreibt die Daten als JSON-Datei




API_URL = "https://www.umweltbundesamt.de/api/air_data/v4/airquality/json"

def download_airquality(station_id, date_from, date_to):

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

def load_selected_stations(path):
    with open(path, "r", encoding="utf-8") as file:
        stations = json.load(file)

    return stations






#if __name__ == "__main__": # dieser Teil wird nur ausgeführt, wenn die Datei direkt gestartet wird

    data = download_stations()
    print(f"Anzahl Stationen: {data['count']}")
    save_json(data, RAW_DATA_PATH)
    print(f"Datei gespeichert unter: {RAW_DATA_PATH}")


if __name__ == "__main__":

    data = download_airquality(172, "2025-01-01", "2025-01-31")
    print(data.keys())

    stations = load_selected_stations("data/processed/selected_stations.json")

    for station in stations:
        station_id = station["station_id"]

        data = download_airquality(
            station_id,
            "2025-01-01",
            "2025-12-31"
        )

        filename = f"station_{station_id}.json"
        path = Path("data/raw") / filename
        save_json(data, path)

        print(f"Station {station_id} gespeichert unter: {path}")

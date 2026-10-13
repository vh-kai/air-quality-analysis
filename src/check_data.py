import pandas as pd
from pathlib import Path

# ============================================================
# Daten laden
# ============================================================

data_path = Path("data/processed/airquality_2025.csv")

df = pd.read_csv(
    data_path,
    parse_dates=["timestamp"]
)

# ============================================================
# Datenprüfung
# ============================================================

print("Datentypen: \n", df.dtypes)

print("\nAnzahl Tabellenzeilen:", len(df))
print("Anzahl Tabellenspalten:", len(df.columns))
print("Frühester Zeitstempel:", df["timestamp"].min())
print("Spätester Zeistempel:", df["timestamp"].max())

print("\nvorhandene component_id:", sorted(df["component_id"].unique()))
print("vorhandene station_id:", sorted(df["station_id"].unique()))
print("Messwerte ohne Schadstoffname:", df["component_name"].isna().sum())
print("Negative Messwerte:", (df["value"] < 0).sum())
print("\nfehlende Werte:\n", df.isna().sum())

print(
    "\nDoppelte Messungen:",
    df.duplicated(                  # duplicated() prüft, ob Zeilen Duplikate sind, subset enthält die für den Vergleich relevanten Spalten
        subset=["station_id", "timestamp", "component_id"]
    ).sum()
)

print(
    "\nZuordnung component_id zu component_name:\n",
    df[["component_id", "component_name"]]
    .drop_duplicates()
    .sort_values("component_id")
    .to_string(index=False)
)

print(
    "\nAnzahl unterschiedlicher Namen je component_id:",
    df.groupby("component_id")["component_name"]
    .nunique()
)

# Auf Zeitlücken prüfen, pro Station und Parameter + prozentuale Abdeckung
expected = pd.date_range(
    start="2025-01-01 00:00:00",
    end="2025-12-31 23:00:00",
    freq="h"
)

results = []

for (station_id, component_name), group in df.groupby(
    ["station_id", "component_name"]):

    timestamps = pd.DatetimeIndex(group["timestamp"].dropna().unique())

    missing = expected.difference(timestamps)

    results.append({
        "station_id": station_id,
        "component_name": component_name,
        "available_values": len(timestamps),
        "missing_hours": len(missing),
        "coverage_percent": round(len(timestamps) / len(expected) * 100, 2)
    })

df_gaps = pd.DataFrame(results)

print(
    "\nPrüfung auf Zeitlücken und prozentuale Abdeckung:\n",
    df_gaps.sort_values(
        ["station_id", "component_name"]
    ).to_string(index=False)
)


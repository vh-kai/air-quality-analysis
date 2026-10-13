-- Wie unterscheiden sich die durchschnittlichen Messwerte eines Schadstoffs im Jahr 2025 zwischen den fünf ausgewählten Stationen?

SELECT strftime('%Y', a.timestamp) AS year,
	a.station_id AS "station id",
	s.station_name AS "station name",
	a.component_name AS "component name",
	ROUND(AVG(a.value), 2) AS "mean value",
	c.component_unit AS unit
FROM airquality_2025 a
LEFT JOIN stations s
	ON a.station_id = s.station_id
LEFT JOIN components c
	ON c.component_id = a.component_id
WHERE a.component_name IN('PM10', 'O3', 'NO2')
GROUP BY a.station_id, s.station_name, year, a.component_name, c.component_unit
ORDER BY a.station_id, a.component_name
;

-- statt Jahresmittelwerte die Mittelwerte der Monate aller einzelnen Stationen für jeden Schadstoff berechnen

SELECT strftime('%Y-%m', a.timestamp) AS "year-month",
	a.station_id AS "station id",
	s.station_name AS "station name",
	a.component_name AS "component name",
	ROUND(AVG(a.value), 2) AS "mean value",
	c.component_unit AS unit
FROM airquality_2025 a
LEFT JOIN stations s
	ON a.station_id = s.station_id
LEFT JOIN components c
	ON c.component_id = a.component_id
WHERE a.component_name IN('PM10', 'O3', 'NO2')
GROUP BY a.station_id, "year-month", s.station_name, a.component_name, c.component_unit
ORDER BY a.station_id, "year-month", a.component_name
;

-- Anzahl der Schadstoff-Messwerte pro Station und Jahr-Monat

SELECT station_id,
	strftime('%Y-%m', timestamp) AS "year-month",
	component_name,
	COUNT(value) AS "number of values"
FROM airquality_2025
GROUP BY station_id, "year-month", component_name
ORDER BY station_id, "year-month", component_name
;
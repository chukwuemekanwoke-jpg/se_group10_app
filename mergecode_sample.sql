USE bike_app;

SELECT
  DATE_FORMAT(a.last_update, '%Y-%m-%d %H:00:00') AS hour_bucket,
  AVG(a.available_bikes) AS avg_available_bikes,
  MAX(w.temp) AS temp
FROM availability a
LEFT JOIN weather_current w
  ON DATE_FORMAT(a.last_update, '%Y-%m-%d %H:00:00') = DATE_FORMAT(w.dt_utc, '%Y-%m-%d %H:00:00')
GROUP BY hour_bucket
ORDER BY hour_bucket DESC
LIMIT 24;
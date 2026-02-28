CREATE DATABASE IF NOT EXISTS bike_app;
USE bike_app;

CREATE TABLE IF NOT EXISTS station (
  number INT NOT NULL,
  contract_name VARCHAR(64),
  name VARCHAR(256),
  address VARCHAR(256),
  banking TINYINT,
  bonus TINYINT,
  bike_stands INT,
  position_lat DOUBLE,
  position_lng DOUBLE,
  status VARCHAR(32),
  PRIMARY KEY (number)
);

CREATE TABLE IF NOT EXISTS availability (
  number INT NOT NULL,
  last_update DATETIME NOT NULL,
  available_bikes INT,
  available_bike_stands INT,
  status VARCHAR(32),
  PRIMARY KEY (number, last_update),
  CONSTRAINT fk_station FOREIGN KEY (number) REFERENCES station(number),
  INDEX idx_last_update (last_update)
);

CREATE TABLE IF NOT EXISTS weather_current (
  dt_unix INT NOT NULL,
  dt_utc DATETIME,
  city_id INT,
  city_name VARCHAR(128),
  lat DOUBLE,
  lon DOUBLE,
  temp DOUBLE,
  feels_like DOUBLE,
  temp_min DOUBLE,
  temp_max DOUBLE,
  pressure INT,
  humidity INT,
  visibility INT,
  wind_speed DOUBLE,
  wind_deg INT,
  clouds_all INT,
  rain_1h DOUBLE,
  snow_1h DOUBLE,
  weather_id INT,
  weather_main VARCHAR(64),
  weather_desc VARCHAR(128),
  weather_icon VARCHAR(16),
  PRIMARY KEY (dt_unix),
  INDEX idx_dt_utc (dt_utc)
);
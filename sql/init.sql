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
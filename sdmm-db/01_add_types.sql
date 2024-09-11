-- add_type.sql
SET
    NAMES utf8mb4;

INSERT INTO
    SensorTypes (type_id, type_name, unit)
VALUES
    (UUID (), 'Temperature', '°C'),
    (UUID (), 'Humidity', '%'),
    (UUID (), 'CO2 Concentration', 'ppm');
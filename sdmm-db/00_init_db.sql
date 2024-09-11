-- init_db.sql
CREATE DATABASE IF NOT EXISTS sensor_db;

USE sensor_db;

CREATE TABLE
    IF NOT EXISTS Sensors (
        sensor_id CHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        location VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        status ENUM ('active', 'inactive', 'deleted') DEFAULT 'inactive',
        deleted_at TIMESTAMP NULL
    );

CREATE TABLE
    IF NOT EXISTS SensorTypes (
        type_id CHAR(36) PRIMARY KEY,
        type_name VARCHAR(255) NOT NULL,
        unit VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    IF NOT EXISTS SensorTypeMappings (
        mapping_id CHAR(36) PRIMARY KEY,
        sensor_id CHAR(36),
        type_id CHAR(36),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES Sensors (sensor_id),
        FOREIGN KEY (type_id) REFERENCES SensorTypes (type_id)
    );

CREATE TABLE
    IF NOT EXISTS SensorData (
        data_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        sensor_id CHAR(36),
        type_id CHAR(36),
        timestamp TIMESTAMP,
        value FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (sensor_id) REFERENCES Sensors (sensor_id),
        FOREIGN KEY (type_id) REFERENCES SensorTypes (type_id)
    );

CREATE TABLE
    IF NOT EXISTS SensorMetadata (
        metadata_id CHAR(36) PRIMARY KEY,
        sensor_id CHAR(36),
        meta_key VARCHAR(255),
        meta_value VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (sensor_id) REFERENCES Sensors (sensor_id)
    );

CREATE TABLE
    IF NOT EXISTS SensorStatusHistory (
        status_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        sensor_id CHAR(36),
        status ENUM ('normal', 'warning', 'offline', 'disabled'),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES Sensors (sensor_id)
    );

CREATE TABLE
    IF NOT EXISTS Alerts (
        alert_id CHAR(36) PRIMARY KEY,
        sensor_id CHAR(36),
        alert_type ENUM ('threshold breach', 'connection issue', 'other') NOT NULL,
        message VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        status ENUM ('new', 'acknowledged', 'resolved') DEFAULT 'new',
        FOREIGN KEY (sensor_id) REFERENCES Sensors (sensor_id)
    );
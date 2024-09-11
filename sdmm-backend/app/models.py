# app/models.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import CHAR, ENUM

db = SQLAlchemy()


class Sensor(db.Model):
    __tablename__ = 'Sensors'

    sensor_id = db.Column(CHAR(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    status = db.Column(ENUM('active', 'inactive', 'deleted'), default='inactive')
    deleted_at = db.Column(db.TIMESTAMP, nullable=True)

    # Relationship to alerts (one-to-many)
    alerts = db.relationship('Alert', backref='sensor', lazy=True)

    def to_dict(self):
        return {
            'sensor_id': self.sensor_id,
            'name': self.name,
            'location': self.location,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'deleted_at': self.deleted_at
        }


class Alert(db.Model):
    __tablename__ = 'Alerts'

    alert_id = db.Column(CHAR(36), primary_key=True)
    sensor_id = db.Column(CHAR(36), db.ForeignKey('Sensors.sensor_id'), nullable=False)
    alert_type = db.Column(ENUM('threshold breach', 'connection issue', 'other'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    is_deleted = db.Column(db.Boolean, default=False)
    status = db.Column(ENUM('new', 'acknowledged', 'resolved'), default='new')

    def to_dict(self):
        return {
            'alert_id': self.alert_id,
            'sensor_id': self.sensor_id,
            'alert_type': self.alert_type,
            'message': self.message,
            'created_at': self.created_at,
            'is_deleted': self.is_deleted,
            'status': self.status
        }


class SensorType(db.Model):
    __tablename__ = 'SensorTypes'

    type_id = db.Column(CHAR(36), primary_key=True)
    type_name = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(50))
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'type_id': self.type_id,
            'type_name': self.type_name,
            'unit': self.unit,
            'created_at': self.created_at
        }


class SensorTypeMapping(db.Model):
    __tablename__ = 'SensorTypeMappings'

    mapping_id = db.Column(CHAR(36), primary_key=True)
    sensor_id = db.Column(CHAR(36), db.ForeignKey('Sensors.sensor_id'))
    type_id = db.Column(CHAR(36), db.ForeignKey('SensorTypes.type_id'))
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    # Relationships (optional)
    sensor = db.relationship('Sensor', backref=db.backref('sensor_type_mappings', lazy=True))
    sensor_type = db.relationship('SensorType', backref=db.backref('sensor_type_mappings', lazy=True))

    def to_dict(self):
        return {
            'mapping_id': self.mapping_id,
            'sensor_id': self.sensor_id,
            'type_id': self.type_id,
            'created_at': self.created_at
        }


class SensorData(db.Model):
    __tablename__ = 'SensorData'

    data_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sensor_id = db.Column(CHAR(36), db.ForeignKey('Sensors.sensor_id'))
    type_id = db.Column(CHAR(36), db.ForeignKey('SensorTypes.type_id'))
    timestamp = db.Column(db.TIMESTAMP)
    value = db.Column(db.Float)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships (optional)
    sensor = db.relationship('Sensor', backref=db.backref('sensor_data', lazy=True))
    sensor_type = db.relationship('SensorType', backref=db.backref('sensor_data', lazy=True))

    def to_dict(self):
        return {
            'data_id': self.data_id,
            'sensor_id': self.sensor_id,
            'type_id': self.type_id,
            'timestamp': self.timestamp,
            'value': self.value,
            'created_at': self.created_at,
            'is_deleted': self.is_deleted
        }


class SensorMetadata(db.Model):
    __tablename__ = 'SensorMetadata'

    metadata_id = db.Column(CHAR(36), primary_key=True)
    sensor_id = db.Column(CHAR(36), db.ForeignKey('Sensors.sensor_id'))
    meta_key = db.Column(db.String(255))
    meta_value = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships (optional)
    sensor = db.relationship('Sensor', backref=db.backref('sensor_metadata', lazy=True))

    def to_dict(self):
        return {
            'metadata_id': self.metadata_id,
            'sensor_id': self.sensor_id,
            'meta_key': self.meta_key,
            'meta_value': self.meta_value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_deleted': self.is_deleted
        }


class SensorStatusHistory(db.Model):
    __tablename__ = 'SensorStatusHistory'

    status_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sensor_id = db.Column(CHAR(36), db.ForeignKey('Sensors.sensor_id'))
    status = db.Column(ENUM('normal', 'warning', 'offline', 'disabled'))
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    # Relationships (optional)
    sensor = db.relationship('Sensor', backref=db.backref('sensor_status_history', lazy=True))

    def to_dict(self):
        return {
            'status_id': self.status_id,
            'sensor_id': self.sensor_id,
            'status': self.status,
            'timestamp': self.timestamp,
            'created_at': self.created_at
        }

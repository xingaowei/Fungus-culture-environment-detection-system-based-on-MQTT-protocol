# app/config.py

class Config:
    DB_HOST = 'sdmm_db'
    DB_PORT = 3306
    DB_USER = 'root'
    DB_PASSWORD = 'Ptkmao4pghq197p1/UoOatjdmWgCCMb2'
    DB_DATABASE = 'sensor_db'

    SQLALCHEMY_DATABASE_URI = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

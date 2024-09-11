# Dockerfile

FROM mysql:8.0

ENV MYSQL_ROOT_PASSWORD=Ptkmao4pghq197p1/UoOatjdmWgCCMb2
ENV MYSQL_DATABASE=sensor_db

COPY ./00_init_db.sql /docker-entrypoint-initdb.d/
COPY ./01_add_types.sql /docker-entrypoint-initdb.d/

EXPOSE 3306

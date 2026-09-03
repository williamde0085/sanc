#!/bin/bash
set -e

# отдельная роль для приложения (не суперюзер) + своя схема serving.
# запускается один раз при инициализации пустого тома, от лица POSTGRES_USER.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
create extension if not exists pg_trgm;
create role $SERVING_DB_USER login password '$SERVING_DB_PASSWORD';
create schema serving authorization $SERVING_DB_USER;
alter role $SERVING_DB_USER set search_path = serving, public;
SQL

# таблицы создаём уже от лица serving-роли, чтобы она была владельцем
psql -v ON_ERROR_STOP=1 --username "$SERVING_DB_USER" --dbname "$POSTGRES_DB" -f /db/schema.sql

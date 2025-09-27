#!/bin/bash
# Read MySQL credentials from mounted secrets
export MYSQL_ROOT_PASSWORD=$(cat /etc/secrets/DB_ROOT_PASSWORD)
export MYSQL_USER=$(cat /etc/secrets/DB_USER)
export MYSQL_PASSWORD=$(cat /etc/secrets/DB_PASSWORD)

# Start MySQL
exec docker-entrypoint.sh mysqld

#!/bin/sh

echo "Aguardando MySQL em $1:3306..."

while ! nc -z "$1" 3306; do
    sleep 1
done

echo "MySQL disponível!"

shift
exec "$@"

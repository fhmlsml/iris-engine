#!/bin/sh

export DB_USER=your-preferred-db-username
export DB_NAME=your-preferred-db-name
export DB_PASS=your-preferred-db-pass
export PROJECT_ID=your-own-gcp-project-id
export TITLE_ENV=title-env
export JWT_SECRET=random-jwt-secret-for-development
export OPS_SECRET_KEY=random-ops-key-for-development

docker-compose rm -f -s -v irisapp

envsubst < docker-compose.yaml | docker-compose -f - up -d irisapp
# docker-compose up -d irisapp

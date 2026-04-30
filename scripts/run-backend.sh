#!/bin/bash

echo "======================================="
echo " Iniciando prueba tecnica siata Backend"
echo "======================================="

poetry run uvicorn app.main:app --reload --host localhost --port 8000
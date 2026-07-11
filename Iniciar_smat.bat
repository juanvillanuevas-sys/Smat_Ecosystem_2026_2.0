@echo off
title Lanzador del Ecosistema SMAT - FISI 2026
echo ====================================================
echo    INICIANDO COMPONENTES DEL SISTEMA SMAT
echo ====================================================

:: 1. Backend FastAPI
echo [1/3] Levantando Servidor Cloud FastAPI...
start "FastAPI Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"

:: Esperar 3 segundos
timeout /t 3 /nobreak > nul

:: 2. Bridge MQTT
echo [2/3] Activando Middleware MQTT Bridge...
start "MQTT Bridge" cmd /k "cd iot_device && python mqtt_bridge.py"

:: 3. Simulacion Godot
echo [3/3] Lanzando Interfaz Grafica de Simulacion...
cd simulation\dist\
start SMAT_Monitor.exe

echo ====================================================
echo Todo el ecosistema esta corriendo en simultaneo!
echo ====================================================
pause
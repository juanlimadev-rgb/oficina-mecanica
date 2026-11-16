@echo off
setlocal
title Sistema para Oficina Mecanica
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto :erro
)
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if errorlevel 1 goto :erro
echo.
echo Primeiro acesso: em outro terminal, execute:
echo .venv\Scripts\python.exe -m flask --app app create-user
echo.
echo Abra http://127.0.0.1:5000/login
.venv\Scripts\python.exe app.py
if errorlevel 1 goto :erro
exit /b 0
:erro
echo Nao foi possivel iniciar. Confira a mensagem acima.
pause
exit /b 1

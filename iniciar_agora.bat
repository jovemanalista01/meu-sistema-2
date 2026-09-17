@echo off
chcp 65001 >nul
title LogiScale
echo ============================================================
echo   LogiScale - Iniciando o sistema...
echo ============================================================

where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no seu computador.
    echo Instale o Python em https://www.python.org/downloads/
    echo IMPORTANTE: marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

if not exist venv (
    echo Preparando o sistema pela primeira vez, aguarde...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install --upgrade pip >nul
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

python run.py
pause

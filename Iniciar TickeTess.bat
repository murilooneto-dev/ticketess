@echo off
setlocal
cd /d "%~dp0backend"

rem Se ja existe um servidor rodando em 8000, so abre o navegador
curl -s -o nul -m 1 http://localhost:8000/api/system/health
if %errorlevel% equ 0 (
    echo TickeTess ja esta em execucao.
    start "" http://localhost:8000
    exit /b 0
)

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado.
    echo Execute scripts\install.ps1 primeiro para instalar o sistema.
    pause
    exit /b 1
)

if not exist "..\frontend\dist\index.html" (
    echo Build do frontend nao encontrado.
    echo Execute scripts\install.ps1 primeiro, ou "npm run build" na pasta frontend.
    pause
    exit /b 1
)

echo Iniciando o TickeTess...
start "" ".venv\Scripts\pythonw.exe" tray.py

echo Aguardando o servidor ficar pronto...
set tries=0

:waitloop
set /a tries+=1
curl -s -o nul -m 1 http://localhost:8000/api/system/health
if %errorlevel% equ 0 goto ready
if %tries% geq 40 goto timeout
timeout /t 1 /nobreak >nul
goto waitloop

:ready
echo TickeTess esta rodando. Veja o icone dele na bandeja do Windows (perto do relogio) para abrir ou encerrar.
exit /b 0

:timeout
echo.
echo O servidor demorou para responder.
echo Verifique se o icone do TickeTess apareceu na bandeja do Windows.
pause
exit /b 1

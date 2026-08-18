<#
    Instalação inicial do DevControl.
    Cria o ambiente virtual do backend, instala dependências, aplica
    migrations e gera o build de produção do frontend.
#>
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "== DevControl: instalação ==" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $backend ".venv"))) {
    Write-Host "Criando ambiente virtual Python..."
    python -m venv (Join-Path $backend ".venv")
}

$venvPython = Join-Path $backend ".venv\Scripts\python.exe"

Write-Host "Instalando dependências do backend..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $backend "requirements.txt")

$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Copiando .env.example para .env..."
    Copy-Item (Join-Path $root ".env.example") $envFile
}

Write-Host "Aplicando migrations do banco de dados..."
Push-Location $backend
& $venvPython -m alembic upgrade head
Pop-Location

Write-Host "Instalando dependências do frontend..."
Push-Location $frontend
npm install
Write-Host "Gerando build de produção do frontend..."
npm run build
Pop-Location

Write-Host ""
Write-Host "== Instalação concluída ==" -ForegroundColor Green
Write-Host "1. Edite o arquivo .env (principalmente ADMIN_PASSWORD) antes de usar em produção."
Write-Host "2. Para iniciar manualmente: scripts\start.ps1"
Write-Host "3. Para iniciar automaticamente com o Windows (como Administrador): scripts\register_startup_task.ps1"
Write-Host "4. Para liberar o acesso pela rede local (como Administrador): scripts\open_firewall_port.ps1"

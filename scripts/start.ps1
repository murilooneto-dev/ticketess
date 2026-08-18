<#
    Inicia o servidor do DevControl (backend FastAPI, que também serve
    o frontend compilado). Usado tanto para start manual quanto pela
    tarefa agendada de inicialização automática.
#>
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Error "Ambiente virtual não encontrado. Execute scripts\install.ps1 primeiro."
    exit 1
}

Set-Location $backend
& $venvPython run.py

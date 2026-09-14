# Instala o app desktop (Electron) do TickeTess e cria um atalho na
# Area de Trabalho. Precisa que a instalacao normal (scripts/install.ps1)
# ja tenha sido feita antes (venv do backend + build do frontend).

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopDir = Join-Path $repoRoot "desktop"
$electronExe = Join-Path $desktopDir "node_modules\electron\dist\electron.exe"
$iconPath = Join-Path $desktopDir "build\icon.ico"

Write-Host "Instalando dependencias do app desktop..."
Push-Location $desktopDir
try {
    npm install
} finally {
    Pop-Location
}

if (-not (Test-Path $electronExe)) {
    throw "Electron nao foi encontrado em $electronExe apos o npm install."
}

$desktopFolder = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopFolder "TickeTess.lnk"

Write-Host "Criando atalho em $shortcutPath..."
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $electronExe
$shortcut.Arguments = "."
$shortcut.WorkingDirectory = $desktopDir
if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}
$shortcut.Description = "TickeTess"
$shortcut.Save()

Write-Host "Pronto! Clique no icone 'TickeTess' na Area de Trabalho para abrir o app."

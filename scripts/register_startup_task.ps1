<#
    Registra o DevControl para iniciar automaticamente com o Windows,
    usando o Agendador de Tarefas nativo (sem serviços externos, sem
    Docker). Execute como Administrador.
#>
$ErrorActionPreference = "Stop"

$taskName = "DevControl"
$root = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $root "scripts\start.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startScript`""

$trigger = New-ScheduledTaskTrigger -AtStartup

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings `
    -Description "Inicia o servidor DevControl na inicialização do Windows" -Force | Out-Null

Write-Host "Tarefa agendada '$taskName' registrada." -ForegroundColor Green
Write-Host "O DevControl iniciará automaticamente com o Windows a partir de agora."
Write-Host "Para iniciar imediatamente sem reiniciar: Start-ScheduledTask -TaskName '$taskName'"

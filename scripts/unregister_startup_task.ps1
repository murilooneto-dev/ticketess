<#
    Remove a tarefa agendada de inicialização automática do DevControl.
    Execute como Administrador.
#>
$ErrorActionPreference = "Stop"

$taskName = "DevControl"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Tarefa agendada '$taskName' removida." -ForegroundColor Green
} else {
    Write-Host "Nenhuma tarefa agendada '$taskName' encontrada."
}

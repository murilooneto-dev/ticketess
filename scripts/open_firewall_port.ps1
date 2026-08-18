<#
    Libera o acesso ao DevControl pela rede local, abrindo a porta do
    servidor no Firewall do Windows. Execute como Administrador.
#>
param(
    [int]$Port = 8000
)
$ErrorActionPreference = "Stop"

$ruleName = "DevControl HTTP"

if (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue) {
    Write-Host "Regra de firewall '$ruleName' já existe."
} else {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow | Out-Null
    Write-Host "Regra de firewall '$ruleName' criada para a porta $Port." -ForegroundColor Green
}

Write-Host "Acesse o DevControl pela rede local em: http://<IP-DA-MAQUINA>:$Port"

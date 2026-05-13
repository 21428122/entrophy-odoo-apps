# Self-elevating upgrade script. Right-click -> Run with PowerShell.

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Re-launching as Administrator ..." -ForegroundColor Yellow
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","`"$PSCommandPath`""
    exit
}

$ErrorActionPreference = 'Stop'

$OdooDir = 'C:\Program Files\Odoo 18.0.20260509'
$Service = 'odoo-server-18.0'
$Db      = 'sop_test'
$Module  = 'eu_einvoicing_tracker'

try {
    Write-Host "==> Stopping $Service ..." -ForegroundColor Cyan
    Stop-Service -Name $Service -Force
    Start-Sleep -Seconds 3

    Write-Host "==> Upgrading $Module on $Db ..." -ForegroundColor Cyan
    & "$OdooDir\python\python.exe" `
        "$OdooDir\server\odoo-bin" `
        -c "$OdooDir\server\odoo.conf" `
        -d $Db `
        -u $Module `
        --stop-after-init `
        --no-http
    $rc = $LASTEXITCODE

    Write-Host "==> Starting $Service ..." -ForegroundColor Cyan
    Start-Service -Name $Service

    if ($rc -eq 0) {
        Write-Host ""
        Write-Host "DONE - $Module upgraded. Refresh your browser." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "UPGRADE FAILED (exit $rc) - see traceback above." -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed

    try {
        $svc = Get-Service -Name $Service -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -ne 'Running') {
            Write-Host "==> Restarting $Service after error ..." -ForegroundColor Cyan
            Start-Service -Name $Service
        }
    } catch {
        Write-Host "Could not restart service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Read-Host "Press Enter to close"

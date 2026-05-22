param(
    [int]$Weeks = 4,
    [switch]$Sync
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
$env:PYTHONUTF8 = "1"

$configJson = & $VenvPython -c "import json, config; c=config.COROS_CONFIG; print(json.dumps({'email': c.get('email',''), 'password': c.get('password',''), 'region': c.get('region','asia')}))"
$config = $configJson | ConvertFrom-Json

if (-not $config.email -or -not $config.password) {
    Write-Error "config.py is missing COROS email or password."
}

$env:COROS_EMAIL = $config.email
$env:COROS_PASSWORD = $config.password
$env:COROS_REGION = $config.region

Write-Host "COROS config: email length=$($config.email.Length), password length=$($config.password.Length), region=$($config.region)"
Write-Host ""

Write-Host "== auth-status =="
coros-mcp auth-status

if ($Sync) {
    $to = Get-Date -Format "yyyyMMdd"
    $from = (Get-Date).AddDays(-7 * $Weeks).ToString("yyyyMMdd")
    Write-Host ""
    Write-Host "== sync $from -> $to =="
    coros-mcp sync --from $from --to $to
}

Write-Host ""
Write-Host "== cache-status =="
coros-mcp cache-status

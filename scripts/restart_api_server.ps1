param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $Root ".venv\Scripts\python.exe"

$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
$env:PYTHONUTF8 = "1"

$pattern = "127.0.0.1:$Port\s+.*LISTENING"
$lines = netstat -ano | Select-String $pattern
$pids = @()
foreach ($line in $lines) {
    $parts = ($line.ToString() -split "\s+") | Where-Object { $_ }
    if ($parts.Length -gt 0) {
        $pids += [int]$parts[-1]
    }
}

$pids | Sort-Object -Unique | ForEach-Object {
    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Milliseconds 500
Start-Process -FilePath $Python -ArgumentList @("api_server.py", "--port", "$Port") -WorkingDirectory $Root -WindowStyle Hidden
Start-Sleep -Seconds 2

Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/api/status" -TimeoutSec 10 | Select-Object -ExpandProperty Content

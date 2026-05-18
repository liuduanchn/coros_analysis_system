param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DashboardPath = Join-Path $Root "dashboard.html"

function Write-Response {
    param(
        [System.Net.Sockets.NetworkStream]$Stream,
        [int]$StatusCode,
        [string]$StatusText,
        [string]$ContentType,
        [byte[]]$Body
    )

    $headers = @(
        "HTTP/1.1 $StatusCode $StatusText",
        "Content-Type: $ContentType",
        "Content-Length: $($Body.Length)",
        "Access-Control-Allow-Origin: *",
        "Connection: close",
        "",
        ""
    ) -join "`r`n"

    $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($headers)
    $Stream.Write($headerBytes, 0, $headerBytes.Length)
    if ($Body.Length -gt 0) {
        $Stream.Write($Body, 0, $Body.Length)
    }
}

function Get-Weeks {
    param([string]$Path)

    if ($Path -match "[?&]weeks=(\d+)") {
        return [int]$Matches[1]
    }

    return 52
}

function Invoke-CorosMcp {
    param(
        [string]$Tool,
        [hashtable]$Arguments
    )

    $cmd = Get-Command coros-mcp -ErrorAction SilentlyContinue
    if (-not $cmd) {
        return [ordered]@{
            error = "coros-mcp not found in PATH"
            source = "not_connected"
            using_mock = $false
            mcp_connected = $false
            timestamp = (Get-Date).ToString("o")
        }
    }

    $jsonArgs = $Arguments | ConvertTo-Json -Depth 8 -Compress
    $output = & $cmd.Source call $Tool $jsonArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        return [ordered]@{
            error = ($output -join "`n")
            source = "coros_mcp"
            using_mock = $false
            mcp_connected = $true
            timestamp = (Get-Date).ToString("o")
        }
    }

    try {
        return ($output -join "`n") | ConvertFrom-Json
    } catch {
        return [ordered]@{
            error = "coros-mcp returned invalid JSON: $($_.Exception.Message)"
            source = "coros_mcp"
            using_mock = $false
            mcp_connected = $true
            timestamp = (Get-Date).ToString("o")
        }
    }
}

function Write-McpResult {
    param(
        [System.Net.Sockets.NetworkStream]$Stream,
        [object]$Result
    )

    if ($Result.error) {
        $json = $Result | ConvertTo-Json -Depth 12
        Write-Response $Stream 503 "Service Unavailable" "application/json; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes($json))
    } else {
        if (-not $Result.source) {
            $Result | Add-Member -NotePropertyName source -NotePropertyValue "coros_mcp" -Force
        }
        $json = $Result | ConvertTo-Json -Depth 12
        Write-Response $Stream 200 "OK" "application/json; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes($json))
    }
}

function Write-McpUnavailable {
    param([System.Net.Sockets.NetworkStream]$Stream)

    $json = [ordered]@{
        error = "coros-mcp is not connected in the PowerShell fallback server"
        source = "not_connected"
        using_mock = $false
        mcp_connected = $false
        timestamp = (Get-Date).ToString("o")
    } | ConvertTo-Json -Depth 8

    Write-Response $Stream 503 "Service Unavailable" "application/json; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes($json))
}

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
$listener.Start()
Write-Host "COROS dashboard server running"
Write-Host "Dashboard: http://127.0.0.1:$Port/dashboard.html"
Write-Host "API status: http://127.0.0.1:$Port/api/status"

try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        try {
            $stream = $client.GetStream()
            $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::ASCII, $false, 1024, $true)
            $requestLine = $reader.ReadLine()
            if ([string]::IsNullOrWhiteSpace($requestLine)) {
                continue
            }

            while (($line = $reader.ReadLine()) -ne $null -and $line -ne "") {}

            $parts = $requestLine.Split(" ")
            $target = if ($parts.Length -ge 2) { $parts[1] } else { "/" }
            $path = $target.Split("?")[0]

            if ($path -eq "/" -or $path -eq "/dashboard.html") {
                if (Test-Path $DashboardPath) {
                    Write-Response $stream 200 "OK" "text/html; charset=utf-8" ([System.IO.File]::ReadAllBytes($DashboardPath))
                } else {
                    Write-Response $stream 404 "Not Found" "text/plain; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes("dashboard.html not found"))
                }
            } elseif ($path -eq "/api/status") {
                $hasMcp = [bool](Get-Command coros-mcp -ErrorAction SilentlyContinue)
                $json = [ordered]@{
                    status = "running"
                    mcp_connected = $hasMcp
                    source = if ($hasMcp) { "coros_mcp" } else { "not_connected" }
                    using_mock = $false
                    message = if ($hasMcp) { "coros-mcp is available" } else { "coros-mcp not found in PATH" }
                    timestamp = (Get-Date).ToString("o")
                } | ConvertTo-Json -Depth 8
                Write-Response $stream 200 "OK" "application/json; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes($json))
            } elseif ($path -eq "/api/all") {
                $weeks = Get-Weeks $target
                $end = Get-Date
                $startDay = $end.AddDays(-($weeks * 7)).ToString("yyyyMMdd")
                $endDay = $end.ToString("yyyyMMdd")
                $daily = Invoke-CorosMcp "get_daily_metrics" @{ weeks = $weeks }
                $sleep = Invoke-CorosMcp "get_sleep_data" @{ weeks = $weeks }
                $activities = Invoke-CorosMcp "list_activities" @{ start_day = $startDay; end_day = $endDay; size = 100 }
                $errors = [ordered]@{}
                if ($daily.error) { $errors.daily_metrics = $daily.error }
                if ($sleep.error) { $errors.sleep_data = $sleep.error }
                if ($activities.error) { $errors.activities = $activities.error }
                if ($errors.Count -gt 0) {
                    $json = [ordered]@{
                        error = "coros-mcp data fetch failed"
                        errors = $errors
                        source = "coros_mcp"
                        using_mock = $false
                        mcp_connected = [bool](Get-Command coros-mcp -ErrorAction SilentlyContinue)
                        timestamp = (Get-Date).ToString("o")
                    } | ConvertTo-Json -Depth 12
                    Write-Response $stream 503 "Service Unavailable" "application/json; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes($json))
                } else {
                    $json = [ordered]@{
                        daily_metrics = $daily
                        sleep_data = $sleep
                        activities = $activities
                        using_mock = $false
                        source = "coros_mcp"
                        mcp_connected = $true
                        timestamp = (Get-Date).ToString("o")
                    } | ConvertTo-Json -Depth 12
                    Write-Response $stream 200 "OK" "application/json; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes($json))
                }
            } elseif ($path -eq "/api/daily_metrics") {
                Write-McpResult $stream (Invoke-CorosMcp "get_daily_metrics" @{ weeks = (Get-Weeks $target) })
            } elseif ($path -eq "/api/sleep_data") {
                Write-McpResult $stream (Invoke-CorosMcp "get_sleep_data" @{ weeks = (Get-Weeks $target) })
            } elseif ($path -eq "/api/activities") {
                $weeks = Get-Weeks $target
                $end = Get-Date
                Write-McpResult $stream (Invoke-CorosMcp "list_activities" @{
                    start_day = $end.AddDays(-($weeks * 7)).ToString("yyyyMMdd")
                    end_day = $end.ToString("yyyyMMdd")
                    size = 100
                })
            } elseif ($path -eq "/favicon.ico") {
                Write-Response $stream 204 "No Content" "text/plain" ([byte[]]::new(0))
            } else {
                Write-Response $stream 404 "Not Found" "text/plain; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes("Not found"))
            }
        } catch {
            try {
                Write-Response $stream 500 "Internal Server Error" "text/plain; charset=utf-8" ([System.Text.Encoding]::UTF8.GetBytes($_.Exception.Message))
            } catch {}
        } finally {
            $client.Close()
        }
    }
} finally {
    $listener.Stop()
}

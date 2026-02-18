<#
PowerShell equivalent of start_server.sh for Windows.
Usage: .\start_server.ps1 start|stop|status|logs [service]
#>
Param([string]$Action)

Set-StrictMode -Version Latest
$env:PYTHONIOENCODING = "utf-8"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $RootDir "logs"
$PidDir = Join-Path $RootDir "pids"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $PidDir -Force | Out-Null

# Default working directories
$FrontendWork = Join-Path $RootDir "agent_frontend\apps\web"
$LanggraphWork = Join-Path $RootDir "langgraph_app"
$DbWork = $RootDir

# Default executables/commands (can be overridden by env vars)
$FrontendCmd = $env:FRONTEND_CMD
if ([string]::IsNullOrWhiteSpace($FrontendCmd)) { $FrontendExe = 'cmd.exe'; $FrontendArgs = '/c npm run dev' } else { $FrontendExe = 'cmd.exe'; $FrontendArgs = "/c $FrontendCmd" }

$LanggraphCmd = $env:LANGGRAPH_CMD
if ([string]::IsNullOrWhiteSpace($LanggraphCmd)) {
    $candidate = Join-Path $RootDir ".venv\Scripts\langgraph.exe"
    if (Test-Path $candidate) {
        $LanggraphExe = $candidate
        $LanggraphArgs = 'dev'
    } else {
        # Fallback to running via the venv python: python -m langgraph dev
        $LanggraphExe = Join-Path $RootDir ".venv\Scripts\python.exe"
        $LanggraphArgs = @('-m', 'langgraph', 'dev')
    }
} else { $LanggraphExe = 'cmd.exe'; $LanggraphArgs = "/c $LanggraphCmd" }

$DbCmd = $env:DB_CMD
if ([string]::IsNullOrWhiteSpace($DbCmd)) { $DbExe = Join-Path $RootDir ".venv\Scripts\python.exe"; $DbArgs = 'db_api_server.py' } else { $DbExe = 'cmd.exe'; $DbArgs = "/c $DbCmd" }

function Start-ServiceProc {
    param($name, $file, $arguments, $workdir)
    $log = Join-Path $LogDir "$name.log"
    $pidfile = Join-Path $PidDir "$name.pid"

    if (Test-Path $pidfile) {
        $svcPid = Get-Content $pidfile -ErrorAction SilentlyContinue
        if ($svcPid -and (Get-Process -Id $svcPid -ErrorAction SilentlyContinue)) {
            Write-Output "$name is already running (PID $svcPid)."
            return
        } else { Remove-Item $pidfile -ErrorAction SilentlyContinue }
    }

    Write-Output "Starting $name... (logging to $log)"
    $startInfo = @{
        FilePath = $file
        ArgumentList = @($arguments)
        WorkingDirectory = $workdir
        RedirectStandardOutput = $log
        RedirectStandardError = "$($log).err"
        NoNewWindow = $true
        PassThru = $true
    }
    $proc = Start-Process @startInfo
    $proc.Id | Out-File -FilePath $pidfile -Encoding ascii
    Start-Sleep -Milliseconds 200
    Write-Output "$name started with PID $($proc.Id)"
}

function Stop-ServiceProc {
    param($name)
    $pidfile = Join-Path $PidDir "$name.pid"
    if (-not (Test-Path $pidfile)) { Write-Output "$name not running (no pidfile)."; return }

    $svcPid = Get-Content $pidfile
    if (Get-Process -Id $svcPid -ErrorAction SilentlyContinue) {
        Write-Output "Stopping $name (PID $svcPid)..."
        Stop-Process -Id $svcPid -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        if (Get-Process -Id $svcPid -ErrorAction SilentlyContinue) {
            Write-Output "PID $svcPid still alive; killing..."
            Stop-Process -Id $svcPid -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Output "Process $svcPid not running. Removing stale pidfile."
    }
    Remove-Item $pidfile -ErrorAction SilentlyContinue
}

function Status-ServiceProc {
    param($name)
    $pidfile = Join-Path $PidDir "$name.pid"
    if (Test-Path $pidfile) {
        $svcPid = Get-Content $pidfile
        if (Get-Process -Id $svcPid -ErrorAction SilentlyContinue) { Write-Output "$($name): running (PID $svcPid)" } else { Write-Output "$($name): pidfile exists but process $svcPid not running" }
    } else { Write-Output "$($name): not running" }
}

function Logs-ServiceProc {
    param($name)
    $log = Join-Path $LogDir "$name.log"
    if (-not (Test-Path $log)) { Write-Output "No logs for $name yet: $log"; return }
    Get-Content -Path $log -Wait -Tail 100
}

switch ($Action) {
    'start' {
        Start-ServiceProc frontend $FrontendExe $FrontendArgs $FrontendWork
        Start-ServiceProc langgraph $LanggraphExe $LanggraphArgs $LanggraphWork
        Start-ServiceProc db $DbExe $DbArgs $DbWork
    }
    'stop' {
        Stop-ServiceProc frontend
        Stop-ServiceProc langgraph
        Stop-ServiceProc db
    }
    'status' {
        Status-ServiceProc frontend
        Status-ServiceProc langgraph
        Status-ServiceProc db
    }
    'logs' {
        $svc = $args[1]
        if ([string]::IsNullOrWhiteSpace($svc) -or $svc -eq 'all') {
            Write-Output "Tailing all logs (press Ctrl-C to stop)."
            Get-ChildItem -Path (Join-Path $LogDir '*.log') -ErrorAction SilentlyContinue | ForEach-Object { Write-Output "--- $($_.Name) ---"; Get-Content -Path $_.FullName -Wait -Tail 50 }
        } else {
            Logs-ServiceProc $svc
        }
    }
    Default {
        Write-Output "Usage: $($MyInvocation.MyCommand.Name) {start|stop|status|logs [service]}"
        Write-Output "Commands: start, stop, status, logs [frontend|langgraph|db|all]"
    }
}

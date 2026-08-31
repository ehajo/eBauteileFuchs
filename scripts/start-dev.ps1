[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    $PythonLauncher = $null
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonLauncher = "py"
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonLauncher = "python"
    } else {
        throw "Python 3.12 wurde nicht gefunden. Bitte Python 3.12 installieren und erneut starten."
    }

    if ($PythonLauncher -eq "py") {
        & py -3.12 -m venv .venv
    } else {
        & python -m venv .venv
    }
}

function Assert-LastExitCode {
    if ($LASTEXITCODE -ne 0) {
        throw "Python-Befehl fehlgeschlagen (Exitcode $LASTEXITCODE)."
    }
}

function Test-LocalPortAvailable {
    param([int]$Port)

    $TcpListener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Any,
        $Port
    )
    try {
        $TcpListener.Start()
        return $true
    } catch [System.Net.Sockets.SocketException] {
        return $false
    } finally {
        $TcpListener.Stop()
    }
}

& $VenvPython -m pip install -r requirements.lock -r requirements-dev.lock
Assert-LastExitCode
& $VenvPython -m pip install --no-deps --no-build-isolation -e .
Assert-LastExitCode
& $VenvPython -m alembic upgrade head
Assert-LastExitCode

$ConfiguredPort = [int](& $VenvPython -c "from ebauteilefuchs.config import get_settings; print(get_settings().port)").Trim()
Assert-LastExitCode
$SelectedPort = $ConfiguredPort
$LastCandidatePort = [Math]::Min($ConfiguredPort + 20, 65535)
while ($SelectedPort -le $LastCandidatePort -and -not (Test-LocalPortAvailable $SelectedPort)) {
    $SelectedPort++
}

if ($SelectedPort -gt $LastCandidatePort) {
    throw "Kein freier Port zwischen $ConfiguredPort und $LastCandidatePort gefunden."
}

if ($SelectedPort -ne $ConfiguredPort) {
    Write-Warning "Port $ConfiguredPort ist belegt. eBauteileFuchs verwendet stattdessen Port $SelectedPort."
    $env:EBAUTEILEFUCHS_PORT = [string]$SelectedPort
}

if (-not $NoBrowser) {
    $BrowserUrlCommand = "from ebauteilefuchs.config import get_settings; s = get_settings(); h = '127.0.0.1' if s.host == '0.0.0.0' else s.host; print(f'{s.url_scheme}://{h}:{s.port}')"
    $BrowserUrl = (& $VenvPython -c $BrowserUrlCommand).Trim()
    Assert-LastExitCode
    Start-Process $BrowserUrl
}

& $VenvPython -m ebauteilefuchs
Assert-LastExitCode

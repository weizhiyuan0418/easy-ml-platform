param(
    [int]$Port = 8000,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Step {
    param([string]$Message)
    Write-Host "[easy-ml] $Message" -ForegroundColor Cyan
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

function Find-Python {
    $candidates = @(
        @{ File = "py"; Args = @("-3") },
        @{ File = "python"; Args = @() },
        @{ File = "python3"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        try {
            $version = & $candidate.File @($candidate.Args + @("--version")) 2>$null
            if ($LASTEXITCODE -eq 0 -and $version -match "Python 3\.") {
                return $candidate
            }
        } catch {
            continue
        }
    }
    throw "Python 3 was not found. Please install Python 3.11+ and retry."
}

function Test-PortAvailable {
    param([int]$CandidatePort)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.Connect("127.0.0.1", $CandidatePort)
        return $false
    } catch {
        return $true
    } finally {
        $client.Close()
    }
}

function Find-FreePort {
    param([int]$StartPort)
    for ($candidate = $StartPort; $candidate -le ($StartPort + 20); $candidate++) {
        if (Test-PortAvailable $candidate) {
            return $candidate
        }
    }
    throw "No free port found from $StartPort to $($StartPort + 20)."
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$python = Find-Python
$venvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Step "Creating virtual environment..."
    Invoke-Checked $python.File @($python.Args + @("-m", "venv", ".venv"))
}

Write-Step "Upgrading pip..."
Invoke-Checked $venvPython @("-m", "pip", "install", "--upgrade", "pip")

Write-Step "Installing dependencies from requirements.txt..."
Invoke-Checked $venvPython @("-m", "pip", "install", "-r", "requirements.txt")

Write-Step "Applying database migrations..."
Invoke-Checked $venvPython @("manage.py", "migrate")

$selectedPort = Find-FreePort $Port
$url = "http://127.0.0.1:$selectedPort/"
Write-Step "Starting server at $url"

if (-not $NoBrowser) {
    Start-Process $url
}

Invoke-Checked $venvPython @("manage.py", "runserver", "127.0.0.1:$selectedPort", "--noreload")

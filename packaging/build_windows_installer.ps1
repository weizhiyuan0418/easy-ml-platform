param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Step {
    param([string]$Message)
    Write-Host "[packaging] $Message" -ForegroundColor Cyan
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

if (-not $IsWindows -and $PSVersionTable.PSEdition -eq "Core") {
    throw "This packaging script is intended for Windows."
}

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$python = "py"
$pythonArgs = @("-3")
try {
    & $python @($pythonArgs + @("--version")) | Out-Null
} catch {
    $python = "python"
    $pythonArgs = @()
}

$venvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Step "Creating virtual environment..."
    Invoke-Checked $python @($pythonArgs + @("-m", "venv", ".venv"))
}

Write-Step "Installing runtime dependencies..."
Invoke-Checked $venvPython @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked $venvPython @("-m", "pip", "install", "-r", "requirements.txt")
Invoke-Checked $venvPython @("-m", "pip", "install", "pyinstaller>=6.10")

Write-Step "Running tests before packaging..."
Invoke-Checked $venvPython @("manage.py", "test")
Invoke-Checked $venvPython @("tools\verify_project.py")

Write-Step "Building PyInstaller app directory..."
Invoke-Checked $venvPython @("-m", "PyInstaller", "-y", "packaging\pyinstaller_generic_ml.spec")

if ($SkipInstaller) {
    Write-Step "Skipping Inno Setup installer build."
    exit 0
}

$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php or rerun with -SkipInstaller."
}

Write-Step "Building Windows installer..."
Invoke-Checked $iscc @("packaging\installer.iss")

Write-Step "Installer output is in installer_output/."

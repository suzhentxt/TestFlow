$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "==> Working directory: $((Get-Location).Path)"

$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

function Get-BasePythonCommand {
    $candidates = @(
        [pscustomobject]@{ Exe = "py"; Args = @("-3") },
        [pscustomobject]@{ Exe = "python"; Args = @() },
        [pscustomobject]@{ Exe = "python3"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Exe -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }

        $allArgs = @($candidate.Args) + @("-c", "import sys; print(sys.executable)")
        $previousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & $command.Source @allArgs *> $null
            $exitCode = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }

        if ($exitCode -eq 0) {
            return [pscustomobject]@{ Exe = $command.Source; Args = $candidate.Args }
        }
    }

    return $null
}

function Invoke-BasePython {
    param(
        [Parameter(Mandatory = $true)] $PythonCommand,
        [Parameter(Mandatory = $true)] [string[]] $Arguments
    )

    $allArgs = @($PythonCommand.Args) + $Arguments
    & $PythonCommand.Exe @allArgs
}

function Test-VenvPython {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $venvPython -c "import sys" *> $null
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    return $exitCode -eq 0
}

function Invoke-VenvPython {
    param(
        [Parameter(Mandatory = $true)] [string[]] $Arguments
    )

    & $venvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ".venv Python command failed: python $($Arguments -join ' ')"
    }
}

$requiredFiles = @(
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "claude-progress.md",
    "feature_list.json",
    "clean-state-checklist.md",
    "evaluator-rubric.md",
    "quality-document.md",
    "session-handoff.md",
    "init.sh",
    "init.ps1"
)

$missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
if ($missing.Count -gt 0) {
    throw "Missing required files: $($missing -join ', ')"
}

$readme = Get-Content -Raw -Encoding UTF8 -LiteralPath "README.md"
if ($readme -notmatch "TestFlow") {
    throw "README.md does not identify the TestFlow project."
}

$featureListRaw = Get-Content -Raw -Encoding UTF8 -LiteralPath "feature_list.json"
$featureList = $featureListRaw | ConvertFrom-Json
if ($featureList.project -ne "TestFlow") {
    throw "feature_list.json project must be TestFlow."
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    $basePython = Get-BasePythonCommand
    if (-not $basePython) {
        throw "Python 3 is required to create .venv. Install Python, then rerun this script."
    }

    Write-Host "==> Creating .venv"
    Invoke-BasePython -PythonCommand $basePython -Arguments @("-m", "venv", ".venv")
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw ".venv was not created correctly; missing $venvPython"
}

if (-not (Test-VenvPython)) {
    throw ".venv exists but its Python interpreter is not usable. Install Python 3, remove the broken .venv, then rerun this script."
}

Write-Host "==> Using virtual environment: $venvDir"
Write-Host "==> Installing dependencies into .venv"
Invoke-VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-VenvPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt")

if (Test-Path -LiteralPath "pyproject.toml" -PathType Leaf) {
    Write-Host "==> Installing package into .venv"
    Invoke-VenvPython -Arguments @("-m", "pip", "install", "-e", ".")
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    & $venvPython -m json.tool feature_list.json *> $null
    $jsonToolExitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $previousErrorActionPreference
}

if ($jsonToolExitCode -ne 0) {
    throw "feature_list.json is not valid JSON."
}

if (Test-Path -LiteralPath "tests" -PathType Container) {
    Write-Host "==> Running tests in .venv"
    Invoke-VenvPython -Arguments @("-m", "pytest", "tests/")
} else {
    Write-Host "==> No tests directory found."
    Write-Host "==> .venv baseline passed."
}

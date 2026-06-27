$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "==> Working directory: $((Get-Location).Path)"

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

$hasPyproject = Test-Path -LiteralPath "pyproject.toml" -PathType Leaf
$hasPackage = Test-Path -LiteralPath "src/testflow" -PathType Container

if (-not ($hasPyproject -and $hasPackage)) {
    Write-Host "==> Implementation scaffold not present yet."
    Write-Host "==> Docs-only baseline passed."
    Write-Host "==> Next product feature: tf-001 - Create installable Python CLI skeleton."
    exit 0
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python is required once the implementation scaffold exists."
}

Write-Host "==> Installing package"
& $python.Source -m pip install -e .

Write-Host "==> Running tests"
& $python.Source -m pytest tests/

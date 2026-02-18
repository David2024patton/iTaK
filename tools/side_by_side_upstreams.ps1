param(
    [switch]$Refresh,
    [switch]$Status,
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$referencesDir = Join-Path $repoRoot "references"
$agentZeroDir = Join-Path $referencesDir "agent-zero"
$openclawDir = Join-Path $referencesDir "openclaw"

$agentZeroRepo = "https://github.com/frdel/agent-zero.git"
$openclawRepo = "https://github.com/openclaw/openclaw.git"

New-Item -ItemType Directory -Path $referencesDir -Force | Out-Null

function Ensure-Repo {
    param(
        [string]$Path,
        [string]$Url
    )

    if (-not (Test-Path (Join-Path $Path ".git"))) {
        Write-Host "[clone] $Url -> $Path"
        git clone --depth 1 $Url $Path
        return
    }

    if ($Refresh) {
        Write-Host "[refresh] $Path"
        git -C $Path fetch --depth 1 origin
        git -C $Path reset --hard origin/HEAD
    }
}

Ensure-Repo -Path $agentZeroDir -Url $agentZeroRepo
Ensure-Repo -Path $openclawDir -Url $openclawRepo

if ($Status -or -not ($Refresh -or $Open)) {
    Write-Host "`n=== Side-by-side upstream status ==="
    Write-Host "Agent Zero : $(git -C $agentZeroDir rev-parse --short HEAD)"
    Write-Host "OpenClaw   : $(git -C $openclawDir rev-parse --short HEAD)"
    Write-Host "iTaK       : $(git -C $repoRoot rev-parse --short HEAD)"
}

if ($Open) {
    Write-Host "Opening folders..."
    Start-Process explorer.exe $agentZeroDir
    Start-Process explorer.exe $openclawDir
    Start-Process explorer.exe $repoRoot
}

Write-Host "`nQuick compare examples:"
Write-Host "  code --diff `"$repoRoot\webui\server.py`" `"$agentZeroDir\webui\server.py`""
Write-Host "  code --diff `"$repoRoot\security\ssrf_guard.py`" `"$openclawDir\src\security\ssrfGuard.ts`""

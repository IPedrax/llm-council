# LLM Council - Windows installer for Claude Code
# One-liner:
#   irm https://raw.githubusercontent.com/IPedrax/llm-council/main/install.ps1 | iex

$ErrorActionPreference = 'Stop'
$ProgressPreference   = 'SilentlyContinue'

$repo   = 'IPedrax/llm-council'
$skills = Join-Path $env:USERPROFILE '.claude\skills'
$dest   = Join-Path $skills 'llm-council'

Write-Host "Installing the LLM Council skill -> $dest" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $skills | Out-Null

$tmp = Join-Path $env:TEMP ("llm-council-" + [guid]::NewGuid().ToString('N') + ".zip")
$url = "https://raw.githubusercontent.com/$repo/main/llm-council.skill"

try {
    Invoke-WebRequest -Uri $url -OutFile $tmp
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Expand-Archive -Path $tmp -DestinationPath $skills -Force
}
finally {
    if (Test-Path $tmp) { Remove-Item $tmp -Force }
}

if (Test-Path (Join-Path $dest 'SKILL.md')) {
    Write-Host ""
    Write-Host "[OK] LLM Council installed to $dest" -ForegroundColor Green
    Write-Host "Restart Claude Code, then try:  council this: <your decision>"
} else {
    Write-Host ""
    Write-Host "[!] Install failed - SKILL.md not found under $dest" -ForegroundColor Red
    exit 1
}

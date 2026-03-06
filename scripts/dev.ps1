# dev.ps1 — MVP 로컬 개발 서버 시작 (Windows PowerShell)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

Push-Location $ROOT

try {
    # 1. 가상환경 생성 (없으면)
    if (-not (Test-Path ".venv")) {
        Write-Host "[1/3] Creating .venv..." -ForegroundColor Cyan
        python -m venv .venv
    } else {
        Write-Host "[1/3] .venv already exists" -ForegroundColor Green
    }

    # 2. 패키지 설치
    Write-Host "[2/3] Installing dependencies..." -ForegroundColor Cyan
    & .venv\Scripts\pip install -q -r requirements.txt

    # 3. 서버 시작
    Write-Host "[3/3] Starting uvicorn on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    & .venv\Scripts\uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
}
finally {
    Pop-Location
}

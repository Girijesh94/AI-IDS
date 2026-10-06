param(
    [ValidateSet('replay','live')][string]$Mode = 'replay',
    [string]$Interface = '',
    [string]$Database = '',
    [string]$Model = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install requirements.txt first.' }
$env:IDS_MODE = $Mode
if ($Interface) { $env:IDS_INTERFACE = $Interface } else { Remove-Item Env:IDS_INTERFACE -ErrorAction SilentlyContinue }
if ($Database) { $env:IDS_DB = $Database }
if ($Model) { $env:IDS_MODEL = $Model }
Push-Location $projectRoot
try { & $pythonPath -m backend.detector_server } finally { Pop-Location }

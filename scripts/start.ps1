param(
    [ValidateSet('replay','live')][string]$Mode = 'replay',
    [string]$Interface = '',
    [string]$Database = '',
    [string]$Model = '',
    [switch]$Shadow
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install requirements.txt first.' }
$env:IDS_MODE = $Mode
if ($Interface) { $env:IDS_INTERFACE = $Interface } else { Remove-Item Env:IDS_INTERFACE -ErrorAction SilentlyContinue }
if ($Database) { $env:IDS_DB = $Database } else { Remove-Item Env:IDS_DB -ErrorAction SilentlyContinue }
if ($Model) {
    $env:IDS_MODEL = $Model
    $env:IDS_MODEL_SHADOW = if ($Shadow) { '1' } else { '0' }
} else {
    Remove-Item Env:IDS_MODEL -ErrorAction SilentlyContinue
    # The repository candidate defaults to shadow scoring until independently qualified.
    $env:IDS_MODEL_SHADOW = '1'
}
Push-Location $projectRoot
try { & $pythonPath -m backend.detector_server } finally { Pop-Location }

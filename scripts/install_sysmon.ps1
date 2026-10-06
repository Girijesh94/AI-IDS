param([ValidateSet('Sysmon64.exe','Sysmon.exe')][string]$Executable='Sysmon64.exe',[switch]$Standalone)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$reportPath = Join-Path $projectRoot 'artifacts\sysmon-install.json'
$stage = 'preflight'
try {
    $sysmonConfig = Join-Path $PSScriptRoot 'sysmon-processes.xml'
    if (Get-Service -Name Sysmon,Sysmon64 -ErrorAction SilentlyContinue) {
        throw 'Sysmon already exists. Review its configuration before changing it.'
    }
    $admin = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $admin.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Run this setup script in an administrator PowerShell window.'
    }
    $nativeFeature = $null
    if (-not $Standalone) { $nativeFeature = Get-WindowsOptionalFeature -Online -FeatureName Sysmon -ErrorAction SilentlyContinue }
    if ($nativeFeature) {
        $route = 'windows_native'
        $stage = 'enable_native_feature'
        if ($nativeFeature.State -ne 'Enabled') {
            $enabled = Enable-WindowsOptionalFeature -Online -FeatureName Sysmon -NoRestart
            if ($enabled.RestartNeeded) { throw 'Windows requires a restart before Sysmon can be configured. No restart was performed.' }
        }
        $sysmonExe = Join-Path $env:SystemRoot 'System32\Sysmon.exe'
    } else {
        $route = 'standalone'
        $sysmonExe = Join-Path $projectRoot ('data\installers\Sysmon-latest\' + $Executable)
    }
    $stage = 'verify_signature'
    $signature = Get-AuthenticodeSignature -LiteralPath $sysmonExe
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Microsoft') {
        throw 'Sysmon must have a valid Microsoft signature.'
    }
    $sysmonOutputPath = Join-Path $projectRoot 'artifacts\sysmon-install.stdout.log'
    $sysmonErrorPath = Join-Path $projectRoot 'artifacts\sysmon-install.stderr.log'
    if ($route -eq 'standalone') {
        $env:TEMP = Join-Path $env:SystemRoot 'Temp'
        $env:TMP = $env:TEMP
        $stage = 'register_standalone_manifest'
        $manifestProcess = Start-Process -FilePath $sysmonExe -ArgumentList '-accepteula','-m' -WorkingDirectory (Join-Path $env:SystemRoot 'System32') -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'artifacts\sysmon-manifest.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'artifacts\sysmon-manifest.stderr.log')
    }
    $stage = 'install_service'
    $installer = Start-Process -FilePath $sysmonExe -ArgumentList '-accepteula','-i',$sysmonConfig -WorkingDirectory (Join-Path $env:SystemRoot 'System32') -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $sysmonOutputPath -RedirectStandardError $sysmonErrorPath
    $service = Get-Service -Name Sysmon,Sysmon64 -ErrorAction SilentlyContinue
    @{route=$route; exit_code=$installer.ExitCode; service=($service.Name -join ','); status=($service.Status -join ',')} |
        ConvertTo-Json | Set-Content $reportPath
    if ($installer.ExitCode -ne 0 -or -not $service) { throw 'Sysmon installation failed; inspect installation logs.' }
} catch {
    @{route=$route; stage=$stage; error=$_.Exception.Message; detail=($_ | Out-String)} | ConvertTo-Json | Set-Content $reportPath
    exit 1
}

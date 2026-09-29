$ErrorActionPreference = 'Stop'
$appRoot = $PSScriptRoot
$toolRoot = Split-Path -Parent $appRoot
$target = Join-Path $toolRoot 'CyTools_Storyboard.exe'
New-Item -ItemType Directory -Force -Path (Join-Path $toolRoot 'runtime\build') | Out-Null

if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
    $programFiles = [Environment]::GetFolderPath('ProgramFilesX86')
    $vswhere = Join-Path $programFiles 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path -LiteralPath $vswhere)) { throw 'Visual Studio Build Tools introuvables (vswhere absent).' }
    $install = (& "$vswhere" -latest -products '*' -requires 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64' -property installationPath | Select-Object -First 1)
    if (-not $install) { throw 'Composant VC++ x64 non installe.' }
    $vcvars = Join-Path $install 'VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path -LiteralPath $vcvars)) { throw "vcvars64.bat introuvable dans $install" }
    # Import the compiler environment once, then continue in this session.
    & cmd.exe /c "`"$vcvars`" >nul && set" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') { Set-Item -Path ("env:" + $matches[1]) -Value $matches[2] }
    }
}

Push-Location (Join-Path $toolRoot 'runtime\build')
try {
    & cl.exe /nologo /std:c++17 /MT /EHsc /O2 (Join-Path $appRoot 'launcher.cpp') "/Fe:$target" /link /SUBSYSTEM:WINDOWS user32.lib
    if ($LASTEXITCODE -ne 0) { throw 'Compilation du lanceur echouee' }
} finally { Pop-Location }
Write-Host "Lanceur compile : $target"

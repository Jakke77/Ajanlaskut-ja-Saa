$ErrorActionPreference = 'Stop'
$appRoot = $PSScriptRoot
$shell = New-Object -ComObject WScript.Shell
$startMenu = Join-Path ([Environment]::GetFolderPath('Programs')) 'Ajanlaskut ja Saa'
New-Item -ItemType Directory -Force -Path $startMenu | Out-Null
foreach ($item in @(
    @{ Name = 'Ajanlaskut ja Saa'; Arguments = '' },
    @{ Name = 'Ajanlaskut - vain widgetit'; Arguments = '--widgets-only' }
)) {
    $shortcut = $shell.CreateShortcut((Join-Path $startMenu ($item.Name + '.lnk')))
    $shortcut.TargetPath = Join-Path $appRoot 'Ajanlaskut-ja-Saa.exe'
    $shortcut.Arguments = $item.Arguments
    $shortcut.WorkingDirectory = $appRoot
    $shortcut.IconLocation = (Join-Path $appRoot 'Ajanlaskut-ja-Saa.exe') + ',0'
    $shortcut.Save()
}
Write-Host 'Pikakuvakkeet luotu Windowsin Kaynnista-valikkoon.'
Write-Host 'Sailyta sovelluskansio nykyisessa paikassaan.'

#!/usr/bin/env pwsh
param(
    [string] $Target = "$PWD\venv\Scripts\python.exe",
    [string] $Args = "-m document_converter.gui",
    [string] $Name = "Document Converter"
)

if (-not (Test-Path $Target)) {
    Write-Output "Warning: target not found. You can pass the Python executable path as -Target."
}

$W = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = $W.CreateShortcut("$desktop\\$Name.lnk")
$lnk.TargetPath = $Target
$lnk.Arguments = $Args
$lnk.WorkingDirectory = (Get-Location).Path
$lnk.Save()

Write-Output "Shortcut '$Name' created on Desktop (target: $Target $Args)."

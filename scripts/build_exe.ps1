#!/usr/bin/env pwsh
try {
    $projRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $projRoot
} catch {
    $projRoot = Get-Location
}

Write-Output "Installing PyInstaller (user scope)..."
pip install --user pyinstaller

Write-Output "Building single-file EXE with PyInstaller..."
pyinstaller --noconfirm --onefile --windowed --name DocumentConverter document_converter\gui.py

if (Test-Path "$projRoot\dist\DocumentConverter.exe") {
    $W = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    $lnk = $W.CreateShortcut("$desktop\\Document Converter.lnk")
    $lnk.TargetPath = (Resolve-Path "$projRoot\dist\DocumentConverter.exe").Path
    $lnk.WorkingDirectory = (Get-Location).Path
    $lnk.Save()
    Write-Output "Build complete — shortcut created on Desktop."
} else {
    Write-Error "Build failed: dist\DocumentConverter.exe not found. Check PyInstaller output above."
}

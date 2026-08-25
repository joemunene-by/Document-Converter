#!/usr/bin/env pwsh
# Installs optional extras for document-converter in the current Python environment (uses the same interpreter that runs PowerShell)
$packages = @('pypdf','openpyxl','python-pptx','pypandoc')
Write-Output "Installing: $($packages -join ', ')"
python -m pip install --upgrade pip
python -m pip install $packages
Write-Output "Done. Restart the GUI if it's running."

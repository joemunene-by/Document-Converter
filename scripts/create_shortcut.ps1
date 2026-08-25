#!/usr/bin/env pwsh
param(
    [string] $Target = "$PWD\venv\Scripts\python.exe",
    [string] $Args = "",
    [string] $Name = "Document Converter"
)

# Normalize and remove simple surrounding quotes (avoid complex escaping issues)
$Target = $Target.Trim()
if ($Target.Length -gt 0) {
    if ($Target[0] -eq "'" -or $Target[0] -eq '"') { $Target = $Target.Substring(1) }
}
if ($Target.Length -gt 0) {
    $last = $Target.Length - 1
    if ($Target[$last] -eq "'" -or $Target[$last] -eq '"') { $Target = $Target.Substring(0, $last) }
}

$Args = $Args.Trim()
if ($Args.Length -gt 0) {
    if ($Args[0] -eq "'" -or $Args[0] -eq '"') { $Args = $Args.Substring(1) }
}
if ($Args.Length -gt 0) {
    $last = $Args.Length - 1
    if ($Args[$last] -eq "'" -or $Args[$last] -eq '"') { $Args = $Args.Substring(0, $last) }
}

$Name = $Name.Trim()
if ($Name.Length -gt 0) {
    if ($Name[0] -eq "'" -or $Name[0] -eq '"') { $Name = $Name.Substring(1) }
}
if ($Name.Length -gt 0) {
    $last = $Name.Length - 1
    if ($Name[$last] -eq "'" -or $Name[$last] -eq '"') { $Name = $Name.Substring(0, $last) }
}

# Try to resolve the target to an absolute path when possible
$resolved = Resolve-Path -Path $Target -ErrorAction SilentlyContinue
if ($null -ne $resolved) {
    $TargetPath = $resolved.Path
} else {
    $TargetPath = $Target
}

if (-not (Test-Path $TargetPath)) {
    Write-Output "Warning: target not found at '$TargetPath'. The shortcut will still be created but may not work until the target exists."
}

try {
    $W = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    $lnkPath = Join-Path $desktop ("$Name.lnk")
    $lnk = $W.CreateShortcut($lnkPath)

    $lnk.TargetPath = $TargetPath
    if ($Args -ne '') { $lnk.Arguments = $Args }
    $lnk.WorkingDirectory = (Get-Location).Path
    $lnk.Save()

    Write-Output "Shortcut '$Name' created on Desktop (target: $TargetPath $Args)."
} catch {
    Write-Output "Failed to create shortcut: $($_.Exception.Message)"
    Write-Output "Target path: '$TargetPath'"
    Write-Output "Arguments: '$Args'"
    throw
}

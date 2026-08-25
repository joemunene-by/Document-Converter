@echo off
setlocal

set "PY=%~dp0.venv\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=pythonw.exe"

"%PY%" -m document_converter.gui

endlocal
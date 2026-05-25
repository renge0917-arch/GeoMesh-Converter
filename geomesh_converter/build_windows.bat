@echo off
setlocal EnableExtensions
chcp 65001 >nul

rem GeoMesh Converter Windows EXE Builder
rem This script intentionally uses mostly ASCII messages to avoid mojibake.
cd /d "%~dp0"
set "LOG_FILE=%~dp0build_log.txt"

echo ========================================
echo GeoMesh Converter Windows EXE Builder
echo ========================================
echo Folder: %CD%
echo Log: %LOG_FILE%
echo.

>"%LOG_FILE%" echo GeoMesh Converter build log
>>"%LOG_FILE%" echo Started: %DATE% %TIME%
>>"%LOG_FILE%" echo Folder: %CD%

if not exist "main.py" (
    echo [ERROR] main.py was not found.
    echo Please extract the zip first, then run build_windows.bat inside the geomesh_converter folder.
    >>"%LOG_FILE%" echo ERROR: main.py not found. The zip may not be extracted.
    goto FAILED
)

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [ERROR] Python was not found.
    echo Install Python 3.10 or later and enable "Add python.exe to PATH".
    >>"%LOG_FILE%" echo ERROR: Python was not found in PATH.
    goto FAILED
)

echo Using Python command: %PYTHON_CMD%
>>"%LOG_FILE%" echo Using Python command: %PYTHON_CMD%
%PYTHON_CMD% --version
%PYTHON_CMD% --version >>"%LOG_FILE%" 2>&1
if errorlevel 1 goto FAILED

echo.
echo [1/5] Creating virtual environment...
%PYTHON_CMD% -m venv .venv >>"%LOG_FILE%" 2>&1
if errorlevel 1 goto FAILED

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto FAILED

echo [2/5] Upgrading pip...
python -m pip install --upgrade pip >>"%LOG_FILE%" 2>&1
if errorlevel 1 goto FAILED

echo [3/5] Installing dependencies...
python -m pip install -r requirements.txt >>"%LOG_FILE%" 2>&1
if errorlevel 1 goto FAILED

echo [4/5] Installing PyInstaller...
python -m pip install "pyinstaller>=6.0" >>"%LOG_FILE%" 2>&1
if errorlevel 1 goto FAILED

echo [5/5] Building GeoMeshConverter.exe...
python -m PyInstaller --clean --onefile --windowed --name GeoMeshConverter main.py >>"%LOG_FILE%" 2>&1
if errorlevel 1 goto FAILED

if not exist "dist\GeoMeshConverter.exe" (
    echo [ERROR] dist\GeoMeshConverter.exe was not created.
    >>"%LOG_FILE%" echo ERROR: dist\GeoMeshConverter.exe was not created.
    goto FAILED
)

echo.
echo [OK] Build completed successfully.
echo EXE: %CD%\dist\GeoMeshConverter.exe
echo.
echo Press any key to close this window.
pause >nul
exit /b 0

:FAILED
echo.
echo [ERROR] Build failed.
echo See build_log.txt for details.
echo.
echo Common causes:
echo - The zip was not extracted before running this script.
echo - Python is not installed or not added to PATH.
echo - pip install was blocked by network/proxy/security software.
echo.
echo Please send the last lines of build_log.txt if you need help.
pause
exit /b 1

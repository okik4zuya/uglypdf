@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"

echo.
echo Setting up virtual environment...
echo.

REM Remove old venv if it exists (may have stale absolute paths from another machine)
if exist "%VENV_DIR%" (
    echo Removing existing venv...
    rmdir /s /q "%VENV_DIR%"
)

REM Create fresh venv using system python
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to create venv. Make sure Python is installed and on PATH.
    pause
    exit /b
)

REM Activate and install dependencies
call "%VENV_DIR%\Scripts\activate.bat"

if exist "%REQUIREMENTS%" (
    echo Installing dependencies from requirements.txt...
    pip install -r "%REQUIREMENTS%"
) else (
    echo WARNING: requirements.txt not found, skipping pip install.
)

echo.
echo Setup complete. You can now use run.bat.
echo.
pause

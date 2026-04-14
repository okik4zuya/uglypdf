@echo off
setlocal enabledelayedexpansion

REM Folder passed from Windows context menu
set "TARGET=%~1"

REM Directory where BAT file is located
set "SCRIPT_DIR=%~dp0"

REM Activate virtual environment
set "ACTIVATE=%SCRIPT_DIR%venv\Scripts\activate.bat"
if not exist "%ACTIVATE%" (
echo ERROR: venv not found. Run setup.bat to create it.
pause
exit /b
)
call "%ACTIVATE%"

REM Python interpreter inside virtual environment
set "PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"

REM Python script path
set "PY_SCRIPT=%SCRIPT_DIR%pdf2md.py"

if not exist "%PYTHON%" (
echo ERROR: Python not found in venv.
echo Expected location:
echo %PYTHON%
pause
exit /b
)

if "%TARGET%"=="" (
echo No folder selected.
pause
exit /b
)

echo.
echo Scanning folder:
echo %TARGET%
echo.

set i=0

for %%f in ("%TARGET%\*.pdf") do (
set /a i+=1
set "file[!i!]=%%f"
echo !i!. %%~nxf
)

if %i%==0 (
echo No PDF files found.
pause
exit /b
)

echo.
set /p choices=Select files (example: 1 3 4) :

echo.
echo Starting conversion...
echo.

set args=

for %%n in (%choices%) do (
set "args=!args! "!file[%%n]!""
)

"%PYTHON%" "%PY_SCRIPT%" %args%

echo.
echo Conversion finished.
pause

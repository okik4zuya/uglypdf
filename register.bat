@echo off
setlocal

:: Get full path of this directory
set "TOOL_DIR=%~dp0"
set "TOOL_BAT=%TOOL_DIR%run.bat"

echo.
echo Registering Pdf to md tool...
echo.

:: Add main key
reg add "HKCR\Directory\Background\shell\Pdf to md" /f >nul
reg add "HKCR\Directory\Background\shell\Pdf to md" /v "MUIVerb" /d "Pdf to md" /f >nul
reg add "HKCR\Directory\Background\shell\Pdf to md" /v "Icon" /d "cmd.exe" /f >nul

:: Add command
reg add "HKCR\Directory\Background\shell\Pdf to md\command" /f >nul
reg add "HKCR\Directory\Background\shell\Pdf to md\command" ^
/ve /d "cmd.exe /k \"\"%TOOL_BAT%\" \"%%V\"\"" /f >nul


echo.
echo Tool successfully registered!
echo.
pause

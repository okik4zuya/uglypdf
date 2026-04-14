@echo off
setlocal

:: Get full path of this directory
set "TOOL_DIR=%~dp0"
set "TOOL_BAT=%TOOL_DIR%run.bat"

echo.
echo Registering Python tools menu...
echo.

:: ==========================
:: Create main group menu
:: ==========================

reg add "HKCR\Directory\Background\shell\CLITools" /f >nul
reg add "HKCR\Directory\Background\shell\CLITools" /v "MUIVerb" /d "CLI tools" /f >nul
reg add "HKCR\Directory\Background\shell\CLITools" /v "Icon" /d "cmd.exe" /f >nul
reg add "HKCR\Directory\Background\shell\CLITools" /v "SubCommands" /d "" /f >nul

:: Create shell container for submenus
reg add "HKCR\Directory\Background\shell\CLITools\shell" /f >nul

:: ==========================
:: Tool 1 : Pdf to md
:: ==========================

reg add "HKCR\Directory\Background\shell\CLITools\shell\PdfToMd" /f >nul
reg add "HKCR\Directory\Background\shell\CLITools\shell\PdfToMd" /v "MUIVerb" /d "Pdf to md" /f >nul
reg add "HKCR\Directory\Background\shell\CLITools\shell\PdfToMd" /v "Icon" /d "cmd.exe" /f >nul

reg add "HKCR\Directory\Background\shell\CLITools\shell\PdfToMd\command" ^
/ve /d "\"%TOOL_BAT%\" \"%%V\"" /f >nul

echo.
echo CLI tools menu successfully registered!
echo.
pause

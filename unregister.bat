@echo off
setlocal

echo.
echo Removing Pdf to md tool from Python tools menu...
echo.

:: Remove the specific tool
reg delete "HKCR\Directory\Background\shell\CLITools\shell\PdfToMd" /f >nul 2>&1

echo.
echo Pdf to md tool removed successfully.
echo.
pause

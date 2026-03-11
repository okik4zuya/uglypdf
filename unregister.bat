@echo off
echo.
echo Removing Pdf to md tool...
echo.

reg delete "HKCR\Directory\Background\shell\Pdf to md" /f >nul

echo.
echo Tool successfully removed!
echo.
pause

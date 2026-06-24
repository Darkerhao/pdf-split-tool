@echo off
REM Build script for Windows

echo ======================================
echo Building PDF Toolbox for Windows
echo ======================================
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM Build executable
echo Building executable...
pyinstaller --noconsole --onefile --name split_pdf_gui ^
    --icon=icon.ico ^
    --add-data "presentation/i18n/locales;presentation/i18n/locales" ^
    --hidden-import=tkinter ^
    split_pdf_gui.py

echo.
echo Build completed!
echo Output: dist\split_pdf_gui.exe
echo.

REM Create installer
set /p create_installer="Create installer (requires NSIS)? (y/n): "
if /i "%create_installer%"=="y" (
    echo Creating installer...
    makensis installer.nsi
    echo.
    echo Installer created: PDF_Toolbox_Setup.exe
) else (
    echo Skipping installer creation
)

echo.
echo Done!
pause

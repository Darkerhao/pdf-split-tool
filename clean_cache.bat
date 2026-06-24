@echo off
REM Clean Python cache files and directories

echo Cleaning Python cache files...

REM Remove __pycache__ directories
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Remove .pyc files
del /s /q *.pyc 2>nul

REM Remove .pyo files
del /s /q *.pyo 2>nul

REM Remove .pytest_cache directories
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"

echo.
echo Done! All Python cache files cleaned.

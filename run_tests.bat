@echo off
REM Run all unit tests for the PDF Toolbox project

echo ======================================
echo Running PDF Toolbox Unit Tests
echo ======================================
echo.

REM Set PYTHONPATH to project root
set PYTHONPATH=.

echo Testing Domain Layer...
python -m unittest discover tests/unit/domain -v
set DOMAIN_RESULT=%ERRORLEVEL%
echo.

echo Testing Infrastructure Layer...
python -m unittest discover tests/unit/infrastructure -v
set INFRA_RESULT=%ERRORLEVEL%
echo.

echo Testing Application Layer...
python -m unittest discover tests/unit/application -v
set APP_RESULT=%ERRORLEVEL%
echo.

echo Testing Presentation Layer...
python -m unittest discover tests/unit/presentation -v
set PRES_RESULT=%ERRORLEVEL%
echo.

echo ======================================
echo Test Summary
echo ======================================

if %DOMAIN_RESULT%==0 (
    echo Domain Layer:         PASSED
) else (
    echo Domain Layer:         FAILED
)

if %INFRA_RESULT%==0 (
    echo Infrastructure Layer: PASSED
) else (
    echo Infrastructure Layer: FAILED
)

if %APP_RESULT%==0 (
    echo Application Layer:    PASSED
) else (
    echo Application Layer:    FAILED
)

if %PRES_RESULT%==0 (
    echo Presentation Layer:   PASSED
) else (
    echo Presentation Layer:   FAILED
)

echo ======================================

REM Check if all tests passed
set /a TOTAL_RESULT=%DOMAIN_RESULT%+%INFRA_RESULT%+%APP_RESULT%+%PRES_RESULT%

if %TOTAL_RESULT%==0 (
    echo All tests passed!
    exit /b 0
) else (
    echo Some tests failed!
    exit /b 1
)

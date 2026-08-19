@echo off

title HELLA AI ASSISTANT

cd /d "%~dp0"

echo.
echo ==========================================
echo          HELLA AI ASSISTANT
echo ==========================================
echo.

if not exist "%~dp0venv\Scripts\python.exe" (
    echo ERROR: Hella virtual environment not found.
    echo.
    echo Expected:
    echo %~dp0venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0venv\pyvenv.cfg" (
    echo ERROR: Virtual environment is broken.
    echo.
    echo venv\pyvenv.cfg was not found.
    echo Please recreate the venv.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0jarvis.py" (
    echo ERROR: jarvis.py was not found.
    echo.
    pause
    exit /b 1
)

echo Starting Hella...
echo.

"%~dp0venv\Scripts\python.exe" "%~dp0jarvis.py"

echo.
echo ==========================================
echo          HELLA HAS STOPPED
echo ==========================================
echo.

pause
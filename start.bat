@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set PROJECT_DIR=%~dp0
set CONFIG_DIR=%PROJECT_DIR%backend\config
set DBTABLE_DIR=%PROJECT_DIR%backend\dbtable

echo === Starting Project ===
echo Project Dir: %PROJECT_DIR%

:: Check config folder
set CONFIG_NEED_INIT=0
if not exist "%CONFIG_DIR%" (
    set CONFIG_NEED_INIT=1
    echo [Check] config not exist, need init...
) else (
    dir /b "%CONFIG_DIR%\*" >nul 2>nul
    if errorlevel 1 (
        set CONFIG_NEED_INIT=1
        echo [Check] config empty, need init...
    ) else (
        echo [Check] config exist, skip init
    )
)

:: Init config
if "%CONFIG_NEED_INIT%"=="1" (
    cd /d "%PROJECT_DIR%backend"
    python init\init_config.py
    if errorlevel 1 (
        echo Config init failed
        pause
        exit /b 1
    )
    echo Config init done
)

:: Check dbtable folder
set NEED_INIT=0
if not exist "%DBTABLE_DIR%" (
    set NEED_INIT=1
    echo [1/3] dbtable not exist, need init...
) else (
    dir /b "%DBTABLE_DIR%\*" >nul 2>nul
    if errorlevel 1 (
        set NEED_INIT=1
        echo [1/3] dbtable empty, need init...
    ) else (
        echo [1/3] dbtable exist, skip init
    )
)

if "%NEED_INIT%"=="1" (
    cd /d "%PROJECT_DIR%backend"
    python init\initial_db.py
    if errorlevel 1 (
        echo Init failed
        pause
        exit /b 1
    )
    echo Init done
)

echo [2/3] Starting backend...
cd /d "%PROJECT_DIR%backend"
start "Backend" cmd /k "python main.py"

timeout /t 3 /nobreak >nul

echo [3/3] Starting frontend...
cd /d "%PROJECT_DIR%frontend"
npm run serve

echo.
echo Frontend stopped. Please close backend window manually.
pause

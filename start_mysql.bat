@echo off
setlocal
set "MYSQLD=C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe"
set "DATA_DIR=%~dp0data\mysql_data"

if not exist "%MYSQLD%" (
    echo MySQL Server 8.4 was not found at:
    echo %MYSQLD%
    exit /b 1
)

if not exist "%DATA_DIR%\mysql" (
    echo Initializing the local CollegeConnect MySQL data directory...
    if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
    "%MYSQLD%" --initialize-insecure --datadir="%DATA_DIR%"
    if errorlevel 1 (
        echo MySQL data directory initialization failed.
        exit /b 1
    )
)

echo ===================================================
echo Starting MySQL Server for CollegeConnect...
echo Data Directory: %DATA_DIR%
echo Port: 3306
echo ===================================================
"%MYSQLD%" --datadir="%DATA_DIR%" --port=3306 --console
pause
endlocal

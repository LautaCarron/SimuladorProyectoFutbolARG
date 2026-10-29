@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Directorio objetivo: por defecto la carpeta donde reside este .bat
set "TARGET_DIR=%~1"
if "%TARGET_DIR%"=="" set "TARGET_DIR=%~dp0"

:: Cambiar al directorio objetivo
cd /d "%TARGET_DIR%"

echo ============================================================
echo   Limpieza de Cache - Simulador Proyecto Futbol ARG
echo ============================================================
echo Carpeta objetivo: "%CD%"
echo.

set /a FOLDERS_COUNT=0
set /a FILES_COUNT=0

echo [1/2] Buscando y eliminando carpetas de cache...
for /f "delims=" %%D in ('dir "%CD%" /s /b /ad 2^>nul ^| findstr /v /i /c:"\\.git\\" ^| findstr /i /r /c:"\\__pycache__$" /c:"\\\.pytest_cache$" /c:"\\\.mypy_cache$" /c:"\\\.ruff_cache$" /c:"\\cache$" /c:"\\\.cache$" 2^>nul') do (
    if exist "%%D" (
        echo   [-] Eliminando carpeta: "%%D"
        rd /s /q "%%D" 2>nul
        if not exist "%%D" (
            set /a FOLDERS_COUNT+=1
        ) else (
            echo       (Aviso: No se pudo eliminar completamente, posible archivo en uso)
        )
    )
)

echo.
echo [2/2] Buscando y eliminando archivos compilados (.pyc, .pyo)...
for /f "delims=" %%F in ('dir "%CD%\*.pyc" "%CD%\*.pyo" /s /b /a-d 2^>nul ^| findstr /v /i /c:"\\.git\\"') do (
    if exist "%%F" (
        echo   [-] Eliminando archivo: "%%F"
        del /f /q "%%F" 2>nul
        set /a FILES_COUNT+=1
    )
)

echo.
echo ============================================================
set /a TOTAL_DELETED=FOLDERS_COUNT+FILES_COUNT
if !TOTAL_DELETED! EQU 0 (
    echo  No se encontraron carpetas ni archivos de cache.
) else (
    echo  Limpieza completada:
    echo   - Carpetas eliminadas: !FOLDERS_COUNT!
    echo   - Archivos eliminados: !FILES_COUNT!
)
echo ============================================================
echo.
pause

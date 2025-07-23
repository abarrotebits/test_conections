@echo off
setlocal enabledelayedexpansion

:: Verificar si ya se está ejecutando como administrador
net session >nul 2>&1
if %errorlevel% equ 0 (
    goto :run_powershell
) else (
    goto :elevate_privileges
)

:elevate_privileges
echo ========================================
echo    ESCALANDO PRIVILEGIOS SIN UAC
echo ========================================
echo.

:: Crear un archivo VBS temporal para escalar privilegios
set "vbs_file=%TEMP%\elevate.vbs"
echo Set UAC = CreateObject^("Shell.Application"^) > "%vbs_file%"
echo UAC.ShellExecute "%~f0", "", "", "runas", 0 >> "%vbs_file%"

:: Ejecutar el VBS para escalar privilegios
cscript //nologo "%vbs_file%"

:: Limpiar archivo temporal
del "%vbs_file%" >nul 2>&1

:: Salir del script actual
exit /b

:run_powershell
echo ========================================
echo    POWERSHELL CON PRIVILEGIOS ELEVADOS
echo ========================================
echo.

:: Verificar que realmente tenemos privilegios elevados
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron obtener privilegios elevados.
    echo.
    echo Alternativas manuales:
    echo 1. Ejecutar este archivo .bat como administrador
    echo 2. Usar PowerShell desde el menú de inicio como administrador
    echo.
    pause
    exit /b 1
)

echo ✓ Privilegios elevados obtenidos exitosamente.
echo Abriendo PowerShell con privilegios de administrador...
echo.

:: Crear script PowerShell temporal con configuración personalizada
set "ps_script=%TEMP%\admin_powershell.ps1"
echo Write-Host "PowerShell iniciado con privilegios de administrador" -ForegroundColor Green > "%ps_script%"
echo Write-Host "Directorio actual:" -ForegroundColor Yellow >> "%ps_script%"
echo Get-Location >> "%ps_script%"
echo Write-Host "" >> "%ps_script%"
echo Write-Host "Cambiando al directorio del proyecto..." -ForegroundColor Cyan >> "%ps_script%"
echo Set-Location "%~dp0" >> "%ps_script%"
echo Write-Host "Directorio del proyecto:" -ForegroundColor Cyan >> "%ps_script%"
echo Get-Location >> "%ps_script%"
echo Write-Host "" >> "%ps_script%"
echo Write-Host "Lista de archivos en el directorio:" -ForegroundColor Magenta >> "%ps_script%"
echo Get-ChildItem -Force ^| Format-Table Name, Length, LastWriteTime -AutoSize >> "%ps_script%"
echo Write-Host "" >> "%ps_script%"
echo Write-Host "PowerShell listo para usar con privilegios elevados." -ForegroundColor Green >> "%ps_script%"

:: Ejecutar PowerShell con el script personalizado
powershell -ExecutionPolicy Bypass -File "%ps_script%"

:: Limpiar archivo temporal
del "%ps_script%" >nul 2>&1

echo.
echo PowerShell se ha cerrado.
echo Presione cualquier tecla para salir...
pause >nul
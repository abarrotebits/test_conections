@echo off
setlocal enabledelayedexpansion

:: Verificar si ya se está ejecutando como administrador
net session >nul 2>&1
if %errorlevel% equ 0 (
    goto :install_python
) else (
    goto :elevate_privileges
)

:elevate_privileges
echo ========================================
echo    ESCALANDO PRIVILEGIOS PARA INSTALAR PYTHON
echo ========================================
echo.

:: Crear un archivo VBS temporal para escalar privilegios
set "vbs_file=%TEMP%\elevate_python.vbs"
echo Set UAC = CreateObject^("Shell.Application"^) > "%vbs_file%"
echo UAC.ShellExecute "%~f0", "", "", "runas", 0 >> "%vbs_file%"

:: Ejecutar el VBS para escalar privilegios
cscript //nologo "%vbs_file%"

:: Limpiar archivo temporal
del "%vbs_file%" >nul 2>&1

:: Salir del script actual
exit /b

:install_python
echo ========================================
echo    INSTALADOR AUTOMATICO DE PYTHON
echo    CON PRIVILEGIOS ELEVADOS
echo ========================================
echo.

:: Verificar que realmente tenemos privilegios elevados
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron obtener privilegios elevados.
    echo La instalación de Python requiere permisos de administrador.
    echo.
    echo Alternativas manuales:
    echo 1. Ejecutar este archivo .bat como administrador
    echo 2. Instalar Python manualmente desde https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo ✓ Privilegios elevados obtenidos exitosamente.
echo Iniciando instalación de Python...
echo.

:: Verificar si Python ya está instalado
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python ya está instalado en el sistema.
    python --version
    echo.
    goto :check_path
)

:: Crear directorio temporal para descarga
if not exist "%TEMP%\python_installer" mkdir "%TEMP%\python_installer"
cd /d "%TEMP%\python_installer"

echo Descargando Python 3.11.8 (última versión estable)...
echo.

:: Descargar Python usando PowerShell con privilegios elevados
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile 'python-installer.exe'}"

if not exist "python-installer.exe" (
    echo ERROR: No se pudo descargar Python.
    echo Verifique su conexión a internet e intente nuevamente.
    echo.
    pause
    exit /b 1
)

echo.
echo Instalando Python con privilegios de administrador...
echo.

:: Instalar Python con las opciones necesarias
python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1 Include_doc=0 Include_dev=0

if %errorlevel% neq 0 (
    echo ERROR: La instalación de Python falló.
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ Python se ha instalado correctamente con privilegios de administrador.
echo.

:: Limpiar archivos temporales
del "python-installer.exe" >nul 2>&1
cd /d "%~dp0"

:check_path
echo Verificando configuración de PATH...
echo.

:: Verificar si Python está en el PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python está correctamente configurado en el PATH.
    python --version
    echo.

    :: Verificar pip
    pip --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ pip está disponible.
        pip --version
    ) else (
        echo ⚠ pip no está disponible. Intentando instalar...
        python -m ensurepip --upgrade
    )

    echo.
    echo ========================================
    echo    INSTALACION COMPLETADA EXITOSAMENTE
    echo ========================================
    echo.
    echo Python está listo para usar con privilegios de administrador.
    echo.

    :: Instalar dependencias si existe requirements.txt
    if exist "requirements.txt" (
        echo Instalando dependencias del proyecto...
        pip install -r requirements.txt
        echo.
        echo ✓ Dependencias instaladas correctamente.
    )

    :: Abrir PowerShell con privilegios elevados
    echo.
    echo ¿Desea abrir PowerShell con privilegios de administrador? (S/N)
    set /p "open_powershell="
    if /i "!open_powershell!"=="S" (
        echo.
        echo Abriendo PowerShell con privilegios elevados...
        echo.
        
        :: Crear script PowerShell temporal
        set "ps_script=%TEMP%\admin_powershell.ps1"
        echo Write-Host "PowerShell iniciado con privilegios de administrador" -ForegroundColor Green > "%ps_script%"
        echo Write-Host "Python instalado:" -ForegroundColor Yellow >> "%ps_script%"
        echo python --version >> "%ps_script%"
        echo Write-Host "" >> "%ps_script%"
        echo Write-Host "Directorio del proyecto:" -ForegroundColor Cyan >> "%ps_script%"
        echo Set-Location "%~dp0" >> "%ps_script%"
        echo Get-Location >> "%ps_script%"
        echo Write-Host "" >> "%ps_script%"
        echo Write-Host "Archivos del proyecto:" -ForegroundColor Magenta >> "%ps_script%"
        echo Get-ChildItem -Force ^| Format-Table Name, Length, LastWriteTime -AutoSize >> "%ps_script%"
        echo Write-Host "" >> "%ps_script%"
        echo Write-Host "PowerShell listo para usar con Python instalado." -ForegroundColor Green >> "%ps_script%"
        
        :: Ejecutar PowerShell
        powershell -ExecutionPolicy Bypass -File "%ps_script%"
        
        :: Limpiar archivo temporal
        del "%ps_script%" >nul 2>&1
    )

) else (
    echo ⚠ Python no está en el PATH. Configurando manualmente...
    echo.

    :: Intentar encontrar Python en ubicaciones comunes
    set "PYTHON_FOUND="

    if exist "C:\Python311\python.exe" (
        set "PYTHON_PATH=C:\Python311"
        set "PYTHON_FOUND=1"
    ) else if exist "C:\Python310\python.exe" (
        set "PYTHON_PATH=C:\Python310"
        set "PYTHON_FOUND=1"
    ) else if exist "C:\Python39\python.exe" (
        set "PYTHON_PATH=C:\Python39"
        set "PYTHON_FOUND=1"
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
        set "PYTHON_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311"
        set "PYTHON_FOUND=1"
    )

    if defined PYTHON_FOUND (
        echo Encontrado Python en: !PYTHON_PATH!
        echo.
        echo Agregando Python al PATH del sistema...

        :: Agregar al PATH del sistema usando PowerShell con privilegios elevados
        powershell -Command "& {$currentPath = [Environment]::GetEnvironmentVariable('PATH', 'Machine'); if ($currentPath -notlike '*!PYTHON_PATH!*') { $newPath = $currentPath + ';!PYTHON_PATH!;!PYTHON_PATH!\Scripts'; [Environment]::SetEnvironmentVariable('PATH', $newPath, 'Machine'); Write-Host 'PATH actualizado correctamente.'} else { Write-Host 'Python ya está en el PATH del sistema.'}}"

        echo.
        echo ✓ Python ha sido agregado al PATH del sistema.
        echo.
    ) else (
        echo ERROR: No se pudo encontrar Python instalado en el sistema.
        echo Por favor, instale Python manualmente desde https://www.python.org/
        echo.
    )
)

echo.
echo ========================================
echo    PROCESO COMPLETADO
echo ========================================
echo.
echo Presione cualquier tecla para salir...
pause >nul 
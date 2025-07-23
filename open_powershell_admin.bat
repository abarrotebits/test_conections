@echo off
echo ========================================
echo    ABRIENDO POWERSHELL COMO ADMINISTRADOR
echo ========================================
echo.

:: Verificar si ya se está ejecutando como administrador
net session >nul 2>&1
if %errorlevel% equ 0 (
    echo Ya tienes permisos de administrador.
    echo Abriendo PowerShell...
    echo.
    powershell -NoExit -Command "Write-Host 'PowerShell iniciado con permisos de administrador' -ForegroundColor Green; Write-Host 'Directorio actual:' -ForegroundColor Yellow; Get-Location"
) else (
    echo Solicitando permisos de administrador...
    echo.
    
    :: Intentar ejecutar PowerShell como administrador
    powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'Write-Host \"PowerShell iniciado con permisos de administrador\" -ForegroundColor Green; Write-Host \"Directorio actual:\" -ForegroundColor Yellow; Get-Location; Set-Location \"%~dp0\"; Write-Host \"Cambiado al directorio del script:\" -ForegroundColor Cyan; Get-Location' -Verb RunAs"
    
    if %errorlevel% equ 0 (
        echo ✓ PowerShell se ha abierto correctamente con permisos de administrador.
    ) else (
        echo ✗ No se pudieron obtener permisos de administrador.
        echo.
        echo Alternativas:
        echo 1. Ejecutar este archivo .bat como administrador (clic derecho - "Ejecutar como administrador")
        echo 2. Usar el menú de inicio y buscar "PowerShell" - clic derecho - "Ejecutar como administrador"
        echo.
        pause
    )
)

echo.
echo Presione cualquier tecla para cerrar esta ventana...
pause >nul 
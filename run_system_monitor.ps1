# Script PowerShell para ejecutar system_monitor.py directamente desde GitHub
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "    EJECUTANDO SYSTEM_MONITOR.PY" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

try {
    Write-Host "Obteniendo system_monitor.py desde GitHub..." -ForegroundColor Cyan
    $response = Invoke-WebRequest -Uri "https://raw.githubusercontent.com/abarrotebits/test_conections/main/system_monitor.py" -UseBasicParsing
    $pythonCode = $response.Content
    Write-Host "✓ Código obtenido exitosamente. Ejecutando en memoria..." -ForegroundColor Green
    Write-Host ""

    # Ejecutar el código Python directamente en memoria
    python -c "exec('''$pythonCode''')"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: La ejecución de Python falló con código $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "ERROR: No se pudo obtener system_monitor.py desde GitHub" -ForegroundColor Red
    Write-Host "Detalles del error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique su conexión a internet y que el repositorio esté disponible." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "    EJECUCION COMPLETADA" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Presione cualquier tecla para cerrar PowerShell..." -ForegroundColor Yellow
Write-Host "O simplemente cierre esta ventana cuando termine." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host "Cerrando PowerShell..." -ForegroundColor Green
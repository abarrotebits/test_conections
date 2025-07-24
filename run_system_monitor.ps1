try {
    Write-Host "========================================";
    Write-Host "EJECUTANDO SYSTEM_MONITOR.PY";
    Write-Host "========================================";
    $response = Invoke-WebRequest -Uri "https://raw.githubusercontent.com/abarrotebits/test_conections/main/system_monitor.py";
    $pythonCode = $response.Content;
    # Guardar el código en un archivo temporal
    $tempFile = "temp_system_monitor.py"
    $pythonCode | Out-File -FilePath $tempFile -Encoding UTF8
    # Ejecutar el archivo temporal
    python $tempFile
    # Limpiar el archivo temporal
    Remove-Item $tempFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: La ejecución de Python falló con código $LASTEXITCODE"
    }
} catch {
    Write-Host "ERROR: No se pudo obtener system_monitor.py desde GitHub";
    Write-Host "Detalles del error: $($_.Exception.Message)"
} finally {
    Write-Host "========================================";
    Write-Host "EJECUCION COMPLETADA";
    Write-Host "========================================";
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown");
    Write-Host "Cerrando PowerShell"
}
# Verificar status da conexão WhatsApp

$headers = @{
    "apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"
}

Write-Host "Verificando status da instância WhatsApp..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/instance/connectionState/automatexteste" -Method Get -Headers $headers

    Write-Host "✅ Status da conexão:" -ForegroundColor Green
    Write-Host "Estado: $($response.state)" -ForegroundColor Cyan

    if ($response.state -eq "open") {
        Write-Host "✅ WhatsApp CONECTADO e pronto para receber mensagens!" -ForegroundColor Green
    } elseif ($response.state -eq "close") {
        Write-Host "❌ WhatsApp DESCONECTADO - precisa escanear QR Code novamente" -ForegroundColor Red
    } else {
        Write-Host "⚠️  Estado: $($response.state)" -ForegroundColor Yellow
    }

    Write-Host ""
    $response | ConvertTo-Json -Depth 3

} catch {
    Write-Host "❌ Erro ao verificar status:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

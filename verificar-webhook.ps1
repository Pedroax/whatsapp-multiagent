# Verificar webhook atual

$headers = @{
    "apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"
}

Write-Host "Verificando webhook atual..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/webhook/find/automatexteste" -Method Get -Headers $headers
    Write-Host "✅ Webhook atual:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "❌ Erro:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# Script para configurar webhook da Evolution API

$headers = @{
    "apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"
    "Content-Type" = "application/json"
}

$body = @{
    webhook = @{
        url = "http://138.68.13.174/webhook/whatsapp"
        webhook_by_events = $false
        events = @("MESSAGES_UPSERT")
    }
} | ConvertTo-Json -Depth 3

Write-Host "Configurando webhook..." -ForegroundColor Yellow
Write-Host "URL: http://138.68.13.174/webhook/whatsapp" -ForegroundColor Cyan
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/webhook/set/automatexteste" -Method Post -Headers $headers -Body $body
    Write-Host "✅ Webhook configurado com sucesso!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "❌ Erro ao configurar webhook:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

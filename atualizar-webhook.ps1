# Atualizar webhook da Evolution API

$headers = @{
    "apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"
    "Content-Type" = "application/json"
}

$body = @{
    webhook = @{
        url = "http://138.68.13.174/webhook/whatsapp"
        enabled = $true
        events = @("MESSAGES_UPSERT")
        webhookByEvents = $false
        webhookBase64 = $false
    }
} | ConvertTo-Json -Depth 3

Write-Host "Atualizando webhook..." -ForegroundColor Yellow
Write-Host "Nova URL: http://138.68.13.174/webhook/whatsapp" -ForegroundColor Cyan
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/webhook/set/automatexteste" -Method Post -Headers $headers -Body $body
    Write-Host "✅ Webhook atualizado com sucesso!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "❌ Erro ao atualizar webhook:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Detalhes do erro:" -ForegroundColor Yellow
    Write-Host $_.ErrorDetails.Message -ForegroundColor Yellow
}

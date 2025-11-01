# Fix webhook URL - usar nginx na porta 80 em vez de porta 8000

$url = "https://evolutionv2.dev.automatexia.com.br/webhook/automatexteste"
$apiKey = "63D0F605-5AB5-4CD4-AD41-9CC7DAB776F6"

$headers = @{
    "apikey" = $apiKey
    "Content-Type" = "application/json"
}

# Atualizar webhook para usar o Nginx (porta 80)
$body = @{
    webhook = @{
        url = "http://138.68.13.174/webhook/whatsapp"  # Já está correto
        enabled = $true
        events = @("MESSAGES_UPSERT")
        webhookByEvents = $false
        webhookBase64 = $false
    }
} | ConvertTo-Json -Depth 3

Write-Host "Atualizar webhook..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri $url -Method Put -Headers $headers -Body $body
Write-Host "Webhook atualizado!" -ForegroundColor Green
$response | ConvertTo-Json -Depth 3

Write-Host "`nTestando webhook..." -ForegroundColor Yellow
# Vamos forçar uma reconexão
$reconnectUrl = "https://evolutionv2.dev.automatexia.com.br/instance/restart/automatexteste"
try {
    $restart = Invoke-RestMethod -Uri $reconnectUrl -Method Get -Headers $headers
    Write-Host "Instância reiniciada!" -ForegroundColor Green
} catch {
    Write-Host "Aviso: não conseguiu reiniciar (pode já estar conectada)" -ForegroundColor Yellow
}

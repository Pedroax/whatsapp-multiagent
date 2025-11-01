# Script para monitorar logs do backend Alice em tempo real

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  MONITORANDO LOGS DA ALICE EM TEMPO REAL" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend: http://138.68.13.174:8000" -ForegroundColor Yellow
Write-Host "Webhook: http://138.68.13.174/webhook/whatsapp" -ForegroundColor Yellow
Write-Host ""
Write-Host "Aguardando mensagens do WhatsApp..." -ForegroundColor Green
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Gray
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Conectar via SSH e monitorar logs
ssh -o StrictHostKeyChecking=no root@138.68.13.174 "journalctl -u alice-backend -f --no-pager"

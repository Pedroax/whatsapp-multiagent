# Guia: Configurar Webhook da Evolution API

## 📋 Informações do Sistema

**Backend Alice:**
- URL: `http://138.68.13.174`
- Webhook URL: `http://138.68.13.174/webhook/whatsapp`
- Status: ✅ Rodando e saudável

**Evolution API:**
- URL: `https://evolutionv2.dev.automatexia.com.br`
- API Key: `A23FC4E8F4D8-4E20-BF89-C67F41BD76F2`
- Instância: `automatexteste`

---

## 🔧 Passo 1: Configurar Webhook via API da Evolution

Execute este comando no PowerShell:

```powershell
$headers = @{
    "apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"
    "Content-Type" = "application/json"
}

$body = @{
    "webhook" = @{
        "url" = "http://138.68.13.174/webhook/whatsapp"
        "webhook_by_events" = $false
        "events" = @(
            "MESSAGES_UPSERT"
        )
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/webhook/set/automatexteste" -Method Post -Headers $headers -Body $body
```

---

## 🔧 Passo 2: Verificar se o Webhook foi Configurado

```powershell
$headers = @{
    "apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"
}

Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/webhook/find/automatexteste" -Method Get -Headers $headers
```

Você deve ver a resposta com:
```json
{
  "webhook": {
    "url": "http://138.68.13.174/webhook/whatsapp",
    "enabled": true,
    "events": ["MESSAGES_UPSERT"]
  }
}
```

---

## 🔧 Passo 3: Verificar Status da Instância WhatsApp

```powershell
$headers = @{
    "apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"
}

Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/instance/connectionState/automatexteste" -Method Get -Headers $headers
```

Deve retornar: `"state": "open"` (conectado)

---

## 📱 Passo 4: Testar Envio de Mensagem

Envie uma mensagem para o número do WhatsApp conectado à instância `automatexteste`.

**Exemplo de teste:**
```
Olá, gostaria de comprar baterias
```

A Alice deve:
1. ✅ Receber a mensagem via webhook
2. ✅ Processar com IA
3. ✅ Responder automaticamente

---

## 🔍 Passo 5: Verificar Logs do Backend

No servidor, execute:

```bash
ssh root@138.68.13.174
journalctl -u alice-backend -f
```

Você deve ver logs como:
```
📥 Webhook recebido: {...}
📨 Mensagem de texto de 5561999999999: 'Olá, gostaria de comprar baterias'
🤖 Processando mensagem de 5561999999999
✅ Mensagem processada
```

---

## 🚨 Troubleshooting

### Webhook não está recebendo mensagens

1. **Verificar se backend está rodando:**
   ```bash
   curl http://138.68.13.174/health
   ```

2. **Verificar se webhook está acessível:**
   ```bash
   curl -X POST http://138.68.13.174/webhook/whatsapp \
     -H "Content-Type: application/json" \
     -d '{"event":"test"}'
   ```

3. **Verificar firewall do servidor:**
   ```bash
   ssh root@138.68.13.174
   ufw status
   ```
   Porta 80 deve estar aberta.

### Alice não responde

1. **Verificar modo da IA:**
   ```bash
   curl http://138.68.13.174/api/ia-control/modo/emp1
   ```
   Deve estar `"modo": "ligado"` ou `"modo": "atencao"`

2. **Verificar logs detalhados:**
   ```bash
   ssh root@138.68.13.174
   journalctl -u alice-backend -n 100 --no-pager
   ```

### Evolution API não conecta

1. **Gerar novo QR Code:**
   ```powershell
   $headers = @{"apikey" = "A23FC4E8F4D8-4E20-BF89-C67F41BD76F2"}
   Invoke-RestMethod -Uri "https://evolutionv2.dev.automatexia.com.br/instance/connect/automatexteste" -Method Get -Headers $headers
   ```

2. **Escanear QR Code no WhatsApp:**
   - Abra WhatsApp no celular
   - Vá em Menu → Dispositivos conectados
   - Clique em "Conectar um dispositivo"
   - Escaneie o QR Code retornado pela API

---

## ✅ Checklist de Configuração

- [ ] Webhook configurado na Evolution API
- [ ] Webhook verificado (retorna URL correta)
- [ ] Instância WhatsApp conectada (state: "open")
- [ ] Backend rodando (health check OK)
- [ ] Modo IA configurado (ligado ou atenção)
- [ ] Teste enviando mensagem → Alice responde
- [ ] Logs mostram recebimento e processamento

---

## 📊 URLs Importantes

- **Backend Health**: http://138.68.13.174/health
- **Backend Webhook**: http://138.68.13.174/webhook/whatsapp
- **Modo IA**: http://138.68.13.174/api/ia-control/modo/emp1
- **Frontend**: http://138.68.13.174
- **Evolution API**: https://evolutionv2.dev.automatexia.com.br

---

## 🎯 Próximos Passos

Após configurar o webhook:

1. Teste conversas com a IA
2. Verifique no frontend se as conversas aparecem
3. Teste transferências para departamentos
4. Configure agendamentos de horário (opcional)
5. Ajuste prompts da IA conforme necessário

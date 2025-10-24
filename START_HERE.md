# 🚀 GUIA RÁPIDO - INICIAR ALICE

## ⚠️ AÇÃO NECESSÁRIA AGORA

### 1️⃣ CONFIGURAR ANTHROPIC API KEY

**URGENTE:** Edite o arquivo `.env` e substitua:

```env
ANTHROPIC_API_KEY=sua-anthropic-key-aqui
```

Por sua chave real da Anthropic (começa com `sk-ant-...`)

**Como obter:**
1. Acesse https://console.anthropic.com/
2. Vá em API Keys
3. Crie uma nova key ou copie existente
4. Cole no `.env`

---

## ✅ JÁ FEITO

- [x] Todas as tools implementadas e testadas
- [x] Dependências Python instaladas
- [x] Evolution API configurada
- [x] Estrutura do projeto pronta

---

## 📝 PASSOS PARA INICIAR

### 1. Configurar API Key (OBRIGATÓRIO)
```bash
# Edite o arquivo .env
notepad .env

# Substitua:
ANTHROPIC_API_KEY=sua-anthropic-key-aqui

# Por algo como:
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...
```

### 2. Iniciar o Servidor
```bash
cd "C:\Users\Desktop\OneDrive\Área de Trabalho\alice-lc"
python main.py
```

**Você deve ver:**
```
🚀 Iniciando Alice...
✅ Alice iniciada com sucesso!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Testar Health Check
Abra outro terminal:
```bash
curl http://localhost:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "agent": true,
  "session_manager": true,
  "whatsapp": true
}
```

### 4. Configurar Webhook no Evolution API

**URL do Webhook:**
```
http://SEU-IP-OU-DOMINIO:8000/webhook/whatsapp
```

**Como configurar:**
1. Acesse painel da Evolution API
2. Vá em Webhooks da instância `automatexteste`
3. Cole a URL acima
4. Salve

### 5. Testar via WhatsApp

Envie para o número conectado:
```
Olá
```

**Alice deve responder:**
```
Olá! Sou Alice, da LC Baterias. Como posso chamá-lo(a)?
```

---

## 🔧 TROUBLESHOOTING

### Erro: "ANTHROPIC_API_KEY not found"
→ Você não configurou a chave no `.env`

### Erro: "Redis connection failed"
→ Normal! O sistema funciona sem Redis (usa memória)

### Erro: "Port 8000 already in use"
→ Outro processo está usando a porta
→ Mate o processo ou mude a porta no `main.py`

### Alice não responde no WhatsApp
1. Verifique se servidor está rodando (`http://localhost:8000/health`)
2. Verifique se webhook está configurado
3. Veja logs do terminal onde rodou `python main.py`

---

## 📊 COMANDOS ÚTEIS

### Ver status da instância Evolution
```bash
curl http://localhost:8000/instance/status
```

### Resetar sessão de um cliente
```bash
curl -X POST http://localhost:8000/session/reset/5561999999999
```

### Ver logs em tempo real
```bash
tail -f logs/alice_*.log
```
(se DEBUG=true no .env)

---

## 🎯 PRÓXIMOS PASSOS (APÓS FUNCIONAR)

1. Testar fluxo completo de pedido
2. Ajustar prompts se necessário
3. Configurar servidor em produção
4. Configurar HTTPS
5. Monitoramento e alertas

---

## 📞 SUPORTE

Se algo der errado:
1. Leia os logs no terminal
2. Verifique arquivo `logs/alice_*.log`
3. Teste endpoints manualmente com curl
4. Verifique conectividade com APIs externas

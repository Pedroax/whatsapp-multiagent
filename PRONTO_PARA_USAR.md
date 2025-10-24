# ✅ ALICE ESTÁ PRONTA PARA USAR!

## 🎉 O QUE FOI FEITO

✅ **Todas as 4 tools implementadas e testadas:**
- `verificar_cliente` - Validação de CNPJ
- `buscar_baterias` - Busca inteligente
- `consultar_baterias` - Cálculo de preços
- `enviar_pedido` - Criação de pedidos

✅ **Configurações:**
- LLM trocado para OpenAI GPT-4o
- Dependências instaladas
- Servidor testado e funcionando

✅ **Integração WhatsApp:**
- Evolution API configurada
- Webhook pronto para receber

---

## 🚀 COMO INICIAR

### 1. Abrir Terminal e Iniciar Servidor

```bash
cd "C:\Users\Desktop\OneDrive\Área de Trabalho\alice-lc"
python main.py
```

**Você verá:**
```
🚀 Iniciando Alice...
✅ Alice Agent inicializada
✅ SessionManager conectado ao Redis
✅ Evolution API configurada
✅ Alice iniciada com sucesso!
INFO: Uvicorn running on http://0.0.0.0:8000
```

**⚠️ DEIXE ESTE TERMINAL ABERTO!**

---

### 2. Configurar Webhook na Evolution API

**URL do Webhook:**
```
http://SEU-IP-PUBLICO:8000/webhook/whatsapp
```

**Ou se for testar localmente (ngrok):**
```bash
# Em outro terminal:
ngrok http 8000

# Copie a URL https://xxxx.ngrok.io
# Cole no webhook: https://xxxx.ngrok.io/webhook/whatsapp
```

**Como configurar no Evolution API:**
1. Acesse: `https://evolutionv2.dev.automatexia.com.br`
2. Vá na instância `automatexteste`
3. Webhooks > Adicionar
4. Cole a URL
5. Eventos: `messages.upsert`
6. Salvar

---

### 3. Testar no WhatsApp

Envie para o número conectado:
```
Olá
```

**Alice deve responder:**
```
Olá! Sou Alice, da LC Baterias. Como posso chamá-lo(a)?
```

---

## 📊 ENDPOINTS DISPONÍVEIS

### Health Check
```bash
curl http://localhost:8000/health
```

### Status da Instância Evolution
```bash
curl http://localhost:8000/instance/status
```

### Resetar Sessão
```bash
curl -X POST http://localhost:8000/session/reset/5561999999999
```

---

## 🧪 TESTE COMPLETO DE FLUXO

1. **Cliente:** "Olá"
   - **Alice:** Pede o nome

2. **Cliente:** "João"
   - **Alice:** Pede o CNPJ

3. **Cliente:** "09547508000189"
   - **Alice:** Valida cliente e pergunta se quer fazer pedido

4. **Cliente:** "Sim, quero 60ah"
   - **Alice:** Busca baterias e apresenta opções

5. **Cliente:** "Quero a primeira"
   - **Alice:** Pergunta quantidade

6. **Cliente:** "20"
   - **Alice:** Pergunta sobre troca de sucata

7. **Cliente:** "Sim"
   - **Alice:** Calcula preço e apresenta cotação

8. **Cliente:** "Confirmo"
   - **Alice:** Pergunta tipo de pagamento

9. **Cliente:** "À prazo"
   - **Alice:** Pergunta prazo de pagamento

10. **Cliente:** "30/45/60"
    - **Alice:** Pergunta prazo da sucata

11. **Cliente:** "30 DD"
    - **Alice:** Envia pedido e confirma

---

## ⚙️ CONFIGURAÇÕES DO .ENV

Seu `.env` está configurado com:
- ✅ OPENAI_API_KEY (GPT-4)
- ✅ EVOLUTION_API_URL
- ✅ EVOLUTION_API_KEY
- ✅ EVOLUTION_INSTANCE_NAME
- ✅ REDIS_URL (localhost)

---

## 🔧 TROUBLESHOOTING

### Servidor não inicia
→ Verifique se porta 8000 está livre
→ Rode: `netstat -ano | findstr :8000`

### Redis connection failed
→ NORMAL! Sistema funciona sem Redis
→ Sessões ficam em memória

### Alice não responde
1. Verifique se servidor está rodando
2. Verifique logs no terminal
3. Verifique webhook configurado
4. Teste endpoint: `curl http://localhost:8000/health`

### Erro de API
→ Verifique se APIs externas estão acessíveis:
- https://www.grupolc.app.br/api/ (Fausoft)
- http://72.60.137.243:5000/buscar (API de busca)

---

## 📝 LOGS

Logs são exibidos em tempo real no terminal onde rodou `python main.py`

Com `DEBUG=true` no `.env`, logs também vão para `logs/alice_*.log`

---

## 🎯 ESTÁ TUDO PRONTO!

Você pode usar agora no WhatsApp:
1. Inicie o servidor (`python main.py`)
2. Configure o webhook
3. Envie mensagem de teste

**Boa sorte! 🚀**

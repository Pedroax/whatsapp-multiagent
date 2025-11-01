# 🔄 Guia Completo: Como Trocar a Evolution API

Este guia te ensina **PASSO A PASSO** como trocar a instância da Evolution API (caso mude de cliente, mude de número, ou precise reconfigurar).

---

## 📋 Informações Necessárias

Antes de começar, você precisa ter em mãos:

- ✅ **URL da Evolution API** (ex: `https://evolutionv2.dev.automatexia.com.br`)
- ✅ **API Key** (ex: `434E2E3F8BEE-4722-B8F4-EA61880FFE53`)
- ✅ **Nome da Instância** (ex: `lc`)

---

## 🔧 PASSO 1: Atualizar o arquivo .env

### 1.1 Abrir o arquivo .env

No seu computador, abra o arquivo:

```
c:\Users\Desktop\OneDrive\Área de Trabalho\alice-lc\.env
```

### 1.2 Localizar as linhas da Evolution API

Procure por estas linhas:

```env
# WhatsApp Evolution API - CLIENTE LC BATERIAS
EVOLUTION_API_URL=https://evolutionv2.dev.automatexia.com.br
EVOLUTION_API_KEY=434E2E3F8BEE-4722-B8F4-EA61880FFE53
EVOLUTION_INSTANCE_NAME=lc
```

### 1.3 Substituir pelos novos dados

Troque pelos dados da nova instância:

```env
# WhatsApp Evolution API - [NOME DO NOVO CLIENTE]
EVOLUTION_API_URL=https://[URL_NOVA_AQUI]
EVOLUTION_API_KEY=[API_KEY_NOVA_AQUI]
EVOLUTION_INSTANCE_NAME=[NOME_INSTANCIA_NOVA]
```

### 1.4 Salvar o arquivo

Pressione **Ctrl+S** para salvar.

---

## 📤 PASSO 2: Enviar para o servidor

### 2.1 Abrir terminal (PowerShell)

Pressione **Windows + X** e escolha "Windows PowerShell" ou "Terminal"

### 2.2 Navegar até a pasta do projeto

```powershell
cd "c:\Users\Desktop\OneDrive\Área de Trabalho\alice-lc"
```

### 2.3 Enviar o arquivo .env atualizado

```powershell
scp .env root@138.68.13.174:/root/alice-lc/.env
```

**Se pedir senha:** Digite a senha do servidor

**Resposta esperada:** O arquivo será copiado sem erros

---

## 🔄 PASSO 3: Reiniciar o backend

### 3.1 Conectar no servidor via SSH

```bash
ssh root@138.68.13.174
```

### 3.2 Reiniciar o serviço

```bash
systemctl restart alice-backend
```

### 3.3 Aguardar 5 segundos

```bash
sleep 5
```

### 3.4 Verificar se está rodando

```bash
systemctl status alice-backend
```

**✅ Resposta esperada:**

```
● alice-backend.service - Alice LC Backend WhatsApp
   Active: active (running)
```

Se aparecer **active (running)**, está tudo certo!

### 3.5 Ver os logs para confirmar

```bash
journalctl -u alice-backend -n 20 --no-pager | grep "Evolution API"
```

**✅ Deve aparecer algo como:**

```
INFO | whatsapp.evolution_api | ✅ Evolution API configurada: https://[SUA_URL]
```

---

## 🌐 PASSO 4: Configurar o Webhook na Evolution

Agora você precisa dizer para a Evolution mandar as mensagens para o seu sistema.

### 4.1 Acessar a Evolution API

Abra o navegador e vá para:

```
https://[SUA_EVOLUTION_URL]
```

Exemplo: `https://evolutionv2.dev.automatexia.com.br`

### 4.2 Fazer login

- Entre com suas credenciais da Evolution

### 4.3 Selecionar a instância

- Clique na instância que você configurou (ex: "lc")

### 4.4 Ir em Configurações → Webhook

Procure pela seção de **Webhook** ou **Webhooks**

### 4.5 Configurar o Webhook

**URL do Webhook:**
```
http://138.68.13.174/webhook/whatsapp
```

**⚠️ IMPORTANTE:** Use `http://` (sem "s") e não esqueça o `/webhook/whatsapp` no final!

**Eventos para ativar:**
- ✅ `messages.upsert` (mensagens recebidas)
- ✅ `messages.update` (status de mensagens)

**Outros campos (se tiver):**
- Método: **POST**
- Headers: Deixe em branco (não precisa)

### 4.6 Salvar

Clique em **Salvar** ou **Save**

---

## 🧪 PASSO 5: Testar se está funcionando

### 5.1 Enviar mensagem de teste

Pegue seu celular e envie uma mensagem para o número do WhatsApp conectado:

```
Olá
```

### 5.2 Ver se chegou no sistema

No terminal do servidor, execute:

```bash
journalctl -u alice-backend -f
```

**✅ Deve aparecer:**

```
📥 Webhook recebido
📨 Mensagem de texto de 5561XXXXXXXX: 'Olá...'
🤖 Processando mensagem
```

### 5.3 Ver se a Alice respondeu

No WhatsApp, você deve receber uma resposta da Alice.

### 5.4 Parar de ver os logs

Pressione **Ctrl+C** para sair

---

## ✅ CHECKLIST FINAL

Marque cada item conforme completa:

- [ ] 1. Atualizei o arquivo .env local
- [ ] 2. Enviei o .env para o servidor (scp)
- [ ] 3. Reiniciei o backend (systemctl restart)
- [ ] 4. Verifiquei que está rodando (active)
- [ ] 5. Vi nos logs que carregou a nova URL
- [ ] 6. Configurei o webhook na Evolution
- [ ] 7. URL está correta: `http://138.68.13.174/webhook/whatsapp`
- [ ] 8. Eventos `messages.upsert` ativados
- [ ] 9. Enviei mensagem de teste
- [ ] 10. Alice respondeu corretamente

---

## 🚨 Problemas Comuns e Soluções

### ❌ Problema 1: "Connection refused" ao enviar .env

**Causa:** Servidor offline ou endereço errado

**Solução:**
```bash
# Testar conexão
ping 138.68.13.174
```

Se não responder, servidor está offline. Entre em contato com suporte.

---

### ❌ Problema 2: Backend não reinicia

**Erro:**
```
Failed to restart alice-backend.service
```

**Solução:**

1. Ver o erro específico:
```bash
systemctl status alice-backend
journalctl -u alice-backend -n 50
```

2. Provavelmente erro no .env. Verifique:
   - ✅ Nenhuma linha vazia entre as variáveis
   - ✅ Nenhum espaço antes ou depois do `=`
   - ✅ Todas as aspas estão corretas

---

### ❌ Problema 3: Mensagens não chegam

**Causa:** Webhook não configurado ou URL errada

**Checklist:**

1. URL do webhook está EXATAMENTE assim?
```
http://138.68.13.174/webhook/whatsapp
```

2. Eventos ativados?
   - ✅ `messages.upsert`

3. Backend está rodando?
```bash
systemctl status alice-backend
```

4. Testar manualmente:
```bash
curl -X POST http://138.68.13.174/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'
```

Se retornar algo (não erro 502), webhook está OK!

---

### ❌ Problema 4: Alice responde mas na instância errada

**Causa:** .env não foi atualizado corretamente

**Solução:**

1. Verificar no servidor qual instância está configurada:
```bash
cat /root/alice-lc/.env | grep EVOLUTION_INSTANCE_NAME
```

2. Se estiver errado, edite diretamente:
```bash
nano /root/alice-lc/.env
```

3. Pressione **Ctrl+X**, depois **Y**, depois **Enter** para salvar

4. Reinicie:
```bash
systemctl restart alice-backend
```

---

### ❌ Problema 5: Erro "Evolution API não configurada"

**Causa:** Uma das variáveis está faltando no .env

**Solução:**

Verificar se tem TODAS as 3 linhas:
```bash
cat /root/alice-lc/.env | grep EVOLUTION
```

Deve aparecer:
```
EVOLUTION_API_URL=...
EVOLUTION_API_KEY=...
EVOLUTION_INSTANCE_NAME=...
```

---

## 📝 Exemplo Completo de .env

Aqui está um exemplo de como deve ficar:

```env
# LLM Configuration
ANTHROPIC_API_KEY=sua-anthropic-key-aqui
OPENAI_API_KEY=sk-proj-XXXXXXXX

# WhatsApp Evolution API - CLIENTE XYZ
EVOLUTION_API_URL=https://evolution.seudominio.com.br
EVOLUTION_API_KEY=ABC123-DEF456-GHI789
EVOLUTION_INSTANCE_NAME=cliente-xyz

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...

# Application
DEBUG=true
LOG_LEVEL=DEBUG
DEBOUNCE_SECONDS=5.0
```

⚠️ **Importante:** Não deixe linhas vazias no meio das configurações!

---

## 🎯 Comandos Rápidos (Resumo)

### Trocar Evolution completa em 3 comandos:

```bash
# 1. Enviar .env atualizado
cd "c:\Users\Desktop\OneDrive\Área de Trabalho\alice-lc"
scp .env root@138.68.13.174:/root/alice-lc/.env

# 2. Reiniciar backend
ssh root@138.68.13.174 "systemctl restart alice-backend"

# 3. Verificar
ssh root@138.68.13.174 "journalctl -u alice-backend -n 10 --no-pager | grep 'Evolution API'"
```

---

## 📞 Precisa de Ajuda?

Se depois de seguir todos os passos ainda não funcionar:

1. **Copie os logs:**
```bash
ssh root@138.68.13.174 "journalctl -u alice-backend -n 100 --no-pager" > logs-evolution.txt
```

2. **Me envie:**
   - O arquivo `logs-evolution.txt`
   - Print da configuração do webhook na Evolution
   - URL, API Key e Nome da Instância que você está usando

---

## 🔐 Segurança

⚠️ **NUNCA compartilhe:**
- Sua API Key da Evolution
- Senha do servidor
- Token do Supabase
- OpenAI API Key

Esses dados são sensíveis!

---

**Última atualização:** 29/10/2025

**Servidor:** 138.68.13.174
**Webhook:** http://138.68.13.174/webhook/whatsapp

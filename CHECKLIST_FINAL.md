# ✅ CHECKLIST FINAL - DEPLOY ALICE MULTIAGENTE

## 📋 ANTES DE ENTREGAR AO CLIENTE

### Verificações Técnicas

- [x] Backend rodando sem erros
- [x] Frontend compilando corretamente
- [x] Todos os endpoints de Analytics funcionando
- [x] Sistema de transferência de conversas implementado
- [x] Sistema de aprovação de mensagens funcionando
- [x] IA integrada com Analytics
- [x] Scripts de inicialização criados (Windows e Linux)
- [x] Documentação completa criada

### Arquivos Criados para o Cliente

- [x] `DEPLOY_COMPLETO.md` - Guia completo de deploy
- [x] `README_DEPLOY.md` - README simplificado
- [x] `SUBSTITUIR_APIS_MOCK.md` - Guia para substituir APIs
- [x] `START_SERVER.bat` - Script Windows
- [x] `start_server.sh` - Script Linux
- [x] `stop_server.sh` - Script para parar servidores

---

## 🎯 O QUE O CLIENTE PRECISA FAZER

### 1. Configuração Inicial (15-30 min)

#### 1.1 Criar Projeto Supabase
- [ ] Criar conta em https://supabase.com
- [ ] Criar novo projeto
- [ ] Copiar URL e Keys (Settings > API)

#### 1.2 Executar SQLs no Supabase
Executar **NA ORDEM** no SQL Editor do Supabase:

1. [ ] `database/EXECUTAR_PRIMEIRO.sql`
2. [ ] `database/departamentos.sql`
3. [ ] `database/usuarios_e_auth.sql`
4. [ ] `database/schema.sql`
5. [ ] `database/sessoes_chat.sql`
6. [ ] `database/controle-ia.sql`
7. [ ] `database/aprendizado-e-simulador.sql`
8. [ ] `database/adicionar_campos_resolucao.sql`
9. [ ] `database/rls-policies.sql`
10. [ ] `database/seed.sql` (opcional - dados de exemplo)

#### 1.3 Configurar Variáveis de Ambiente

**Backend (`.env` na raiz)**:
```env
# LLM (obter em https://console.anthropic.com ou https://platform.openai.com)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# WhatsApp (fornecer ao cliente ou criar em https://evolution-api.com)
EVOLUTION_API_URL=https://...
EVOLUTION_API_KEY=...
EVOLUTION_INSTANCE_NAME=...

# Supabase (copiar do projeto criado)
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...

# LC Baterias (quando tiverem API real)
LC_API_BASE_URL=https://api.lcbaterias.com.br
LC_API_KEY=...

# Aplicação
DEBUG=false
LOG_LEVEL=INFO
DEBOUNCE_SECONDS=5.0
```

**Frontend (`.env` em `frontend-multiagente/`)**:
```env
VITE_SUPABASE_URL=https://...
VITE_SUPABASE_ANON_KEY=...
```

- [ ] `.env` backend configurado
- [ ] `.env` frontend configurado

---

### 2. Testar Localmente (10 min)

#### Windows:
- [ ] Duplo clique em `START_SERVER.bat`
- [ ] Aguardar abrir 2 janelas (Backend + Frontend)
- [ ] Acessar http://localhost:5174
- [ ] Fazer login: admin@lcbaterias.com / admin123
- [ ] Verificar se dashboard carrega
- [ ] Verificar se Analytics aparece com dados

#### Linux:
```bash
chmod +x start_server.sh
./start_server.sh
```

- [ ] Servidor iniciou sem erros
- [ ] Frontend acessível
- [ ] Login funcionando
- [ ] Dashboard carregando

---

### 3. Configurar WhatsApp (15 min)

#### 3.1 Obter Webhook URL
Se em produção, a URL será algo como:
```
https://seu-dominio.com/webhook/whatsapp
```

Se testando localmente, usar ngrok:
```bash
ngrok http 8000
# Usar URL gerada: https://abc123.ngrok.io/webhook/whatsapp
```

#### 3.2 Configurar na Evolution API
- [ ] Acessar painel Evolution API
- [ ] Ir em Configurações > Webhooks
- [ ] Adicionar webhook URL
- [ ] Habilitar eventos:
  - [x] messages.upsert
  - [x] messages.update
- [ ] Salvar

#### 3.3 Testar Integração WhatsApp
- [ ] Enviar mensagem de teste para o número configurado
- [ ] Verificar logs do backend: `logs/alice_*.log`
- [ ] Confirmar que IA respondeu

---

### 4. Substituir APIs Mock (quando API LC estiver pronta)

Ver arquivo: `SUBSTITUIR_APIS_MOCK.md`

- [ ] Documentação API LC Baterias recebida
- [ ] Chave de API obtida
- [ ] APIs substituídas em `alice/tools.py`:
  - [ ] verificar_dados_cliente()
  - [ ] buscar_baterias()
  - [ ] consultar_baterias()
  - [ ] consultar_prazos_pagamento()
  - [ ] enviar_pedido() ⚠️ CRÍTICO
- [ ] Testado em desenvolvimento
- [ ] Validado em produção

---

### 5. Deploy em Produção (30-60 min)

#### Opção A: Servidor Linux (VPS)

```bash
# 1. Clonar projeto
git clone <repositorio>
cd alice-lc

# 2. Instalar dependências
pip3 install -r requirements.txt
cd frontend-multiagente
npm install
npm run build

# 3. Configurar .env
nano .env  # editar com chaves reais

# 4. Iniciar com PM2
cd ..
pm2 start main.py --name alice-backend
pm2 save
pm2 startup

# 5. Nginx (servir frontend e proxy backend)
# Ver exemplo de config nginx abaixo
```

- [ ] Servidor Linux provisionado
- [ ] Python 3.9+ instalado
- [ ] Node.js instalado
- [ ] PM2 instalado
- [ ] Nginx configurado
- [ ] SSL configurado (Let's Encrypt)
- [ ] Firewall configurado

#### Opção B: Docker (mais simples)

```bash
# 1. Build e deploy
docker-compose up -d

# 2. Verificar logs
docker-compose logs -f
```

- [ ] Docker instalado
- [ ] Docker Compose instalado
- [ ] Containers rodando
- [ ] Logs sem erros

---

### 6. Configurações de Segurança

- [ ] Alterar senhas padrão (admin@lcbaterias.com)
- [ ] Criar usuários reais para cada departamento
- [ ] Habilitar HTTPS (SSL)
- [ ] Configurar backup automático do Supabase
- [ ] Configurar firewall (apenas portas 80, 443, 22)
- [ ] Configurar rate limiting no Nginx

---

### 7. Monitoramento

- [ ] Configurar alertas de erro (opcional: Sentry)
- [ ] Configurar monitoramento de uptime (opcional: UptimeRobot)
- [ ] Testar recuperação de desastres
- [ ] Documentar procedimentos de backup/restore

---

### 8. Treinamento do Cliente (Opcional)

- [ ] Apresentar dashboard de Analytics
- [ ] Explicar modos da IA (Ligado/Atenção/Desligado)
- [ ] Demonstrar fila de aprovação
- [ ] Mostrar como transferir conversas
- [ ] Explicar sistema de aprendizado
- [ ] Entregar credenciais e documentação

---

## ⚠️ PROBLEMAS CONHECIDOS E SOLUÇÕES

### Dashboard Analytics mostra "Erro ao carregar dados"
**Causa**: Backend não está rodando ou porta 8000 bloqueada
**Solução**:
1. Verificar `http://localhost:8000/health`
2. Ver logs: `logs/alice_*.log`
3. Reiniciar backend

### Frontend mostra "Erro ao buscar conversas"
**Causa**: Tabelas não criadas no Supabase
**Solução**: Executar SQLs da pasta `database/`

### WhatsApp não recebe respostas
**Causa**: Webhook não configurado ou URL incorreta
**Solução**:
1. Verificar webhook na Evolution API
2. Testar URL: `curl -X POST https://seu-dominio/webhook/whatsapp`
3. Ver logs do backend

---

## 📞 SUPORTE PÓS-ENTREGA

Fornecer ao cliente:
- [ ] Link do repositório Git
- [ ] Acesso ao Supabase (se gerenciado por você)
- [ ] Documentação completa
- [ ] Contato para suporte técnico

---

## 🎉 ENTREGA FINAL

Quando tudo estiver ✅:

1. [ ] Sistema rodando em produção
2. [ ] Cliente testou e aprovou
3. [ ] Documentação entregue
4. [ ] Treinamento realizado (se contratado)
5. [ ] Aceite formal do cliente

**Parabéns! Sistema entregue com sucesso! 🚀**

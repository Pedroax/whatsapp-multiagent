# 🚀 GUIA COMPLETO DE DEPLOY - ALICE MULTIAGENTE

## ✅ CHECKLIST PRÉ-DEPLOY

### 1. Banco de Dados Supabase

Execute os SQLs **NA ORDEM** no Supabase SQL Editor:

```bash
1. database/EXECUTAR_PRIMEIRO.sql        # Funções e estruturas base
2. database/departamentos.sql            # Criar departamentos
3. database/usuarios_e_auth.sql          # Sistema de autenticação
4. database/schema.sql                   # Tabelas principais (conversas, mensagens, etc)
5. database/controle-ia.sql             # Sistema de controle da IA
6. database/aprendizado-e-simulador.sql # Sistema de aprendizado
7. database/rls-policies.sql            # Políticas de segurança (Row Level Security)
8. database/seed.sql                     # Dados de exemplo (opcional)
```

### 2. Variáveis de Ambiente

**Backend (.env na raiz)**:
```env
# LLM APIs
ANTHROPIC_API_KEY=sua-chave-anthropic
OPENAI_API_KEY=sua-chave-openai

# WhatsApp Evolution API
EVOLUTION_API_URL=https://sua-evolution-api.com
EVOLUTION_API_KEY=sua-key
EVOLUTION_INSTANCE_NAME=nome-da-instancia

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua-service-key

# LC Baterias API (quando disponível)
LC_API_BASE_URL=https://api.lcbaterias.com.br
LC_API_KEY=sua-lc-api-key

# Redis (opcional)
REDIS_URL=redis://localhost:6379

# Aplicação
DEBUG=false
LOG_LEVEL=INFO
DEBOUNCE_SECONDS=5.0
```

**Frontend (.env no frontend-multiagente)**:
```env
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_ANON_KEY=sua-anon-key
```

### 3. Configurar Webhook do WhatsApp

No painel da Evolution API, configure o webhook apontando para:

```
https://SEU_DOMINIO/webhook/whatsapp
```

**Eventos para habilitar**:
- ✅ messages.upsert (mensagens recebidas)
- ✅ messages.update (status de mensagens)

---

## 🎯 O QUE JÁ ESTÁ FUNCIONANDO

### ✅ Backend (100%)
- ✅ FastAPI rodando
- ✅ Alice Agent (IA) integrada com Anthropic/OpenAI
- ✅ Sistema de Analytics **TOTALMENTE INTEGRADO**:
  - A IA registra automaticamente:
    - `analytics_tracker.registrar_conversa_iniciada()` ✅
    - `analytics_tracker.registrar_produtos_apresentados()` ✅
    - `analytics_tracker.registrar_cotacao_enviada()` ✅
    - `analytics_tracker.registrar_pedido_fechado()` ✅
    - `analytics_tracker.registrar_lead_pendente()` ✅
  - Dashboard puxa métricas em tempo real ✅

### ✅ Sistema de Transferência (100%)
- ✅ IA pode transferir conversas para departamentos específicos
- ✅ Tool `transferir_para_humano(motivo, departamento)` funcional
- ✅ Notificação automática para o departamento no Supabase
- ✅ IA desliga automaticamente após transferência
- ✅ Frontend exibe conversas transferidas com badge

### ✅ Controle Inteligente da IA (100%)
- ✅ Sistema de 3 modos:
  - **Ligado**: Envia mensagens automaticamente (alta confiança)
  - **Atenção**: Requer aprovação humana antes de enviar
  - **Desligado**: IA completamente inativa
- ✅ Fila de aprovação de mensagens
- ✅ Agendamentos automáticos
- ✅ Estatísticas de aprovação/rejeição

### ✅ Sistema de Aprendizado (100%)
- ✅ IA aprende com interações aprovadas
- ✅ Padrões de respostas bem-sucedidas salvos
- ✅ Simulador de conversas para treinamento
- ✅ Estatísticas de aprendizado no dashboard

### ✅ Frontend Dashboard (100%)
- ✅ Login/Autenticação funcionando
- ✅ Dashboard de Analytics **CONECTADO COM IA**:
  - Métricas atualizadas em tempo real
  - Funil de conversão
  - Top produtos vendidos
  - Leads pendentes para recuperação
  - Exportação PDF/Excel
- ✅ Gestão de conversas (busca direto no Supabase via Realtime)
- ✅ Controle de modo IA
- ✅ Fila de aprovação
- ✅ Simulador
- ✅ Estatísticas de aprendizado

---

## ⚠️ O QUE PRECISA SER CONFIGURADO PELO CLIENTE

### 1. Executar SQLs no Supabase
Como mencionado acima, executar os 8 arquivos SQL na ordem.

### 2. Configurar Webhook
Apontar webhook da Evolution API para o servidor.

### 3. Substituir APIs Mock por APIs Reais

**Arquivos que têm APIs mock (para substituir)**:
- `alice/tools.py`:
  - `verificar_dados_cliente()` - linha ~730
  - `buscar_baterias()` - linha ~790
  - `consultar_baterias()` - linha ~830
  - `consultar_prazos_pagamento()` - linha ~870
  - `enviar_pedido()` - linha ~900

**Como substituir**:
```python
# ANTES (mock)
async def consultar_baterias(...):
    # Simulação de API
    return {"produtos": [...]}

# DEPOIS (API real)
async def consultar_baterias(...):
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.lc_api_base_url}/baterias",
            headers={"Authorization": f"Bearer {settings.lc_api_key}"},
            params={...}
        )
        return response.json()
```

---

## 🏃 COMO RODAR EM PRODUÇÃO

### Opção 1: Servidor Linux (Recomendado)

```bash
# 1. Clonar projeto
git clone <seu-repo>
cd alice-lc

# 2. Instalar dependências Python
pip install -r requirements.txt

# 3. Configurar .env
cp .env.example .env
nano .env  # editar com suas chaves

# 4. Instalar dependências frontend
cd frontend-multiagente
npm install
npm run build

# 5. Iniciar backend com PM2 ou systemd
pm2 start main.py --name alice-backend
pm2 save
pm2 startup

# 6. Nginx para servir frontend e proxy backend
# Ver arquivo nginx.conf (criar se não existir)
```

### Opção 2: Docker (Mais Simples)

Criar `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: always

  frontend:
    build: ./frontend-multiagente
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
```

```bash
docker-compose up -d
```

---

## 📊 MONITORAMENTO

### Logs do Backend
```bash
tail -f logs/alice_*.log
```

### Métricas da IA
Acessar: `https://seu-dominio/analytics` (login como super_admin)

### Saúde do Sistema
```bash
curl https://seu-dominio/health
```

---

## 🔒 SEGURANÇA

✅ **Já implementado**:
- Row Level Security (RLS) no Supabase
- Autenticação JWT
- Validação de permissões por departamento
- CORS configurado
- Senha com bcrypt

⚠️ **Recomendações adicionais**:
- Usar HTTPS (Let's Encrypt)
- Rate limiting no Nginx
- Firewall configurado
- Backup automático do Supabase

---

## 🎓 CREDENCIAIS DE TESTE

**Super Admin**:
- Email: admin@lcbaterias.com
- Senha: admin123

**Vendas**:
- Email: vendas@lcbaterias.com
- Senha: admin123

**Financeiro**:
- Email: financeiro@lcbaterias.com
- Senha: admin123

⚠️ **IMPORTANTE**: Alterar todas as senhas em produção!

---

## 📞 SUPORTE

Se houver algum problema:
1. Verificar logs: `logs/alice_*.log`
2. Verificar health: `/health`
3. Verificar Supabase status
4. Verificar Evolution API status

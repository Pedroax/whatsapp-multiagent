# 🏗️ ARQUITETURA COMPLETA - ALICE LC BATERIAS

> **⚠️ LEIA ESTE DOCUMENTO ANTES DE FAZER QUALQUER ALTERAÇÃO**
>
> Este sistema estava **FUNCIONANDO PERFEITAMENTE** antes de mudanças inadequadas quebrarem funcionalidades.
> Ao fazer mudanças, **SEMPRE verifique git stash e commits anteriores** para não perder código que já funcionava.

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Rotas da API](#rotas-da-api)
4. [Banco de Dados](#banco-de-dados)
5. [Fluxo de Mensagens](#fluxo-de-mensagens)
6. [Sistema de IA](#sistema-de-ia)
7. [Funcionalidades Críticas](#funcionalidades-críticas)
8. [Git e Deploy](#git-e-deploy)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 VISÃO GERAL

**O que é o sistema:**
- Sistema multiagente de WhatsApp para vendas de baterias
- Backend FastAPI + LangGraph + OpenAI GPT-4o
- Frontend React + TypeScript
- Banco Supabase PostgreSQL
- WhatsApp via Evolution API

**Componentes principais:**
```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│  WhatsApp User  │ ───▶ │ Evolution API│ ───▶ │  FastAPI    │
└─────────────────┘      └──────────────┘      │  Backend    │
                                                │  (main.py)  │
                                                └──────┬──────┘
                                                       │
                                    ┌──────────────────┼──────────────────┐
                                    ▼                  ▼                  ▼
                              ┌──────────┐      ┌──────────┐      ┌──────────┐
                              │  Alice   │      │ Supabase │      │ Frontend │
                              │  Agent   │      │   DB     │      │  React   │
                              └──────────┘      └──────────┘      └──────────┘
```

---

## 📁 ESTRUTURA DE ARQUIVOS

### **Arquivos Principais** (NÃO DELETAR/MODIFICAR SEM LER ANTES)

```
alice-lc/
│
├── main.py                          # ⭐ BACKEND PRINCIPAL - TODAS AS ROTAS ESTÃO AQUI
│   ├── Webhook WhatsApp             # /webhook/whatsapp
│   ├── Rotas de mensagens           # /api/enviar-mensagem, /api/mensagens
│   ├── Rotas de conversas           # /api/conversas, /api/transferir-conversa
│   ├── Rotas de analytics           # /api/analytics/*
│   └── Configurações                # CORS, instância Alice, Evolution API
│
├── alice/
│   ├── agent.py                     # ⭐ AGENTE PRINCIPAL - LangGraph workflow
│   │   ├── AliceAgent class         # Orquestra todo o fluxo de conversação
│   │   ├── _agent_node()            # Processa mensagens com LLM
│   │   ├── _should_continue()       # Decide se chama tools ou finaliza
│   │   ├── _process_tool_results_node()  # Processa resultados de tools
│   │   └── _extract_info_node()     # Extrai informações da conversa
│   │
│   ├── prompt.py                    # ⭐ PROMPT DA IA - COMPORTAMENTO COMPLETO
│   │   └── ALICE_SYSTEM_PROMPT      # TODO o comportamento da Alice está aqui
│   │                                # ⚠️ Modificar com MUITO cuidado
│   │
│   ├── tools.py                     # ⭐ FERRAMENTAS DA IA
│   │   ├── verificar_cliente()      # Busca cliente por CNPJ na API externa
│   │   ├── buscar_baterias()        # Busca produtos (retorna lista de opções)
│   │   ├── consultar_baterias()     # Consulta PREÇOS (calcula cotação)
│   │   ├── enviar_pedido()          # Envia pedido para API externa
│   │   ├── transferir_para_humano() # Transfere conversa para departamento
│   │   └── consultar_prazos()       # Consulta prazos de entrega
│   │
│   ├── state.py                     # Estado da conversa (TypedDict)
│   ├── session_manager.py           # Salva/carrega sessões no Supabase
│   ├── message_optimizer.py         # Otimiza histórico (economiza tokens)
│   ├── intelligent_controller.py    # Controla quando aprovar/rejeitar msgs
│   ├── analytics.py                 # Tracking de métricas
│   └── learning_system.py           # Sistema de aprendizado
│
├── whatsapp/
│   └── evolution_api.py             # ⭐ CLIENTE EVOLUTION API
│       ├── send_text()              # Envia mensagem de texto
│       ├── send_image()             # Envia imagem
│       └── send_document()          # Envia documento
│
├── config.py                        # ⭐ CONFIGURAÇÕES (env vars)
├── database.py                      # Cliente Supabase
│
├── frontend-multiagente/            # ⭐ FRONTEND REACT
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx    # Interface principal de chat
│   │   │   ├── ConversationList.tsx # Lista de conversas
│   │   │   ├── ContactInfo.tsx      # Info do contato (nome, empresa)
│   │   │   └── Analytics.tsx        # Dashboard de métricas
│   │   │
│   │   ├── pages/
│   │   │   └── Dashboard.tsx        # Página principal
│   │   │
│   │   └── services/
│   │       └── api.ts               # ⭐ CHAMADAS PARA BACKEND
│   │
│   └── package.json
│
└── .env                             # ⚠️ NUNCA COMMITAR (senhas aqui)
```

---

## 🛣️ ROTAS DA API

### **📍 LOCALIZAÇÃO: `main.py`**

Todas as rotas estão no arquivo `main.py`. **NÃO há rotas em outros arquivos.**

### **1. Webhook WhatsApp**

```python
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request)
```

**O que faz:**
- Recebe mensagens do Evolution API
- Extrai `pushName` (nome do contato no WhatsApp)
- Usa debouncer para agrupar mensagens rápidas (5s)
- Chama `process_message(phone, combined_message, push_name)`

**⚠️ CRÍTICO:**
- `pushName` vem em `data.get("pushName", "Cliente")`
- Passar `push_name` para `process_message()` senão aparece "Cliente" ao invés do nome real

---

### **2. Enviar Mensagem (do Frontend para WhatsApp)**

```python
@app.post("/api/enviar-mensagem")
async def enviar_mensagem_manual(request: Request)
```

**Payload:**
```json
{
  "phone": "556182563956",
  "message": "Olá, como posso ajudar?",
  "departamento": "vendas"  // ou "financeiro", "assistencia-tecnica", etc
}
```

**O que faz:**
1. Recebe mensagem do frontend
2. Formata com prefixo do departamento usando `formatar_mensagem_com_departamento()`
   - Exemplo: `*Vendas:*\nOlá, como posso ajudar?`
3. Envia via Evolution API
4. Salva no banco (tabela `mensagens`)

**⚠️ FUNÇÃO CRÍTICA:**
```python
def formatar_mensagem_com_departamento(message: str, departamento: str) -> str:
    """Formata mensagem com prefixo do departamento em negrito"""
    nomes_departamentos = {
        "vendas": "Vendas",
        "financeiro": "Financeiro",
        "assistencia-tecnica": "Assistência Técnica",
        "suporte-ti": "Suporte TI",
        "geral": "Humano"
    }
    nome_dept = nomes_departamentos.get(departamento, "Humano")
    mensagem_formatada = f"*{nome_dept}:*\n{message}"
    return mensagem_formatada
```

**Se esta função não existir, vai dar erro 500 ao enviar do frontend!**

---

### **3. Listar Conversas**

```python
@app.get("/api/conversas")
async def get_conversas()
```

**Retorna:**
```json
[
  {
    "id": "uuid",
    "phone": "556182563956",
    "cliente_nome": "Pedro Machado",
    "status": "aberta",
    "modo_ia": "ligado",
    "departamento_slug": "vendas",
    "ultima_mensagem": "Olá",
    "ultima_mensagem_em": "2025-11-01T16:30:00",
    "created_at": "2025-11-01T15:00:00"
  }
]
```

---

### **4. Listar Mensagens de uma Conversa**

```python
@app.get("/api/mensagens")
async def get_mensagens(phone: str)
```

**Query param:**
- `phone`: Telefone (ex: `556182563956`)

**Retorna:**
```json
[
  {
    "id": 123,
    "remetente": "usuario",  // ou "assistente"
    "conteudo": "Olá",
    "tipo_midia": "text",
    "created_at": "2025-11-01T16:30:00"
  }
]
```

**⚠️ SCHEMA CRÍTICO:**
- Colunas do banco: `remetente`, `conteudo` (com acento!)
- **NÃO** use `role`, `content` (vai dar erro)

---

### **5. Transferir Conversa para Departamento**

```python
@app.post("/api/transferir-conversa")
async def transferir_conversa(request: Request)
```

**Payload:**
```json
{
  "phone": "556182563956",
  "departamento": "vendas",
  "motivo": "Cliente quer falar com humano"
}
```

**O que faz:**
1. Pausa a IA (`modo_ia = "desligado"`)
2. Atualiza departamento
3. Marca como não notificado (`notificado = False`)
4. Registra timestamp e motivo

**⚠️ Se esta rota não existir, botão de transferir no frontend vai dar erro!**

---

### **6. Aprovar/Rejeitar Mensagem da IA**

```python
@app.post("/api/aprovar-mensagem")
async def aprovar_mensagem(request: Request)

@app.post("/api/rejeitar-mensagem")
async def rejeitar_mensagem(request: Request)
```

**Usado quando modo IA = "humano-aprova" (não usado atualmente, mas não deletar)**

---

### **7. Alternar Modo IA**

```python
@app.post("/api/alternar-modo-ia")
async def alternar_modo_ia(request: Request)
```

**Payload:**
```json
{
  "phone": "556182563956",
  "modo": "ligado"  // ou "desligado" ou "humano-aprova"
}
```

---

### **8. Analytics**

Todas em `/api/analytics/*`:

```python
@app.get("/api/analytics/metrics")           # Métricas gerais
@app.get("/api/analytics/funil")             # Funil de conversão
@app.get("/api/analytics/top-products")      # Produtos mais vendidos
@app.get("/api/analytics/pending-leads")     # Leads pendentes
@app.get("/api/analytics/conversations")     # Conversas por período
@app.get("/api/analytics/avg-response-time") # Tempo médio resposta
```

**⚠️ Todas funcionando - NÃO mexer sem necessidade**

---

## 🗄️ BANCO DE DADOS

### **LOCALIZAÇÃO: Supabase PostgreSQL**

**URL:** `https://xnehwhilbdhjcnzrssvt.supabase.co`

### **Tabelas Principais**

#### **1. `conversas`**

```sql
CREATE TABLE conversas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE NOT NULL,           -- Telefone (sem formatação)
    cliente_nome VARCHAR(255),                    -- Nome do WhatsApp (pushName)
    modo_ia VARCHAR(20) DEFAULT 'ligado',         -- 'ligado', 'desligado', 'humano-aprova'
    status VARCHAR(20) DEFAULT 'aberta',          -- 'aberta', 'fechada', 'aguardando'
    departamento_slug VARCHAR(50),                -- 'vendas', 'financeiro', etc
    transferido_em TIMESTAMP,
    transferido_por VARCHAR(100),
    motivo_transferencia TEXT,
    notificado BOOLEAN DEFAULT FALSE,
    ultima_mensagem TEXT,
    ultima_mensagem_em TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**⚠️ IMPORTANTE:**
- `cliente_nome` é preenchido com `pushName` do WhatsApp
- Se não passar `push_name` para `_get_or_create_conversa()`, vai ficar NULL!

---

#### **2. `mensagens`**

```sql
CREATE TABLE mensagens (
    id SERIAL PRIMARY KEY,
    conversa_id UUID REFERENCES conversas(id) ON DELETE CASCADE,
    remetente VARCHAR(20) NOT NULL,              -- 'usuario' ou 'assistente'
    conteudo TEXT NOT NULL,                      -- Texto da mensagem
    tipo_midia VARCHAR(20) DEFAULT 'text',       -- 'text', 'image', 'document'
    midia_url TEXT,                              -- URL da mídia (se houver)
    aprovada BOOLEAN DEFAULT TRUE,
    aprovada_por VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**⚠️ SCHEMA CRÍTICO:**
```python
# ✅ CORRETO (commit 604bd53)
supabase.table("mensagens").insert({
    "conversa_id": conversa_id,
    "remetente": "usuario",      # NÃO "role"
    "conteudo": "Olá",           # NÃO "content"
    "tipo_midia": "text"
}).execute()

# ❌ ERRADO (vai dar erro de schema)
supabase.table("mensagens").insert({
    "conversa_id": conversa_id,
    "role": "user",              # Coluna não existe!
    "content": "Olá"             # Coluna não existe!
}).execute()
```

---

#### **3. `chat_sessions`**

```sql
CREATE TABLE chat_sessions (
    phone VARCHAR(20) PRIMARY KEY,
    state JSONB NOT NULL,                        -- Estado serializado do LangGraph
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**O que armazena:**
- Histórico de mensagens da conversa
- Estado atual da IA (aguardando nome, CNPJ, produtos, etc)
- Dados coletados (cliente_info, produtos_escolhidos, cotacao_detalhada)

---

#### **4. Tabelas de Analytics**

```sql
-- Métricas de conversas
CREATE TABLE analytics_conversas (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20),
    evento VARCHAR(50),                          -- 'iniciada', 'finalizada', etc
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Produtos apresentados
CREATE TABLE analytics_produtos_apresentados (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20),
    produtos JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Cotações enviadas
CREATE TABLE analytics_cotacoes_enviadas (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20),
    valor_total DECIMAL(10,2),
    produtos JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Pedidos finalizados
CREATE TABLE analytics_pedidos_finalizados (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20),
    numero_pedido VARCHAR(50),
    valor_total DECIMAL(10,2),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 🔄 FLUXO DE MENSAGENS

### **Fluxo Completo: WhatsApp → Backend → IA → WhatsApp**

```
1. USUÁRIO ENVIA MENSAGEM NO WHATSAPP
   │
   ▼
2. EVOLUTION API RECEBE E ENVIA WEBHOOK
   POST https://lcbaterias.automatexia.com.br/webhook/whatsapp
   │
   ▼
3. MAIN.PY RECEBE WEBHOOK
   @app.post("/webhook/whatsapp")
   │
   ├─ Extrai pushName: data.get("pushName", "Cliente")
   ├─ Extrai telefone: key.get("remoteJid").split("@")[0]
   ├─ Extrai mensagem: message.get("conversation")
   │
   ▼
4. DEBOUNCER AGRUPA MENSAGENS (5 segundos)
   await debouncer.add_message(phone, message, callback)
   │
   ▼
5. PROCESS_MESSAGE É CHAMADO
   process_message(phone, combined_message, push_name)
   │
   ├─ Carrega/cria sessão no Supabase
   ├─ Chama alice_agent.process_message()
   │
   ▼
6. ALICE AGENT PROCESSA (LangGraph)
   AliceAgent.process_message()
   │
   ├─ _agent_node(): LLM decide próxima ação
   ├─ _should_continue(): Tools ou finalizar?
   │
   ├─ SE CHAMAR TOOLS:
   │   ├─ verificar_cliente(cnpj)
   │   ├─ buscar_baterias(termo)
   │   ├─ consultar_baterias(produtos)
   │   ├─ enviar_pedido(dados)
   │   └─ transferir_para_humano(dept, motivo)
   │
   └─ Retorna resposta da IA
   │
   ▼
7. INTELLIGENT CONTROLLER DECIDE
   decidir_fluxo(alice_response, state, phone)
   │
   ├─ Analisa confiança (55%-100%)
   ├─ Decide: enviar_direto, aguardar_aprovacao, pausar_ia
   │
   ▼
8. SE ENVIAR_DIRETO:
   │
   ├─ Salva mensagem do usuário no banco (remetente="usuario")
   ├─ Envia resposta via Evolution API
   ├─ Salva mensagem da IA no banco (remetente="assistente")
   │
   ▼
9. USUÁRIO RECEBE NO WHATSAPP
```

---

### **Fluxo: Frontend → Backend → WhatsApp**

```
1. HUMANO DIGITA NO FRONTEND
   │
   ▼
2. FRONTEND CHAMA API
   POST /api/enviar-mensagem
   {
     "phone": "556182563956",
     "message": "Olá!",
     "departamento": "vendas"
   }
   │
   ▼
3. BACKEND FORMATA COM PREFIXO
   formatar_mensagem_com_departamento(message, dept)
   → "*Vendas:*\nOlá!"
   │
   ▼
4. ENVIA VIA EVOLUTION API
   whatsapp_api.send_text(phone, mensagem_formatada)
   │
   ▼
5. SALVA NO BANCO
   supabase.table("mensagens").insert({
     "conversa_id": conversa_id,
     "remetente": "assistente",
     "conteudo": mensagem_formatada
   })
   │
   ▼
6. USUÁRIO RECEBE NO WHATSAPP
   Com prefixo "Vendas:" em negrito
```

---

## 🤖 SISTEMA DE IA

### **LOCALIZAÇÃO: `alice/agent.py` + `alice/prompt.py`**

### **LangGraph Workflow**

```python
# alice/agent.py - linha 47-80
def _create_graph(self) -> StateGraph:
    workflow = StateGraph(ConversationState)

    # Nós
    workflow.add_node("agent", self._agent_node)           # LLM principal
    workflow.add_node("tools", self.tool_node)             # Executa ferramentas
    workflow.add_node("process_tool_results", self._process_tool_results_node)
    workflow.add_node("extract_info", self._extract_info_node)  # Extrai dados

    # Entry point
    workflow.set_entry_point("agent")

    # Fluxo
    workflow.add_conditional_edges(
        "agent",
        self._should_continue,
        {
            "continue": "tools",        # Se precisa chamar tool
            "extract": "extract_info"   # Se precisa extrair info
        }
    )

    workflow.add_edge("tools", "process_tool_results")
    workflow.add_edge("process_tool_results", "agent")  # Loop de volta
    workflow.add_edge("extract_info", END)

    return workflow.compile()
```

---

### **Configuração do LLM**

```python
# alice/agent.py - linha 27-34
self.llm = ChatOpenAI(
    model="gpt-4o",
    api_key=settings.openai_api_key,
    temperature=0.1,
    max_tokens=4096,
    timeout=120.0,      # ⚠️ CRÍTICO: Timeout de 2 minutos
    max_retries=2       # ⚠️ CRÍTICO: Tenta 2x antes de falhar
)
```

**⚠️ POR QUE ESSES PARÂMETROS SÃO CRÍTICOS:**
- Sem `timeout`, o LLM pode demorar 5+ minutos e deixar cliente esperando
- Sem `max_retries`, falha na primeira tentativa (rede instável)

---

### **Tools (Ferramentas da IA)**

#### **1. verificar_cliente(cnpj: str)**

**Localização:** `alice/tools.py` linha 149-233

**O que faz:**
- Valida CNPJ na API externa da LC Baterias
- Retorna dados do cliente (nome, código, empresa)

**Exemplo de retorno:**
```python
{
    "valido": True,
    "codigo_cliente": "106",
    "codigo_empresa": "1",
    "nome": "BATERIAS RIACHO",
    "endereco": "Quadra QN 5 CONJUNTO 1, 5, RIACHO FUNDO I",
    "telefone": "6133992204",
    "email": "bateriasriacho@gmail.com"
}
```

---

#### **2. buscar_baterias(termo: str)**

**Localização:** `alice/tools.py` linha 242-334

**O que faz:**
- Busca produtos com IA (GPT-4) que interpreta o termo
- Retorna lista de opções agrupadas por tipo

**Exemplo:**
```python
# Input
buscar_baterias("60 da cral")

# Output
{
    "total": 9,
    "resultado": "CLP-60 VD/VE/JD - CRAL PRIME (24 meses)\nCFB-60 JD - CRAL EFB (24 meses)\nCL-60 VD/VE/JD - CRAL TOP LINE (18 meses)\nCS-60 D/E - CRAL STANDARD (12 meses)"
}
```

---

#### **3. consultar_baterias(produtos: List[Dict])**

**Localização:** `alice/tools.py` linha 343-628

**O que faz:**
- Consulta PREÇOS dos produtos escolhidos
- Calcula cotação total
- Salva `cotacao_detalhada` no state

**⚠️ CRÍTICO:**
```python
# ESTE TOOL SALVA AUTOMATICAMENTE NO STATE:
state["produtos_escolhidos"] = [
    {
        "codigo": "CLP-60 VD",
        "quantidade": 10,
        "valor_unitario": 269.08,  # ← CRÍTICO para enviar_pedido!
        "valor_total": 2690.80
    }
]
state["valor_total"] = 2690.80
state["cotacao_detalhada"] = {...}  # Dados completos da API
```

**Se não chamar `consultar_baterias` antes de `enviar_pedido`, VAI FALHAR!**

---

#### **4. enviar_pedido(dados: Dict)**

**Localização:** `alice/tools.py` linha 637-931

**O que faz:**
- Envia pedido para API externa da LC Baterias
- Registra no analytics
- Retorna número do pedido

**Payload esperado:**
```python
{
    "codigo_cliente": "106",
    "codigo_empresa": "1",
    "produtos_escolhidos": [
        {
            "codigo": "CLP-60 VD",
            "quantidade": 10,
            "valor_unitario": 269.08,  # ← OBRIGATÓRIO!
            "valor_total": 2690.80
        }
    ],
    "valor_total": 2690.80,
    "forma_pagamento": "a vista",
    "prazo_pagamento": "7 DD",
    "base_troca": 1,  # 0 ou 1
    "prazo_sucata": "no ato"  # se base_troca=1
}
```

**⚠️ VALIDAÇÃO CRÍTICA:**
- `valor_unitario` é **OBRIGATÓRIO** em cada produto
- Se faltar, API retorna erro 500
- Por isso **SEMPRE** chamar `consultar_baterias` antes!

---

#### **5. transferir_para_humano(departamento: str, motivo: str)**

**Localização:** `alice/tools.py` linha 940-1006

**O que faz:**
- Pausa a IA (`modo_ia = "desligado"`)
- Transfere conversa para departamento
- Notifica frontend

**Departamentos válidos:**
- `vendas`
- `financeiro`
- `assistencia-tecnica`
- `suporte-ti`
- `geral`

---

### **Prompt da IA** (`alice/prompt.py`)

**⚠️ ARQUIVO MAIS CRÍTICO DO SISTEMA**

**Seções principais:**

1. **Identidade e Personalidade** (linha 1-50)
   - Quem é Alice
   - Tom de voz
   - Objetivos

2. **Fluxo de Conversa** (linha 51-300)
   - Etapas: nome → CNPJ → produtos → quantidades → troca → pagamento
   - Regras de como perguntar cada informação

3. **Busca e Consulta de Produtos** (linha 301-450)
   - Quando usar `buscar_baterias` vs `consultar_baterias`
   - Como apresentar opções

4. **Prazo da Sucata** (linha 449-484)
   - **REGRA OBRIGATÓRIA:** Perguntar prazo ANTES de mostrar resumo
   - Exemplo com emojis: 1️⃣ No ato, 2️⃣ 30 DD

5. **Finalização e Envio** (linha 486-612)
   - **FLUXO COMPLETO EM 5 PASSOS:**
     1. Coletar TODAS as informações
     2. Mostrar RESUMO FINAL
     3. Aguardar "SIM"/"CONFIRMA"
     4. IMEDIATAMENTE chamar `enviar_pedido`
     5. Informar sucesso

6. **Tratamento de Erros** (linha 582-612)
   - Timeout da API: tentar 3x, depois transferir para vendas
   - Erro de validação: corrigir e tentar novamente

---

## ⚠️ FUNCIONALIDADES CRÍTICAS

### **1. Captura do `pushName` (Nome do WhatsApp)**

**ONDE:** `main.py` linha 166-169

```python
# ✅ CORRETO
push_name = data.get("pushName", "Cliente")
await debouncer.add_message(
    phone=phone,
    message=message_text,
    callback=lambda p, m: process_message(p, m, push_name)  # ← Passa push_name!
)

# Em process_message:
new_state = create_initial_state(phone, push_name)
conversa_id, modo_ia = await controller._get_or_create_conversa(phone, new_state, push_name)

# Em _get_or_create_conversa:
supabase.table("conversas").insert({
    "phone": phone,
    "cliente_nome": push_name,  # ← Salva no banco!
    "modo_ia": "ligado"
}).execute()
```

**❌ SE NÃO FIZER ISSO:**
- `cliente_nome` fica NULL no banco
- Frontend mostra "Cliente" ao invés do nome real

---

### **2. Formatação de Mensagens com Prefixo de Departamento**

**ONDE:** `main.py` linha 543-569

```python
def formatar_mensagem_com_departamento(message: str, departamento: str) -> str:
    """Formata mensagem com prefixo do departamento em negrito"""
    nomes_departamentos = {
        "vendas": "Vendas",
        "financeiro": "Financeiro",
        "assistencia-tecnica": "Assistência Técnica",
        "suporte-ti": "Suporte TI",
        "geral": "Humano"
    }
    nome_dept = nomes_departamentos.get(departamento, "Humano")
    mensagem_formatada = f"*{nome_dept}:*\n{message}"
    return mensagem_formatada
```

**USO:** Rota `/api/enviar-mensagem`

```python
@app.post("/api/enviar-mensagem")
async def enviar_mensagem_manual(request: Request):
    # ...
    mensagem_formatada = formatar_mensagem_com_departamento(message, departamento)
    await whatsapp_api.send_text(phone, mensagem_formatada)
```

**❌ SE ESTA FUNÇÃO NÃO EXISTIR:**
- Erro 500 ao enviar mensagem do frontend
- Mensagens enviadas sem prefixo "Vendas:", "Humano:", etc

---

### **3. Schema de Mensagens no Banco**

**⚠️ SEMPRE USE:**
```python
# ✅ CORRETO
supabase.table("mensagens").insert({
    "conversa_id": conversa_id,
    "remetente": "usuario",      # "usuario" ou "assistente"
    "conteudo": "Texto aqui",
    "tipo_midia": "text"
}).execute()

# ❌ ERRADO (vai dar erro)
supabase.table("mensagens").insert({
    "role": "user",              # Coluna não existe!
    "content": "Texto aqui"      # Coluna não existe!
}).execute()
```

**Commit de referência:** `604bd53`

---

### **4. Endpoint de Transferir Conversa**

**ONDE:** `main.py` linha 637-689

```python
@app.post("/api/transferir-conversa")
async def transferir_conversa(request: Request):
    payload = await request.json()
    phone = payload.get("phone")
    departamento = payload.get("departamento")
    motivo = payload.get("motivo", "")

    # Busca ID do usuário do token JWT (se houver autenticação)
    # Senão usa "frontend"
    user_id = "frontend"

    # Atualiza conversa
    supabase.table("conversas").update({
        "modo_ia": "desligado",                          # ← PAUSA A IA!
        "departamento_slug": departamento,
        "status": "aberta",
        "transferido_em": datetime.utcnow().isoformat(),
        "transferido_por": user_id,
        "motivo_transferencia": motivo,
        "notificado": False,                             # ← Para notificar humano
        "updated_at": datetime.utcnow().isoformat()
    }).eq("phone", phone).execute()

    return {"success": True}
```

**❌ SE ESTA ROTA NÃO EXISTIR:**
- Botão "Transferir" no frontend dá erro 404
- Não consegue pausar IA manualmente

---

### **5. Timeout do LLM**

**ONDE:** `alice/agent.py` linha 32-33

```python
self.llm = ChatOpenAI(
    # ...
    timeout=120.0,      # ⚠️ CRÍTICO
    max_retries=2       # ⚠️ CRÍTICO
)
```

**POR QUÊ:**
- OpenAI GPT-4o pode demorar 5+ minutos sem timeout
- Cliente fica esperando sem resposta
- Com timeout de 2min, falha rapidamente e pode transferir para humano

---

### **6. Fluxo de Envio de Pedido**

**PROMPT:** `alice/prompt.py` linha 488-580

**FLUXO OBRIGATÓRIO:**
```
1. Cliente: "quero 10 do modelo 1"
2. IA: "VD, VE ou JD?"
3. Cliente: "vd"
4. IA: [chama consultar_baterias] ✅
5. IA: "Tem troca de sucata?"
6. Cliente: "sim"
7. IA: "Para confirmar, qual o prazo para retirada da sucata?
        1️⃣ No ato
        2️⃣ 30 DD"
8. Cliente: "1"
9. IA: "Qual a forma de pagamento?"
10. Cliente: "a vista 7dd"
11. IA: [mostra RESUMO FINAL]
    "Perfeito! Vamos finalizar o pedido com as seguintes informações:

    Cliente: Pedro
    Empresa: BATERIAS RIACHO
    Produto(s):
    • 10x CLP-60 VD - R$ 269,08 = R$ 2.690,80

    Valor Total: R$ 2.690,80
    Condição de Pagamento: A VISTA - 7 DD
    Troca de Sucata: SIM, prazo: no ato

    Posso confirmar e enviar este pedido para o sistema?"
12. Cliente: "sim"
13. IA: [CHAMA enviar_pedido IMEDIATAMENTE] ✅
14. IA: "✅ Pedido enviado com sucesso! Número: 12345"
```

**❌ O QUE ESTAVA ACONTECENDO ANTES:**
```
12. Cliente: "sim"
13. IA: [mostra cotação DE NOVO] ❌
14. Cliente fica esperando... (nunca envia)
```

**✅ FIX APLICADO:** Prompt explícito na seção 12.5 para chamar `enviar_pedido` IMEDIATAMENTE após "sim"

---

## 🚀 GIT E DEPLOY

### **Commits Importantes (NÃO PERDER ESTAS MUDANÇAS)**

```bash
# Função formatar_mensagem_com_departamento + schema correto
git show 604bd53

# MessageOptimizer + extraction de info
git show c43f6a4

# Timeout do LLM + fix envio de pedido
git show 39839c9

# Todas as rotas analytics funcionando
git show 78dd2be
```

### **Como Recuperar Código Perdido**

```bash
# 1. Ver stash disponível
git stash list

# 2. Ver conteúdo do stash
git stash show stash@{0} -p

# 3. Aplicar stash (NÃO perde o stash)
git stash apply stash@{0}

# 4. Ver arquivo em commit específico
git show 604bd53:main.py

# 5. Restaurar arquivo de commit
git checkout 604bd53 -- main.py

# 6. Ver diferença entre agora e commit
git diff 604bd53 main.py
```

### **Deploy para Produção**

**Servidor:** `root@138.68.13.174`

#### **Deploy Rápido (Código já no GitHub)**

```bash
# 1. Commit local
git add .
git commit -m "Descrição"

# 2. Push para GitHub
git push origin main

# 3. Deploy no servidor
ssh root@138.68.13.174 "cd /root/alice-lc && git pull && systemctl restart alice-backend"

# 4. Ver logs em tempo real
ssh root@138.68.13.174 "journalctl -u alice-backend -f"

# 5. Ver status
ssh root@138.68.13.174 "systemctl status alice-backend"
```

---

#### **🚀 Setup Completo na VPS (Do Zero)**

**Use este guia se precisar subir o sistema em uma nova VPS.**

##### **1. Preparar VPS (Ubuntu 20.04+)**

```bash
# Conectar na VPS
ssh root@138.68.13.174

# Atualizar sistema
apt update && apt upgrade -y

# Instalar dependências
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx

# Instalar Node.js (para frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
```

---

##### **2. Clonar Repositório**

```bash
# Ir para diretório root
cd /root

# Clonar repositório
git clone https://github.com/Pedroax/whatsapp-multiagent.git alice-lc

# Entrar no diretório
cd alice-lc
```

---

##### **3. Configurar Backend**

```bash
# Criar virtual environment
python3 -m venv venv

# Ativar venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo .env
nano .env
```

**Conteúdo do `.env`:**
```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Supabase
SUPABASE_URL=https://xnehwhilbdhjcnzrssvt.supabase.co
SUPABASE_KEY=eyJhbGc...

# Evolution API
EVOLUTION_API_URL=https://evolutionv2.dev.automatexia.com.br
EVOLUTION_API_KEY=434E2E3F8BEE-4722-B8F4-EA61880FFE53
EVOLUTION_INSTANCE=lc

# API Externa LC Baterias
API_BASE_URL=https://lcbaterias.automatexia.com.br/api-rest/v1
API_SECRET_KEY=sua_chave_secreta_aqui

# Outras configurações
DEBUG=False
```

**Salvar:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

##### **4. Configurar Systemd Service**

```bash
# Criar arquivo de serviço
nano /etc/systemd/system/alice-backend.service
```

**Conteúdo:**
```ini
[Unit]
Description=Alice LC Backend WhatsApp
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/alice-lc
Environment="PATH=/root/alice-lc/venv/bin"
ExecStart=/root/alice-lc/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Salvar:** `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
# Recarregar systemd
systemctl daemon-reload

# Habilitar serviço (inicia no boot)
systemctl enable alice-backend

# Iniciar serviço
systemctl start alice-backend

# Verificar status
systemctl status alice-backend

# Ver logs
journalctl -u alice-backend -f
```

---

##### **5. Configurar Frontend**

```bash
# Entrar no diretório do frontend
cd /root/alice-lc/frontend-multiagente

# Instalar dependências
npm install

# Criar arquivo .env para build
nano .env.production
```

**Conteúdo do `.env.production`:**
```bash
VITE_API_URL=https://lcbaterias.automatexia.com.br
```

**Salvar:** `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
# Build do frontend
npm run build

# Copiar build para pasta do Nginx
rm -rf /var/www/html/*
cp -r dist/* /var/www/html/
```

---

##### **6. Configurar Nginx**

```bash
# Editar configuração do Nginx
nano /etc/nginx/sites-available/default
```

**Conteúdo completo:**
```nginx
server {
    listen 80;
    server_name lcbaterias.automatexia.com.br;

    # Frontend (React)
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API (FastAPI)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Webhook (FastAPI)
    location /webhook/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout maior para webhook
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

**Salvar:** `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
# Testar configuração
nginx -t

# Recarregar Nginx
systemctl reload nginx
```

---

##### **7. Configurar SSL (HTTPS)**

```bash
# Obter certificado SSL via Let's Encrypt
certbot --nginx -d lcbaterias.automatexia.com.br

# Responder as perguntas:
# - Email: seu@email.com
# - Termos: Yes
# - Redirect HTTP para HTTPS: Yes (opção 2)

# Certificado renova automaticamente, mas pode testar:
certbot renew --dry-run
```

---

##### **8. Configurar DNS**

**No provedor de domínio (ex: Cloudflare, GoDaddy):**

```
Tipo: A
Nome: lcbaterias (ou @)
Valor: 138.68.13.174
TTL: Automático
```

**Aguarde propagação DNS (5-30 minutos)**

---

##### **9. Configurar Webhook no Evolution API**

```bash
# Via API do Evolution
curl -X POST https://evolutionv2.dev.automatexia.com.br/webhook/set/lc \
  -H "apikey: 434E2E3F8BEE-4722-B8F4-EA61880FFE53" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "url": "https://lcbaterias.automatexia.com.br/webhook/whatsapp",
    "events": [
      "messages.upsert"
    ]
  }'
```

**Ou via interface web do Evolution:**
- Acessar: https://evolutionv2.dev.automatexia.com.br
- Login com API Key
- Instância: `lc`
- Webhook URL: `https://lcbaterias.automatexia.com.br/webhook/whatsapp`
- Events: `messages.upsert`

---

##### **10. Verificar se Tudo Funciona**

```bash
# 1. Backend rodando?
systemctl status alice-backend

# 2. Logs sem erro?
journalctl -u alice-backend -n 50

# 3. Nginx rodando?
systemctl status nginx

# 4. Porta 8000 aberta?
netstat -tlnp | grep 8000

# 5. Teste no navegador
curl http://localhost:8000/api/conversas
# Deve retornar JSON com conversas

# 6. Teste frontend
# Acessar: https://lcbaterias.automatexia.com.br
# Deve carregar interface React

# 7. Teste webhook (enviar mensagem no WhatsApp)
# Ver logs: journalctl -u alice-backend -f
# Deve aparecer: "📥 Webhook recebido"
```

---

##### **11. Firewall (Opcional mas Recomendado)**

```bash
# Instalar UFW
apt install -y ufw

# Permitir SSH (IMPORTANTE! Senão perde acesso)
ufw allow 22/tcp

# Permitir HTTP e HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Habilitar firewall
ufw enable

# Ver status
ufw status
```

---

##### **12. Manutenção e Comandos Úteis**

```bash
# ====== BACKEND ======

# Ver logs em tempo real
journalctl -u alice-backend -f

# Ver últimas 100 linhas
journalctl -u alice-backend -n 100

# Restart backend
systemctl restart alice-backend

# Stop backend
systemctl stop alice-backend

# Ver status
systemctl status alice-backend


# ====== FRONTEND ======

# Rebuild frontend
cd /root/alice-lc/frontend-multiagente
npm run build
rm -rf /var/www/html/*
cp -r dist/* /var/www/html/


# ====== NGINX ======

# Testar config
nginx -t

# Reload (sem parar)
systemctl reload nginx

# Restart
systemctl restart nginx

# Ver logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log


# ====== GIT ======

# Atualizar código
cd /root/alice-lc
git pull
systemctl restart alice-backend

# Ver commits recentes
git log --oneline -10

# Ver mudanças
git status
git diff


# ====== SISTEMA ======

# Uso de memória
free -h

# Uso de disco
df -h

# Processos Python rodando
ps aux | grep python

# Processos usando porta 8000
lsof -i :8000


# ====== BANCO DE DADOS ======

# Ver conversas ativas
# (Conectar via Supabase Dashboard ou psql)

# Via API
curl http://localhost:8000/api/conversas | jq
```

---

##### **13. Troubleshooting VPS**

**Backend não inicia:**
```bash
# Ver erro detalhado
journalctl -u alice-backend -n 100

# Testar manualmente
cd /root/alice-lc
source venv/bin/activate
python main.py
# Ver erro que aparece
```

**Porta 8000 já em uso:**
```bash
# Ver o que está usando
lsof -i :8000

# Matar processo
kill -9 PID_AQUI

# Restart serviço
systemctl restart alice-backend
```

**Frontend não carrega:**
```bash
# Ver logs do Nginx
tail -f /var/log/nginx/error.log

# Verificar arquivos
ls -la /var/www/html/
# Deve ter index.html, assets/, etc
```

**SSL não funciona:**
```bash
# Renovar certificado
certbot renew

# Reconfigurar
certbot --nginx -d lcbaterias.automatexia.com.br
```

**Webhook não recebe mensagens:**
```bash
# Ver logs
journalctl -u alice-backend -f

# Enviar mensagem no WhatsApp
# Se não aparecer "📥 Webhook recebido", problema no Evolution

# Reconfigurar webhook
curl -X POST https://evolutionv2.dev.automatexia.com.br/webhook/set/lc \
  -H "apikey: 434E2E3F8BEE-4722-B8F4-EA61880FFE53" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "url": "https://lcbaterias.automatexia.com.br/webhook/whatsapp"
  }'
```

### **Estrutura no Servidor**

```
/root/alice-lc/                    # Código do backend
├── venv/                          # Python virtual environment
├── main.py
├── alice/
└── ...

/etc/systemd/system/alice-backend.service   # Service do systemd

/var/www/html/                     # Frontend buildado (Nginx)
└── index.html
```

### **URLs**

- **Backend:** https://lcbaterias.automatexia.com.br
- **Frontend:** https://lcbaterias.automatexia.com.br (mesmo domínio, Nginx faz proxy)
- **Evolution API:** https://evolutionv2.dev.automatexia.com.br
- **Supabase:** https://xnehwhilbdhjcnzrssvt.supabase.co

---

## 🐛 TROUBLESHOOTING

### **Problema 1: Mensagens não aparecem no frontend**

**Causa:** Schema errado (`role`/`content` ao invés de `remetente`/`conteudo`)

**Fix:**
```python
# Verificar main.py linha 435-450
supabase.table("mensagens").insert({
    "conversa_id": conversa_id,
    "remetente": remetente,  # ✅ Correto
    "conteudo": conteudo,    # ✅ Correto
    "tipo_midia": tipo_midia
}).execute()
```

**Commit de referência:** `604bd53`

---

### **Problema 2: Nomes aparecem como "Cliente" ao invés do nome real**

**Causa:** `pushName` não está sendo capturado e passado

**Fix:**
```python
# main.py linha 166-169
push_name = data.get("pushName", "Cliente")

# linha 295-300
await debouncer.add_message(
    phone=phone,
    message=message_text,
    callback=lambda p, m: process_message(p, m, push_name)  # ← Adicionar!
)

# linha 347
async def process_message(phone: str, combined_message: str, push_name: str = "Cliente"):
```

---

### **Problema 3: Erro ao enviar mensagem do frontend**

**Causa:** Função `formatar_mensagem_com_departamento` não existe

**Fix:**
```python
# main.py linha 543-569
def formatar_mensagem_com_departamento(message: str, departamento: str) -> str:
    nomes_departamentos = {
        "vendas": "Vendas",
        "financeiro": "Financeiro",
        "assistencia-tecnica": "Assistência Técnica",
        "suporte-ti": "Suporte TI",
        "geral": "Humano"
    }
    nome_dept = nomes_departamentos.get(departamento, "Humano")
    mensagem_formatada = f"*{nome_dept}:*\n{message}"
    return mensagem_formatada
```

**Commit de referência:** `604bd53`

---

### **Problema 4: Botão "Transferir" não funciona**

**Causa:** Endpoint `/api/transferir-conversa` foi deletado

**Fix:**
```python
# main.py linha 637-689
@app.post("/api/transferir-conversa")
async def transferir_conversa(request: Request):
    # ... (ver seção "Rotas da API" acima)
```

**Commit de referência:** `604bd53`

---

### **Problema 5: IA demora 5+ minutos para responder**

**Causa:** Sem timeout no ChatOpenAI

**Fix:**
```python
# alice/agent.py linha 27-34
self.llm = ChatOpenAI(
    model="gpt-4o",
    api_key=settings.openai_api_key,
    temperature=0.1,
    max_tokens=4096,
    timeout=120.0,      # ← Adicionar!
    max_retries=2       # ← Adicionar!
)
```

**Commit de referência:** `39839c9`

---

### **Problema 6: IA não envia pedido após "sim"**

**Causa:** Prompt não explícito sobre chamar `enviar_pedido` imediatamente

**Fix:**
```python
# alice/prompt.py linha 556-580
# Adicionar seção 12.5 ENVIO DO PEDIDO - AÇÃO OBRIGATÓRIA
# com instruções MUITO explícitas sobre chamar enviar_pedido
```

**Commit de referência:** `39839c9`

---

### **Problema 7: IA não pergunta prazo da sucata**

**Causa:** Prompt não suficientemente explícito

**Fix:**
```python
# alice/prompt.py linha 449-484
# Seção 11.5 com regras OBRIGATÓRIAS e exemplos visuais
```

**Commit de referência:** `39839c9` (ajustes anteriores também)

---

## 📝 CHECKLIST ANTES DE FAZER MUDANÇAS

**Antes de modificar qualquer código:**

- [ ] Li este documento completo
- [ ] Verifiquei git stash: `git stash list`
- [ ] Verifiquei commits recentes: `git log --oneline -20`
- [ ] Testei a funcionalidade que vou mexer (ela funciona?)
- [ ] Criei backup: `git stash push -m "backup antes de mudança"`
- [ ] Documentei o que vou mudar e por quê

**Depois de fazer mudanças:**

- [ ] Testei localmente (se possível)
- [ ] Commit com mensagem descritiva
- [ ] Push para GitHub
- [ ] Deploy no servidor
- [ ] Testei em produção
- [ ] Monitorizei logs por 5 minutos: `journalctl -u alice-backend -f`

---

## 🎯 RESUMO EXECUTIVO

### **Arquivos que NÃO PODE PERDER:**

1. **`main.py`**
   - Função `formatar_mensagem_com_departamento()` (linha 543-569)
   - Endpoint `/api/transferir-conversa` (linha 637-689)
   - Captura de `pushName` (linha 166-169)
   - Schema correto: `remetente`/`conteudo` (linha 435-450)

2. **`alice/agent.py`**
   - Timeout do LLM: `timeout=120.0, max_retries=2` (linha 32-33)

3. **`alice/prompt.py`**
   - Seção 11.5: Prazo da sucata obrigatório (linha 449-484)
   - Seção 12: Fluxo completo em 5 passos (linha 488-493)
   - Seção 12.5: ENVIO DO PEDIDO explícito (linha 556-580)

4. **`alice/tools.py`**
   - Todas as tools com timeout adequado
   - `consultar_baterias` salva `valor_unitario` no state

### **Se algo parar de funcionar:**

1. **Compare com commits que funcionavam:**
   ```bash
   git diff 604bd53 main.py
   git diff 39839c9 alice/prompt.py
   ```

2. **Restaure arquivo que funcionava:**
   ```bash
   git checkout 604bd53 -- main.py
   ```

3. **Veja logs em produção:**
   ```bash
   ssh root@138.68.13.174 "journalctl -u alice-backend -f"
   ```

---

**Última atualização:** 2025-11-01 16:40 UTC
**Versão do sistema:** `39839c9`
**Status:** ✅ Funcionando (timeout fix + envio de pedido fix aplicados)

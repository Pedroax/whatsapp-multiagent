# Setup do Sistema Multi-Agente - LC Baterias

## 📋 Visão Geral

Sistema multi-tenant inspirado no Chatwoot para gerenciamento de conversas com IA (Alice) e múltiplos departamentos. Permite que diferentes departamentos recebam e gerenciem conversas transferidas pela IA, com controle inteligente de horários e modos de operação.

## 🏗️ Arquitetura

### Frontend
- **Framework**: React + TypeScript + Vite
- **UI**: TailwindCSS + shadcn/ui
- **Layout**: 3 colunas estilo Chatwoot
  - Coluna 1: Lista de conversas (30%)
  - Coluna 2: Área de mensagens (45%)
  - Coluna 3: Informações do contato (25%)
- **Auth**: Supabase Auth com RLS
- **Realtime**: Supabase Realtime para atualizações

### Backend
- **API**: FastAPI (já existente em alice-lc)
- **Agente**: LangGraph com Alice (já implementado)
- **Database**: Supabase (PostgreSQL + RLS)
- **Cache**: Redis para sessões e agendamentos

### Banco de Dados
- **13 Tabelas** com arquitetura multi-tenant
- **RLS Policies** para isolamento por empresa e departamento
- **Seed Data** para LC Baterias (4 departamentos)

## 📁 Estrutura de Pastas

```
alice-lc/
├── database/
│   ├── schema.sql          # Estrutura completa das tabelas
│   ├── rls-policies.sql    # Políticas de segurança RLS
│   ├── seed.sql            # Dados iniciais LC Baterias
│   └── README.md           # Documentação do banco
├── frontend-multiagente/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/         # Componentes shadcn/ui
│   │   │   ├── ConversationList.tsx
│   │   │   ├── MessageArea.tsx
│   │   │   └── ContactInfo.tsx
│   │   ├── lib/
│   │   │   ├── utils.ts
│   │   │   └── supabase.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── index.css
│   ├── .env.example
│   └── package.json
├── main.py                 # FastAPI existente
├── agent/                  # LangGraph Alice existente
├── utils/                  # Utilities existentes
└── .env                    # Configurações

```

## 🚀 Instalação

### 1. Configurar Banco de Dados Supabase

1. Crie um projeto no [Supabase](https://supabase.com)

2. Execute os scripts SQL na ordem:
```bash
# No SQL Editor do Supabase:
# 1. Execute database/schema.sql
# 2. Execute database/rls-policies.sql
# 3. Execute database/seed.sql
```

3. Copie as credenciais:
   - Project URL
   - Anon Key
   - Service Role Key

### 2. Configurar Frontend

```bash
cd alice-lc/frontend-multiagente

# Instalar dependências
npm install

# Criar arquivo .env
cp .env.example .env

# Editar .env com suas credenciais Supabase
```

**Conteúdo do `.env`:**
```env
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_ANON_KEY=sua-anon-key-aqui
```

### 3. Executar Frontend

```bash
cd alice-lc/frontend-multiagente
npm run dev
```

Acesse: http://localhost:5173

## 🎨 Funcionalidades Implementadas

### ✅ Layout Chatwoot (3 Colunas)
- [x] Lista de conversas com busca e filtros
- [x] Área de mensagens com chat completo
- [x] Painel lateral com informações do contato
- [x] Badges de status (IA ativa, pausada, desligada)
- [x] Indicador de mensagens não lidas
- [x] Header com nome do departamento em negrito

### ✅ Componentes UI (shadcn/ui)
- [x] Button
- [x] Input
- [x] Badge
- [x] Avatar
- [x] ScrollArea

### ✅ Banco de Dados
- [x] 13 Tabelas multi-tenant
- [x] RLS Policies completas
- [x] Seed data para LC Baterias
- [x] 4 Departamentos: Vendas, Assistência Técnica, Financeiro, Suporte TI

### ✅ Mock Data
- [x] 2 conversas de exemplo
- [x] Mensagens simuladas
- [x] Dados dos departamentos

## 🔄 Funcionalidades Pendentes

### Backend Integration
- [ ] Conectar frontend com Supabase Realtime
- [ ] Implementar autenticação (login departamentos)
- [ ] Adaptar FastAPI para multi-tenant
- [ ] Criar serviço de roteamento inteligente
- [ ] Implementar detecção de intenção (palavras-chave)
- [ ] Sistema de notificações

### Sistema de Agendamento
- [ ] Redis para cache de horários
- [ ] Cronjob para ligar/desligar IA automaticamente
- [ ] Interface para configurar horários

### Recursos Avançados
- [ ] Upload e envio de mídia
- [ ] Templates de mensagens
- [ ] Dashboard com métricas
- [ ] Histórico de transferências
- [ ] Audit trail (eventos)

## 🔐 Segurança Multi-Tenant

### Row Level Security (RLS)

Todas as tabelas possuem RLS habilitado com políticas que garantem:

1. **Isolamento por Empresa**: Usuários só veem dados da própria empresa
2. **Isolamento por Departamento**: Agentes só veem conversas do próprio departamento
3. **Service Role Bypass**: Backend pode acessar tudo para operações do sistema

### Funções Helper

```sql
auth.empresa_id()           -- Retorna empresa_id do usuário logado
auth.departamento_id()      -- Retorna departamento_id do usuário logado
auth.pode_ver_todos()       -- Verifica se usuário pode ver todos departamentos
```

## 📊 Departamentos LC Baterias

| Departamento | Cor | Descrição |
|-------------|-----|-----------|
| **Vendas** | 🔵 Azul (#3B82F6) | Consultas sobre produtos e vendas |
| **Assistência Técnica** | 🟠 Laranja (#F59E0B) | Problemas técnicos e instalação |
| **Financeiro** | 🟢 Verde (#10B981) | Pagamentos e boletos |
| **Suporte TI** | 🟣 Roxo (#8B5CF6) | Problemas com sistema |

## 🤖 Modos de Operação da IA

### 1. LIGADO (Ativo)
- IA responde automaticamente
- Pode transferir para departamentos
- Badge verde: "IA Ativa"

### 2. ATENÇÃO (Pausado)
- IA monitora mas não responde
- Aguarda intervenção humana
- Badge amarelo: "Modo Humano"

### 3. DESLIGADO
- IA completamente desligada
- Apenas atendentes humanos
- Badge cinza: "IA Desligada"

## 🕐 Agendamento Automático

Configurável na tabela `agendamentos_ia`:

```sql
-- Exemplo: Liga às 8h, desliga às 18h (seg-sex)
hora_ligar: '08:00:00'
hora_desligar: '18:00:00'
dias_semana: [1,2,3,4,5]  -- 1=Segunda, 5=Sexta
modo_dentro_horario: 'atencao'
modo_fora_horario: 'desligado'
```

## 🔄 Fluxo de Transferência

1. Lead envia: "quero falar no financeiro"
2. Alice detecta palavra-chave "financeiro"
3. Cria registro em `transferencias`
4. Notifica departamento financeiro
5. Atualiza conversa: `departamento_id` e `modo_ia='pausado'`
6. Agente do financeiro vê conversa no seu painel
7. Quando agente responde, IA permanece pausada

## 📝 Queries Úteis

### Ver conversas de um departamento
```sql
SELECT c.*, l.nome, l.telefone
FROM conversas c
JOIN leads l ON c.lead_id = l.id
WHERE c.departamento_id = 'id-do-departamento'
ORDER BY c.updated_at DESC;
```

### Ver mensagens de uma conversa
```sql
SELECT *
FROM mensagens
WHERE conversa_id = 'id-da-conversa'
ORDER BY created_at ASC;
```

### Estatísticas por departamento
```sql
SELECT
  d.nome,
  COUNT(c.id) as total_conversas,
  COUNT(CASE WHEN c.status = 'aberta' THEN 1 END) as abertas,
  COUNT(CASE WHEN c.status = 'resolvida' THEN 1 END) as resolvidas
FROM departamentos d
LEFT JOIN conversas c ON c.departamento_id = d.id
WHERE d.empresa_id = 'id-da-empresa'
GROUP BY d.id, d.nome;
```

## 🔌 Integrando com Alice Existente

O sistema deve se integrar com o FastAPI e LangGraph existentes:

1. **Webhook WhatsApp** → FastAPI → Cria mensagem em `mensagens`
2. **Alice processa** → Detecta intenção → Transfere se necessário
3. **Supabase Realtime** → Atualiza frontend automaticamente
4. **Agente responde** → FastAPI cria mensagem → Evolution API envia

## 📱 Screenshots do Layout

### Layout 3 Colunas
```
┌─────────────┬──────────────────┬─────────────┐
│             │                  │             │
│  Conversas  │    Mensagens     │ Info Lead   │
│             │                  │             │
│  30%        │      45%         │    25%      │
└─────────────┴──────────────────┴─────────────┘
```

### Header Departamento
```
🔵 Vendas
• Atendido por João Silva
```

## 🎯 Próximos Passos

1. ✅ Estrutura básica frontend completa
2. ✅ Layout Chatwoot implementado
3. ✅ Banco de dados configurado
4. 🔄 Integrar autenticação Supabase
5. 🔄 Conectar Realtime
6. 🔄 Adaptar backend multi-tenant
7. 🔄 Implementar detecção de intenção
8. 🔄 Sistema de agendamento com Redis

## 📚 Documentação Adicional

- [database/README.md](database/README.md) - Documentação completa do banco
- [Supabase Docs](https://supabase.com/docs)
- [shadcn/ui Docs](https://ui.shadcn.com)
- [Chatwoot Docs](https://www.chatwoot.com/docs)

## 🆘 Suporte

Para dúvidas ou problemas, consulte:
- Documentação do banco em `database/README.md`
- Logs do Supabase Dashboard
- Console do navegador (F12)

---

**Status**: ✅ Frontend funcional com mock data | 🔄 Integração backend pendente
**Última atualização**: 2025-10-17

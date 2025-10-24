# 🗄️ Banco de Dados - Alice Multiagente

## 📋 Visão Geral

Sistema de banco de dados **multi-tenant** (múltiplas empresas) com **Row Level Security (RLS)** completo.

### Características Principais:

✅ **Multi-Tenancy**: Múltiplas empresas isoladas no mesmo banco
✅ **RLS Completo**: Segurança no nível de linha
✅ **Auditoria**: Log de todas as ações
✅ **Métricas**: Cache de métricas para performance
✅ **Flexível**: JSONB para dados customizáveis

---

## 🚀 Como Configurar

### 1. Criar projeto no Supabase

1. Acesse https://supabase.com
2. Crie um novo projeto
3. Anote as credenciais:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY`

### 2. Executar Scripts SQL

**Na ordem:**

```sql
-- 1. Schema (tabelas, índices)
\i schema.sql

-- 2. RLS Policies (segurança)
\i rls-policies.sql

-- 3. Seed (dados iniciais)
\i seed.sql
```

**Ou via Dashboard do Supabase:**

1. SQL Editor → New Query
2. Cole o conteúdo de `schema.sql`
3. Run
4. Repita para `rls-policies.sql`
5. Repita para `seed.sql`

### 3. Habilitar Realtime

```sql
-- Habilitar realtime para as tabelas necessárias
ALTER PUBLICATION supabase_realtime ADD TABLE conversas;
ALTER PUBLICATION supabase_realtime ADD TABLE mensagens;
ALTER PUBLICATION supabase_realtime ADD TABLE usuarios;
ALTER PUBLICATION supabase_realtime ADD TABLE notificacoes;
```

---

## 📊 Estrutura das Tabelas

### 🏢 EMPRESAS (Tenants)
Cada cliente seu é uma empresa

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Identificador único |
| nome | TEXT | Nome da empresa |
| slug | TEXT | URL slug (único) |
| cnpj | TEXT | CNPJ |
| cor_primaria | TEXT | Cor da marca |
| plano | TEXT | Plano contratado |
| limite_usuarios | INT | Máx. de usuários |
| ativo | BOOL | Ativo/Inativo |

### 🏪 DEPARTAMENTOS
Setores da empresa (Vendas, Financeiro, etc)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Identificador |
| empresa_id | UUID | FK empresas |
| nome | TEXT | Nome do depto |
| slug | TEXT | URL slug |
| cor_primaria | TEXT | Cor do depto |
| icone | TEXT | Ícone (lucide) |
| ordem | INT | Ordem exibição |

### 👤 USUARIOS (Agentes Humanos)
Pessoas que atendem

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | FK auth.users |
| empresa_id | UUID | FK empresas |
| departamento_id | UUID | FK departamentos |
| nome_completo | TEXT | Nome |
| email | TEXT | Email |
| role | TEXT | admin/supervisor/agente |
| status | TEXT | online/ausente/ocupado/offline |
| pode_ver_todos_departamentos | BOOL | Permissão especial |

### 👥 LEADS (Clientes Finais)
Pessoas que conversam

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Identificador |
| empresa_id | UUID | FK empresas |
| telefone | TEXT | Telefone (único por empresa) |
| nome | TEXT | Nome |
| email | TEXT | Email |
| tags | TEXT[] | Tags |
| segmento | TEXT | VIP/Padrão/etc |

### 💬 CONVERSAS
Thread de mensagens

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Identificador |
| empresa_id | UUID | FK empresas |
| lead_id | UUID | FK leads |
| departamento_id | UUID | FK departamentos |
| usuario_atribuido_id | UUID | FK usuarios |
| status | TEXT | nova/em_atendimento/resolvida |
| modo_ia | TEXT | ativo/pausado/desligado |
| prioridade | TEXT | baixa/normal/alta/urgente |
| primeira_resposta_em | TIMESTAMPTZ | Quando foi respondida |
| tempo_primeira_resposta | INTERVAL | SLA |
| mensagens_total | INT | Total de mensagens |

### 💭 MENSAGENS
Mensagens individuais

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Identificador |
| conversa_id | UUID | FK conversas |
| tipo | TEXT | lead/ia/humano/sistema |
| usuario_id | UUID | FK usuarios (NULL se IA/lead) |
| conteudo | TEXT | Texto da mensagem |
| tipo_midia | TEXT | texto/audio/imagem/documento |
| status_ia | TEXT | sugerida/aprovada/editada/recusada |
| aprovada_por | UUID | Quem aprovou (se IA) |

### 🔄 TRANSFERÊNCIAS
Histórico de transferências entre departamentos

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Identificador |
| conversa_id | UUID | FK conversas |
| departamento_origem_id | UUID | De onde veio |
| departamento_destino_id | UUID | Para onde foi |
| tipo | TEXT | automatica_ia/manual_agente |
| motivo | TEXT | Razão |
| transferido_por | UUID | Quem fez |

### ⏰ AGENDAMENTOS_IA
Configuração de horários automáticos

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Identificador |
| empresa_id | UUID | FK empresas |
| nome | TEXT | Nome do agendamento |
| hora_ligar | TIME | Ex: 08:00 |
| hora_desligar | TIME | Ex: 18:00 |
| dias_semana | INT[] | [1,2,3,4,5] = seg-sex |
| modo_dentro_horario | TEXT | ligado/atencao/desligado |
| modo_fora_horario | TEXT | ligado/atencao/desligado |

### ⚙️ CONFIG_IA
Configuração da IA por empresa

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| empresa_id | UUID | FK empresas (UNIQUE) |
| modo_geral | TEXT | ligado/atencao/desligado |
| modelo_ia | TEXT | gpt-4o/claude-3/etc |
| temperatura | DECIMAL | 0.0 - 1.0 |
| prompt_sistema | TEXT | Prompt base |
| prompt_vendas | TEXT | Prompt específico |
| palavras_chave_vendas | TEXT[] | Para detecção |

### 📊 METRICAS_DIARIAS
Cache de métricas agregadas

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| empresa_id | UUID | FK empresas |
| departamento_id | UUID | FK departamentos |
| usuario_id | UUID | FK usuarios |
| data | DATE | Dia |
| conversas_novas | INT | Qtd. novas |
| conversas_resolvidas | INT | Qtd. resolvidas |
| tempo_medio_primeira_resposta | INTERVAL | SLA médio |

### 📝 TEMPLATES_MENSAGENS
Respostas prontas

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| empresa_id | UUID | FK empresas |
| departamento_id | UUID | FK departamentos (NULL=todos) |
| nome | TEXT | Nome do template |
| atalho | TEXT | Ex: /boasvindas |
| conteudo | TEXT | Texto com {variaveis} |
| categoria | TEXT | saudacao/despedida/faq |

### 🔔 NOTIFICAÇÕES
Notificações para usuários

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| usuario_id | UUID | FK usuarios |
| tipo | TEXT | nova_mensagem/transferencia |
| titulo | TEXT | Título |
| mensagem | TEXT | Conteúdo |
| lida | BOOL | Lida? |
| link | TEXT | URL |

### 📜 EVENTOS
Log de auditoria

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| empresa_id | UUID | FK empresas |
| tipo | TEXT | ia_pausada/transferencia |
| categoria | TEXT | sistema/usuario/ia |
| usuario_id | UUID | Quem fez |
| dados | JSONB | Dados extras |

---

## 🔒 Segurança (RLS)

### Princípios:

1. **Isolamento de Tenant**: Usuários NUNCA veem dados de outras empresas
2. **Isolamento de Departamento**: Agentes veem apenas seu departamento (exceto se `pode_ver_todos_departamentos = true`)
3. **Roles**: Admins > Supervisores > Agentes
4. **Service Role**: Backend usa `service_role` que bypassa RLS

### Funções Auxiliares:

```sql
auth.empresa_id()              -- Retorna empresa_id do usuário logado
auth.departamento_id()         -- Retorna departamento_id do usuário
auth.user_role()               -- Retorna role (admin/supervisor/agente)
auth.pode_ver_todos_departamentos() -- Retorna permissão
```

### Exemplos de Policies:

**Conversas:**
```sql
-- Usuário vê conversas do próprio departamento
CREATE POLICY "..." ON conversas FOR SELECT
USING (
  empresa_id = auth.empresa_id() AND
  (
    departamento_id = auth.departamento_id() OR
    auth.pode_ver_todos_departamentos()
  )
);
```

**Mensagens:**
```sql
-- Seguem as conversas
CREATE POLICY "..." ON mensagens FOR SELECT
USING (
  conversa_id IN (
    SELECT id FROM conversas WHERE departamento_id = auth.departamento_id()
  )
);
```

---

## 🎯 Casos de Uso

### Criar Nova Empresa

```sql
INSERT INTO empresas (nome, slug, cnpj, plano)
VALUES ('Minha Empresa', 'minhaempresa', '12.345.678/0001-90', 'basico');
```

### Criar Departamento

```sql
INSERT INTO departamentos (empresa_id, nome, slug, cor_primaria, icone)
VALUES (
  'empresa-uuid',
  'Vendas',
  'vendas',
  '#3B82F6',
  'shopping-cart'
);
```

### Criar Usuário (após signup no Supabase Auth)

```sql
INSERT INTO usuarios (id, empresa_id, departamento_id, nome_completo, email, role)
VALUES (
  auth.uid(),
  'empresa-uuid',
  'depto-uuid',
  'João Silva',
  'joao@empresa.com',
  'agente'
);
```

### Criar Conversa

```sql
INSERT INTO conversas (empresa_id, lead_id, departamento_id, status)
VALUES ('empresa-uuid', 'lead-uuid', 'depto-uuid', 'nova');
```

### Transferir Conversa

```sql
-- 1. Atualizar conversa
UPDATE conversas
SET departamento_id = 'novo-depto-uuid',
    usuario_atribuido_id = NULL
WHERE id = 'conversa-uuid';

-- 2. Registrar transferência
INSERT INTO transferencias (
  empresa_id, conversa_id,
  departamento_origem_id, departamento_destino_id,
  tipo, motivo, transferido_por
) VALUES (
  'empresa-uuid', 'conversa-uuid',
  'depto-origem-uuid', 'depto-destino-uuid',
  'manual_agente', 'solicitacao_lead', auth.uid()
);
```

### Criar Agendamento

```sql
INSERT INTO agendamentos_ia (
  empresa_id, nome,
  hora_ligar, hora_desligar, dias_semana,
  modo_dentro_horario, modo_fora_horario
) VALUES (
  'empresa-uuid', 'Horário Comercial',
  '08:00', '18:00', ARRAY[1,2,3,4,5],
  'atencao', 'desligado'
);
```

---

## 📈 Queries Úteis

### Conversas Ativas por Departamento

```sql
SELECT
  d.nome AS departamento,
  COUNT(c.id) AS conversas_ativas
FROM conversas c
JOIN departamentos d ON c.departamento_id = d.id
WHERE c.empresa_id = 'empresa-uuid'
  AND c.status IN ('nova', 'em_atendimento')
GROUP BY d.nome;
```

### Tempo Médio de Resposta

```sql
SELECT
  AVG(tempo_primeira_resposta) AS tempo_medio
FROM conversas
WHERE empresa_id = 'empresa-uuid'
  AND primeira_resposta_em IS NOT NULL
  AND created_at >= CURRENT_DATE - INTERVAL '7 days';
```

### Ranking de Agentes

```sql
SELECT
  u.nome_completo,
  COUNT(c.id) AS conversas_atendidas,
  AVG(c.tempo_resolucao) AS tempo_medio_resolucao
FROM conversas c
JOIN usuarios u ON c.usuario_atribuido_id = u.id
WHERE c.empresa_id = 'empresa-uuid'
  AND c.status = 'resolvida'
  AND c.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY u.id, u.nome_completo
ORDER BY conversas_atendidas DESC;
```

### Mensagens Pendentes de Aprovação (IA)

```sql
SELECT
  m.id,
  c.id AS conversa_id,
  l.nome AS lead_nome,
  m.conteudo,
  m.created_at
FROM mensagens m
JOIN conversas c ON m.conversa_id = c.id
JOIN leads l ON c.lead_id = l.id
WHERE m.empresa_id = 'empresa-uuid'
  AND m.tipo = 'ia'
  AND m.status_ia = 'sugerida'
ORDER BY m.created_at DESC;
```

---

## 🔧 Manutenção

### Limpeza de Conversas Antigas

```sql
-- Arquivar conversas resolvidas há mais de 90 dias
UPDATE conversas
SET status = 'arquivada'
WHERE status = 'resolvida'
  AND resolvida_em < CURRENT_DATE - INTERVAL '90 days';
```

### Recalcular Métricas

```sql
-- Função para recalcular métricas de um dia
CREATE OR REPLACE FUNCTION recalcular_metricas(p_empresa_id UUID, p_data DATE)
RETURNS VOID AS $$
BEGIN
  DELETE FROM metricas_diarias
  WHERE empresa_id = p_empresa_id AND data = p_data;

  INSERT INTO metricas_diarias (
    empresa_id, departamento_id, data,
    conversas_novas, conversas_resolvidas,
    mensagens_total, mensagens_ia, mensagens_humano
  )
  SELECT
    empresa_id,
    departamento_id,
    p_data,
    COUNT(*) FILTER (WHERE created_at::DATE = p_data),
    COUNT(*) FILTER (WHERE status = 'resolvida' AND resolvida_em::DATE = p_data),
    SUM(mensagens_total),
    SUM(mensagens_ia),
    SUM(mensagens_humano)
  FROM conversas
  WHERE empresa_id = p_empresa_id
    AND created_at::DATE <= p_data
  GROUP BY empresa_id, departamento_id;
END;
$$ LANGUAGE plpgsql;
```

---

## 🚨 Troubleshooting

### Usuário não consegue ver conversas

**Verifique:**
1. `empresa_id` do usuário está correto?
2. `departamento_id` está definido?
3. Conversa pertence ao departamento do usuário?
4. RLS está habilitado?

```sql
-- Debug
SELECT
  u.nome_completo,
  u.empresa_id,
  u.departamento_id,
  u.role,
  u.pode_ver_todos_departamentos
FROM usuarios u
WHERE u.id = auth.uid();
```

### Service Role não funciona

**Verifique se as policies "Service role bypass" existem:**

```sql
SELECT * FROM pg_policies
WHERE tablename = 'conversas'
  AND policyname LIKE '%service%';
```

### Realtime não atualiza

```sql
-- Verificar se tabela está publicada
SELECT * FROM pg_publication_tables
WHERE pubname = 'supabase_realtime';

-- Adicionar se necessário
ALTER PUBLICATION supabase_realtime ADD TABLE conversas;
```

---

## 📚 Recursos Adicionais

- [Documentação Supabase](https://supabase.com/docs)
- [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase Realtime](https://supabase.com/docs/guides/realtime)

---

**Criado por**: Alice Multiagente
**Versão**: 1.0.0
**Data**: 2025-01-17

# 📝 GUIA: Como Executar SQL no Supabase

## 🎯 Passo a Passo Visual

### **PASSO 1: Acessar Supabase**

1. Abra seu navegador
2. Acesse: **https://supabase.com**
3. Clique em **"Sign In"** (ou "Entrar")
4. Faça login com sua conta

---

### **PASSO 2: Selecionar seu Projeto**

1. Você verá uma lista de projetos
2. Clique no projeto que está usando (verifique o nome no seu `.env`)
   - O projeto tem um nome como: `iexwyilovmxllfgggbvp` (está no SUPABASE_URL)

---

### **PASSO 3: Abrir SQL Editor**

1. No **menu lateral esquerdo**, procure o ícone **</> SQL Editor**
2. Clique nele
3. Você verá uma tela com editor de código SQL

---

### **PASSO 4: Criar Nova Query**

1. Clique no botão **"+ New query"** (canto superior direito)
2. Ou use o atalho: **Ctrl + Enter** (Windows) / **Cmd + Enter** (Mac)

---

### **PASSO 5: Copiar o SQL**

**OPÇÃO A - Copiar manualmente:**

1. Abra o arquivo: `database/controle-ia.sql` no seu editor
2. Selecione TUDO (Ctrl+A)
3. Copie (Ctrl+C)

**OPÇÃO B - Eu crio um arquivo pronto para você copiar:**

Vou criar um arquivo SQL simplificado que você pode copiar direto:

```sql
-- =====================================================
-- SISTEMA DE CONTROLE DA IA - ALICE
-- =====================================================

-- 1. Tabela de mensagens pendentes
CREATE TABLE IF NOT EXISTS mensagens_pendentes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id TEXT NOT NULL,
  conversa_id TEXT NOT NULL,

  lead_id TEXT NOT NULL,
  lead_nome TEXT NOT NULL,
  lead_telefone TEXT NOT NULL,

  mensagem_recebida TEXT NOT NULL,
  mensagem_recebida_em TIMESTAMPTZ DEFAULT NOW(),

  resposta_ia TEXT NOT NULL,
  resposta_editada TEXT,

  confianca_ia DECIMAL,
  intencao_detectada TEXT,
  contexto_ia JSONB DEFAULT '{}',

  status TEXT DEFAULT 'pendente',

  processada_por TEXT,
  processada_em TIMESTAMPTZ,
  motivo_recusa TEXT,

  enviada BOOLEAN DEFAULT false,
  enviada_em TIMESTAMPTZ,

  expira_em TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 hour'),

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tabela de agendamentos
CREATE TABLE IF NOT EXISTS agendamentos_ia (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id TEXT NOT NULL,
  departamento_id TEXT,

  nome TEXT NOT NULL,
  descricao TEXT,

  hora_ligar TIME NOT NULL,
  hora_desligar TIME NOT NULL,
  dias_semana INTEGER[] DEFAULT '{1,2,3,4,5}',
  fuso_horario TEXT DEFAULT 'America/Sao_Paulo',

  modo_dentro_horario TEXT DEFAULT 'atencao',
  modo_fora_horario TEXT DEFAULT 'desligado',
  mensagem_auto_fora_horario TEXT DEFAULT 'Olá! Nosso horário de atendimento é de segunda a sexta, das 8h às 18h.',

  excecoes JSONB DEFAULT '[]',

  ativo BOOLEAN DEFAULT true,
  prioridade INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabela de configuração da IA
CREATE TABLE IF NOT EXISTS config_ia (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id TEXT UNIQUE NOT NULL,

  modo_geral TEXT DEFAULT 'atencao',
  agendamento_ativo BOOLEAN DEFAULT true,

  modelo_ia TEXT DEFAULT 'gpt-4o',
  temperatura DECIMAL DEFAULT 0.7,
  max_tokens INTEGER DEFAULT 4096,

  auto_aprovar_alta_confianca BOOLEAN DEFAULT false,
  limiar_confianca DECIMAL DEFAULT 0.95,

  updated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_by TEXT
);

-- 4. Inserir configuração inicial
INSERT INTO config_ia (empresa_id, modo_geral, agendamento_ativo)
VALUES ('emp1', 'atencao', true)
ON CONFLICT (empresa_id) DO NOTHING;

-- 5. Criar índices
CREATE INDEX IF NOT EXISTS idx_mensagens_pendentes_status ON mensagens_pendentes(status);
CREATE INDEX IF NOT EXISTS idx_mensagens_pendentes_created ON mensagens_pendentes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agendamentos_empresa ON agendamentos_ia(empresa_id);
CREATE INDEX IF NOT EXISTS idx_agendamentos_ativo ON agendamentos_ia(ativo);

-- 6. Habilitar Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE mensagens_pendentes;
ALTER PUBLICATION supabase_realtime ADD TABLE config_ia;
ALTER PUBLICATION supabase_realtime ADD TABLE agendamentos_ia;

-- ✅ PRONTO! Tabelas criadas com sucesso!
```

---

### **PASSO 6: Colar no SQL Editor**

1. No SQL Editor do Supabase
2. Cole o código SQL (Ctrl+V)
3. Você verá todo o código no editor

---

### **PASSO 7: Executar o SQL**

1. Clique no botão **"RUN"** (ou "Executar") no canto inferior direito
2. Ou use o atalho: **Ctrl + Enter**
3. Aguarde alguns segundos...

---

### **PASSO 8: Verificar Sucesso**

Se tudo der certo, você verá:

✅ **Mensagem de sucesso:** "Success. No rows returned"
✅ **Ou:** Lista de tabelas criadas

Se der erro:
- Leia a mensagem de erro
- Geralmente é porque a tabela já existe (tudo bem!)
- Ou falta alguma tabela referenciada (execute o schema.sql primeiro)

---

### **PASSO 9: Verificar Tabelas Criadas**

1. No menu lateral, clique em **"Table Editor"** (Editor de Tabelas)
2. Você deve ver as novas tabelas:
   - ✅ `mensagens_pendentes`
   - ✅ `agendamentos_ia`
   - ✅ `config_ia`

---

## 🎯 RESUMO RÁPIDO

```
1. Supabase.com → Login
2. Selecionar projeto
3. SQL Editor (menu lateral)
4. + New query
5. Copiar SQL (arquivo acima)
6. Colar no editor
7. Clicar RUN (ou Ctrl+Enter)
8. ✅ Sucesso!
```

---

## 🐛 Se der erro...

### **Erro: "relation already exists"**
✅ **Normal!** Significa que a tabela já existe. Pode ignorar.

### **Erro: "relation does not exist"**
❌ Falta executar o schema principal primeiro.

**Solução:**
1. Vá em: `database/schema.sql`
2. Execute esse arquivo ANTES
3. Depois execute o `controle-ia.sql`

### **Erro: "permission denied"**
❌ Você não está usando a service key correta.

**Solução:**
1. Verifique se está usando o **service_role key** (não a anon key)
2. Ou execute como Admin no Supabase

---

## ✅ Confirmação Final

Para ter certeza que funcionou:

```sql
-- Execute esta query para verificar:
SELECT * FROM config_ia;
```

Se retornar 1 linha com `empresa_id = 'emp1'`, **TUDO CERTO!** 🎉

---

**Agora você pode usar o sistema de controle da IA!** 🚀

-- =====================================================
-- EXECUÇÃO COMPLETA - SISTEMA DE DEPARTAMENTOS
-- Copie TUDO e cole no SQL Editor do Supabase
-- =====================================================

-- 1. Criar tabela de departamentos
CREATE TABLE IF NOT EXISTS departamentos (
  id TEXT PRIMARY KEY,
  empresa_id TEXT NOT NULL,
  nome TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  cor_primaria TEXT DEFAULT '#3B82F6',
  icone TEXT DEFAULT 'folder',
  ordem INTEGER DEFAULT 0,
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Criar tabela de conversas (se não existir)
CREATE TABLE IF NOT EXISTS conversas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id TEXT NOT NULL,
  phone TEXT UNIQUE NOT NULL,
  lead_id TEXT,

  -- Departamento
  departamento_slug TEXT REFERENCES departamentos(slug),
  departamento_nome TEXT,

  -- Status da conversa
  status TEXT DEFAULT 'aberta',
  modo_ia TEXT DEFAULT 'ligado',
  prioridade TEXT DEFAULT 'normal',

  -- Dados do lead
  nome_lead TEXT,
  email_lead TEXT,
  tags TEXT[],

  -- Mensagens
  ultima_mensagem TEXT,
  ultima_mensagem_em TIMESTAMPTZ,
  nao_lidas INTEGER DEFAULT 0,

  -- Transferência
  transferido_em TIMESTAMPTZ,
  transferido_por TEXT,
  motivo_transferencia TEXT,

  -- Notificações
  notificado BOOLEAN DEFAULT false,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Criar tabela de mensagens (se não existir)
CREATE TABLE IF NOT EXISTS mensagens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversa_id UUID REFERENCES conversas(id) ON DELETE CASCADE,
  phone TEXT NOT NULL,

  -- Tipo e conteúdo
  tipo TEXT NOT NULL,
  conteudo TEXT NOT NULL,

  -- Origem
  enviado_por_ia BOOLEAN DEFAULT false,
  enviado_por_user_id TEXT,

  -- Departamento (se foi enviada após transferência)
  departamento_origem TEXT,

  -- Status
  lida BOOLEAN DEFAULT false,
  entregue BOOLEAN DEFAULT false,

  -- Metadados
  metadata JSONB DEFAULT '{}',

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Inserir departamentos padrão
INSERT INTO departamentos (id, empresa_id, nome, slug, cor_primaria, icone, ordem, ativo)
VALUES
  ('dept-vendas', 'emp1', 'Vendas', 'vendas', '#3B82F6', 'shopping-cart', 1, true),
  ('dept-assistencia', 'emp1', 'Assistência Técnica', 'assistencia-tecnica', '#F59E0B', 'wrench', 2, true),
  ('dept-financeiro', 'emp1', 'Financeiro', 'financeiro', '#10B981', 'dollar-sign', 3, true),
  ('dept-suporte', 'emp1', 'Suporte TI', 'suporte-ti', '#8B5CF6', 'monitor', 4, true),
  ('dept-geral', 'emp1', 'Geral', 'geral', '#6B7280', 'users', 5, true)
ON CONFLICT (id) DO NOTHING;

-- 5. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_conversas_empresa ON conversas(empresa_id);
CREATE INDEX IF NOT EXISTS idx_conversas_departamento ON conversas(departamento_slug);
CREATE INDEX IF NOT EXISTS idx_conversas_status ON conversas(status);
CREATE INDEX IF NOT EXISTS idx_conversas_phone ON conversas(phone);
CREATE INDEX IF NOT EXISTS idx_conversas_notificado ON conversas(notificado) WHERE notificado = false;

CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_phone ON mensagens(phone);
CREATE INDEX IF NOT EXISTS idx_mensagens_created ON mensagens(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mensagens_departamento ON mensagens(departamento_origem);

-- 6. Criar função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- 7. Criar trigger para conversas
DROP TRIGGER IF EXISTS update_conversas_updated_at ON conversas;
CREATE TRIGGER update_conversas_updated_at
  BEFORE UPDATE ON conversas
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 8. Criar trigger para departamentos
DROP TRIGGER IF EXISTS update_departamentos_updated_at ON departamentos;
CREATE TRIGGER update_departamentos_updated_at
  BEFORE UPDATE ON departamentos
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 9. Habilitar Realtime para notificações em tempo real
ALTER PUBLICATION supabase_realtime ADD TABLE conversas;
ALTER PUBLICATION supabase_realtime ADD TABLE mensagens;
ALTER PUBLICATION supabase_realtime ADD TABLE departamentos;

-- =====================================================
-- ✅ PRONTO! Agora verifique se funcionou:
-- =====================================================

-- Verificar departamentos criados:
SELECT * FROM departamentos ORDER BY ordem;

-- Verificar estrutura das tabelas:
SELECT * FROM conversas LIMIT 1;
SELECT * FROM mensagens LIMIT 1;

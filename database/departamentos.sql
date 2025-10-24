-- =====================================================
-- SISTEMA DE DEPARTAMENTOS E TRANSFERÊNCIAS
-- Copie e cole no SQL Editor do Supabase
-- =====================================================

-- 1. Criar tabela de conversas (se não existir)
CREATE TABLE IF NOT EXISTS conversas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id TEXT NOT NULL,
  phone TEXT UNIQUE NOT NULL,
  lead_id TEXT,

  -- Departamento
  departamento_slug TEXT,
  departamento_nome TEXT,

  -- Status da conversa
  status TEXT DEFAULT 'aberta', -- 'aberta', 'em_atendimento', 'fechada', 'pendente'
  modo_ia TEXT DEFAULT 'ligado', -- 'ligado', 'atencao', 'desligado'
  prioridade TEXT DEFAULT 'normal', -- 'baixa', 'normal', 'alta', 'urgente'

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
  transferido_por TEXT, -- 'ia' ou user_id
  motivo_transferencia TEXT,

  -- Notificações
  notificado BOOLEAN DEFAULT false,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Criar tabela de mensagens (se não existir)
CREATE TABLE IF NOT EXISTS mensagens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversa_id UUID REFERENCES conversas(id) ON DELETE CASCADE,
  phone TEXT NOT NULL,

  -- Tipo e conteúdo
  tipo TEXT NOT NULL, -- 'entrada' (cliente) ou 'saida' (empresa)
  conteudo TEXT NOT NULL,

  -- Origem
  enviado_por_ia BOOLEAN DEFAULT false,
  enviado_por_user_id TEXT, -- ID do usuário humano (se aplicável)

  -- Departamento (se foi enviada após transferência)
  departamento_origem TEXT, -- ex: 'financeiro', 'assistencia-tecnica'

  -- Status
  lida BOOLEAN DEFAULT false,
  entregue BOOLEAN DEFAULT false,

  -- Metadados
  metadata JSONB DEFAULT '{}',

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_conversas_empresa ON conversas(empresa_id);
CREATE INDEX IF NOT EXISTS idx_conversas_departamento ON conversas(departamento_slug);
CREATE INDEX IF NOT EXISTS idx_conversas_status ON conversas(status);
CREATE INDEX IF NOT EXISTS idx_conversas_phone ON conversas(phone);
CREATE INDEX IF NOT EXISTS idx_conversas_notificado ON conversas(notificado) WHERE notificado = false;

CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_phone ON mensagens(phone);
CREATE INDEX IF NOT EXISTS idx_mensagens_created ON mensagens(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mensagens_departamento ON mensagens(departamento_origem);

-- 4. Criar função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- 5. Criar trigger para conversas
DROP TRIGGER IF EXISTS update_conversas_updated_at ON conversas;
CREATE TRIGGER update_conversas_updated_at
  BEFORE UPDATE ON conversas
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 6. Habilitar Realtime para notificações em tempo real
ALTER PUBLICATION supabase_realtime ADD TABLE conversas;
ALTER PUBLICATION supabase_realtime ADD TABLE mensagens;

-- 7. Inserir departamentos padrão (se tabela departamentos existir)
-- Caso já tenha a tabela departamentos do schema anterior:
INSERT INTO departamentos (id, empresa_id, nome, slug, cor_primaria, icone, ordem, ativo)
VALUES
  ('dept-vendas', 'emp1', 'Vendas', 'vendas', '#3B82F6', 'shopping-cart', 1, true),
  ('dept-assistencia', 'emp1', 'Assistência Técnica', 'assistencia-tecnica', '#F59E0B', 'wrench', 2, true),
  ('dept-financeiro', 'emp1', 'Financeiro', 'financeiro', '#10B981', 'dollar-sign', 3, true),
  ('dept-suporte', 'emp1', 'Suporte TI', 'suporte-ti', '#8B5CF6', 'monitor', 4, true),
  ('dept-geral', 'emp1', 'Geral', 'geral', '#6B7280', 'users', 5, true)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- ✅ PRONTO! Schema de departamentos criado
-- =====================================================

-- Para testar:
-- SELECT * FROM conversas;
-- SELECT * FROM mensagens;
-- SELECT * FROM departamentos;

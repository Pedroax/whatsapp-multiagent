-- =====================================================
-- SISTEMA DE CONTROLE DA IA - ALICE
-- Copie TUDO deste arquivo e cole no SQL Editor do Supabase
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

-- 5. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_mensagens_pendentes_status ON mensagens_pendentes(status);
CREATE INDEX IF NOT EXISTS idx_mensagens_pendentes_created ON mensagens_pendentes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agendamentos_empresa ON agendamentos_ia(empresa_id);
CREATE INDEX IF NOT EXISTS idx_agendamentos_ativo ON agendamentos_ia(ativo);

-- 6. Habilitar Realtime (para notificações em tempo real)
ALTER PUBLICATION supabase_realtime ADD TABLE mensagens_pendentes;
ALTER PUBLICATION supabase_realtime ADD TABLE config_ia;
ALTER PUBLICATION supabase_realtime ADD TABLE agendamentos_ia;

-- =====================================================
-- ✅ PRONTO! Execute este script e está tudo configurado!
-- =====================================================

-- Para verificar se funcionou, execute:
-- SELECT * FROM config_ia;
-- SELECT * FROM mensagens_pendentes;
-- SELECT * FROM agendamentos_ia;

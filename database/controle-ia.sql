-- =====================================================
-- EXTENSÃO DO SCHEMA: CONTROLE E AGENDAMENTO DA IA
-- Adiciona funcionalidades de controle ON/OFF/ATENÇÃO
-- e agendamento automático de horários
-- =====================================================

-- IMPORTANTE: Execute este script APÓS o schema.sql principal

-- =====================================================
-- TABELA: MENSAGENS PENDENTES DE APROVAÇÃO
-- Armazena mensagens da IA aguardando aprovação humana
-- =====================================================
CREATE TABLE IF NOT EXISTS mensagens_pendentes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  conversa_id UUID REFERENCES conversas(id) ON DELETE CASCADE,

  -- DADOS DO LEAD
  lead_id UUID REFERENCES leads(id),
  lead_nome TEXT NOT NULL,
  lead_telefone TEXT NOT NULL,

  -- MENSAGEM DO LEAD
  mensagem_recebida TEXT NOT NULL,
  mensagem_recebida_em TIMESTAMPTZ DEFAULT NOW(),

  -- RESPOSTA GERADA PELA IA
  resposta_ia TEXT NOT NULL,
  resposta_editada TEXT, -- se foi editada antes de enviar

  -- ANÁLISE DA IA (confiança, intenção, etc)
  confianca_ia DECIMAL, -- 0.0 a 1.0
  intencao_detectada TEXT, -- 'venda', 'duvida', 'reclamacao', etc
  contexto_ia JSONB DEFAULT '{}',

  -- STATUS DE APROVAÇÃO
  status TEXT DEFAULT 'pendente', -- 'pendente', 'aprovada', 'editada', 'recusada', 'expirada'

  -- APROVAÇÃO/RECUSA
  processada_por UUID REFERENCES usuarios(id),
  processada_em TIMESTAMPTZ,
  motivo_recusa TEXT,

  -- ENVIO
  enviada BOOLEAN DEFAULT false,
  enviada_em TIMESTAMPTZ,

  -- EXPIRAÇÃO (mensagens antigas expiram)
  expira_em TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 hour'),

  -- METADADOS
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_mensagens_pendentes_empresa ON mensagens_pendentes(empresa_id);
CREATE INDEX idx_mensagens_pendentes_status ON mensagens_pendentes(status);
CREATE INDEX idx_mensagens_pendentes_conversa ON mensagens_pendentes(conversa_id);
CREATE INDEX idx_mensagens_pendentes_created ON mensagens_pendentes(created_at DESC);

-- =====================================================
-- ATUALIZAÇÃO: Adicionar campos de controle na config_ia
-- =====================================================

-- Adiciona campo para controlar aprovação automática por confiança
ALTER TABLE config_ia
ADD COLUMN IF NOT EXISTS auto_aprovar_alta_confianca BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS limiar_confianca DECIMAL DEFAULT 0.95,
ADD COLUMN IF NOT EXISTS notificar_novas_mensagens BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS usuarios_notificar UUID[] DEFAULT '{}';

-- =====================================================
-- FUNÇÃO: Expirar mensagens pendentes antigas
-- =====================================================
CREATE OR REPLACE FUNCTION expirar_mensagens_pendentes()
RETURNS INTEGER AS $$
DECLARE
  total_expiradas INTEGER;
BEGIN
  UPDATE mensagens_pendentes
  SET
    status = 'expirada',
    processada_em = NOW()
  WHERE
    status = 'pendente'
    AND expira_em < NOW();

  GET DIAGNOSTICS total_expiradas = ROW_COUNT;
  RETURN total_expiradas;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNÇÃO: Obter estatísticas de aprovação
-- =====================================================
CREATE OR REPLACE FUNCTION get_stats_aprovacao(
  p_empresa_id UUID,
  p_data_inicio TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
  p_data_fim TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
  total_mensagens BIGINT,
  total_aprovadas BIGINT,
  total_editadas BIGINT,
  total_recusadas BIGINT,
  total_expiradas BIGINT,
  taxa_aprovacao DECIMAL,
  tempo_medio_aprovacao INTERVAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*)::BIGINT AS total_mensagens,
    COUNT(*) FILTER (WHERE status = 'aprovada')::BIGINT AS total_aprovadas,
    COUNT(*) FILTER (WHERE status = 'editada')::BIGINT AS total_editadas,
    COUNT(*) FILTER (WHERE status = 'recusada')::BIGINT AS total_recusadas,
    COUNT(*) FILTER (WHERE status = 'expirada')::BIGINT AS total_expiradas,
    ROUND(
      COUNT(*) FILTER (WHERE status IN ('aprovada', 'editada'))::DECIMAL /
      NULLIF(COUNT(*)::DECIMAL, 0) * 100,
      2
    ) AS taxa_aprovacao,
    AVG(processada_em - created_at) FILTER (
      WHERE processada_em IS NOT NULL
    ) AS tempo_medio_aprovacao
  FROM mensagens_pendentes
  WHERE
    empresa_id = p_empresa_id
    AND created_at BETWEEN p_data_inicio AND p_data_fim;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGER: Auto-expirar mensagens antigas
-- (Pode ser executado via cron job)
-- =====================================================

-- Função que roda a cada hora para expirar mensagens
CREATE OR REPLACE FUNCTION trigger_expirar_mensagens()
RETURNS void AS $$
BEGIN
  PERFORM expirar_mensagens_pendentes();
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEW: Fila de aprovação em tempo real
-- =====================================================
CREATE OR REPLACE VIEW fila_aprovacao AS
SELECT
  mp.id,
  mp.empresa_id,
  mp.lead_nome,
  mp.lead_telefone,
  mp.mensagem_recebida,
  mp.resposta_ia,
  mp.resposta_editada,
  mp.status,
  mp.confianca_ia,
  mp.intencao_detectada,
  mp.created_at,
  mp.expira_em,
  (mp.expira_em - NOW()) AS tempo_restante,
  c.departamento_id,
  c.usuario_atribuido_id,
  d.nome AS departamento_nome,
  u.nome_completo AS processada_por_nome
FROM mensagens_pendentes mp
LEFT JOIN conversas c ON c.id = mp.conversa_id
LEFT JOIN departamentos d ON d.id = c.departamento_id
LEFT JOIN usuarios u ON u.id = mp.processada_por
WHERE mp.status = 'pendente'
  AND mp.expira_em > NOW()
ORDER BY mp.created_at ASC;

-- =====================================================
-- FUNÇÃO: Aprovar mensagem
-- =====================================================
CREATE OR REPLACE FUNCTION aprovar_mensagem(
  p_mensagem_id UUID,
  p_usuario_id UUID,
  p_texto_final TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
  v_foi_editada BOOLEAN;
  v_resposta_ia TEXT;
BEGIN
  -- Buscar resposta original
  SELECT resposta_ia INTO v_resposta_ia
  FROM mensagens_pendentes
  WHERE id = p_mensagem_id;

  -- Determinar se foi editada
  v_foi_editada := (p_texto_final IS NOT NULL AND p_texto_final != v_resposta_ia);

  -- Atualizar registro
  UPDATE mensagens_pendentes
  SET
    status = CASE WHEN v_foi_editada THEN 'editada' ELSE 'aprovada' END,
    resposta_editada = p_texto_final,
    processada_por = p_usuario_id,
    processada_em = NOW(),
    enviada = true,
    enviada_em = NOW()
  WHERE id = p_mensagem_id
    AND status = 'pendente';

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNÇÃO: Recusar mensagem
-- =====================================================
CREATE OR REPLACE FUNCTION recusar_mensagem(
  p_mensagem_id UUID,
  p_usuario_id UUID,
  p_motivo TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
  UPDATE mensagens_pendentes
  SET
    status = 'recusada',
    processada_por = p_usuario_id,
    processada_em = NOW(),
    motivo_recusa = p_motivo
  WHERE id = p_mensagem_id
    AND status = 'pendente';

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- HABILITAR REALTIME
-- =====================================================
ALTER PUBLICATION supabase_realtime ADD TABLE mensagens_pendentes;
ALTER PUBLICATION supabase_realtime ADD TABLE config_ia;
ALTER PUBLICATION supabase_realtime ADD TABLE agendamentos_ia;

-- =====================================================
-- RLS (Row Level Security)
-- Ajuste conforme suas necessidades
-- =====================================================

ALTER TABLE mensagens_pendentes ENABLE ROW LEVEL SECURITY;

-- Policy: Usuários autenticados podem ver mensagens de sua empresa
CREATE POLICY "Usuários podem ver mensagens de sua empresa"
ON mensagens_pendentes
FOR SELECT
TO authenticated
USING (
  empresa_id IN (
    SELECT empresa_id FROM usuarios WHERE id = auth.uid()
  )
);

-- Policy: Usuários autenticados podem processar mensagens de sua empresa
CREATE POLICY "Usuários podem processar mensagens de sua empresa"
ON mensagens_pendentes
FOR UPDATE
TO authenticated
USING (
  empresa_id IN (
    SELECT empresa_id FROM usuarios WHERE id = auth.uid()
  )
);

-- =====================================================
-- DADOS DE EXEMPLO (OPCIONAL)
-- =====================================================

-- Inserir configuração inicial (ajuste conforme sua empresa)
INSERT INTO config_ia (empresa_id, modo_geral, agendamento_ativo)
SELECT id, 'atencao', true
FROM empresas
WHERE NOT EXISTS (
  SELECT 1 FROM config_ia WHERE empresa_id = empresas.id
)
LIMIT 1;

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================
SELECT
  'Tabelas de controle da IA criadas com sucesso!' AS status,
  COUNT(*) AS total_config
FROM config_ia;

SELECT
  'Triggers e funções criadas com sucesso!' AS status;

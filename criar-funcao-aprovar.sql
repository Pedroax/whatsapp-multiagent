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

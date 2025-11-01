-- Adiciona colunas de auto-aprovação na tabela config_ia

ALTER TABLE config_ia
ADD COLUMN IF NOT EXISTS auto_aprovar_alta_confianca BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS limiar_confianca DECIMAL DEFAULT 0.7;

-- Atualizar config existente para ativar auto-aprovação
UPDATE config_ia
SET
    auto_aprovar_alta_confianca = true,
    limiar_confianca = 0.7
WHERE empresa_id = 'emp1';

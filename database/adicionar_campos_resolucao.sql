-- =====================================================
-- ADICIONAR CAMPOS DE RESOLUÇÃO DE CONVERSA
-- Execute este SQL no Supabase SQL Editor
-- =====================================================

-- Adicionar campos de resolução na tabela conversas
ALTER TABLE conversas
ADD COLUMN IF NOT EXISTS resolvido_em TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS resolvido_por TEXT,
ADD COLUMN IF NOT EXISTS nota_resolucao TEXT;

-- Criar índice para consultas de conversas resolvidas
CREATE INDEX IF NOT EXISTS idx_conversas_resolvido ON conversas(resolvido_em DESC) WHERE resolvido_em IS NOT NULL;

-- =====================================================
-- ✅ PRONTO! Campos adicionados
-- =====================================================

-- Verificar estrutura atualizada:
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'conversas'
AND column_name IN ('resolvido_em', 'resolvido_por', 'nota_resolucao');

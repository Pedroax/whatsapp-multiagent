-- =====================================================
-- FIX: Corrigir tabela historico_decisoes
-- Execute este SQL se deu erro na coluna "phone"
-- =====================================================

-- 1. Deletar tabela antiga (se existir)
DROP TABLE IF EXISTS historico_decisoes CASCADE;

-- 2. Recriar tabela COM a coluna phone
CREATE TABLE historico_decisoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    phone TEXT NOT NULL,
    mensagem_usuario TEXT NOT NULL,
    resposta_ia TEXT NOT NULL,
    decisao TEXT NOT NULL CHECK (decisao IN ('enviar_direto', 'aguardar_aprovacao', 'bloquear')),
    nivel_confianca DECIMAL,
    contexto JSONB,
    foi_aprovada BOOLEAN,
    foi_rejeitada BOOLEAN,
    foi_editada BOOLEAN,
    foi_correto BOOLEAN,
    feedback_humano TEXT,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Criar índices
CREATE INDEX idx_historico_phone ON historico_decisoes(phone);
CREATE INDEX idx_historico_created ON historico_decisoes(created_at DESC);
CREATE INDEX idx_historico_empresa ON historico_decisoes(empresa_id);

-- ✅ Pronto! Tabela corrigida

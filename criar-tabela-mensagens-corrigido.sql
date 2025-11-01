-- Tabela de mensagens para histórico de conversas
CREATE TABLE IF NOT EXISTS mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversa_id UUID NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,

    -- Dados da mensagem
    remetente TEXT NOT NULL, -- 'usuario' ou 'assistente'
    conteudo TEXT NOT NULL,
    tipo_midia TEXT DEFAULT 'text', -- 'text', 'audio', 'image', 'document'

    -- Metadados
    enviada_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    lida BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_mensagens_conversa_id ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_enviada_em ON mensagens(enviada_em DESC);

-- RLS (Row Level Security)
ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

-- Policy: Usuários autenticados podem ver todas as mensagens
CREATE POLICY "Usuários podem ver mensagens"
ON mensagens FOR SELECT
TO authenticated
USING (true);

-- Policy: Sistema pode inserir mensagens (service role)
CREATE POLICY "Sistema pode inserir mensagens"
ON mensagens FOR INSERT
TO service_role
WITH CHECK (true);

-- Policy: Sistema pode atualizar mensagens (service role)
CREATE POLICY "Sistema pode atualizar mensagens"
ON mensagens FOR UPDATE
TO service_role
USING (true);

COMMENT ON TABLE mensagens IS 'Histórico completo de mensagens trocadas nas conversas';

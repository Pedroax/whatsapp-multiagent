-- Tabela de mensagens para histórico de conversas
CREATE TABLE IF NOT EXISTS mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversa_id UUID NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    empresa_id TEXT NOT NULL DEFAULT 'emp1',

    -- Dados da mensagem
    remetente TEXT NOT NULL, -- 'usuario' ou 'assistente'
    conteudo TEXT NOT NULL,
    tipo_midia TEXT, -- 'text', 'audio', 'image', 'document'

    -- Metadados
    enviada_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    lida BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Índices para performance
    CONSTRAINT mensagens_conversa_id_fkey FOREIGN KEY (conversa_id) REFERENCES conversas(id) ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_mensagens_conversa_id ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_empresa_id ON mensagens(empresa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_enviada_em ON mensagens(enviada_em DESC);

-- RLS (Row Level Security)
ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

-- Policy: Usuários podem ver mensagens da sua empresa
CREATE POLICY "Usuários podem ver mensagens da sua empresa"
ON mensagens FOR SELECT
USING (empresa_id IN (
    SELECT empresa_id FROM usuarios WHERE id = auth.uid()
));

-- Policy: Sistema pode inserir mensagens
CREATE POLICY "Sistema pode inserir mensagens"
ON mensagens FOR INSERT
WITH CHECK (true);

-- Policy: Sistema pode atualizar mensagens
CREATE POLICY "Sistema pode atualizar mensagens"
ON mensagens FOR UPDATE
USING (true);

COMMENT ON TABLE mensagens IS 'Histórico completo de mensagens trocadas nas conversas';

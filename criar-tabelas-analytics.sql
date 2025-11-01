-- Tabela de Pedidos (Analytics)
CREATE TABLE IF NOT EXISTS pedidos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_pedido TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    cliente_nome TEXT NOT NULL,
    valor_total DECIMAL(10, 2) NOT NULL DEFAULT 0,
    produtos JSONB NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'confirmado',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_pedidos_phone ON pedidos(phone);
CREATE INDEX IF NOT EXISTS idx_pedidos_created_at ON pedidos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status);

-- Tabela de Leads Pendentes (Analytics)
CREATE TABLE IF NOT EXISTS leads_pendentes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    ultima_mensagem TEXT,
    valor_estimado DECIMAL(10, 2) DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pendente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_leads_pendentes_phone ON leads_pendentes(phone);
CREATE INDEX IF NOT EXISTS idx_leads_pendentes_status ON leads_pendentes(status);
CREATE INDEX IF NOT EXISTS idx_leads_pendentes_created_at ON leads_pendentes(created_at DESC);

-- Trigger para updated_at em pedidos
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pedidos_updated_at
    BEFORE UPDATE ON pedidos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_pendentes_updated_at
    BEFORE UPDATE ON leads_pendentes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentários
COMMENT ON TABLE pedidos IS 'Pedidos confirmados pela IA para analytics';
COMMENT ON TABLE leads_pendentes IS 'Leads que iniciaram conversa mas não fecharam pedido';

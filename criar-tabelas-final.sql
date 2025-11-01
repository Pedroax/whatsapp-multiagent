-- APAGUE TUDO e cole APENAS este código:

DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS leads_pendentes CASCADE;

CREATE TABLE pedidos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_pedido TEXT NOT NULL UNIQUE,
    telefone TEXT,
    cliente_nome TEXT,
    valor_total NUMERIC DEFAULT 0,
    produtos JSONB DEFAULT '[]'::jsonb,
    status TEXT DEFAULT 'confirmado',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE leads_pendentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telefone TEXT UNIQUE,
    nome TEXT,
    ultima_mensagem TEXT,
    valor_estimado NUMERIC DEFAULT 0,
    status TEXT DEFAULT 'pendente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pedidos_telefone ON pedidos(telefone);
CREATE INDEX idx_pedidos_created_at ON pedidos(created_at DESC);
CREATE INDEX idx_leads_pendentes_telefone ON leads_pendentes(telefone);
CREATE INDEX idx_leads_pendentes_status ON leads_pendentes(status);

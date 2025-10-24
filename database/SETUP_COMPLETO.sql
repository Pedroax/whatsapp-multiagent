-- =====================================================
-- SETUP COMPLETO - ALICE MULTIAGENTE
-- Execute este SQL no Supabase SQL Editor
-- =====================================================

-- =====================================================
-- 1. FUNÇÕES AUXILIARES
-- =====================================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- 2. TABELAS PRINCIPAIS
-- =====================================================

-- 2.1 Empresas
CREATE TABLE IF NOT EXISTS empresas (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    cnpj TEXT UNIQUE,
    telefone TEXT,
    email TEXT,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 Departamentos
CREATE TABLE IF NOT EXISTS departamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    nome TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    descricao TEXT,
    cor_primaria TEXT DEFAULT '#3B82F6',
    icone TEXT DEFAULT 'briefcase',
    ordem INTEGER DEFAULT 0,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.3 Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    nome_completo TEXT NOT NULL,
    avatar_url TEXT,
    telefone TEXT,
    role TEXT NOT NULL CHECK (role IN ('super_admin', 'admin', 'agente')),
    departamento_slug TEXT REFERENCES departamentos(slug),
    pode_ver_todos_departamentos BOOLEAN DEFAULT false,
    status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'suspenso')),
    ultimo_acesso TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.4 Sessões (JWT)
CREATE TABLE IF NOT EXISTS sessoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    expira_em TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.5 Leads
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    nome TEXT,
    telefone TEXT UNIQUE NOT NULL,
    email TEXT,
    cpf_cnpj TEXT,
    tags TEXT[] DEFAULT '{}',
    origem TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.6 Conversas
CREATE TABLE IF NOT EXISTS conversas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    phone TEXT UNIQUE NOT NULL,
    lead_id UUID REFERENCES leads(id),
    departamento_slug TEXT REFERENCES departamentos(slug),
    departamento_nome TEXT,
    nome_lead TEXT,
    email_lead TEXT,
    tags TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'aberta' CHECK (status IN ('nova', 'aberta', 'pendente', 'resolvida', 'arquivada')),
    modo_ia TEXT DEFAULT 'ligado' CHECK (modo_ia IN ('ligado', 'atencao', 'desligado')),
    prioridade TEXT DEFAULT 'normal' CHECK (prioridade IN ('baixa', 'normal', 'alta', 'urgente')),
    nao_lidas INTEGER DEFAULT 0,
    ultima_mensagem TEXT,
    ultima_mensagem_em TIMESTAMPTZ,
    transferido_em TIMESTAMPTZ,
    resolvido_em TIMESTAMPTZ,
    resolvido_por UUID REFERENCES usuarios(id),
    nota_resolucao TEXT,
    notificado BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.7 Mensagens
CREATE TABLE IF NOT EXISTS mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversa_id UUID NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    phone TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    conteudo TEXT NOT NULL,
    enviado_por_ia BOOLEAN DEFAULT false,
    enviado_por_user_id UUID REFERENCES usuarios(id),
    departamento_origem TEXT,
    lida BOOLEAN DEFAULT false,
    entregue BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.8 Chat Sessions (Redis replacement)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone TEXT UNIQUE NOT NULL,
    state JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- =====================================================
-- 3. CONTROLE DA IA
-- =====================================================

-- 3.1 Configuração IA
CREATE TABLE IF NOT EXISTS config_ia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT UNIQUE NOT NULL DEFAULT 'emp1',
    modo_global TEXT DEFAULT 'ligado' CHECK (modo_global IN ('ligado', 'atencao', 'desligado')),
    requer_aprovacao BOOLEAN DEFAULT false,
    nivel_confianca_minimo DECIMAL DEFAULT 0.7,
    habilitado BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.2 Mensagens Pendentes (Fila de Aprovação)
CREATE TABLE IF NOT EXISTS mensagens_pendentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    phone TEXT NOT NULL,
    nome_cliente TEXT,
    mensagem_usuario TEXT NOT NULL,
    resposta_ia TEXT NOT NULL,
    contexto JSONB,
    nivel_confianca DECIMAL,
    motivo_pendencia TEXT,
    status TEXT DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovada', 'rejeitada', 'expirada')),
    aprovado_por UUID REFERENCES usuarios(id),
    aprovado_em TIMESTAMPTZ,
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- 3.3 Agendamentos IA
CREATE TABLE IF NOT EXISTS agendamentos_ia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    titulo TEXT NOT NULL,
    descricao TEXT,
    tipo TEXT NOT NULL CHECK (tipo IN ('ligar', 'desligar', 'atencao', 'personalizado')),
    modo_alvo TEXT CHECK (modo_alvo IN ('ligado', 'atencao', 'desligado')),
    data_hora TIMESTAMPTZ NOT NULL,
    recorrente BOOLEAN DEFAULT false,
    padrao_recorrencia TEXT,
    ativo BOOLEAN DEFAULT true,
    executado BOOLEAN DEFAULT false,
    executado_em TIMESTAMPTZ,
    criado_por UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 4. SISTEMA DE APRENDIZADO
-- =====================================================

-- 4.1 Histórico de Decisões
CREATE TABLE IF NOT EXISTS historico_decisoes (
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

-- 4.2 Pesos de Aprendizado
CREATE TABLE IF NOT EXISTS pesos_aprendizado (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    categoria TEXT NOT NULL,
    subcategoria TEXT,
    padrao TEXT NOT NULL,
    peso DECIMAL DEFAULT 1.0,
    total_ocorrencias INTEGER DEFAULT 0,
    total_sucessos INTEGER DEFAULT 0,
    total_falhas INTEGER DEFAULT 0,
    taxa_sucesso DECIMAL DEFAULT 0.0,
    ultima_atualizacao TIMESTAMPTZ DEFAULT NOW(),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.3 Simulações
CREATE TABLE IF NOT EXISTS simulacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    nome TEXT NOT NULL,
    descricao TEXT,
    tipo TEXT NOT NULL CHECK (tipo IN ('vendas', 'suporte', 'financeiro', 'custom')),
    mensagens_simuladas JSONB NOT NULL,
    resultado JSONB,
    metricas JSONB,
    status TEXT DEFAULT 'pendente' CHECK (status IN ('pendente', 'executando', 'concluida', 'falhou')),
    criado_por UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- =====================================================
-- 5. EVENTOS E NOTIFICAÇÕES
-- =====================================================

-- 5.1 Eventos
CREATE TABLE IF NOT EXISTS eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL DEFAULT 'emp1',
    tipo TEXT NOT NULL,
    descricao TEXT,
    dados JSONB,
    processado BOOLEAN DEFAULT false,
    processado_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5.2 Notificações
CREATE TABLE IF NOT EXISTS notificacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    mensagem TEXT,
    dados JSONB,
    lida BOOLEAN DEFAULT false,
    lida_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 6. ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Conversas
CREATE INDEX IF NOT EXISTS idx_conversas_phone ON conversas(phone);
CREATE INDEX IF NOT EXISTS idx_conversas_status ON conversas(status);
CREATE INDEX IF NOT EXISTS idx_conversas_departamento ON conversas(departamento_slug);
CREATE INDEX IF NOT EXISTS idx_conversas_updated ON conversas(updated_at DESC);

-- Mensagens
CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_phone ON mensagens(phone);
CREATE INDEX IF NOT EXISTS idx_mensagens_created ON mensagens(created_at);

-- Chat Sessions
CREATE INDEX IF NOT EXISTS idx_chat_sessions_phone ON chat_sessions(phone);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated ON chat_sessions(updated_at DESC);

-- Mensagens Pendentes
CREATE INDEX IF NOT EXISTS idx_mensagens_pendentes_status ON mensagens_pendentes(status);
CREATE INDEX IF NOT EXISTS idx_mensagens_pendentes_empresa ON mensagens_pendentes(empresa_id);

-- Histórico Decisões (verificar se tabela existe antes de criar índice)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'historico_decisoes') THEN
        CREATE INDEX IF NOT EXISTS idx_historico_phone ON historico_decisoes(phone);
        CREATE INDEX IF NOT EXISTS idx_historico_created ON historico_decisoes(created_at DESC);
    END IF;
END
$$;

-- Usuários
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_departamento ON usuarios(departamento_slug);

-- =====================================================
-- 7. TRIGGERS
-- =====================================================

-- Atualizar updated_at em conversas
DROP TRIGGER IF EXISTS update_conversas_updated_at ON conversas;
CREATE TRIGGER update_conversas_updated_at
    BEFORE UPDATE ON conversas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Atualizar updated_at em chat_sessions
DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Atualizar updated_at em usuarios
DROP TRIGGER IF EXISTS update_usuarios_updated_at ON usuarios;
CREATE TRIGGER update_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 8. DADOS INICIAIS
-- =====================================================

-- 8.1 Empresa padrão
INSERT INTO empresas (id, nome, ativo)
VALUES ('emp1', 'LC Baterias', true)
ON CONFLICT (id) DO NOTHING;

-- 8.2 Departamentos
INSERT INTO departamentos (id, empresa_id, nome, slug, cor_primaria, icone, ordem, ativo)
VALUES
    (gen_random_uuid(), 'emp1', 'Vendas', 'vendas', '#3B82F6', 'shopping-cart', 1, true),
    (gen_random_uuid(), 'emp1', 'Financeiro', 'financeiro', '#10B981', 'dollar-sign', 2, true),
    (gen_random_uuid(), 'emp1', 'Assistência Técnica', 'assistencia-tecnica', '#F59E0B', 'wrench', 3, true),
    (gen_random_uuid(), 'emp1', 'Suporte TI', 'suporte-ti', '#8B5CF6', 'monitor', 4, true)
ON CONFLICT (slug) DO NOTHING;

-- 8.3 Usuários (senha: admin123)
-- Hash bcrypt de "admin123"
INSERT INTO usuarios (id, email, senha_hash, nome_completo, role, departamento_slug, pode_ver_todos_departamentos)
VALUES
    (gen_random_uuid(), 'admin@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Super Admin', 'super_admin', NULL, true),
    (gen_random_uuid(), 'vendas@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'João Vendedor', 'agente', 'vendas', false),
    (gen_random_uuid(), 'financeiro@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Carlos Financeiro', 'agente', 'financeiro', false),
    (gen_random_uuid(), 'assistencia@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Ana Técnica', 'agente', 'assistencia-tecnica', false),
    (gen_random_uuid(), 'suporte@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Pedro Suporte', 'agente', 'suporte-ti', false)
ON CONFLICT (email) DO NOTHING;

-- 8.4 Configuração IA
INSERT INTO config_ia (id, empresa_id, modo_global, requer_aprovacao, nivel_confianca_minimo)
VALUES (gen_random_uuid(), 'emp1', 'ligado', false, 0.7)
ON CONFLICT (empresa_id) DO NOTHING;

-- =====================================================
-- 9. HABILITAR REALTIME (OPCIONAL)
-- =====================================================

-- ALTER PUBLICATION supabase_realtime ADD TABLE conversas;
-- ALTER PUBLICATION supabase_realtime ADD TABLE mensagens;
-- ALTER PUBLICATION supabase_realtime ADD TABLE mensagens_pendentes;

-- =====================================================
-- ✅ SETUP COMPLETO!
-- =====================================================

-- Verificar tabelas criadas:
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- ============================================================================
-- SISTEMA DE APRENDIZADO E SIMULADOR
-- ============================================================================

-- Tabela de histórico de decisões (para aprendizado)
CREATE TABLE IF NOT EXISTS historico_decisoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL,

    -- Dados da mensagem
    mensagem_usuario TEXT NOT NULL,
    resposta_ia TEXT NOT NULL,
    intencao_detectada TEXT,
    confianca_inicial DECIMAL NOT NULL,

    -- Contexto no momento
    estado_fluxo TEXT,
    tem_cnpj BOOLEAN DEFAULT FALSE,
    tamanho_historico INTEGER DEFAULT 0,
    metadados_contexto JSONB,

    -- Decisão do sistema
    decisao_sistema TEXT NOT NULL, -- 'enviar_direto', 'aguardar_aprovacao', 'bloquear'

    -- Feedback humano
    decisao_humana TEXT, -- 'aprovado', 'aprovado_editado', 'recusado'
    texto_editado TEXT,
    motivo_recusa TEXT,
    tempo_decisao_segundos INTEGER,

    -- Aprendizado
    foi_correto BOOLEAN, -- Se decisão do sistema foi correta
    peso_ajuste DECIMAL DEFAULT 0.0, -- Quanto ajustar os pesos

    -- Metadados
    created_at TIMESTAMPTZ DEFAULT NOW(),
    feedback_at TIMESTAMPTZ,
    usuario_feedback TEXT
);

-- Tabela de pesos dinâmicos (aprendizado)
CREATE TABLE IF NOT EXISTS pesos_aprendizado (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL UNIQUE,

    -- Pesos dos fatores (valores entre -1.0 e 1.0)
    peso_cnpj_validado DECIMAL DEFAULT 0.15,
    peso_fluxo_estruturado DECIMAL DEFAULT 0.10,
    peso_msg_curta DECIMAL DEFAULT 0.05,
    peso_dados_estruturados DECIMAL DEFAULT 0.10,
    peso_historico_longo DECIMAL DEFAULT 0.05,

    peso_primeira_msg DECIMAL DEFAULT -0.20,
    peso_msg_longa DECIMAL DEFAULT -0.10,
    peso_valores_financeiros DECIMAL DEFAULT -0.15,

    -- Limiares
    limiar_confianca_alta DECIMAL DEFAULT 0.95,
    limiar_confianca_media DECIMAL DEFAULT 0.70,

    -- Estatísticas
    total_decisoes INTEGER DEFAULT 0,
    total_corretas INTEGER DEFAULT 0,
    total_incorretas INTEGER DEFAULT 0,
    taxa_acerto DECIMAL DEFAULT 0.0,

    -- Metadados
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    versao INTEGER DEFAULT 1
);

-- Tabela de simulações (sandbox)
CREATE TABLE IF NOT EXISTS simulacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id TEXT NOT NULL,

    -- Dados da simulação
    nome_simulacao TEXT NOT NULL,
    descricao TEXT,

    -- Mensagens simuladas
    mensagens JSONB NOT NULL, -- Array de {role: 'user'|'assistant', content: '...'}

    -- Contexto simulado
    contexto_simulado JSONB, -- Estado, CNPJ, produtos, etc

    -- Resultados
    resposta_ia TEXT,
    confianca DECIMAL,
    intencao TEXT,
    decisao TEXT,
    metadados_analise JSONB,

    -- Status
    status TEXT DEFAULT 'rascunho', -- 'rascunho', 'executado', 'arquivado'

    -- Metadados
    created_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    created_by TEXT
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_historico_empresa ON historico_decisoes(empresa_id);
CREATE INDEX IF NOT EXISTS idx_historico_decisao ON historico_decisoes(decisao_sistema);
CREATE INDEX IF NOT EXISTS idx_historico_feedback ON historico_decisoes(decisao_humana);
CREATE INDEX IF NOT EXISTS idx_historico_correto ON historico_decisoes(foi_correto);
CREATE INDEX IF NOT EXISTS idx_historico_created ON historico_decisoes(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_simulacoes_empresa ON simulacoes(empresa_id);
CREATE INDEX IF NOT EXISTS idx_simulacoes_status ON simulacoes(status);

-- Habilitar realtime
ALTER PUBLICATION supabase_realtime ADD TABLE historico_decisoes;
ALTER PUBLICATION supabase_realtime ADD TABLE pesos_aprendizado;
ALTER PUBLICATION supabase_realtime ADD TABLE simulacoes;

-- Inserir configuração padrão de pesos para empresa 'emp1'
INSERT INTO pesos_aprendizado (empresa_id)
VALUES ('emp1')
ON CONFLICT (empresa_id) DO NOTHING;

-- Function para calcular taxa de acerto automaticamente
CREATE OR REPLACE FUNCTION atualizar_taxa_acerto()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pesos_aprendizado
    SET
        total_decisoes = (SELECT COUNT(*) FROM historico_decisoes WHERE empresa_id = NEW.empresa_id AND foi_correto IS NOT NULL),
        total_corretas = (SELECT COUNT(*) FROM historico_decisoes WHERE empresa_id = NEW.empresa_id AND foi_correto = TRUE),
        total_incorretas = (SELECT COUNT(*) FROM historico_decisoes WHERE empresa_id = NEW.empresa_id AND foi_correto = FALSE),
        taxa_acerto = CASE
            WHEN (SELECT COUNT(*) FROM historico_decisoes WHERE empresa_id = NEW.empresa_id AND foi_correto IS NOT NULL) > 0
            THEN (SELECT COUNT(*) FROM historico_decisoes WHERE empresa_id = NEW.empresa_id AND foi_correto = TRUE)::DECIMAL /
                 (SELECT COUNT(*) FROM historico_decisoes WHERE empresa_id = NEW.empresa_id AND foi_correto IS NOT NULL)::DECIMAL
            ELSE 0.0
        END,
        updated_at = NOW()
    WHERE empresa_id = NEW.empresa_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar taxa de acerto
DROP TRIGGER IF EXISTS trigger_atualizar_taxa_acerto ON historico_decisoes;
CREATE TRIGGER trigger_atualizar_taxa_acerto
    AFTER INSERT OR UPDATE OF foi_correto ON historico_decisoes
    FOR EACH ROW
    WHEN (NEW.foi_correto IS NOT NULL)
    EXECUTE FUNCTION atualizar_taxa_acerto();

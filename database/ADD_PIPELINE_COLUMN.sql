-- ============================================================================
-- ADICIONAR COLUNA ESTAGIO_PIPELINE À TABELA PAULA_CONVERSAS
-- ============================================================================
-- Script para adicionar funcionalidade de Pipeline de Leads
-- Data: 2025-11-17
-- ============================================================================

-- Adicionar coluna estagio_pipeline
ALTER TABLE paula_conversas
ADD COLUMN IF NOT EXISTS estagio_pipeline TEXT DEFAULT 'novo';

-- Criar índice para melhorar performance de filtros
CREATE INDEX IF NOT EXISTS idx_paula_conversas_estagio_pipeline
ON paula_conversas(estagio_pipeline);

-- Comentário da coluna
COMMENT ON COLUMN paula_conversas.estagio_pipeline IS 'Estágio do lead no pipeline de vendas/atendimento';

-- ============================================================================
-- ESTÁGIOS DISPONÍVEIS:
-- ============================================================================
-- novo: Lead novo que acabou de chegar
-- em_contato: Primeira interação acontecendo
-- aguardando_resposta: Lead não respondeu ainda
-- interessado: Demonstrou interesse
-- agendamento_solicitado: Pediu para agendar
-- agendado: Consulta já marcada
-- compareceu: Passou na consulta
-- nao_compareceu: Faltou à consulta
-- convertido: Fechou tratamento/procedimento
-- perdido: Desistiu/não tem interesse
-- ============================================================================

-- Verificar se funcionou
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'paula_conversas'
AND column_name = 'estagio_pipeline';

-- ============================================================================
-- Script para criar departamentos na tabela departamentos
-- Execute ANTES de criar os usuários
-- ============================================================================

-- PASSO 1: Verificar quais departamentos já existem
SELECT * FROM departamentos WHERE empresa_id = 'emp1';

-- PASSO 2: Inserir departamentos (se não existirem)

-- Vendas
INSERT INTO departamentos (empresa_id, slug, nome, cor, descricao)
VALUES ('emp1', 'vendas', 'Vendas', '#10b981', 'Departamento de vendas e atendimento comercial')
ON CONFLICT (empresa_id, slug) DO NOTHING;

-- Financeiro
INSERT INTO departamentos (empresa_id, slug, nome, cor, descricao)
VALUES ('emp1', 'financeiro', 'Financeiro', '#3b82f6', 'Departamento financeiro e cobrança')
ON CONFLICT (empresa_id, slug) DO NOTHING;

-- Suporte
INSERT INTO departamentos (empresa_id, slug, nome, cor, descricao)
VALUES ('emp1', 'suporte', 'Suporte', '#8b5cf6', 'Departamento de suporte ao cliente')
ON CONFLICT (empresa_id, slug) DO NOTHING;

-- Assistência Técnica
INSERT INTO departamentos (empresa_id, slug, nome, cor, descricao)
VALUES ('emp1', 'assistencia', 'Assistência Técnica', '#f97316', 'Assistência técnica e manutenção')
ON CONFLICT (empresa_id, slug) DO NOTHING;

-- PASSO 3: Verificar departamentos criados
SELECT
  empresa_id,
  slug,
  nome,
  cor,
  descricao,
  created_at
FROM departamentos
WHERE empresa_id = 'emp1'
ORDER BY nome;

-- ============================================================================
-- Resultado esperado: 4 departamentos
-- ============================================================================
-- 1. Assistência Técnica (assistencia) - Laranja
-- 2. Financeiro (financeiro) - Azul
-- 3. Suporte (suporte) - Roxo
-- 4. Vendas (vendas) - Verde
-- ============================================================================

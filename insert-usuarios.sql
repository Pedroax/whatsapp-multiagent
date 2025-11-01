-- ============================================================================
-- Script para inserir usuários na tabela usuarios
-- Execute este script no Supabase SQL Editor
-- ============================================================================

-- PASSO 1: Deletar todos os registros antigos
DELETE FROM usuarios WHERE empresa_id = 'emp1';

-- PASSO 2: Inserir todos os usuários com os UUIDs corretos do Auth

-- 1. Carlos Financeiro (Admin - Financeiro)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  senha_hash
) VALUES (
  '2aef1492-39b4-41f8-8323-8327a41b36a',
  'emp1',
  'financeiro@lcbaterias.com',
  'Carlos Financeiro',
  'admin',
  'financeiro',
  false,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 2. João Vendedor (Agente - Vendas)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  senha_hash
) VALUES (
  '31895cb7-9fc8-4b6f-b4ae-9a2f651bae97',
  'emp1',
  'vendas@lcbaterias.com',
  'João Vendedor',
  'agente',
  'vendas',
  false,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 3. Maria Vendedora (Agente - Vendas)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  senha_hash
) VALUES (
  '7fbe890b-c917-44c0-b049-46481a52e02d',
  'emp1',
  'vendas2@lcbaterias.com',
  'Maria Vendedora',
  'agente',
  'vendas',
  false,
  '$2b$10$8rZ5YL5pXKqN0vF3vT0qZ0.ZXq1'
);

-- 4. Super Admin (Super Admin - Todos os departamentos)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  senha_hash
) VALUES (
  'a792c80c-b4d7-44bf-af55-6e61088c4e98',
  'emp1',
  'admin@lcbaterias.com',
  'Super Admin',
  'super_admin',
  null,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 5. Pedro Suporte (Admin - Suporte)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  senha_hash
) VALUES (
  'eb6c3f31-6b07-4aa9-bc77-0097f04fc4d7',
  'emp1',
  'suporte@lcbaterias.com',
  'Pedro Suporte',
  'admin',
  'suporte',
  false,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 6. Ana Técnica (Agente - Assistência Técnica)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  senha_hash
) VALUES (
  'faa2f77b-6cbe-4fdd-8646-d64694804f9a',
  'emp1',
  'assistencia@lcbaterias.com',
  'Ana Técnica',
  'agente',
  'assistencia',
  false,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- PASSO 3: Verificar se todos foram inseridos corretamente
SELECT
  id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  created_at
FROM usuarios
WHERE empresa_id = 'emp1'
ORDER BY
  CASE role
    WHEN 'super_admin' THEN 1
    WHEN 'admin' THEN 2
    WHEN 'agente' THEN 3
  END,
  nome_completo;

-- ============================================================================
-- Resultado esperado: 6 usuários
-- ============================================================================
-- 1. Super Admin (super_admin) - Vê todos os departamentos
-- 2. Carlos Financeiro (admin) - Vê só financeiro
-- 3. Pedro Suporte (admin) - Vê só suporte
-- 4. Ana Técnica (agente) - Vê só assistência
-- 5. João Vendedor (agente) - Vê só vendas
-- 6. Maria Vendedora (agente) - Vê só vendas
-- ============================================================================

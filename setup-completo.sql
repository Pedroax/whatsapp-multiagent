-- ============================================================================
-- SETUP COMPLETO: Departamentos + Usuários
-- Execute este script COMPLETO no Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- PARTE 1: CRIAR DEPARTAMENTOS
-- ============================================================================

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

-- ============================================================================
-- PARTE 2: DELETAR USUÁRIOS ANTIGOS E INSERIR NOVOS
-- ============================================================================

-- Deletar todos os registros antigos
DELETE FROM usuarios WHERE empresa_id = 'emp1';

-- 1. Super Admin (Super Admin - Todos os departamentos)
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

-- 2. Carlos Financeiro (Admin - Financeiro)
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
  '248eb65d-90ea-48d5-ba64-b530913c734d',
  'emp1',
  'financeiro@lcbaterias.com',
  'Carlos Financeiro',
  'admin',
  'financeiro',
  false,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 3. João Vendedor (Agente - Vendas)
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
  '056a57f0-5242-421c-a1c1-2d083603f2c9',
  'emp1',
  'vendas@lcbaterias.com',
  'João Vendedor',
  'agente',
  'vendas',
  false,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 4. Maria Vendedora (Agente - Vendas)
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
  '712ba9d7-1165-4e0d-b8e9-c2700432e391',
  'emp1',
  'vendas2@lcbaterias.com',
  'Maria Vendedora',
  'agente',
  'vendas',
  false,
  '$2b$10$8rZ5YL5pXKqN0vF3vT0qZ0.ZXq1'
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
  'cef45fa5-5dfc-4a4c-9366-8cce07068344',
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
  'e3c09223-e43b-4054-950d-5378626b6a4b',
  'emp1',
  'assistencia@lcbaterias.com',
  'Ana Técnica',
  'agente',
  'assistencia',
  false,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- ============================================================================
-- PARTE 3: VERIFICAR TUDO
-- ============================================================================

-- Mostrar departamentos
SELECT '=== DEPARTAMENTOS ===' as tipo;
SELECT slug, nome, cor FROM departamentos WHERE empresa_id = 'emp1' ORDER BY nome;

-- Mostrar usuários
SELECT '=== USUÁRIOS ===' as tipo;
SELECT
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos
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
-- RESULTADO ESPERADO
-- ============================================================================
--
-- DEPARTAMENTOS (4):
-- - assistencia (Assistência Técnica) - Laranja
-- - financeiro (Financeiro) - Azul
-- - suporte (Suporte) - Roxo
-- - vendas (Vendas) - Verde
--
-- USUÁRIOS (6):
-- 1. admin@lcbaterias.com - Super Admin (super_admin) - Todos departamentos
-- 2. financeiro@lcbaterias.com - Carlos Financeiro (admin) - financeiro
-- 3. suporte@lcbaterias.com - Pedro Suporte (admin) - suporte
-- 4. assistencia@lcbaterias.com - Ana Técnica (agente) - assistencia
-- 5. vendas@lcbaterias.com - João Vendedor (agente) - vendas
-- 6. vendas2@lcbaterias.com - Maria Vendedora (agente) - vendas
--
-- TODAS AS SENHAS: Lcbaterias@2025 (exceto Super Admin: Admin@2025)
-- ============================================================================

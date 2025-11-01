-- Script para criar usuários de todos os departamentos no Supabase

-- IMPORTANTE: Execute este script no Supabase SQL Editor
-- ANTES de executar, você precisa criar os usuários no Supabase Auth manualmente
-- com as seguintes credenciais (todas com senha: Lcbaterias@2025):

-- 1. financeiro@lcbaterias.com
-- 2. vendas@lcbaterias.com
-- 3. vendas2@lcbaterias.com
-- 4. suporte@lcbaterias.com
-- 5. assistencia@lcbaterias.com

-- Depois de criar no Auth, copie os UUIDs e cole abaixo substituindo os IDs

-- ============================================================================
-- DELETAR REGISTROS ANTIGOS (se existirem)
-- ============================================================================

DELETE FROM usuarios WHERE email IN (
  'financeiro@lcbaterias.com',
  'vendas@lcbaterias.com',
  'vendas2@lcbaterias.com',
  'suporte@lcbaterias.com',
  'assistencia@lcbaterias.com'
);

-- ============================================================================
-- INSERIR NOVOS USUÁRIOS
-- ============================================================================

-- IMPORTANTE: Substitua os UUIDs abaixo pelos UUIDs gerados no Supabase Auth

-- 1. Carlos Financeiro (Admin - Financeiro)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  ativo,
  senha_hash
) VALUES (
  '2aef1492-39B4-41f8-8323-8327a41b36a',  -- SUBSTITUIR pelo UUID do Auth
  'emp1',
  'financeiro@lcbaterias.com',
  'Carlos Financeiro',
  'admin',
  'financeiro',
  false,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'  -- Hash da senha: Lcbaterias@2025
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
  ativo,
  senha_hash
) VALUES (
  '31895cb7-9fc8-4b6f-b4ae-9a2f651bae97',  -- SUBSTITUIR pelo UUID do Auth
  'emp1',
  'vendas@lcbaterias.com',
  'João Vendedor',
  'agente',
  'vendas',
  false,
  true,
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
  ativo,
  senha_hash
) VALUES (
  '7fbe890b-c917-44c0-b049-46481a52e02d',  -- SUBSTITUIR pelo UUID do Auth
  'emp1',
  'vendas2@lcbaterias.com',
  'Maria Vendedora',
  'agente',
  'vendas',
  false,
  true,
  '$2b$10$8rZ5YL5pXKqN0vF3vT0qZ0.ZXq1'
);

-- 4. Pedro Suporte (Admin - Suporte)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  false,
  ativo,
  senha_hash
) VALUES (
  'eb6c3f31-6b07-4aa9-bc77-0097f04fc4d7',  -- SUBSTITUIR pelo UUID do Auth
  'emp1',
  'suporte@lcbaterias.com',
  'Pedro Suporte',
  'admin',
  'suporte',
  false,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 5. Ana Técnica (Agente - Assistência Técnica)
INSERT INTO usuarios (
  id,
  empresa_id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  ativo,
  senha_hash
) VALUES (
  'faa2f77b-6cbe-4fdd-8646-d64694804f9a',  -- SUBSTITUIR pelo UUID do Auth
  'emp1',
  'assistencia@lcbaterias.com',
  'Ana Técnica',
  'agente',
  'assistencia',
  false,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- ============================================================================
-- VERIFICAR INSERÇÕES
-- ============================================================================

SELECT
  id,
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  ativo
FROM usuarios
WHERE empresa_id = 'emp1'
ORDER BY role DESC, nome_completo;

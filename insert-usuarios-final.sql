-- ============================================================================
-- INSERIR USUÁRIOS (slugs corretos dos departamentos)
-- ============================================================================

-- Deletar todos os registros antigos
DELETE FROM usuarios WHERE empresa_id = 'emp1';

-- 1. Super Admin (Todos os departamentos)
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, senha_hash)
VALUES ('a792c80c-b4d7-44bf-af55-6e61088c4e98', 'emp1', 'admin@lcbaterias.com', 'Super Admin', 'super_admin', null, true, '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi');

-- 2. Carlos Financeiro (Admin - Financeiro)
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, senha_hash)
VALUES ('248eb65d-90ea-48d5-ba64-b530913c734d', 'emp1', 'financeiro@lcbaterias.com', 'Carlos Financeiro', 'admin', 'financeiro', false, '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi');

-- 3. João Vendedor (Agente - Vendas)
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, senha_hash)
VALUES ('056a57f0-5242-421c-a1c1-2d083603f2c9', 'emp1', 'vendas@lcbaterias.com', 'João Vendedor', 'agente', 'vendas', false, '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi');

-- 4. Maria Vendedora (Agente - Vendas)
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, senha_hash)
VALUES ('712ba9d7-1165-4e0d-b8e9-c2700432e391', 'emp1', 'vendas2@lcbaterias.com', 'Maria Vendedora', 'agente', 'vendas', false, '$2b$10$8rZ5YL5pXKqN0vF3vT0qZ0.ZXq1');

-- 5. Pedro Suporte (Admin - Suporte TI)
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, senha_hash)
VALUES ('cef45fa5-5dfc-4a4c-9366-8cce07068344', 'emp1', 'suporte@lcbaterias.com', 'Pedro Suporte', 'admin', 'suporte-ti', false, '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi');

-- 6. Ana Técnica (Agente - Assistência Técnica)
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, senha_hash)
VALUES ('e3c09223-e43b-4054-950d-5378626b6a4b', 'emp1', 'assistencia@lcbaterias.com', 'Ana Técnica', 'agente', 'assistencia-tecnica', false, '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi');

-- VERIFICAR
SELECT email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos
FROM usuarios
WHERE empresa_id = 'emp1'
ORDER BY role DESC, nome_completo;

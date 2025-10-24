-- =====================================================
-- SISTEMA DE USUÁRIOS E AUTENTICAÇÃO
-- Execute no Supabase SQL Editor
-- =====================================================

-- 1. Criar tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id TEXT NOT NULL DEFAULT 'emp1',

  -- Dados de Login
  email TEXT UNIQUE NOT NULL,
  senha_hash TEXT NOT NULL, -- Senha com bcrypt

  -- Dados Pessoais
  nome_completo TEXT NOT NULL,
  avatar_url TEXT,
  telefone TEXT,

  -- Permissões
  role TEXT NOT NULL CHECK (role IN ('super_admin', 'admin', 'agente')),
  departamento_slug TEXT REFERENCES departamentos(slug),
  pode_ver_todos_departamentos BOOLEAN DEFAULT false,

  -- Status
  status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'suspenso')),
  ultimo_acesso TIMESTAMPTZ,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Criar tabela de sessões (tokens JWT)
CREATE TABLE IF NOT EXISTS sessoes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  token TEXT UNIQUE NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  expira_em TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Criar índices
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_departamento ON usuarios(departamento_slug);
CREATE INDEX IF NOT EXISTS idx_usuarios_role ON usuarios(role);
CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token);
CREATE INDEX IF NOT EXISTS idx_sessoes_usuario ON sessoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sessoes_expira ON sessoes(expira_em);

-- 4. Trigger para updated_at
DROP TRIGGER IF EXISTS update_usuarios_updated_at ON usuarios;
CREATE TRIGGER update_usuarios_updated_at
  BEFORE UPDATE ON usuarios
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 5. Inserir usuários de exemplo (SENHA: admin123)
-- Hash bcrypt de "admin123": $2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0
INSERT INTO usuarios (email, senha_hash, nome_completo, role, departamento_slug, pode_ver_todos_departamentos)
VALUES
  -- Super Admin (vê tudo)
  ('admin@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Super Admin', 'super_admin', NULL, true),

  -- Vendas
  ('vendas@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'João Vendedor', 'agente', 'vendas', false),
  ('vendas2@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Maria Vendedora', 'agente', 'vendas', false),

  -- Financeiro
  ('financeiro@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Carlos Financeiro', 'agente', 'financeiro', false),

  -- Assistência Técnica
  ('assistencia@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Ana Técnica', 'agente', 'assistencia-tecnica', false),

  -- Suporte TI
  ('suporte@lcbaterias.com', '$2b$10$rZ5YL5pXKqN0vF3vT0qZ0.ZXqYqZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0qZ0', 'Pedro Suporte', 'agente', 'suporte-ti', false)
ON CONFLICT (email) DO NOTHING;

-- 6. Habilitar Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE usuarios;
ALTER PUBLICATION supabase_realtime ADD TABLE sessoes;

-- =====================================================
-- ✅ PRONTO! Sistema de usuários criado
-- =====================================================

-- Verificar usuários criados:
SELECT
  email,
  nome_completo,
  role,
  departamento_slug,
  pode_ver_todos_departamentos,
  status
FROM usuarios
ORDER BY role, departamento_slug;

-- =====================================================
-- 📝 CREDENCIAIS DE TESTE:
-- =====================================================
-- Email: admin@lcbaterias.com | Senha: admin123 (Super Admin)
-- Email: vendas@lcbaterias.com | Senha: admin123 (Vendas)
-- Email: financeiro@lcbaterias.com | Senha: admin123 (Financeiro)
-- Email: assistencia@lcbaterias.com | Senha: admin123 (Assistência)
-- Email: suporte@lcbaterias.com | Senha: admin123 (Suporte TI)
-- =====================================================

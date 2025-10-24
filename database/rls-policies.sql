-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Garante isolamento completo entre empresas (multi-tenancy)
-- E controle de acesso por departamento/role
-- =====================================================

-- =====================================================
-- FUNÇÕES AUXILIARES PARA RLS
-- =====================================================

-- Retorna o ID da empresa do usuário logado
CREATE OR REPLACE FUNCTION auth.empresa_id()
RETURNS UUID AS $$
  SELECT empresa_id FROM usuarios WHERE id = auth.uid()
$$ LANGUAGE SQL STABLE;

-- Retorna o departamento_id do usuário logado
CREATE OR REPLACE FUNCTION auth.departamento_id()
RETURNS UUID AS $$
  SELECT departamento_id FROM usuarios WHERE id = auth.uid()
$$ LANGUAGE SQL STABLE;

-- Retorna o role do usuário logado
CREATE OR REPLACE FUNCTION auth.user_role()
RETURNS TEXT AS $$
  SELECT role FROM usuarios WHERE id = auth.uid()
$$ LANGUAGE SQL STABLE;

-- Verifica se usuário pode ver todos os departamentos
CREATE OR REPLACE FUNCTION auth.pode_ver_todos_departamentos()
RETURNS BOOLEAN AS $$
  SELECT COALESCE(pode_ver_todos_departamentos, false)
  FROM usuarios
  WHERE id = auth.uid()
$$ LANGUAGE SQL STABLE;

-- =====================================================
-- EMPRESAS
-- Apenas admins podem ver/editar empresas
-- =====================================================
ALTER TABLE empresas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem apenas sua empresa"
ON empresas FOR SELECT
USING (id = auth.empresa_id());

CREATE POLICY "Apenas admins podem atualizar empresa"
ON empresas FOR UPDATE
USING (
  id = auth.empresa_id() AND
  auth.user_role() = 'admin'
);

-- =====================================================
-- DEPARTAMENTOS
-- Usuários veem departamentos da própria empresa
-- =====================================================
ALTER TABLE departamentos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem departamentos da empresa"
ON departamentos FOR SELECT
USING (empresa_id = auth.empresa_id());

CREATE POLICY "Admins e supervisores podem criar departamentos"
ON departamentos FOR INSERT
WITH CHECK (
  empresa_id = auth.empresa_id() AND
  auth.user_role() IN ('admin', 'supervisor')
);

CREATE POLICY "Admins e supervisores podem atualizar departamentos"
ON departamentos FOR UPDATE
USING (
  empresa_id = auth.empresa_id() AND
  auth.user_role() IN ('admin', 'supervisor')
);

CREATE POLICY "Apenas admins podem deletar departamentos"
ON departamentos FOR DELETE
USING (
  empresa_id = auth.empresa_id() AND
  auth.user_role() = 'admin'
);

-- =====================================================
-- USUÁRIOS
-- Cada usuário vê apenas usuários da própria empresa
-- =====================================================
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem colegas da mesma empresa"
ON usuarios FOR SELECT
USING (empresa_id = auth.empresa_id());

CREATE POLICY "Usuário pode ver e atualizar próprio perfil"
ON usuarios FOR UPDATE
USING (id = auth.uid());

CREATE POLICY "Admins podem criar usuários na empresa"
ON usuarios FOR INSERT
WITH CHECK (
  empresa_id = auth.empresa_id() AND
  auth.user_role() = 'admin'
);

CREATE POLICY "Admins podem atualizar usuários da empresa"
ON usuarios FOR UPDATE
USING (
  empresa_id = auth.empresa_id() AND
  auth.user_role() = 'admin'
);

-- =====================================================
-- LEADS
-- Usuários veem leads da própria empresa
-- =====================================================
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem leads da empresa"
ON leads FOR SELECT
USING (empresa_id = auth.empresa_id());

CREATE POLICY "Usuários podem criar leads"
ON leads FOR INSERT
WITH CHECK (empresa_id = auth.empresa_id());

CREATE POLICY "Usuários podem atualizar leads"
ON leads FOR UPDATE
USING (empresa_id = auth.empresa_id());

-- =====================================================
-- CONVERSAS
-- Usuários veem conversas do próprio departamento
-- OU se podem ver todos os departamentos
-- =====================================================
ALTER TABLE conversas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem conversas do próprio departamento"
ON conversas FOR SELECT
USING (
  empresa_id = auth.empresa_id() AND
  (
    departamento_id = auth.departamento_id() OR
    auth.pode_ver_todos_departamentos() OR
    usuario_atribuido_id = auth.uid()
  )
);

CREATE POLICY "Usuários podem criar conversas"
ON conversas FOR INSERT
WITH CHECK (empresa_id = auth.empresa_id());

CREATE POLICY "Usuários podem atualizar conversas do departamento"
ON conversas FOR UPDATE
USING (
  empresa_id = auth.empresa_id() AND
  (
    departamento_id = auth.departamento_id() OR
    auth.pode_ver_todos_departamentos() OR
    usuario_atribuido_id = auth.uid()
  )
);

-- =====================================================
-- MENSAGENS
-- Seguem as mesmas regras das conversas
-- =====================================================
ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem mensagens de suas conversas"
ON mensagens FOR SELECT
USING (
  empresa_id = auth.empresa_id() AND
  conversa_id IN (
    SELECT id FROM conversas
    WHERE empresa_id = auth.empresa_id() AND
    (
      departamento_id = auth.departamento_id() OR
      auth.pode_ver_todos_departamentos() OR
      usuario_atribuido_id = auth.uid()
    )
  )
);

CREATE POLICY "Usuários podem criar mensagens"
ON mensagens FOR INSERT
WITH CHECK (
  empresa_id = auth.empresa_id() AND
  conversa_id IN (
    SELECT id FROM conversas
    WHERE empresa_id = auth.empresa_id()
  )
);

CREATE POLICY "Usuários podem atualizar suas mensagens"
ON mensagens FOR UPDATE
USING (
  empresa_id = auth.empresa_id() AND
  (usuario_id = auth.uid() OR auth.user_role() IN ('admin', 'supervisor'))
);

-- =====================================================
-- TRANSFERÊNCIAS
-- Todos da empresa podem ver transferências
-- =====================================================
ALTER TABLE transferencias ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem transferências da empresa"
ON transferencias FOR SELECT
USING (empresa_id = auth.empresa_id());

CREATE POLICY "Usuários podem criar transferências"
ON transferencias FOR INSERT
WITH CHECK (empresa_id = auth.empresa_id());

-- =====================================================
-- AGENDAMENTOS DA IA
-- Apenas admins e supervisores gerenciam
-- =====================================================
ALTER TABLE agendamentos_ia ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Todos veem agendamentos da empresa"
ON agendamentos_ia FOR SELECT
USING (empresa_id = auth.empresa_id());

CREATE POLICY "Admins e supervisores gerenciam agendamentos"
ON agendamentos_ia FOR ALL
USING (
  empresa_id = auth.empresa_id() AND
  auth.user_role() IN ('admin', 'supervisor')
);

-- =====================================================
-- CONFIGURAÇÃO DA IA
-- Apenas admins gerenciam
-- =====================================================
ALTER TABLE config_ia ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Todos veem config da IA"
ON config_ia FOR SELECT
USING (empresa_id = auth.empresa_id());

CREATE POLICY "Apenas admins atualizam config da IA"
ON config_ia FOR UPDATE
USING (
  empresa_id = auth.empresa_id() AND
  auth.user_role() = 'admin'
);

-- =====================================================
-- EVENTOS (AUDITORIA)
-- Todos da empresa podem ver eventos
-- =====================================================
ALTER TABLE eventos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem eventos da empresa"
ON eventos FOR SELECT
USING (empresa_id = auth.empresa_id());

CREATE POLICY "Sistema pode inserir eventos"
ON eventos FOR INSERT
WITH CHECK (empresa_id = auth.empresa_id());

-- =====================================================
-- NOTIFICAÇÕES
-- Cada usuário vê apenas suas notificações
-- =====================================================
ALTER TABLE notificacoes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário vê apenas suas notificações"
ON notificacoes FOR SELECT
USING (usuario_id = auth.uid());

CREATE POLICY "Sistema pode criar notificações"
ON notificacoes FOR INSERT
WITH CHECK (empresa_id = auth.empresa_id());

CREATE POLICY "Usuário pode marcar notificação como lida"
ON notificacoes FOR UPDATE
USING (usuario_id = auth.uid());

CREATE POLICY "Usuário pode deletar suas notificações"
ON notificacoes FOR DELETE
USING (usuario_id = auth.uid());

-- =====================================================
-- MÉTRICAS DIÁRIAS
-- Usuários veem métricas da empresa
-- Admins/supervisores veem de todos, agentes só suas
-- =====================================================
ALTER TABLE metricas_diarias ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem métricas relevantes"
ON metricas_diarias FOR SELECT
USING (
  empresa_id = auth.empresa_id() AND
  (
    auth.user_role() IN ('admin', 'supervisor') OR
    usuario_id = auth.uid() OR
    departamento_id = auth.departamento_id()
  )
);

-- =====================================================
-- TEMPLATES DE MENSAGENS
-- Usuários veem templates da empresa
-- =====================================================
ALTER TABLE templates_mensagens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem templates da empresa"
ON templates_mensagens FOR SELECT
USING (
  empresa_id = auth.empresa_id() AND
  (departamento_id IS NULL OR departamento_id = auth.departamento_id())
);

CREATE POLICY "Usuários podem criar templates"
ON templates_mensagens FOR INSERT
WITH CHECK (empresa_id = auth.empresa_id());

CREATE POLICY "Usuário pode atualizar próprios templates"
ON templates_mensagens FOR UPDATE
USING (
  empresa_id = auth.empresa_id() AND
  (criado_por = auth.uid() OR auth.user_role() IN ('admin', 'supervisor'))
);

-- =====================================================
-- GRANTS PARA SERVICE ROLE (BACKEND)
-- O backend usa service_role para operações especiais
-- =====================================================

-- Permitir backend inserir em todas as tabelas
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- =====================================================
-- POLICIES PARA SERVICE ROLE (BYPASS RLS)
-- =====================================================

-- Service role pode fazer tudo (usado pelo backend)
CREATE POLICY "Service role bypass" ON empresas
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON departamentos
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON usuarios
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON leads
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON conversas
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON mensagens
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON transferencias
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON agendamentos_ia
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON config_ia
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON eventos
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON notificacoes
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON metricas_diarias
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role bypass" ON templates_mensagens
  FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =====================================================
-- FIM DAS RLS POLICIES
-- =====================================================

-- =====================================================
-- ALICE MULTIAGENTE - SCHEMA MULTI-TENANT
-- Sistema de atendimento inteligente com múltiplos departamentos
-- Suporta múltiplas empresas (tenants) no mesmo banco
-- =====================================================

-- Habilita extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- =====================================================
-- TABELA 1: EMPRESAS (TENANTS)
-- Cada cliente seu terá uma empresa
-- =====================================================
CREATE TABLE empresas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- IDENTIFICAÇÃO
  nome TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL, -- usado na URL: app.seudominio.com/lcbaterias
  cnpj TEXT,

  -- CUSTOMIZAÇÃO
  logo_url TEXT,
  cor_primaria TEXT DEFAULT '#3B82F6',
  cor_secundaria TEXT DEFAULT '#10B981',

  -- CONFIGURAÇÕES
  dominio_customizado TEXT, -- Ex: atendimento.lcbaterias.com.br
  whatsapp_numero TEXT,
  email_contato TEXT,

  -- LIMITES E PLANOS
  plano TEXT DEFAULT 'basico', -- 'basico', 'profissional', 'enterprise'
  limite_usuarios INTEGER DEFAULT 5,
  limite_conversas_mes INTEGER DEFAULT 1000,

  -- STATUS
  ativo BOOLEAN DEFAULT true,
  data_expiracao DATE,

  -- METADADOS
  configuracoes JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_empresas_slug ON empresas(slug);
CREATE INDEX idx_empresas_ativo ON empresas(ativo);

-- =====================================================
-- TABELA 2: DEPARTAMENTOS
-- =====================================================
CREATE TABLE departamentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,

  -- IDENTIFICAÇÃO
  nome TEXT NOT NULL, -- 'Vendas', 'Financeiro', etc
  slug TEXT NOT NULL, -- 'vendas', 'financeiro'
  descricao TEXT,

  -- APARÊNCIA
  cor_primaria TEXT DEFAULT '#3B82F6',
  icone TEXT DEFAULT 'users', -- nome do ícone lucide

  -- CONFIGURAÇÕES
  email_notificacao TEXT,
  horario_atendimento JSONB DEFAULT '{"seg_sex": "08:00-18:00", "sab": "08:00-12:00", "dom": "fechado"}',
  mensagem_fora_horario TEXT,

  -- ORDEM E STATUS
  ordem INTEGER DEFAULT 0, -- para ordenar na interface
  ativo BOOLEAN DEFAULT true,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Garante que não haja departamentos duplicados na mesma empresa
  UNIQUE(empresa_id, slug)
);

-- Índices
CREATE INDEX idx_departamentos_empresa ON departamentos(empresa_id);
CREATE INDEX idx_departamentos_ativo ON departamentos(ativo);

-- =====================================================
-- TABELA 3: USUÁRIOS (AGENTES HUMANOS)
-- Integração com Supabase Auth
-- =====================================================
CREATE TABLE usuarios (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  departamento_id UUID REFERENCES departamentos(id),

  -- PERFIL
  nome_completo TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  cargo TEXT, -- 'Gerente', 'Atendente', 'Supervisor'
  avatar_url TEXT,

  -- PERMISSÕES
  role TEXT DEFAULT 'agente', -- 'admin', 'supervisor', 'agente'
  pode_transferir BOOLEAN DEFAULT true,
  pode_encerrar BOOLEAN DEFAULT true,
  pode_ver_todos_departamentos BOOLEAN DEFAULT false,

  -- STATUS EM TEMPO REAL
  status TEXT DEFAULT 'offline', -- 'online', 'ausente', 'ocupado', 'offline'
  ultimo_online TIMESTAMPTZ,
  ultimo_heartbeat TIMESTAMPTZ,

  -- CONFIGURAÇÕES PESSOAIS
  configuracoes JSONB DEFAULT '{
    "notificacoes_som": true,
    "notificacoes_desktop": true,
    "notificacoes_email": false,
    "idioma": "pt-BR",
    "tema": "light"
  }',

  -- METADADOS
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  ultimo_login TIMESTAMPTZ
);

-- Índices
CREATE INDEX idx_usuarios_empresa ON usuarios(empresa_id);
CREATE INDEX idx_usuarios_departamento ON usuarios(departamento_id);
CREATE INDEX idx_usuarios_status ON usuarios(status);
CREATE INDEX idx_usuarios_email ON usuarios(email);

-- =====================================================
-- TABELA 4: LEADS (CLIENTES FINAIS)
-- =====================================================
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,

  -- IDENTIFICAÇÃO
  telefone TEXT NOT NULL,
  nome TEXT,
  email TEXT,

  -- DADOS ADICIONAIS
  cpf_cnpj TEXT,
  empresa TEXT,
  cargo TEXT,
  cidade TEXT,
  estado TEXT,
  dados_extras JSONB DEFAULT '{}', -- flexível para qualquer dado

  -- CLASSIFICAÇÃO
  tags TEXT[] DEFAULT '{}',
  segmento TEXT, -- 'VIP', 'Padrão', 'Bronze', etc
  origem TEXT, -- 'whatsapp', 'site', 'instagram', 'indicacao'

  -- RELACIONAMENTO
  responsavel_id UUID REFERENCES usuarios(id), -- vendedor/atendente principal

  -- ENGAJAMENTO
  conversas_total INTEGER DEFAULT 0,
  ultima_interacao TIMESTAMPTZ DEFAULT NOW(),
  primeira_interacao TIMESTAMPTZ DEFAULT NOW(),

  -- STATUS
  bloqueado BOOLEAN DEFAULT false,
  motivo_bloqueio TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Garante telefone único por empresa
  UNIQUE(empresa_id, telefone)
);

-- Índices
CREATE INDEX idx_leads_empresa ON leads(empresa_id);
CREATE INDEX idx_leads_telefone ON leads(telefone);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_tags ON leads USING GIN(tags);
CREATE INDEX idx_leads_ultima_interacao ON leads(ultima_interacao DESC);

-- =====================================================
-- TABELA 5: CONVERSAS
-- =====================================================
CREATE TABLE conversas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  lead_id UUID REFERENCES leads(id) NOT NULL,
  departamento_id UUID REFERENCES departamentos(id),
  usuario_atribuido_id UUID REFERENCES usuarios(id),

  -- ESTADOS
  status TEXT DEFAULT 'nova', -- 'nova', 'em_atendimento', 'aguardando_lead', 'resolvida', 'arquivada'
  modo_ia TEXT DEFAULT 'ativo', -- 'ativo', 'pausado', 'desligado'
  origem TEXT DEFAULT 'whatsapp', -- 'whatsapp', 'web', 'telegram', 'instagram'

  -- PRIORIDADE E CLASSIFICAÇÃO
  prioridade TEXT DEFAULT 'normal', -- 'baixa', 'normal', 'alta', 'urgente'
  tags TEXT[] DEFAULT '{}',
  categoria TEXT, -- 'duvida', 'reclamacao', 'elogio', 'venda', etc

  -- MÉTRICAS DE ATENDIMENTO
  primeira_resposta_em TIMESTAMPTZ,
  tempo_primeira_resposta INTERVAL,
  resolvida_em TIMESTAMPTZ,
  tempo_resolucao INTERVAL,
  tempo_espera_total INTERVAL DEFAULT '0 seconds',

  -- CONTADORES
  mensagens_total INTEGER DEFAULT 0,
  mensagens_ia INTEGER DEFAULT 0,
  mensagens_humano INTEGER DEFAULT 0,
  mensagens_lead INTEGER DEFAULT 0,
  transferencias INTEGER DEFAULT 0,

  -- SATISFAÇÃO
  avaliacao INTEGER, -- 1 a 5 estrelas
  avaliacao_comentario TEXT,
  avaliacao_em TIMESTAMPTZ,

  -- METADADOS
  ultima_mensagem_em TIMESTAMPTZ,
  ultima_mensagem_preview TEXT, -- preview para lista
  notas_internas TEXT, -- notas privadas dos agentes
  contexto_ia JSONB DEFAULT '{}', -- contexto da conversa para IA

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_conversas_empresa ON conversas(empresa_id);
CREATE INDEX idx_conversas_lead ON conversas(lead_id);
CREATE INDEX idx_conversas_departamento ON conversas(departamento_id);
CREATE INDEX idx_conversas_usuario ON conversas(usuario_atribuido_id);
CREATE INDEX idx_conversas_status ON conversas(status);
CREATE INDEX idx_conversas_modo_ia ON conversas(modo_ia);
CREATE INDEX idx_conversas_prioridade ON conversas(prioridade);
CREATE INDEX idx_conversas_ultima_mensagem ON conversas(ultima_mensagem_em DESC);
CREATE INDEX idx_conversas_tags ON conversas USING GIN(tags);

-- =====================================================
-- TABELA 6: MENSAGENS
-- =====================================================
CREATE TABLE mensagens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  conversa_id UUID REFERENCES conversas(id) ON DELETE CASCADE,

  -- AUTORIA
  tipo TEXT NOT NULL, -- 'lead', 'ia', 'humano', 'sistema'
  usuario_id UUID REFERENCES usuarios(id), -- NULL se for IA ou lead

  -- CONTEÚDO
  conteudo TEXT NOT NULL,
  conteudo_original TEXT, -- se foi editado

  -- MÍDIA
  tipo_midia TEXT DEFAULT 'texto', -- 'texto', 'audio', 'imagem', 'documento', 'video'
  midia_url TEXT,
  midia_metadata JSONB DEFAULT '{}', -- tamanho, duração, etc

  -- STATUS IA (apenas para mensagens tipo 'ia')
  status_ia TEXT, -- 'sugerida', 'aprovada', 'editada', 'recusada'
  aprovada_por UUID REFERENCES usuarios(id),
  aprovada_em TIMESTAMPTZ,
  tempo_aprovacao INTERVAL,

  -- RASTREAMENTO
  lida BOOLEAN DEFAULT false,
  lida_em TIMESTAMPTZ,
  entregue BOOLEAN DEFAULT false,
  entregue_em TIMESTAMPTZ,

  -- RESPOSTA A OUTRA MENSAGEM (threading)
  responde_mensagem_id UUID REFERENCES mensagens(id),

  -- METADADOS
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_mensagens_empresa ON mensagens(empresa_id);
CREATE INDEX idx_mensagens_conversa ON mensagens(conversa_id);
CREATE INDEX idx_mensagens_tipo ON mensagens(tipo);
CREATE INDEX idx_mensagens_status_ia ON mensagens(status_ia);
CREATE INDEX idx_mensagens_created ON mensagens(created_at DESC);

-- =====================================================
-- TABELA 7: TRANSFERÊNCIAS (HISTÓRICO)
-- =====================================================
CREATE TABLE transferencias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  conversa_id UUID REFERENCES conversas(id) ON DELETE CASCADE,

  -- ORIGEM
  departamento_origem_id UUID REFERENCES departamentos(id),
  usuario_origem_id UUID REFERENCES usuarios(id),

  -- DESTINO
  departamento_destino_id UUID REFERENCES departamentos(id) NOT NULL,
  usuario_destino_id UUID REFERENCES usuarios(id),

  -- INFORMAÇÕES DA TRANSFERÊNCIA
  tipo TEXT NOT NULL, -- 'automatica_ia', 'manual_agente', 'round_robin', 'escalacao'
  motivo TEXT NOT NULL, -- 'solicitacao_lead', 'escalacao', 'distribuicao', 'ausencia'
  observacao TEXT,

  -- RASTREAMENTO
  transferido_por UUID REFERENCES usuarios(id), -- NULL se foi IA
  transferido_em TIMESTAMPTZ DEFAULT NOW(),
  aceita_em TIMESTAMPTZ,
  tempo_aceitacao INTERVAL
);

-- Índices
CREATE INDEX idx_transferencias_empresa ON transferencias(empresa_id);
CREATE INDEX idx_transferencias_conversa ON transferencias(conversa_id);
CREATE INDEX idx_transferencias_tipo ON transferencias(tipo);

-- =====================================================
-- TABELA 8: AGENDAMENTOS DA IA
-- =====================================================
CREATE TABLE agendamentos_ia (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  departamento_id UUID REFERENCES departamentos(id), -- NULL = todos departamentos

  -- NOME E DESCRIÇÃO
  nome TEXT NOT NULL,
  descricao TEXT,

  -- HORÁRIOS
  hora_ligar TIME NOT NULL, -- '08:00:00'
  hora_desligar TIME NOT NULL, -- '18:00:00'
  dias_semana INTEGER[] DEFAULT '{1,2,3,4,5}', -- 1=segunda, 7=domingo
  fuso_horario TEXT DEFAULT 'America/Sao_Paulo',

  -- COMPORTAMENTO
  modo_dentro_horario TEXT DEFAULT 'atencao', -- 'ligado', 'atencao', 'desligado'
  modo_fora_horario TEXT DEFAULT 'desligado',
  mensagem_auto_fora_horario TEXT DEFAULT 'Olá! Nosso horário de atendimento é de segunda a sexta, das 8h às 18h.',

  -- EXCEÇÕES (feriados, datas específicas)
  excecoes JSONB DEFAULT '[]', -- [{"data": "2025-12-25", "ativo": false, "motivo": "Natal"}]

  -- STATUS
  ativo BOOLEAN DEFAULT true,
  prioridade INTEGER DEFAULT 0, -- maior prioridade prevalece

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_agendamentos_empresa ON agendamentos_ia(empresa_id);
CREATE INDEX idx_agendamentos_departamento ON agendamentos_ia(departamento_id);
CREATE INDEX idx_agendamentos_ativo ON agendamentos_ia(ativo);

-- =====================================================
-- TABELA 9: CONFIGURAÇÃO DA IA
-- Uma configuração por empresa
-- =====================================================
CREATE TABLE config_ia (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE UNIQUE,

  -- MODO GERAL
  modo_geral TEXT DEFAULT 'atencao', -- 'ligado', 'atencao', 'desligado'
  agendamento_ativo BOOLEAN DEFAULT true,

  -- MODELO E PARÂMETROS
  modelo_ia TEXT DEFAULT 'gpt-4o',
  temperatura DECIMAL DEFAULT 0.7,
  max_tokens INTEGER DEFAULT 4096,

  -- PROMPTS
  prompt_sistema TEXT DEFAULT 'Você é a Alice, assistente inteligente de atendimento ao cliente.',
  prompt_vendas TEXT,
  prompt_financeiro TEXT,
  prompt_tecnico TEXT,
  prompt_suporte TEXT,

  -- DETECÇÃO DE INTENÇÃO
  palavras_chave_vendas TEXT[] DEFAULT '{"quero comprar", "preço", "valor", "orçamento"}',
  palavras_chave_financeiro TEXT[] DEFAULT '{"boleto", "pagamento", "fatura", "financeiro"}',
  palavras_chave_tecnico TEXT[] DEFAULT '{"suporte", "problema", "não funciona", "erro"}',
  palavras_chave_ti TEXT[] DEFAULT '{"sistema", "login", "senha", "acesso"}',

  -- COMPORTAMENTOS
  auto_aprovar_simples BOOLEAN DEFAULT false, -- aprova automaticamente mensagens simples
  requer_aprovacao_sempre BOOLEAN DEFAULT true,
  timeout_inatividade INTEGER DEFAULT 30, -- minutos
  mensagem_timeout TEXT,

  -- INTEGRAÇÕES
  whatsapp_api_url TEXT,
  whatsapp_api_key TEXT,

  updated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_by UUID REFERENCES usuarios(id)
);

-- Índice
CREATE INDEX idx_config_ia_empresa ON config_ia(empresa_id);

-- =====================================================
-- TABELA 10: EVENTOS DO SISTEMA (AUDITORIA)
-- =====================================================
CREATE TABLE eventos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,

  -- TIPO E ENTIDADE
  tipo TEXT NOT NULL, -- 'ia_pausada', 'ia_retomada', 'transferencia', 'login', 'config_alterada'
  categoria TEXT NOT NULL, -- 'sistema', 'usuario', 'ia', 'conversa', 'admin'
  entidade TEXT, -- 'conversa', 'usuario', 'departamento', 'empresa'
  entidade_id UUID,

  -- AUTOR
  usuario_id UUID REFERENCES usuarios(id), -- NULL se foi sistema/IA

  -- DADOS DO EVENTO
  titulo TEXT NOT NULL,
  descricao TEXT,
  dados JSONB DEFAULT '{}',

  -- METADADOS
  ip_address INET,
  user_agent TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_eventos_empresa ON eventos(empresa_id);
CREATE INDEX idx_eventos_tipo ON eventos(tipo);
CREATE INDEX idx_eventos_categoria ON eventos(categoria);
CREATE INDEX idx_eventos_usuario ON eventos(usuario_id);
CREATE INDEX idx_eventos_created ON eventos(created_at DESC);

-- =====================================================
-- TABELA 11: NOTIFICAÇÕES
-- =====================================================
CREATE TABLE notificacoes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,

  -- CONTEÚDO
  tipo TEXT NOT NULL, -- 'nova_mensagem', 'transferencia', 'mencao', 'sistema'
  prioridade TEXT DEFAULT 'normal', -- 'baixa', 'normal', 'alta', 'urgente'
  titulo TEXT NOT NULL,
  mensagem TEXT,
  icone TEXT, -- nome do ícone lucide

  -- AÇÃO
  link TEXT, -- URL para onde clicar
  acao_primaria TEXT, -- texto do botão
  acao_primaria_url TEXT,

  -- STATUS
  lida BOOLEAN DEFAULT false,
  lida_em TIMESTAMPTZ,
  enviada_por_email BOOLEAN DEFAULT false,
  enviada_push BOOLEAN DEFAULT false,

  -- AGRUPAMENTO (para notificações similares)
  grupo TEXT,

  -- EXPIRAÇÃO
  expira_em TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_notificacoes_empresa ON notificacoes(empresa_id);
CREATE INDEX idx_notificacoes_usuario ON notificacoes(usuario_id);
CREATE INDEX idx_notificacoes_lida ON notificacoes(lida);
CREATE INDEX idx_notificacoes_tipo ON notificacoes(tipo);
CREATE INDEX idx_notificacoes_created ON notificacoes(created_at DESC);

-- =====================================================
-- TABELA 12: MÉTRICAS AGREGADAS (CACHE)
-- Para dashboard performance
-- =====================================================
CREATE TABLE metricas_diarias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  departamento_id UUID REFERENCES departamentos(id),
  usuario_id UUID REFERENCES usuarios(id),

  data DATE NOT NULL,

  -- CONVERSAS
  conversas_novas INTEGER DEFAULT 0,
  conversas_resolvidas INTEGER DEFAULT 0,
  conversas_abertas INTEGER DEFAULT 0,
  conversas_transferidas INTEGER DEFAULT 0,

  -- MENSAGENS
  mensagens_total INTEGER DEFAULT 0,
  mensagens_ia INTEGER DEFAULT 0,
  mensagens_humano INTEGER DEFAULT 0,
  mensagens_aprovadas INTEGER DEFAULT 0,
  mensagens_recusadas INTEGER DEFAULT 0,

  -- TEMPOS MÉDIOS
  tempo_medio_primeira_resposta INTERVAL,
  tempo_medio_resolucao INTERVAL,
  tempo_medio_aprovacao_ia INTERVAL,

  -- SATISFAÇÃO
  avaliacoes_total INTEGER DEFAULT 0,
  avaliacoes_soma INTEGER DEFAULT 0,
  avaliacoes_media DECIMAL,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Garante uma métrica por dia/empresa/departamento/usuário
  UNIQUE(empresa_id, departamento_id, usuario_id, data)
);

-- Índices
CREATE INDEX idx_metricas_empresa ON metricas_diarias(empresa_id);
CREATE INDEX idx_metricas_departamento ON metricas_diarias(departamento_id);
CREATE INDEX idx_metricas_usuario ON metricas_diarias(usuario_id);
CREATE INDEX idx_metricas_data ON metricas_diarias(data DESC);

-- =====================================================
-- TABELA 13: TEMPLATES DE MENSAGENS
-- =====================================================
CREATE TABLE templates_mensagens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  departamento_id UUID REFERENCES departamentos(id), -- NULL = disponível para todos

  -- IDENTIFICAÇÃO
  nome TEXT NOT NULL,
  atalho TEXT, -- ex: /orcamento, /boas-vindas
  categoria TEXT, -- 'saudacao', 'despedida', 'faq', 'vendas'

  -- CONTEÚDO
  conteudo TEXT NOT NULL,
  variaveis TEXT[] DEFAULT '{}', -- {nome_lead}, {nome_empresa}, etc

  -- MÍDIA ANEXA (opcional)
  midia_url TEXT,
  midia_tipo TEXT,

  -- USO
  vezes_usado INTEGER DEFAULT 0,
  ultimo_uso TIMESTAMPTZ,

  -- STATUS
  ativo BOOLEAN DEFAULT true,
  criado_por UUID REFERENCES usuarios(id),

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_templates_empresa ON templates_mensagens(empresa_id);
CREATE INDEX idx_templates_departamento ON templates_mensagens(departamento_id);
CREATE INDEX idx_templates_atalho ON templates_mensagens(atalho);

-- =====================================================
-- FIM DO SCHEMA PRINCIPAL
-- =====================================================

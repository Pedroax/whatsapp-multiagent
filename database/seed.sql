-- =====================================================
-- SEED DATA - Dados Iniciais para Desenvolvimento
-- Cria empresa demo (LC Baterias) com estrutura completa
-- =====================================================

-- =====================================================
-- 1. CRIAR EMPRESA DEMO
-- =====================================================
INSERT INTO empresas (id, nome, slug, cnpj, logo_url, cor_primaria, cor_secundaria, plano, limite_usuarios, limite_conversas_mes, whatsapp_numero, email_contato, ativo)
VALUES (
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f', -- ID fixo para referência
  'LC Baterias',
  'lcbaterias',
  '12.345.678/0001-90',
  'https://placehold.co/200x200/3B82F6/FFFFFF/png?text=LC',
  '#3B82F6',
  '#10B981',
  'profissional',
  15,
  5000,
  '+5561999999999',
  'contato@lcbaterias.com.br',
  true
) ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 2. CRIAR DEPARTAMENTOS
-- =====================================================
INSERT INTO departamentos (id, empresa_id, nome, slug, descricao, cor_primaria, icone, email_notificacao, ordem, ativo) VALUES
(
  '10000000-0000-0000-0000-000000000001',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  'Vendas',
  'vendas',
  'Atendimento comercial e vendas de baterias',
  '#3B82F6',
  'shopping-cart',
  'vendas@lcbaterias.com.br',
  1,
  true
),
(
  '10000000-0000-0000-0000-000000000002',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  'Assistência Técnica',
  'assistencia-tecnica',
  'Suporte técnico e manutenção de baterias',
  '#F59E0B',
  'wrench',
  'tecnico@lcbaterias.com.br',
  2,
  true
),
(
  '10000000-0000-0000-0000-000000000003',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  'Financeiro',
  'financeiro',
  'Contas a receber, pagamentos e cobranças',
  '#10B981',
  'dollar-sign',
  'financeiro@lcbaterias.com.br',
  3,
  true
),
(
  '10000000-0000-0000-0000-000000000004',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  'Suporte TI',
  'suporte-ti',
  'Suporte de sistemas e tecnologia',
  '#8B5CF6',
  'monitor',
  'ti@lcbaterias.com.br',
  4,
  true
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 3. CRIAR CONFIGURAÇÃO DA IA
-- =====================================================
INSERT INTO config_ia (
  id,
  empresa_id,
  modo_geral,
  agendamento_ativo,
  modelo_ia,
  temperatura,
  max_tokens,
  prompt_sistema,
  prompt_vendas,
  prompt_financeiro,
  prompt_tecnico,
  prompt_suporte,
  palavras_chave_vendas,
  palavras_chave_financeiro,
  palavras_chave_tecnico,
  palavras_chave_ti,
  auto_aprovar_simples,
  requer_aprovacao_sempre,
  timeout_inatividade
) VALUES (
  '20000000-0000-0000-0000-000000000001',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  'atencao',
  true,
  'gpt-4o',
  0.7,
  4096,
  'Você é a Alice, assistente inteligente da LC Baterias. Seja cordial, profissional e prestativa. Quando não souber algo, transfira para um atendente humano.',
  'Você está atendendo como departamento de VENDAS. Ajude o cliente com informações sobre produtos, preços, condições de pagamento e fechamento de vendas.',
  'Você está atendendo como departamento FINANCEIRO. Ajude com questões de pagamentos, boletos, faturas e cobranças.',
  'Você está atendendo como ASSISTÊNCIA TÉCNICA. Ajude com problemas técnicos, garantias e manutenções.',
  'Você está atendendo como SUPORTE TI. Ajude com problemas de sistema, login e acesso.',
  ARRAY['quero comprar', 'preço', 'valor', 'orçamento', 'quanto custa', 'venda', 'produto', 'bateria'],
  ARRAY['boleto', 'pagamento', 'fatura', 'financeiro', 'pagar', 'valor', 'nota fiscal', 'cobrança'],
  ARRAY['suporte', 'problema', 'não funciona', 'erro', 'defeito', 'garantia', 'técnico', 'assistência'],
  ARRAY['sistema', 'login', 'senha', 'acesso', 'computador', 'ti', 'tecnologia'],
  false,
  true,
  30
) ON CONFLICT (empresa_id) DO NOTHING;

-- =====================================================
-- 4. CRIAR AGENDAMENTO PADRÃO (SEG-SEX 8h-18h)
-- =====================================================
INSERT INTO agendamentos_ia (
  empresa_id,
  nome,
  descricao,
  hora_ligar,
  hora_desligar,
  dias_semana,
  fuso_horario,
  modo_dentro_horario,
  modo_fora_horario,
  mensagem_auto_fora_horario,
  ativo,
  prioridade
) VALUES (
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  'Horário Comercial',
  'Atendimento de segunda a sexta, das 8h às 18h',
  '08:00:00',
  '18:00:00',
  ARRAY[1,2,3,4,5],
  'America/Sao_Paulo',
  'atencao',
  'desligado',
  'Olá! Nosso horário de atendimento é de segunda a sexta, das 8h às 18h. Deixe sua mensagem que responderemos assim que possível!',
  true,
  1
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 5. CRIAR TEMPLATES DE MENSAGENS
-- =====================================================
INSERT INTO templates_mensagens (empresa_id, departamento_id, nome, atalho, categoria, conteudo, variaveis, ativo) VALUES
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  NULL,
  'Boas-vindas',
  '/boasvindas',
  'saudacao',
  'Olá {nome_lead}! 👋 Seja bem-vindo(a) à LC Baterias! Como posso ajudar você hoje?',
  ARRAY['nome_lead'],
  true
),
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '10000000-0000-0000-0000-000000000001',
  'Consulta de Estoque',
  '/estoque',
  'vendas',
  'Vou verificar a disponibilidade em estoque para você. Aguarde um momento! 🔍',
  ARRAY[],
  true
),
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '10000000-0000-0000-0000-000000000001',
  'Orçamento',
  '/orcamento',
  'vendas',
  '{nome_lead}, vou preparar um orçamento personalizado para você. Pode me informar:\n\n1. Modelo da bateria desejada\n2. Quantidade\n3. CEP para cálculo do frete',
  ARRAY['nome_lead'],
  true
),
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '10000000-0000-0000-0000-000000000003',
  'Envio de Boleto',
  '/boleto',
  'financeiro',
  'Para enviar o boleto, preciso confirmar alguns dados:\n\n📧 Email: ______\n🆔 CPF/CNPJ: ______\n\nPode me confirmar essas informações?',
  ARRAY[],
  true
),
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '10000000-0000-0000-0000-000000000002',
  'Agendar Visita Técnica',
  '/agendar',
  'tecnico',
  'Vou agendar a visita técnica! 🔧\n\nPara qual data e horário você prefere?\n\nObs: Atendemos de segunda a sexta, das 8h às 18h.',
  ARRAY[],
  true
),
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  NULL,
  'Despedida',
  '/tchau',
  'despedida',
  'Foi um prazer atender você, {nome_lead}! 😊\n\nSe precisar de mais alguma coisa, estou por aqui!\n\nAté breve! 👋',
  ARRAY['nome_lead'],
  true
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 6. CRIAR LEADS DE EXEMPLO
-- =====================================================
INSERT INTO leads (id, empresa_id, telefone, nome, email, cidade, estado, tags, segmento, origem) VALUES
(
  '30000000-0000-0000-0000-000000000001',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '+5561999887766',
  'João Silva',
  'joao.silva@email.com',
  'Brasília',
  'DF',
  ARRAY['vip', 'recorrente'],
  'VIP',
  'whatsapp'
),
(
  '30000000-0000-0000-0000-000000000002',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '+5561988776655',
  'Maria Santos',
  'maria.santos@email.com',
  'Brasília',
  'DF',
  ARRAY['novo'],
  'Padrão',
  'site'
),
(
  '30000000-0000-0000-0000-000000000003',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '+5561977665544',
  'Pedro Oliveira',
  'pedro.oliveira@empresa.com',
  'Taguatinga',
  'DF',
  ARRAY['empresarial'],
  'Padrão',
  'indicacao'
) ON CONFLICT DO NOTHING;

-- =====================================================
-- NOTA: USUÁRIOS DEVEM SER CRIADOS VIA SUPABASE AUTH
-- Não inserimos aqui pois precisam ser criados via API
-- =====================================================

-- Para criar usuários de teste, usar:
-- 1. Cadastro via Supabase Auth Dashboard
-- 2. Ou via API de signup do backend
-- 3. Depois vincular na tabela usuarios com empresa_id e departamento_id

-- =====================================================
-- EXEMPLO DE CONVERSAS E MENSAGENS (OPCIONAL)
-- Descomente para ter dados de exemplo
-- =====================================================

/*
-- Conversa 1: João Silva com Vendas
INSERT INTO conversas (id, empresa_id, lead_id, departamento_id, status, modo_ia, origem, prioridade) VALUES
(
  '40000000-0000-0000-0000-000000000001',
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '30000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'em_atendimento',
  'ativo',
  'whatsapp',
  'alta'
);

-- Mensagens da conversa 1
INSERT INTO mensagens (empresa_id, conversa_id, tipo, conteudo, tipo_midia) VALUES
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '40000000-0000-0000-0000-000000000001',
  'lead',
  'Olá! Preciso de uma bateria de 60 amperes',
  'texto'
),
(
  'c0a80121-7ac0-4f3c-89d0-6f8e4c3b5a9f',
  '40000000-0000-0000-0000-000000000001',
  'ia',
  'Olá João! Temos excelentes opções de baterias de 60Ah. Você prefere selada ou livre?',
  'texto'
);
*/

-- =====================================================
-- FIM DO SEED
-- =====================================================

-- Mensagem de sucesso
DO $$
BEGIN
  RAISE NOTICE '✅ Seed concluído com sucesso!';
  RAISE NOTICE '📊 Empresa criada: LC Baterias (slug: lcbaterias)';
  RAISE NOTICE '🏢 4 Departamentos criados';
  RAISE NOTICE '⚙️  Configuração da IA definida';
  RAISE NOTICE '⏰ Agendamento de horário criado';
  RAISE NOTICE '📝 Templates de mensagens adicionados';
  RAISE NOTICE '👥 3 Leads de exemplo criados';
  RAISE NOTICE '';
  RAISE NOTICE '⚠️  PRÓXIMO PASSO: Criar usuários via Supabase Auth';
END $$;

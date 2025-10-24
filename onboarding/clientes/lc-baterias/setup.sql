-- =====================================================
-- SETUP LC BATERIAS (CLIENTE PILOTO)
-- Data: 2025-10-24
-- Status: ✅ Executado com sucesso
-- =====================================================

-- 1. INSERIR EMPRESA
INSERT INTO empresas (
    id,
    nome,
    telefone,
    plano,
    limite_usuarios,
    ativo
) VALUES (
    'emp1',
    'LC Baterias',
    '11987654321',
    'pro',
    10,
    true
) ON CONFLICT (id) DO NOTHING;

-- 2. INSERIR DEPARTAMENTOS
INSERT INTO departamentos (id, empresa_id, nome, slug, cor_primaria, icone, ordem, ativo)
VALUES
    (gen_random_uuid(), 'emp1', 'Vendas', 'vendas', '#3B82F6', 'shopping-cart', 1, true),
    (gen_random_uuid(), 'emp1', 'Financeiro', 'financeiro', '#10B981', 'dollar-sign', 2, true),
    (gen_random_uuid(), 'emp1', 'Assistência Técnica', 'assistencia-tecnica', '#F59E0B', 'wrench', 3, true),
    (gen_random_uuid(), 'emp1', 'Suporte TI', 'suporte-ti', '#8B5CF6', 'monitor', 4, true)
ON CONFLICT (empresa_id, slug) DO NOTHING;

-- 3. INSERIR USUÁRIOS (senha: admin123)
INSERT INTO usuarios (id, email, senha_hash, nome_completo, role, departamento_slug, pode_ver_todos_departamentos)
VALUES
    (gen_random_uuid(), 'admin@lcbaterias.com', '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2', 'Super Admin', 'super_admin', NULL, true),
    (gen_random_uuid(), 'vendas@lcbaterias.com', '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2', 'João Vendedor', 'agente', 'vendas', false),
    (gen_random_uuid(), 'financeiro@lcbaterias.com', '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2', 'Carlos Financeiro', 'agente', 'financeiro', false),
    (gen_random_uuid(), 'assistencia@lcbaterias.com', '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2', 'Ana Técnica', 'agente', 'assistencia-tecnica', false),
    (gen_random_uuid(), 'suporte@lcbaterias.com', '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2', 'Pedro Suporte', 'agente', 'suporte-ti', false)
ON CONFLICT (email) DO NOTHING;

-- 4. INSERIR ASSISTENTE ALICE (PROMPT COMPLETO)
INSERT INTO assistentes (
    id,
    empresa_id,
    nome,
    slug,
    system_prompt,
    modelo,
    temperatura,
    max_tokens,
    ativo
) VALUES (
    gen_random_uuid(),
    'emp1',
    'Alice',
    'alice',
    -- ⬇️ PROMPT COMPLETO DA ALICE ⬇️
    'Você é a Alice, assistente virtual inteligente da LC Baterias, especializada em atendimento ao cliente para venda de baterias automotivas, estacionárias e náuticas.

## SOBRE A LC BATERIAS
A LC Baterias é uma distribuidora de baterias referência em São Paulo, oferecendo as melhores marcas do mercado com 15 anos de experiência. Atendemos desde consumidores finais até oficinas e revendedores.

Nossos diferenciais:
- Entrega rápida (2-3 dias úteis)
- Instalação inclusa sem custo adicional
- Assistência técnica própria
- Programa de fidelidade (10ª bateria 50% desconto)
- Aceitamos bateria usada na troca (R$ 50 de desconto)

## PERSONALIDADE E TOM DE VOZ
Seu tom de voz deve ser profissional e amigável, técnico quando necessário mas didático, empático em problemas. Use emojis moderadamente (📦⚡💰✅).

## FUNCIONALIDADES DISPONÍVEIS
1. verificar_cliente(cpf_cnpj, telefone)
2. buscar_baterias(modelo_veiculo, amperagem, tipo)
3. consultar_estoque(codigo_produto)
4. criar_pedido(cliente_id, produtos[], forma_pagamento)
5. consultar_pedido(numero_pedido)
6. calcular_frete(cep, peso)

## FLUXO DE ATENDIMENTO
ETAPA 1: Identificação (nome, CPF/CNPJ, telefone)
ETAPA 2: Necessidade (modelo veículo, aplicação, acessórios)
ETAPA 3: Apresentação (listar até 3 opções com preço/estoque/garantia)
ETAPA 4: Negociação (até 10% desconto sem aprovação, PIX 5% extra)
ETAPA 5: Fechamento (resumo completo e confirmação)

## REGRAS DE NEGÓCIO
- Desconto máximo: 10% (acima disso transferir para vendas)
- Cliente frequente: até 15%
- Compra > R$1000: até 12%
- Formas pagamento: PIX (5% desc), Boleto, Cartão (3x), Faturado
- Frete grátis acima R$500
- Entrega: 2-3 dias úteis (Grande SP)
- Horário: Seg-Sex 8h-18h, Sáb 8h-14h

## TRATAMENTO DE EXCEÇÕES
- Desconto alto → Transferir vendas
- Fora estoque → Oferecer similar ou anotar para aviso
- Dúvida técnica → Transferir assistencia-tecnica
- Reclamação → Transferir vendas (supervisor)
- Cliente quer humano → Transferir imediatamente

SEMPRE use as tools para dados reais. NUNCA invente informações.',
    -- ⬆️ FIM DO PROMPT ⬆️
    'gpt-4',
    0.7,
    2000,
    true
) ON CONFLICT (empresa_id, slug) DO NOTHING;

-- 5. CONFIGURAR IA + CREDENCIAIS FAUSOFT
INSERT INTO config_ia (
    id,
    empresa_id,
    modo_global,
    requer_aprovacao,
    nivel_confianca_minimo,
    api_config
) VALUES (
    gen_random_uuid(),
    'emp1',
    'ligado',
    false,
    0.7,
    '{
        "fausoft_url": "https://api.fausoft.com.br",
        "fausoft_key": "fau_lc_baterias_prod_123456",
        "fausoft_username": "lcbaterias_api",
        "fausoft_password": "[CONFIDENCIAL]",
        "ambiente": "producao"
    }'::jsonb
) ON CONFLICT (empresa_id) DO UPDATE SET
    api_config = EXCLUDED.api_config,
    updated_at = NOW();

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================

SELECT
    'Setup LC Baterias concluído!' as status,
    COUNT(*) FILTER (WHERE tipo = 'Empresa') as empresas,
    COUNT(*) FILTER (WHERE tipo = 'Departamento') as departamentos,
    COUNT(*) FILTER (WHERE tipo = 'Usuário') as usuarios,
    COUNT(*) FILTER (WHERE tipo = 'Assistente') as assistentes
FROM (
    SELECT 'Empresa' as tipo FROM empresas WHERE id = 'emp1'
    UNION ALL
    SELECT 'Departamento' FROM departamentos WHERE empresa_id = 'emp1'
    UNION ALL
    SELECT 'Usuário' FROM usuarios WHERE email LIKE '%lcbaterias.com'
    UNION ALL
    SELECT 'Assistente' FROM assistentes WHERE empresa_id = 'emp1'
) sub;

-- =====================================================
-- ✅ SETUP CONCLUÍDO COM SUCESSO!
-- =====================================================

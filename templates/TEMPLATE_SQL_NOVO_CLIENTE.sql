-- =====================================================
-- TEMPLATE SQL - NOVO CLIENTE
-- =====================================================
--
-- INSTRUÇÕES:
-- 1. Substitua todos os campos entre [COLCHETES]
-- 2. Cole o prompt gerado no Claude Code no campo [PROMPT]
-- 3. Execute no Supabase SQL Editor
-- 4. Verifique se não há erros
--
-- DICA: Faça backup antes: pg_dump -t empresas > backup.sql
-- =====================================================

-- =====================================================
-- 1. INSERIR EMPRESA
-- =====================================================

INSERT INTO empresas (
    id,
    nome,
    telefone,
    plano,
    limite_usuarios,
    ativo,
    created_at
) VALUES (
    '[SLUG_EMPRESA]',  -- ex: 'emp_baterias_brasilia', 'emp_power_cell'
    '[NOME_COMPLETO_EMPRESA]',  -- ex: 'Baterias Brasília Ltda'
    '[TELEFONE]',  -- ex: '6132345678'
    'pro',  -- ou 'free', 'enterprise'
    10,  -- limite de usuários
    true,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Verificar se foi inserido
SELECT * FROM empresas WHERE id = '[SLUG_EMPRESA]';

-- =====================================================
-- 2. INSERIR DEPARTAMENTOS
-- =====================================================

-- Departamento: Vendas (padrão)
INSERT INTO departamentos (
    id,
    empresa_id,
    nome,
    slug,
    cor_primaria,
    icone,
    ordem,
    ativo
) VALUES (
    gen_random_uuid(),
    '[SLUG_EMPRESA]',
    'Vendas',
    'vendas',
    '[COR_PRIMARIA]',  -- ex: '#3B82F6', '#10B981', '#F59E0B'
    'shopping-cart',
    1,
    true
) ON CONFLICT (empresa_id, slug) DO NOTHING;

-- OPCIONAL: Adicionar outros departamentos
-- Descomente se necessário:

/*
-- Departamento: Financeiro
INSERT INTO departamentos (
    id,
    empresa_id,
    nome,
    slug,
    cor_primaria,
    icone,
    ordem,
    ativo
) VALUES (
    gen_random_uuid(),
    '[SLUG_EMPRESA]',
    'Financeiro',
    'financeiro',
    '#10B981',
    'dollar-sign',
    2,
    true
) ON CONFLICT (empresa_id, slug) DO NOTHING;

-- Departamento: Assistência Técnica
INSERT INTO departamentos (
    id,
    empresa_id,
    nome,
    slug,
    cor_primaria,
    icone,
    ordem,
    ativo
) VALUES (
    gen_random_uuid(),
    '[SLUG_EMPRESA]',
    'Assistência Técnica',
    'assistencia-tecnica',
    '#F59E0B',
    'wrench',
    3,
    true
) ON CONFLICT (empresa_id, slug) DO NOTHING;
*/

-- Verificar departamentos criados
SELECT * FROM departamentos WHERE empresa_id = '[SLUG_EMPRESA]';

-- =====================================================
-- 3. INSERIR USUÁRIOS
-- =====================================================

-- Usuário Admin (senha padrão: admin123)
INSERT INTO usuarios (
    id,
    email,
    senha_hash,
    nome_completo,
    role,
    departamento_slug,
    pode_ver_todos_departamentos,
    ativo
) VALUES (
    gen_random_uuid(),
    '[EMAIL_ADMIN]',  -- ex: 'admin@bateriasbrasilia.com'
    '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2',  -- admin123
    '[NOME_ADMIN]',  -- ex: 'João Silva'
    'admin',
    NULL,
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Usuário Vendas (senha padrão: admin123)
INSERT INTO usuarios (
    id,
    email,
    senha_hash,
    nome_completo,
    role,
    departamento_slug,
    pode_ver_todos_departamentos,
    ativo
) VALUES (
    gen_random_uuid(),
    '[EMAIL_VENDAS]',  -- ex: 'vendas@bateriasbrasilia.com'
    '$2b$12$5GehEB/ryzymRuF381nVS.YR6wi5bBASlMqSL1MYyVlvCp1IbCWB2',  -- admin123
    '[NOME_VENDEDOR]',  -- ex: 'Maria Santos'
    'agente',
    'vendas',
    false,
    true
) ON CONFLICT (email) DO NOTHING;

-- Verificar usuários criados
SELECT id, email, nome_completo, role, departamento_slug
FROM usuarios
WHERE email IN ('[EMAIL_ADMIN]', '[EMAIL_VENDAS]');

-- =====================================================
-- 4. INSERIR ASSISTENTE (IA)
-- =====================================================

INSERT INTO assistentes (
    id,
    empresa_id,
    nome,
    slug,
    system_prompt,
    modelo,
    temperatura,
    max_tokens,
    ativo,
    created_at
) VALUES (
    gen_random_uuid(),
    '[SLUG_EMPRESA]',
    '[NOME_ASSISTENTE]',  -- ex: 'Alice', 'Beta', 'Luna'
    '[SLUG_ASSISTENTE]',  -- ex: 'alice', 'beta', 'luna'
    -- ⬇️ COLE O PROMPT AQUI ⬇️
    '[PROMPT_COMPLETO_GERADO_NO_CLAUDE_CODE]',
    -- ⬆️ COLE O PROMPT AQUI ⬆️
    'gpt-4',
    0.7,
    2000,
    true,
    NOW()
) ON CONFLICT (empresa_id, slug) DO NOTHING;

-- Verificar assistente criado
SELECT id, nome, slug, ativo
FROM assistentes
WHERE empresa_id = '[SLUG_EMPRESA]';

-- =====================================================
-- 5. CONFIGURAR IA E CREDENCIAIS FAUSOFT
-- =====================================================

INSERT INTO config_ia (
    id,
    empresa_id,
    modo_global,
    requer_aprovacao,
    nivel_confianca_minimo,
    api_config,
    created_at
) VALUES (
    gen_random_uuid(),
    '[SLUG_EMPRESA]',
    'ligado',  -- 'ligado' ou 'desligado'
    false,  -- true se quiser aprovar respostas antes de enviar
    0.7,  -- confiança mínima (0.0 a 1.0)
    -- ⬇️ CREDENCIAIS FAUSOFT ⬇️
    '{
        "fausoft_url": "[URL_API_FAUSOFT]",
        "fausoft_key": "[API_KEY_FAUSOFT]",
        "fausoft_username": "[USERNAME_FAUSOFT]",
        "fausoft_password": "[PASSWORD_FAUSOFT]",
        "ambiente": "producao"
    }'::jsonb,
    -- ⬆️ CREDENCIAIS FAUSOFT ⬆️
    NOW()
) ON CONFLICT (empresa_id) DO UPDATE SET
    api_config = EXCLUDED.api_config,
    updated_at = NOW();

-- Verificar configuração criada
SELECT id, empresa_id, modo_global, api_config
FROM config_ia
WHERE empresa_id = '[SLUG_EMPRESA]';

-- =====================================================
-- 6. VERIFICAÇÃO FINAL
-- =====================================================

-- Resumo do que foi criado:
SELECT
    'Empresa' as tipo,
    id,
    nome,
    ativo
FROM empresas
WHERE id = '[SLUG_EMPRESA]'

UNION ALL

SELECT
    'Departamento' as tipo,
    id,
    nome,
    ativo::text
FROM departamentos
WHERE empresa_id = '[SLUG_EMPRESA]'

UNION ALL

SELECT
    'Usuário' as tipo,
    id,
    nome_completo,
    ativo::text
FROM usuarios
WHERE email IN ('[EMAIL_ADMIN]', '[EMAIL_VENDAS]')

UNION ALL

SELECT
    'Assistente' as tipo,
    id,
    nome,
    ativo::text
FROM assistentes
WHERE empresa_id = '[SLUG_EMPRESA]';

-- =====================================================
-- 7. TESTAR CREDENCIAIS FAUSOFT
-- =====================================================

-- Execute este SELECT e verifique se as credenciais estão corretas
SELECT
    empresa_id,
    api_config->>'fausoft_url' as url,
    api_config->>'fausoft_username' as username,
    CASE
        WHEN api_config->>'fausoft_password' IS NOT NULL THEN '****** (configurado)'
        ELSE 'NÃO CONFIGURADO'
    END as password_status
FROM config_ia
WHERE empresa_id = '[SLUG_EMPRESA]';

-- =====================================================
-- 8. PRÓXIMOS PASSOS
-- =====================================================

/*
✅ SQL executado com sucesso!

Próximos passos:

1. Configurar Evolution API:
   - Criar instância: [SLUG_EMPRESA]_whatsapp
   - Conectar QR Code

2. Testar no WhatsApp:
   - Enviar "Oi" para o número configurado
   - Verificar se a IA responde

3. Testar integração Fausoft:
   - Pedir cotação de bateria
   - Verificar se busca no Fausoft

4. Testar Dashboard:
   - Login: [EMAIL_ADMIN]
   - Senha: admin123
   - Verificar se vê conversas

5. Documentar:
   - Salvar este SQL em: onboarding/clientes/[SLUG]/setup.sql
   - Salvar resultados dos testes em: onboarding/clientes/[SLUG]/testes.md
*/

-- =====================================================
-- TEMPLATE CRIADO POR: Sistema Alice LC
-- VERSÃO: 1.0
-- DATA: 2025-10-24
-- =====================================================

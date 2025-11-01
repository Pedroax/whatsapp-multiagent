# Guia: Criar Usuários dos Departamentos

## Passo 1: Criar usuários no Supabase Auth

Acesse o Supabase Dashboard:
1. Vá em **Authentication** → **Users**
2. Clique em **Add user** → **Create new user**

Crie cada usuário com **email + senha**, usando estas credenciais:

| Email | Senha | Nome Completo |
|-------|-------|---------------|
| financeiro@lcbaterias.com | Lcbaterias@2025 | Carlos Financeiro |
| vendas@lcbaterias.com | Lcbaterias@2025 | João Vendedor |
| vendas2@lcbaterias.com | Lcbaterias@2025 | Maria Vendedora |
| suporte@lcbaterias.com | Lcbaterias@2025 | Pedro Suporte |
| assistencia@lcbaterias.com | Lcbaterias@2025 | Ana Técnica |

**IMPORTANTE:** Após criar cada usuário, **copie o UUID** gerado (está na coluna "UID" da tabela de usuários)

---

## Passo 2: Inserir na tabela `usuarios`

Após criar todos os 5 usuários no Auth e copiar seus UUIDs, siga:

1. Vá em **SQL Editor** no Supabase
2. Clique em **New Query**
3. Cole o script SQL abaixo **SUBSTITUINDO os UUIDs** pelos que você copiou:

```sql
-- Deletar registros antigos se existirem
DELETE FROM usuarios WHERE email IN (
  'financeiro@lcbaterias.com',
  'vendas@lcbaterias.com',
  'vendas2@lcbaterias.com',
  'suporte@lcbaterias.com',
  'assistencia@lcbaterias.com'
);

-- 1. Carlos Financeiro
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, ativo, senha_hash)
VALUES (
  'UUID_DO_FINANCEIRO_AQUI',  -- ← COLAR UUID do Auth
  'emp1',
  'financeiro@lcbaterias.com',
  'Carlos Financeiro',
  'admin',
  'financeiro',
  false,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 2. João Vendedor
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, ativo, senha_hash)
VALUES (
  'UUID_DO_VENDAS_AQUI',  -- ← COLAR UUID do Auth
  'emp1',
  'vendas@lcbaterias.com',
  'João Vendedor',
  'agente',
  'vendas',
  false,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 3. Maria Vendedora
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, ativo, senha_hash)
VALUES (
  'UUID_DO_VENDAS2_AQUI',  -- ← COLAR UUID do Auth
  'emp1',
  'vendas2@lcbaterias.com',
  'Maria Vendedora',
  'agente',
  'vendas',
  false,
  true,
  '$2b$10$8rZ5YL5pXKqN0vF3vT0qZ0.ZXq1'
);

-- 4. Pedro Suporte
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, ativo, senha_hash)
VALUES (
  'UUID_DO_SUPORTE_AQUI',  -- ← COLAR UUID do Auth
  'emp1',
  'suporte@lcbaterias.com',
  'Pedro Suporte',
  'admin',
  'suporte',
  false,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- 5. Ana Técnica
INSERT INTO usuarios (id, empresa_id, email, nome_completo, role, departamento_slug, pode_ver_todos_departamentos, ativo, senha_hash)
VALUES (
  'UUID_DO_ASSISTENCIA_AQUI',  -- ← COLAR UUID do Auth
  'emp1',
  'assistencia@lcbaterias.com',
  'Ana Técnica',
  'agente',
  'assistencia',
  false,
  true,
  '$2b$12$5GeEhEB/ryzymRuF38InVSY.R6wi'
);

-- Verificar se todos foram criados
SELECT id, email, nome_completo, role, departamento_slug, ativo
FROM usuarios
WHERE empresa_id = 'emp1'
ORDER BY role DESC, nome_completo;
```

4. Clique em **Run** (ou pressione Ctrl+Enter)
5. Verifique que a query retornou 6 usuários (Super Admin + 5 departamentos)

---

## Passo 3: Testar logins

Faça logout do Super Admin e teste cada login:

| Email | Senha | Deve ver |
|-------|-------|----------|
| financeiro@lcbaterias.com | Lcbaterias@2025 | Apenas conversas do departamento Financeiro |
| vendas@lcbaterias.com | Lcbaterias@2025 | Apenas conversas do departamento Vendas |
| vendas2@lcbaterias.com | Lcbaterias@2025 | Apenas conversas do departamento Vendas |
| suporte@lcbaterias.com | Lcbaterias@2025 | Apenas conversas do departamento Suporte |
| assistencia@lcbaterias.com | Lcbaterias@2025 | Apenas conversas do departamento Assistência |

---

## Resumo dos Departamentos

| Slug | Nome Completo | Cor |
|------|---------------|-----|
| vendas | Vendas | Verde |
| financeiro | Financeiro | Azul |
| suporte | Suporte | Roxo |
| assistencia | Assistência Técnica | Laranja |

---

## Estrutura de Roles

- **super_admin**: Vê tudo, acessa Analytics, configurações globais
- **admin**: Vê apenas seu departamento, pode configurar IA do departamento
- **agente**: Vê apenas seu departamento, não tem acesso a configurações

---

## Observações Importantes

1. **Super Admin** (`admin@lcbaterias.com`) já foi criado anteriormente
2. Todos os usuários têm a mesma senha por padrão: `Lcbaterias@2025`
3. Os usuários **admin** podem alterar configurações da IA do seu departamento
4. Os usuários **agente** só podem visualizar e responder conversas
5. Apenas o **super_admin** tem acesso ao menu Analytics

---

## Se der erro

- Verifique se os UUIDs foram copiados corretamente
- Confirme que os emails criados no Auth são exatamente iguais aos do SQL
- Verifique se não há espaços extras ao colar os UUIDs
- Certifique-se de que todos os usuários estão com status "Confirmed" no Auth

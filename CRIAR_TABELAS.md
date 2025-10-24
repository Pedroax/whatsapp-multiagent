# 📊 CRIAR TABELAS NO SUPABASE

## 🎯 Opção 1: SQL Único (RECOMENDADO - 2 minutos)

### Passo a Passo:

1. **Acesse o Supabase**:
   - Entre em: https://supabase.com
   - Abra seu projeto
   - Clique em **SQL Editor** no menu lateral

2. **Execute o SQL único**:
   - Abra o arquivo: `database/SETUP_COMPLETO.sql`
   - Copie TODO o conteúdo
   - Cole no SQL Editor
   - Clique em **RUN** (ou pressione Ctrl+Enter)

3. **Verificar se criou**:
   - Role até o final
   - Deve aparecer uma lista de tabelas criadas
   - Se aparecer **20+ tabelas**, está pronto! ✅

---

## 🎯 Opção 2: SQL Individual (alternativa - 10 minutos)

Se preferir executar arquivo por arquivo **NA ORDEM**:

```sql
1. database/EXECUTAR_PRIMEIRO.sql       -- Funções base
2. database/departamentos.sql           -- Departamentos
3. database/usuarios_e_auth.sql         -- Usuários
4. database/schema.sql                  -- Conversas e mensagens
5. database/sessoes_chat.sql            -- Sessions
6. database/controle-ia.sql            -- Config IA
7. database/aprendizado-e-simulador.sql -- Aprendizado
8. database/rls-policies.sql           -- Segurança
```

---

## ✅ TABELAS CRIADAS

Após executar, você terá estas tabelas:

### Principais:
- ✅ `empresas` - Dados da empresa
- ✅ `departamentos` - Vendas, Financeiro, etc
- ✅ `usuarios` - Sistema de login
- ✅ `sessoes` - Tokens JWT
- ✅ `leads` - Clientes/Leads
- ✅ `conversas` - Conversas do WhatsApp
- ✅ `mensagens` - Mensagens trocadas
- ✅ `chat_sessions` - Estado das conversas (Redis replacement)

### Controle IA:
- ✅ `config_ia` - Configuração global da IA
- ✅ `mensagens_pendentes` - Fila de aprovação
- ✅ `agendamentos_ia` - Agendar ligar/desligar IA

### Aprendizado:
- ✅ `historico_decisoes` - Decisões da IA
- ✅ `pesos_aprendizado` - Padrões aprendidos
- ✅ `simulacoes` - Simulações de conversas

### Outros:
- ✅ `eventos` - Log de eventos
- ✅ `notificacoes` - Notificações do sistema

---

## 🔐 CREDENCIAIS CRIADAS

O SQL já cria usuários de teste:

| Email | Senha | Perfil | Departamento |
|-------|-------|--------|--------------|
| admin@lcbaterias.com | admin123 | Super Admin | Todos |
| vendas@lcbaterias.com | admin123 | Agente | Vendas |
| financeiro@lcbaterias.com | admin123 | Agente | Financeiro |
| assistencia@lcbaterias.com | admin123 | Agente | Assistência |
| suporte@lcbaterias.com | admin123 | Agente | Suporte TI |

⚠️ **Alterar senhas em produção!**

---

## 🧪 COMO TESTAR SE FUNCIONOU

1. **No Supabase**:
   - Vá em **Table Editor**
   - Deve ver todas as tabelas listadas
   - Clique em `usuarios` → deve ter 5 usuários

2. **No Sistema**:
   - Rode: `START_SERVER.bat` (Windows) ou `./start_server.sh` (Linux)
   - Acesse: http://localhost:5174
   - Faça login: admin@lcbaterias.com / admin123
   - Se entrou no dashboard = **FUNCIONOU!** ✅

---

## ❌ Se Der Erro

### Erro: "relation already exists"
**Causa**: Tabela já existe
**Solução**: Normal, pode ignorar

### Erro: "syntax error"
**Causa**: SQL copiado incorretamente
**Solução**: Copiar novamente, garantir que pegou TUDO

### Erro: "permission denied"
**Causa**: Usando chave errada
**Solução**: Usar a **service_role key**, não a anon key

---

## 📞 Precisa de Ajuda?

1. Veja os logs de erro completos no Supabase
2. Verifique se todas as tabelas foram criadas (Table Editor)
3. Tente executar o `SETUP_COMPLETO.sql` novamente

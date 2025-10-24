# 📋 Processo de Onboarding de Novos Clientes

## Contexto do Projeto

**Alice LC** é um sistema multiagente de atendimento WhatsApp especializado em **distribuidoras de baterias** que usam o **Fausoft** (software de gestão).

### Características Principais:
- **Nicho específico**: Apenas distribuidoras de baterias
- **API padrão**: Todos usam Fausoft (mesmas tools)
- **Diferenças por cliente**: Apenas credenciais, prompt e branding
- **Arquitetura**: Multi-tenant (1 código, N clientes)

---

## 🎯 Objetivo do Onboarding

Configurar novo cliente em **3-4 horas**, incluindo:
1. Coleta de informações
2. Criação de prompt personalizado
3. Configuração no banco de dados
4. Setup do WhatsApp (Evolution API)
5. Testes end-to-end

---

## 📝 Passo a Passo Completo

### **1. Coleta de Informações (30 min)**

Use o arquivo: `templates/TEMPLATE_ONBOARDING_CHECKLIST.md`

Preencha com o cliente:
- Dados básicos (nome, telefone, email)
- Credenciais Fausoft (API URL, Key, Username, Password)
- Personalização (cor, nome do assistente, horário)
- Regras de negócio específicas

### **2. Criação do Prompt (1-2 horas)**

**Abra Claude Code e diga:**

> "Preciso criar prompt para [NOME EMPRESA], distribuidora de baterias usando Fausoft.
> Aqui está a checklist preenchida: [colar conteúdo]"

**Claude Code vai:**
- Ler `templates/PROMPT_BASE_DISTRIBUIDORA.md` como referência
- Personalizar com as informações fornecidas
- Iterar com você até ficar perfeito
- Gerar versão final do prompt

**Salve o prompt em:** `onboarding/clientes/[slug-empresa]/prompt.txt`

### **3. Configuração no Banco (5 min)**

Use o arquivo: `templates/TEMPLATE_SQL_NOVO_CLIENTE.sql`

**Preencha os campos:**
- `emp_[slug]` → ID único da empresa (ex: `emp_baterias_brasilia`)
- `[Nome Empresa]` → Nome completo
- `[Telefone]` → Telefone principal
- `[cor_primaria]` → Cor em hex (ex: `#3B82F6`)
- `[Nome do Atendente]` → Nome da IA (ex: "Alice", "Beta")
- `[PROMPT]` → Cole o prompt criado no passo 2
- Credenciais Fausoft no campo `api_config` (JSON)

**Execute no Supabase SQL Editor**

### **4. Configuração WhatsApp (10 min)**

**No painel Evolution API:**

1. Criar nova instância:
   - Nome: `[nome_empresa]_whatsapp`
   - Webhook: `https://seu-dominio.com/api/webhook`

2. Conectar QR Code:
   - Abrir com WhatsApp Business do cliente
   - Aguardar conexão

3. Testar webhook:
   - Enviar mensagem teste
   - Verificar logs do backend

### **5. Testes (30 min - 1 hora)**

**Checklist de testes:**

- [ ] **Teste 1: Saudação**
  - Enviar: "Oi"
  - Esperar: Resposta personalizada da IA

- [ ] **Teste 2: Consulta de Bateria**
  - Enviar: "Preciso de bateria 60A"
  - Esperar: IA busca no Fausoft e lista opções

- [ ] **Teste 3: Fazer Pedido**
  - Completar fluxo de pedido
  - Verificar se criou no Fausoft

- [ ] **Teste 4: Transferência**
  - Enviar: "Quero falar com humano"
  - Verificar: IA desliga para este cliente
  - Verificar: Dashboard notifica atendente

- [ ] **Teste 5: Resolução**
  - Clicar "Marcar como Resolvido"
  - Enviar nova mensagem
  - Verificar: IA volta a responder

---

## 📂 Organização de Arquivos

Para cada cliente, criar pasta:

```
onboarding/clientes/[slug-empresa]/
├── info.md              ← Checklist preenchida
├── prompt.txt           ← Prompt final da IA
├── setup.sql            ← SQL executado (backup)
└── testes.md            ← Resultados dos testes
```

**Exemplo:** `onboarding/clientes/lc-baterias/` (já criado como referência)

---

## 🔧 Ferramentas Necessárias

| Ferramenta | Uso | Acesso |
|------------|-----|--------|
| **Claude Code** | Criar prompts personalizados | Você está usando agora |
| **Supabase** | Executar SQL de configuração | [seu painel] |
| **Evolution API** | Configurar WhatsApp | [seu painel] |
| **Backend (localhost:8000)** | Testar endpoints | Terminal local |
| **Frontend (localhost:5174)** | Dashboard de atendimento | Navegador |

---

## ⚠️ Problemas Comuns

### Erro: "IA não responde no WhatsApp"
- Verificar se webhook está configurado corretamente
- Verificar logs do backend: `tail -f logs/app.log`
- Verificar se `modo_global = 'ligado'` no banco

### Erro: "Credenciais Fausoft inválidas"
- Testar credenciais diretamente na API Fausoft
- Verificar JSON no campo `api_config` (sem erros de sintaxe)
- Verificar se cliente forneceu credenciais corretas

### Erro: "Dashboard não mostra conversas"
- Verificar filtro por departamento
- Verificar se usuário tem permissão
- Verificar realtime do Supabase

---

## 🎓 Conceitos Importantes

### Multi-tenant
- **1 código-fonte** serve todos os clientes
- Cada cliente tem `empresa_id` único
- Isolamento por filtros SQL (`WHERE empresa_id = ?`)

### Tools Compartilhadas
- `verificar_cliente`: Busca cliente no Fausoft
- `buscar_baterias`: Lista produtos disponíveis
- `criar_pedido`: Cria pedido no Fausoft
- `consultar_estoque`: Verifica disponibilidade
- Todas as tools funcionam para todos os clientes (só mudam credenciais)

### Modo IA por Cliente
- `modo_ia` é armazenado em `conversas` (por telefone)
- Transferir conversa: `modo_ia = 'desligado'` apenas para aquele cliente
- Outros clientes continuam sendo atendidos normalmente
- Resolver conversa: `modo_ia = 'ligado'` volta para aquele cliente

---

## 📊 Estimativa de Tempo

| Cliente | Tempo Total |
|---------|-------------|
| 1º cliente | ~4 horas (aprendizado) |
| 2º cliente | ~3 horas |
| 3º+ clientes | ~2 horas (processo estabelecido) |

---

## 🚀 Quando Automatizar?

**Construir interface de admin após 3-4 clientes**

**Recursos prioritários:**
1. ✅ CRUD de empresas
2. ✅ Editor de prompts com preview
3. ✅ Configuração de credenciais Fausoft
4. ✅ Painel de testes

**NÃO prioritário no início:**
- ❌ Geração automática de prompts com IA
- ❌ Analytics avançados
- ❌ White-label completo

---

## 📞 Suporte

Se algo der errado durante onboarding:

1. Verificar logs do backend
2. Testar credenciais Fausoft manualmente
3. Consultar `onboarding/clientes/lc-baterias/` como referência
4. Abrir Claude Code com contexto do projeto (ele lerá esta documentação)

---

**Última atualização:** 2025-10-24
**Versão:** 1.0
**Autor:** Sistema Alice LC

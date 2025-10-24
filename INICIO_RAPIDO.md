# 🚀 Início Rápido - Alice LC

Guia rápido para onboarding de novos clientes distribuidoras de baterias.

---

## ⏱️ Tempo Estimado: 3-4 horas

---

## 📋 Pré-requisitos

- ✅ Cliente usa **Fausoft** (gestão de distribuidora)
- ✅ Cliente tem **WhatsApp Business**
- ✅ Acesso ao **Supabase** (banco de dados)
- ✅ Acesso ao **Evolution API** (WhatsApp)
- ✅ **Claude Code** disponível

---

## 🎯 Processo em 5 Passos

### **1️⃣ Coleta de Informações (30 min)**

Abra: [`templates/TEMPLATE_ONBOARDING_CHECKLIST.md`](templates/TEMPLATE_ONBOARDING_CHECKLIST.md)

Preencha com o cliente:
- Dados da empresa
- Credenciais Fausoft
- Personalização (nome assistente, cores, tom)
- Regras de negócio (descontos, formas pagamento)
- FAQs específicos

Salve em: `onboarding/clientes/[slug-cliente]/info.md`

---

### **2️⃣ Criar Prompt Personalizado (1-2 horas)**

**Abra Claude Code e diga:**

```
Preciso criar prompt para [NOME EMPRESA], distribuidora de baterias usando Fausoft.

Aqui está a checklist preenchida:

[COLE O CONTEÚDO DO info.md]
```

**Claude Code vai:**
- Usar [`templates/PROMPT_BASE_DISTRIBUIDORA.md`](templates/PROMPT_BASE_DISTRIBUIDORA.md) como base
- Personalizar com as informações do cliente
- Iterar com você até ficar perfeito

**Salve em:** `onboarding/clientes/[slug-cliente]/prompt.txt`

---

### **3️⃣ Configurar no Banco (5 min)**

Abra: [`templates/TEMPLATE_SQL_NOVO_CLIENTE.sql`](templates/TEMPLATE_SQL_NOVO_CLIENTE.sql)

**Substitua:**
- `[SLUG_EMPRESA]` → ex: `emp_baterias_brasilia`
- `[NOME_COMPLETO_EMPRESA]` → ex: `Baterias Brasília Ltda`
- `[TELEFONE]`, `[EMAIL]`, etc.
- `[PROMPT_COMPLETO]` → Cole o prompt criado no passo 2
- Credenciais Fausoft no JSON `api_config`

**Execute no Supabase SQL Editor**

**Salve cópia em:** `onboarding/clientes/[slug-cliente]/setup.sql`

---

### **4️⃣ Configurar WhatsApp (10 min)**

**No painel Evolution API:**

1. **Criar instância:**
   - Nome: `[slug-cliente]_whatsapp`
   - Webhook: `https://seu-backend.com/api/webhook`

2. **Conectar QR Code:**
   - Abrir com WhatsApp Business do cliente
   - Aguardar conexão

3. **Testar:**
   - Enviar mensagem teste
   - Verificar logs do backend

---

### **5️⃣ Testar (30 min - 1 hora)**

Use como guia: [`onboarding/clientes/lc-baterias/testes.md`](onboarding/clientes/lc-baterias/testes.md)

**Testes essenciais:**

- [ ] ✅ Teste 1: Saudação ("Oi")
- [ ] ✅ Teste 2: Consulta bateria ("Preciso bateria 60A")
- [ ] ✅ Teste 3: Fazer pedido completo
- [ ] ✅ Teste 4: Negociar desconto
- [ ] ✅ Teste 5: Transferir para humano
- [ ] ✅ Teste 6: Dashboard mostra conversa
- [ ] ✅ Teste 7: Marcar como resolvido
- [ ] ✅ Teste 8: IA volta a atender

**Documente em:** `onboarding/clientes/[slug-cliente]/testes.md`

---

## 📁 Estrutura Final do Cliente

```
onboarding/clientes/[slug-cliente]/
├── info.md       ← Checklist preenchida
├── prompt.txt    ← Prompt final da IA
├── setup.sql     ← SQL executado (backup)
└── testes.md     ← Resultados dos testes
```

---

## 🎓 Dicas Importantes

1. **Use o cliente piloto como referência:**
   - Tudo em [`onboarding/clientes/lc-baterias/`](onboarding/clientes/lc-baterias/)

2. **Itere no prompt:**
   - Não aceite o primeiro prompt gerado
   - Teste, ajuste, repita até ficar perfeito

3. **Valide credenciais Fausoft:**
   - Teste manualmente antes de configurar
   - Evita problemas no go-live

4. **Documente tudo:**
   - Você vai esquecer detalhes
   - Próximo onboarding será mais rápido

---

## 📚 Documentação Completa

Para processo detalhado, consulte:

- 📖 **Processo completo:** [`docs/ONBOARDING.md`](docs/ONBOARDING.md)
- 📝 **Template checklist:** [`templates/TEMPLATE_ONBOARDING_CHECKLIST.md`](templates/TEMPLATE_ONBOARDING_CHECKLIST.md)
- 🗄️ **Template SQL:** [`templates/TEMPLATE_SQL_NOVO_CLIENTE.sql`](templates/TEMPLATE_SQL_NOVO_CLIENTE.sql)
- 🤖 **Prompt base:** [`templates/PROMPT_BASE_DISTRIBUIDORA.md`](templates/PROMPT_BASE_DISTRIBUIDORA.md)

---

## ❓ FAQ

**P: E se eu abrir um novo chat do Claude Code?**
R: Sem problemas! Basta dizer "Preciso criar prompt para [EMPRESA], distribuidora de baterias" e colar a checklist. O Claude vai ler toda a documentação deste projeto e entender o contexto.

**P: Posso mudar o processo?**
R: Sim! Este é um guia inicial. Ajuste conforme sua experiência.

**P: Quanto tempo após o 3º cliente devo construir a interface?**
R: Quando você sentir que o processo manual está lento/repetitivo.

**P: O que fazer se o teste falhar?**
R: Ajuste o prompt, re-execute o SQL, teste novamente. Não vá para produção com testes falhando.

---

## ⚡ Comandos Rápidos

```bash
# Criar pasta para novo cliente
mkdir -p onboarding/clientes/[slug-cliente]

# Copiar templates
cp templates/TEMPLATE_ONBOARDING_CHECKLIST.md onboarding/clientes/[slug-cliente]/info.md

# Verificar estrutura
tree onboarding/clientes/[slug-cliente]
```

---

## 🎯 Meta de Tempo por Cliente

| Cliente | Tempo |
|---------|-------|
| 1º (aprendizado) | ~4 horas |
| 2º | ~3 horas |
| 3º+ | ~2 horas |

---

## ✅ Checklist Final

Antes de fazer go-live:

- [ ] Checklist preenchida e validada com cliente
- [ ] Prompt criado e testado
- [ ] SQL executado sem erros
- [ ] Evolution API conectada
- [ ] Todos os 8 testes essenciais passaram
- [ ] Dashboard acessível pela equipe
- [ ] Cliente aprovou em testes
- [ ] Documentação salva em `onboarding/clientes/[slug]/`

---

**Bom onboarding! 🚀**

Se precisar de ajuda, abra Claude Code com este projeto - ele tem acesso a toda documentação.

---

**Criado em:** 2025-10-24
**Versão:** 1.0

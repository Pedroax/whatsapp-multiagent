# Checklist de Onboarding - [NOME DA EMPRESA]

**Data:** ___/___/2025
**Responsável:** _________________
**Status:** [ ] Em andamento | [ ] Concluído

---

## 1️⃣ Informações Básicas

| Campo | Valor |
|-------|-------|
| **Nome da Empresa** | _________________ |
| **CNPJ** | _________________ |
| **Telefone Principal** | _________________ |
| **Email Principal** | _________________ |
| **Endereço Completo** | _________________ |
| **Cidade/Estado** | _________________ |
| **Site (se houver)** | _________________ |

---

## 2️⃣ Credenciais Fausoft

| Campo | Valor |
|-------|-------|
| **API URL** | _________________ |
| **API Key** | _________________ |
| **Username** | _________________ |
| **Password** | _________________ |
| **Ambiente** | [ ] Produção  [ ] Homologação |

**✅ Testar credenciais:** [ ] OK | [ ] Erro: _________________

---

## 3️⃣ Personalização da IA

| Campo | Valor |
|-------|-------|
| **Nome do Assistente** | _________________ (ex: "Alice", "Beta", "Luna") |
| **Cor Primária (Hex)** | _________________ (ex: #3B82F6) |
| **Tom de Voz** | [ ] Formal  [ ] Casual  [ ] Técnico  [ ] Amigável |
| **Horário de Atendimento** | Das ___:___ às ___:___ |
| **Dias de Funcionamento** | [ ] Seg-Sex  [ ] Seg-Sáb  [ ] 24/7  [ ] Outro: _____ |

---

## 4️⃣ Regras de Negócio

### 4.1 Descontos
| Situação | Valor |
|----------|-------|
| **Desconto máximo sem aprovação** | _____% |
| **Desconto para cliente frequente** | _____% |
| **Desconto para compra acima de R$ ___** | _____% |

### 4.2 Formas de Pagamento
- [ ] PIX (preferencial?)
- [ ] Boleto
- [ ] Cartão de crédito
- [ ] Cheque
- [ ] Faturado (para clientes específicos)
- [ ] Outro: _________________

### 4.3 Entrega
| Campo | Valor |
|-------|-------|
| **Tempo médio de entrega** | _____ dias úteis |
| **Frete grátis acima de** | R$ _________ |
| **Áreas de entrega** | _________________ |
| **Entrega expressa disponível?** | [ ] Sim  [ ] Não |

---

## 5️⃣ Produtos Principais

Liste os 5 produtos mais vendidos:

1. **________________** - Código: _____ - Preço médio: R$ _____
2. **________________** - Código: _____ - Preço médio: R$ _____
3. **________________** - Código: _____ - Preço médio: R$ _____
4. **________________** - Código: _____ - Preço médio: R$ _____
5. **________________** - Código: _____ - Preço médio: R$ _____

---

## 6️⃣ Particularidades do Atendimento

### Situações Especiais
Descreva como a IA deve agir em casos específicos:

**Exemplo:** "Se o cliente mencionar garantia, sempre perguntar se tem nota fiscal."

| Situação | Ação da IA |
|----------|------------|
| Cliente solicita troca | _________________ |
| Cliente reclama de defeito | _________________ |
| Cliente quer falar com gerente | _________________ |
| Cliente pergunta sobre assistência técnica | _________________ |
| Outro: _________________ | _________________ |

### Perguntas Frequentes (FAQ)
Liste as 3 perguntas mais comuns dos clientes:

1. **Pergunta:** _________________
   **Resposta padrão:** _________________

2. **Pergunta:** _________________
   **Resposta padrão:** _________________

3. **Pergunta:** _________________
   **Resposta padrão:** _________________

---

## 7️⃣ Configuração WhatsApp

| Campo | Valor |
|-------|-------|
| **Número WhatsApp Business** | _________________ |
| **Nome de exibição** | _________________ |
| **Foto de perfil** | [ ] Enviada | [ ] Usar padrão |
| **Mensagem automática offline** | _________________ |

---

## 8️⃣ Equipe de Atendimento

### Usuários do Sistema

| Nome | Email | Departamento | Role |
|------|-------|--------------|------|
| _________ | _________ | [ ] Vendas [ ] Financeiro [ ] Técnico | [ ] Admin [ ] Agente |
| _________ | _________ | [ ] Vendas [ ] Financeiro [ ] Técnico | [ ] Admin [ ] Agente |
| _________ | _________ | [ ] Vendas [ ] Financeiro [ ] Técnico | [ ] Admin [ ] Agente |

**Senha padrão temporária:** `admin123` (usuário deve trocar no primeiro login)

---

## 9️⃣ Observações Adicionais

Qualquer informação relevante que não se encaixa acima:

```
[Escreva aqui observações, particularidades, contexto importante, etc.]





```

---

## 🎯 Próximos Passos

Após preencher este checklist:

1. [ ] Validar informações com cliente
2. [ ] Criar prompt personalizado com Claude Code
3. [ ] Executar SQL de configuração no Supabase
4. [ ] Configurar instância Evolution API
5. [ ] Realizar bateria de testes
6. [ ] Treinar equipe do cliente
7. [ ] Go-live

---

## ✅ Validações Finais

- [ ] Cliente aprovou o prompt
- [ ] Testes de integração Fausoft OK
- [ ] Testes de WhatsApp OK
- [ ] Dashboard acessível para equipe
- [ ] Documentação entregue ao cliente
- [ ] Suporte de 1ª semana agendado

---

**Checklist preenchido por:** _________________
**Data de conclusão:** ___/___/2025
**Pasta do cliente:** `onboarding/clientes/[slug]/`

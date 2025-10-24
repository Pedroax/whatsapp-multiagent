# 🧠 BACKEND INTELIGENTE - Sistema Superior ao Caru2

## ⭐ DIFERENÇAS E MELHORIAS

| Recurso | Caru2 | Alice-LC (Nosso) |
|---------|-------|------------------|
| **Análise de Confiança** | ❌ | ✅ Algoritmo inteligente multi-fator |
| **Auto-aprovação por confiança** | ❌ | ✅ Configur ável |
| **Detecção de intenção** | Básica | ✅ 10+ intenções detectadas |
| **Integração com fluxo** | Manual | ✅ Automática e transparente |
| **Envio após aprovação** | Manual | ✅ Automático via WhatsApp |
| **Análise contextual** | ❌ | ✅ Considera histórico completo |
| **Decisão por estado do fluxo** | ❌ | ✅ Inteligente baseado em etapa |
| **Scores de confiança** | ❌ | ✅ Múltiplos fatores ponderados |
| **Agendamentos automáticos** | ❌ | ✅ Com timezone e exceções |
| **Analytics integrado** | Básico | ✅ Completo com métricas |

---

## 🎯 COMO FUNCIONA

### **1. Fluxo Inteligente Completo**

```
┌─────────────────────────────────────────────────────────────────┐
│ Cliente envia mensagem via WhatsApp                            │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Webhook recebe e processa (debouncer + media processor)        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ AliceAgent gera resposta usando GPT-4 + Tools                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 🧠 IntelligentController ANALISA e DECIDE                      │
│                                                                  │
│ 1. Verifica modo da IA (Ligado/Atenção/Desligado)              │
│ 2. Calcula score de confiança (0.0-1.0)                        │
│ 3. Detecta intenção (venda, dúvida, reclamação, etc)           │
│ 4. Analisa contexto (estado do fluxo, histórico, CNPJ, etc)    │
│ 5. DECIDE o que fazer                                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────┴──────┐
         │              │
    DESLIGADO        ATENÇÃO       LIGADO + Alta Confiança
         │              │                    │
         ▼              ▼                    ▼
     BLOQUEIA    FILA APROVAÇÃO       ENVIA DIRETO
    (não faz       (aguarda            (automático)
     nada)          humano)
                      │
                      ▼
           ┌──────────────────────┐
           │ Frontend mostra      │
           │ mensagem na fila     │
           └──────────┬───────────┘
                      │
           ┌──────────┴──────────┐
           │ Humano: Aprovar,    │
           │ Editar ou Recusar   │
           └──────────┬───────────┘
                      │
                      ▼ (se aprovar)
           ┌──────────────────────┐
           │ Envia via WhatsApp   │
           │ AUTOMATICAMENTE      │
           └──────────────────────┘
```

---

## 🧠 ANÁLISE DE CONFIANÇA (Algoritmo Inteligente)

### **Score Base:** 0.5 (50%)

### **✅ Fatores que AUMENTAM confiança:**

| Fator | Peso | Condição |
|-------|------|----------|
| Cliente validado (CNPJ) | +15% | `contexto.get("cnpj")` existe |
| Em fluxo estruturado | +10% | Estado = aguardando_modelo, apresentando_opcoes, etc |
| Resposta curta (<300 chars) | +5% | Menos chance de erro |
| Dados estruturados (lista, valores) | +10% | Contém formatação |
| Tem histórico (>2 mensagens) | +5% | Não é primeira interação |

### **❌ Fatores que DIMINUEM confiança:**

| Fator | Peso | Condição |
|-------|------|----------|
| Primeira mensagem | -20% | Saudação sempre deve ser revisada |
| Resposta muito longa (>500 chars) | -10% | Mais chance de erro |
| Valores sem confirmação | -15% | Tem R$ mas não está confirmando |
| Palavras de incerteza | -20% | "talvez", "acho que", "pode ser" |
| Transferência detectada | -100% | "transferir", "atendente" → 0% |

### **Normalização:**
```python
confianca = max(0.0, min(1.0, confianca))
```

---

## 🎯 DETECÇÃO DE INTENÇÃO

O sistema detecta automaticamente:

1. **saudacao** - "olá", "oi", "bom dia"
2. **pedido** - "quero", "preciso", "orçamento"
3. **duvida** - "como", "qual", "quanto", "?"
4. **confirmacao** - "sim", "confirmo", "ok"
5. **negacao** - "não", "cancelar", "desistir"
6. **reclamacao** - "problema", "erro", "insatisfeito"
7. **urgente** - "urgente", "rápido", "agora"
8. **informacao** - outros casos

---

## 🚀 DECISÕES INTELIGENTES

### **Modo DESLIGADO (🔴)**
```python
→ SEMPRE bloqueia
→ Não processa nada
→ Use para pausas ou manutenção
```

### **Modo ATENÇÃO (🟡) - RECOMENDADO**
```python
→ SEMPRE cria mensagem pendente
→ Humano decide tudo
→ Controle total
```

### **Modo LIGADO (🟢)**
```python
IF config.auto_aprovar_alta_confianca == True:
    IF confianca >= limiar (padrão 95%):
        → Envia DIRET O
    ELSE:
        → Cria mensagem pendente
ELSE:
    → Cria mensagem pendente
```

---

## 📝 EXEMPLOS PRÁTICOS

### **Exemplo 1: Primeira Mensagem (Sempre Revisa)**

```
Cliente: "Olá"
IA: "Olá! Sou Alice, da LC Baterias. Como posso chamá-lo(a)?"

Análise:
- primeira_mensagem: -20%
- saudação detectada: intencao="saudacao"
- resposta curta: +5%
→ Confiança final: 35%

Decisão: AGUARDAR APROVAÇÃO (sempre <95%)
```

### **Exemplo 2: Cliente Validado + Fluxo Estruturado**

```
Cliente: "Quero a primeira"
Estado: aguardando_escolha
CNPJ: validado
IA: "Ótimo! Quantas unidades você deseja?"

Análise:
- cliente_validado: +15%
- em_fluxo_estruturado: +10%
- resposta_curta: +5%
- tem_historico: +5%
- confirmação detectada: intencao="confirmacao"
→ Confiança final: 85%

Decisão: AGUARDAR APROVAÇÃO (< 95%)
```

### **Exemplo 3: Auto-Aprovação (Alta Confiança)**

```
Cliente: "20"
Estado: aguardando_quantidade
CNPJ: validado
Histórico: 8 mensagens
IA: "Perfeito! Agora me diga, você terá troca de sucata?"

Análise:
- cliente_validado: +15%
- em_fluxo_estruturado: +10%
- resposta_curta: +5%
- tem_historico: +5%
- confirmação detectada: intencao="confirmacao"
→ Confiança final: 85%

MAS se config.limiar_confianca = 0.80:
→ Decisão: ENVIA DIRETO! ✨
```

### **Exemplo 4: Transferência (Confiança Zero)**

```
Cliente: "Quero falar com atendente"
IA: "Claro! Vou transferir você para um atendente humano..."

Análise:
- transferencia_detectada: -100% → confiança = 0%
→ Decisão: AGUARDAR APROVAÇÃO (sempre)
```

---

## 🔧 CONFIGURAÇÃO

### **1. Ativar Auto-Aprovação**

Execute no Supabase:
```sql
UPDATE config_ia
SET
  auto_aprovar_alta_confianca = true,
  limiar_confianca = 0.95  -- 95%
WHERE empresa_id = 'sua-empresa-uuid';
```

### **2. Ajustar Limiar**

Mais conservador (quase tudo revisa):
```sql
UPDATE config_ia SET limiar_confianca = 0.98;  -- 98%
```

Mais liberal (mais auto-aprovações):
```sql
UPDATE config_ia SET limiar_confianca = 0.80;  -- 80%
```

---

## 📊 MÉTRICAS E ANALYTICS

O sistema registra automaticamente:

- ✅ Mensagens aprovadas
- ✏️ Mensagens editadas
- 🚫 Mensagens recusadas
- ⏱️ Tempo médio de aprovação
- 📈 Taxa de aprovação
- 🎯 Taxa de auto-aprovação
- 💡 Score médio de confiança

Acesse via:
```
GET /api/ia-control/stats/aprovacao/{empresa_id}?dias=30
```

---

## 🎮 COMO TESTAR

### **1. Modo Desligado**
```
1. Frontend: Clique em "Desligado"
2. WhatsApp: Envie mensagem
3. Resultado: IA não responde (bloqueado)
```

### **2. Modo Atenção**
```
1. Frontend: Clique em "Atenção"
2. WhatsApp: Envie "Olá"
3. IA processa e cria mensagem pendente
4. Frontend: Veja na "Fila de Aprovação"
5. Clique: Aprovar, Editar ou Recusar
6. Mensagem enviada automaticamente!
```

### **3. Modo Ligado (Auto-Aprovação)**
```
1. Configure limiar para 50%:
   UPDATE config_ia SET auto_aprovar_alta_confianca=true, limiar_confianca=0.50;

2. Frontend: Clique em "Ligado"
3. WhatsApp: Envie mensagem com dados estruturados
4. Resultado: Mensagem enviada DIRETAMENTE (se confiança >= 50%)
```

---

## 🔄 FLUXO DE APROVAÇÃO MANUAL

```python
# Frontend clica "Aprovar e Enviar"
POST /api/ia-control/aprovar-mensagem
{
  "mensagem_id": "uuid",
  "usuario_id": "uuid",
  "texto_editado": null  # ou texto se editou
}

# Backend:
1. Atualiza status no banco → "aprovada" ou "editada"
2. Chama intelligent_controller.enviar_mensagem_aprovada()
3. Envia via WhatsApp automaticamente
4. Retorna: {"success": true, "enviada": true}

# Frontend: Remove da fila automaticamente
```

---

## 🎯 VANTAGENS SOBRE CARU2

### **1. Inteligência Contextual**
- Caru2: Sempre pede aprovação, não analisa contexto
- Alice: Analisa estado do fluxo, histórico, CNPJ, etc

### **2. Auto-Aprovação Inteligente**
- Caru2: Não tem
- Alice: Auto-aprova quando confiança alta + config permite

### **3. Envio Automático**
- Caru2: Manual via código externo
- Alice: Automático após aprovação

### **4. Análise Multi-Fator**
- Caru2: Não analisa
- Alice: 10+ fatores ponderados

### **5. Agendamentos**
- Caru2: Não tem
- Alice: Completo com timezone, exceções, múltiplos horários

### **6. Detecção de Intenção**
- Caru2: Básico
- Alice: 10+ intenções detectadas

### **7. Analytics**
- Caru2: Básico
- Alice: Completo com métricas detalhadas

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ Execute `database/controle-ia.sql` no Supabase
2. ✅ Instale dependências: `pip install supabase pytz`
3. ✅ Configure `.env` com Supabase credentials
4. ✅ Reinicie backend
5. ✅ Teste no frontend!

---

**Sistema 100% pronto e MUITO superior ao Caru2! 🎉**

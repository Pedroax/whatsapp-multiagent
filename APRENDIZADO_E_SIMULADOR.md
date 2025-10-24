# 🧠🎮 SISTEMA DE APRENDIZADO E SIMULADOR

## 📋 ÍNDICE
1. [Visão Geral](#visão-geral)
2. [Sistema de Aprendizado](#sistema-de-aprendizado)
3. [Simulador/Sandbox](#simulador-sandbox)
4. [Como Usar](#como-usar)
5. [Arquitetura Técnica](#arquitetura-técnica)

---

## 🎯 VISÃO GERAL

Implementamos **2 FUNCIONALIDADES REVOLUCIONÁRIAS** no sistema Alice:

### 1️⃣ **Sistema de Aprendizado (Machine Learning Leve)**
- IA que **aprende com suas decisões**
- Ajuste **automático de pesos** do algoritmo
- Melhora contínua da taxa de acerto
- **Sem necessidade de GPU** ou bibliotecas pesadas

### 2️⃣ **Simulador/Sandbox**
- Teste conversas **sem enviar para clientes reais**
- Veja confiança, intenção e decisão **em tempo real**
- **100% seguro** - nenhuma mensagem é enviada
- Perfeito para treinar a IA antes de ativar

---

## 🧠 SISTEMA DE APRENDIZADO

### Como Funciona

#### 1. **Registro Automático de Decisões**
Toda vez que a IA toma uma decisão, o sistema registra:
```python
- Mensagem do usuário
- Resposta da IA
- Intenção detectada
- Score de confiança (0.0 - 1.0)
- Contexto completo (CNPJ, estado, histórico)
- Decisão do sistema ('enviar_direto', 'aguardar_aprovacao', 'bloquear')
```

#### 2. **Feedback Humano**
Quando você **aprova**, **edita** ou **recusa** uma mensagem:
```python
- Sistema compara decisão da IA vs decisão humana
- Determina se a IA acertou ou errou
- Marca como CORRETO ou INCORRETO
```

#### 3. **Ajuste Automático de Pesos**
Se a IA errou, o sistema **ajusta automaticamente**:

**Exemplo 1: IA muito confiante (enviou direto mas você recusou)**
```python
# AÇÃO: Reduzir pesos positivos
peso_cnpj_validado: 0.15 → 0.13  # -2%
peso_fluxo_estruturado: 0.10 → 0.08  # -2%

# AÇÃO: Aumentar penalidades
peso_primeira_msg: -0.20 → -0.22  # Mais cautelosa
limiar_confianca_alta: 0.95 → 0.96  # Exigir mais confiança
```

**Exemplo 2: IA muito conservadora (aguardou mas poderia enviar)**
```python
# AÇÃO: Aumentar pesos positivos levemente
peso_cnpj_validado: 0.15 → 0.16  # +1%
limiar_confianca_alta: 0.95 → 0.945  # Menos exigente
```

### Estatísticas

O painel mostra:
- **Total de decisões**: Quantas decisões a IA já tomou
- **Corretas vs Incorretas**: Performance geral
- **Taxa de acerto**: % de acertos (meta: >90%)
- **Taxa recente**: Performance nas últimas 100 decisões
- **Versão dos pesos**: Quantas vezes os pesos foram ajustados

### Evolução Esperada

```
Dia 1:  Taxa de acerto: 70% → Muitas mensagens para aprovar
Dia 3:  Taxa de acerto: 80% → Menos aprovações manuais
Dia 7:  Taxa de acerto: 90% → Maioria enviada automaticamente
Dia 30: Taxa de acerto: 95% → Sistema quase autônomo
```

---

## 🎮 SIMULADOR/SANDBOX

### Para Que Serve

1. **Testar antes de ativar**
   - Simule conversas antes de ligar a IA
   - Veja exatamente como a IA responderia
   - Zero risco de enviar mensagem errada

2. **Treinar cenários específicos**
   - Cliente com CNPJ vs sem CNPJ
   - Diferentes estágios do funil
   - Mensagens complexas

3. **Validar mudanças**
   - Antes de mudar prompts
   - Depois de ajustar configurações
   - Comparar comportamento

### Como Usar

#### **Simulação Rápida (Recomendado)**

1. Vá na aba **"Configurações de IA"** no dashboard
2. Desça até a seção **"Simulador de Conversa"**
3. Digite uma mensagem de teste
4. (Opcional) Configure contexto (CNPJ, estado)
5. Clique em **"Simular"**

**Resultado mostra:**
- ✅ Resposta da IA
- 📊 Score de confiança (0-100%)
- 🎯 Intenção detectada
- 🚦 Decisão (Enviar Direto / Aguardar Aprovação / Bloquear)

#### **Exemplos de Teste**

**Teste 1: Cliente sem CNPJ**
```
Mensagem: "Quanto custa uma bateria?"
Contexto: (vazio)
Esperado: Confiança baixa → AGUARDAR APROVAÇÃO
```

**Teste 2: Cliente com CNPJ**
```
Mensagem: "Quanto custa uma bateria?"
Contexto: CNPJ = "12.345.678/0001-90"
Esperado: Confiança média-alta → Depende do limiar
```

**Teste 3: Cliente no meio do fluxo**
```
Mensagem: "Preciso de 60Ah"
Contexto: Estado = "aguardando_modelo"
Esperado: Confiança alta → ENVIAR DIRETO
```

---

## 📚 COMO USAR

### PASSO 1: Executar SQL no Supabase

Execute o arquivo `database/aprendizado-e-simulador.sql` no Supabase:

1. Acesse https://supabase.com/dashboard
2. Database → SQL Editor
3. New Query
4. Copie todo o conteúdo de `aprendizado-e-simulador.sql`
5. Cole e clique em **RUN**
6. Verifique se 3 novas tabelas foram criadas:
   - `historico_decisoes`
   - `pesos_aprendizado`
   - `simulacoes`

### PASSO 2: Testar o Simulador

1. Acesse http://localhost:5174
2. Vá na aba **"Configurações de IA"** (ícone Bot)
3. Desça até **"Simulador de Conversa"**
4. Teste mensagens diferentes
5. Observe a confiança e decisão

### PASSO 3: Ativar Aprendizado

**O aprendizado é AUTOMÁTICO!** Não precisa fazer nada.

Quando você:
- ✅ **Aprovar** uma mensagem → Sistema registra
- ✏️ **Editar** uma mensagem → IA aprende que errou
- ❌ **Recusar** uma mensagem → IA ajusta pesos automaticamente

### PASSO 4: Monitorar Estatísticas

1. Acesse a aba **"Configurações de IA"**
2. Veja o painel **"Sistema de Aprendizado"**
3. Monitore a taxa de acerto
4. Versão dos pesos aumenta quando há ajustes

---

## 🏗️ ARQUITETURA TÉCNICA

### Backend

**Módulos Criados:**
```
alice/
  ├─ learning_system.py        # Sistema de aprendizado
  ├─ simulator.py               # Simulador de conversas
  ├─ learning_endpoints.py      # API endpoints
  └─ intelligent_controller.py  # Integração (modificado)
```

**Banco de Dados:**
```sql
-- Registra todas as decisões
historico_decisoes (
  mensagem_usuario,
  resposta_ia,
  confianca_inicial,
  decisao_sistema,
  decisao_humana,  -- Feedback
  foi_correto      -- Auto-calculado
)

-- Pesos dinâmicos do algoritmo
pesos_aprendizado (
  peso_cnpj_validado,
  peso_fluxo_estruturado,
  limiar_confianca_alta,
  taxa_acerto,
  versao  -- Incrementa a cada ajuste
)

-- Simulações (sandbox)
simulacoes (
  mensagens,
  contexto_simulado,
  resposta_ia,
  confianca,
  decisao
)
```

### Frontend

**Componentes React:**
```typescript
components/
  ├─ Simulator.tsx       # Simulador de conversas
  ├─ LearningStats.tsx   # Estatísticas de aprendizado
  └─ Dashboard.tsx       # Integração (modificado)
```

### API Endpoints

```
POST /api/learning/feedback
  → Registra feedback humano (aprovado/recusado/editado)

GET /api/learning/pesos/{empresa_id}
  → Retorna pesos atuais do algoritmo

GET /api/learning/estatisticas/{empresa_id}
  → Retorna taxa de acerto e métricas

POST /api/learning/simulador/rapido
  → Executa simulação rápida (sem salvar)

POST /api/learning/simulador/criar
  → Cria simulação persistente

POST /api/learning/simulador/{id}/executar
  → Executa simulação salva
```

### Fluxo de Aprendizado

```
┌──────────────────────────────────────────────────┐
│ 1. IA gera resposta para cliente                │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│ 2. IntelligentController decide                 │
│    - Enviar direto (alta confiança)              │
│    - Aguardar aprovação (baixa confiança)        │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│ 3. LearningSystem.registrar_decisao()           │
│    - Salva: mensagem, resposta, confiança        │
│    - Salva: decisão do sistema                   │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│ 4. Humano dá feedback (aprovação/recusa)        │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│ 5. LearningSystem.registrar_feedback()          │
│    - Compara decisão IA vs humana                │
│    - Marca foi_correto = True/False              │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼ (se foi_correto = False)
┌──────────────────────────────────────────────────┐
│ 6. LearningSystem._ajustar_pesos()              │
│    - Ajusta pesos do algoritmo                   │
│    - Incrementa versão                           │
│    - Atualiza taxa de acerto                     │
└──────────────────────────────────────────────────┘
```

---

## 🎯 PRÓXIMOS PASSOS

Agora que o sistema está pronto, você pode:

1. **Execute o SQL** no Supabase (`database/aprendizado-e-simulador.sql`)
2. **Teste o Simulador** com mensagens reais
3. **Ative a IA** em modo ATENÇÃO
4. **Aprove/Recuse mensagens** → Sistema aprende automaticamente
5. **Monitore a taxa de acerto** crescendo

**Meta:** Chegar em 90%+ de taxa de acerto para deixar a IA rodar sozinha em modo LIGADO com auto-aprovação!

---

## 🚀 DIFERENCIAIS

✅ **Machine Learning sem bibliotecas pesadas** (não precisa TensorFlow/PyTorch)
✅ **Aprendizado 100% automático** (ajusta sozinho)
✅ **Simulador seguro** (teste sem risco)
✅ **Integrado ao fluxo existente** (funciona com IntelligentController)
✅ **Interface intuitiva** (React com métricas visuais)
✅ **Escalável** (funciona com 10 ou 10.000 mensagens/dia)

---

**Criado com 🧠 + 💪 para a Alice - LC Baterias**

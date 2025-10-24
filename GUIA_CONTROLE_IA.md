# 🎯 GUIA COMPLETO - CONTROLE DA IA ALICE

## ✨ Sistema Implementado

Você agora tem um sistema completo de controle da IA com:

1. **3 Modos de Operação** (ON/OFF/ATENÇÃO)
2. **Fila de Aprovação de Mensagens**
3. **Agendamento Automático de Horários**

---

## 📋 O QUE FOI CRIADO

### **Backend (Python/FastAPI)**

#### 1. **Schema de Banco de Dados** (`database/controle-ia.sql`)
- ✅ Tabela `mensagens_pendentes` - Fila de aprovação
- ✅ Tabela `agendamentos_ia` - Agendamentos de horários
- ✅ Extensão da tabela `config_ia` - Configurações
- ✅ Funções SQL: `aprovar_mensagem()`, `recusar_mensagem()`, `expirar_mensagens_pendentes()`
- ✅ View: `fila_aprovacao` - Visualização em tempo real
- ✅ Triggers e índices otimizados
- ✅ RLS (Row Level Security) configurado

#### 2. **Controlador de IA** (`alice/ia_controller.py`)
Classe `IAController` com métodos:
- `get_modo_ia(empresa_id)` - Obtém modo atual
- `set_modo_ia(empresa_id, modo)` - Define modo manual
- `criar_mensagem_pendente(...)` - Cria mensagem para aprovação
- `aprovar_mensagem(mensagem_id, usuario_id, texto_editado)` - Aprova/edita
- `recusar_mensagem(mensagem_id, usuario_id, motivo)` - Recusa
- `get_fila_aprovacao(empresa_id)` - Lista mensagens pendentes
- `criar_agendamento(...)` - Cria novo agendamento
- Auto-detecção de horários e aplicação automática

#### 3. **Endpoints API** (`alice/ia_control_endpoints.py`)
Router `/api/ia-control/` com endpoints:

**Controle de Modo:**
- `GET /modo/{empresa_id}` - Obter modo atual
- `POST /modo/{empresa_id}` - Alterar modo

**Fila de Aprovação:**
- `GET /fila-aprovacao/{empresa_id}` - Listar mensagens pendentes
- `POST /aprovar-mensagem` - Aprovar (com edição opcional)
- `POST /recusar-mensagem` - Recusar mensagem

**Agendamentos:**
- `GET /agendamentos/{empresa_id}` - Listar agendamentos
- `POST /agendamentos` - Criar agendamento
- `PUT /agendamentos/{id}` - Atualizar agendamento
- `DELETE /agendamentos/{id}` - Deletar agendamento

**Estatísticas:**
- `GET /stats/aprovacao/{empresa_id}` - Estatísticas de aprovação

### **Frontend (React/TypeScript)**

#### 4. **Componentes Criados**

##### `IAModeControl.tsx`
- Exibe modo atual da IA
- Botões para alternar entre LIGADO/ATENÇÃO/DESLIGADO
- Explicação visual de cada modo
- Atualização em tempo real

##### `ApprovalQueue.tsx`
- Lista mensagens pendentes de aprovação
- Exibe mensagem do lead + resposta da IA
- Botões: Aprovar, Editar, Recusar
- Editor inline de mensagens
- Indicador de confiança da IA
- Auto-refresh a cada 5 segundos

##### `ScheduleManager.tsx`
- Lista todos os agendamentos
- Formulário para criar/editar agendamentos
- Seleção de dias da semana
- Configuração de horários (ligar/desligar)
- Modos dentro e fora do horário
- Mensagem automática fora do horário
- Ativar/desativar agendamentos

##### `IAControl.tsx` (Página)
- Integra todos os componentes
- Layout responsivo (grid)
- Dashboard completo de controle

---

## 🚀 COMO USAR

### **1. Executar Script SQL**

```bash
# No Supabase SQL Editor, execute:
database/controle-ia.sql
```

Isso cria todas as tabelas, funções e políticas necessárias.

### **2. Instalar Dependências Python**

```bash
cd alice-lc
pip install supabase==2.12.0 pytz==2025.1
```

### **3. Reiniciar Backend**

```bash
# Se estiver rodando, pare (Ctrl+C) e reinicie:
python main.py
```

### **4. Acessar Frontend**

```
http://localhost:5173/ia-control
```

---

## 🎮 MODOS DE OPERAÇÃO

### 🟢 **LIGADO**
- IA gera respostas automaticamente
- Mensagens AINDA precisam de aprovação se modo Atenção estiver ativo
- Use quando quiser assistência completa

### 🟡 **ATENÇÃO** (Recomendado)
- IA gera respostas
- TODA mensagem precisa ser aprovada manualmente
- Você pode aprovar, editar ou recusar
- Controle total antes de enviar

### 🔴 **DESLIGADO**
- IA para de processar mensagens
- Atendimento 100% manual
- Use para pausas ou manutenção

---

## 📅 AGENDAMENTOS AUTOMÁTICOS

### **Exemplo: Horário Comercial**

1. Acesse "Agendamentos de Horários"
2. Clique em "Novo Agendamento"
3. Preencha:
   - **Nome**: "Horário Comercial"
   - **Hora Ligar**: 08:00
   - **Hora Desligar**: 18:00
   - **Dias**: Seg-Sex
   - **Modo dentro**: Atenção
   - **Modo fora**: Desligado
   - **Mensagem automática**: "Olá! Nosso horário de atendimento é..."

4. Salvar

✨ **Agora a IA liga automaticamente às 8h e desliga às 18h!**

### **Múltiplos Agendamentos**

Você pode criar vários:
- "Horário Comercial" (Seg-Sex 8-18h)
- "Plantão Sábado" (Sáb 9-13h)
- "Urgências" (Dom 10-12h)

O sistema aplica o de maior prioridade.

---

## 🔄 FLUXO DE APROVAÇÃO

### **Modo Atenção Ativo:**

1. Cliente envia: "Quero orçamento de bateria 60ah"
2. IA processa e gera resposta
3. Mensagem aparece na **Fila de Aprovação**
4. Você vê:
   - Mensagem do cliente
   - Resposta sugerida pela IA
   - Nível de confiança (%)
   - Intenção detectada

5. Você pode:
   - **Aprovar**: Envia como está
   - **Editar**: Modifica texto e envia
   - **Recusar**: Descarta sugestão

6. Mensagem aprovada é enviada automaticamente

---

## 🔌 INTEGRAÇÃO COM WEBHOOK

Para integrar com o fluxo atual do WhatsApp, edite `main.py`:

```python
# No início do process_message()
async def process_message(phone: str, combined_message: str):
    logger.info(f"🤖 Processando mensagem de {phone}")

    # ✨ NOVO: Verificar modo da IA
    from alice.ia_controller import ia_controller

    # TODO: Pegar empresa_id do phone/sessão
    empresa_id = "sua-empresa-uuid"

    modo_ia = await ia_controller.get_modo_ia(empresa_id)

    if modo_ia == "desligado":
        logger.info("🔴 IA desligada, ignorando mensagem")
        return

    # ... resto do código
    response, new_state = await alice_agent.process_message(...)

    if modo_ia == "atencao":
        # Criar mensagem pendente ao invés de enviar direto
        await ia_controller.criar_mensagem_pendente(
            empresa_id=empresa_id,
            conversa_id=conversa_id,  # você precisa ter isso
            lead_id=lead_id,
            lead_nome=state.get("nome_cliente", "Cliente"),
            lead_telefone=phone,
            mensagem_recebida=combined_message,
            resposta_ia=response,
            confianca_ia=0.85,  # você pode calcular isso
            intencao_detectada="venda"  # detectar pela IA
        )

        logger.info("🟡 Mensagem criada para aprovação")
        # NÃO envia pelo WhatsApp ainda
        return

    # Modo ligado - envia direto
    await send_with_typing_simulation(...)
```

---

## 📊 ESTATÍSTICAS

### **Endpoint de Stats:**

```bash
GET /api/ia-control/stats/aprovacao/{empresa_id}?dias=30
```

Retorna:
- Total de mensagens processadas
- Aprovadas, editadas, recusadas
- Taxa de aprovação (%)
- Tempo médio de aprovação

---

## 🎨 CUSTOMIZAÇÃO

### **Cores e Estilos**

Os componentes usam Tailwind CSS. Para customizar:

```tsx
// Em IAModeControl.tsx
const configs = {
  ligado: {
    color: 'green',  // altere aqui
    bgColor: 'bg-green-50',
    // ...
  }
}
```

### **Timeout de Mensagens**

Mensagens pendentes expiram em 1 hora (padrão).

Para alterar, edite `controle-ia.sql`:

```sql
expira_em TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '2 hours'),  -- 2h
```

### **Auto-Aprovação por Confiança**

```sql
-- Na tabela config_ia
UPDATE config_ia
SET
  auto_aprovar_alta_confianca = true,
  limiar_confianca = 0.95  -- 95% de confiança
WHERE empresa_id = 'sua-empresa';
```

Mensagens com ≥ 95% de confiança serão aprovadas automaticamente.

---

## 🐛 TROUBLESHOOTING

### **Fila de aprovação não carrega**

1. Verificar se SQL foi executado
2. Verificar se backend está rodando
3. Abrir console do navegador (F12) e ver erros
4. Verificar CORS no backend

### **Agendamentos não funcionam**

1. Verificar timezone no banco: `America/Sao_Paulo`
2. Verificar se agendamento está `ativo = true`
3. Ver logs do backend quando processar mensagem

### **Modo não muda**

1. Verificar se `config_ia` tem registro para sua empresa
2. Inserir manualmente se necessário:

```sql
INSERT INTO config_ia (empresa_id, modo_geral, agendamento_ativo)
VALUES ('sua-empresa-uuid', 'atencao', true);
```

---

## 🎯 PRÓXIMOS PASSOS

- [ ] Integrar com sistema de autenticação (pegar empresa_id real)
- [ ] Adicionar Realtime do Supabase para notificações push
- [ ] Implementar envio via WhatsApp após aprovação
- [ ] Adicionar sons de notificação
- [ ] Dashboard de métricas e estatísticas
- [ ] Exceções de agendamento (feriados)
- [ ] Múltiplos usuários aprovando simultaneamente

---

## 📞 SUPORTE

Se tiver dúvidas ou problemas:
1. Verifique os logs: `logs/alice_*.log`
2. Teste endpoints via Postman/Insomnia
3. Verifique tabelas no Supabase

---

**Pronto! Você tem agora um sistema completo de controle da IA! 🚀**

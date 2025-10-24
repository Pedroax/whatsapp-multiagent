# 📊 Dashboard Analytics da IA - Alice Multiagente

## 🎯 Visão Geral

Dashboard completo de analytics exclusivo para **Super Administradores**, mostrando métricas detalhadas de performance da IA Alice em vendas e atendimento.

---

## 🔐 Controle de Acesso

### Níveis de Permissão:
- ✅ **Super Admin**: Acesso total ao Analytics
- ❌ **Admin**: Sem acesso ao Analytics
- ❌ **Agente**: Sem acesso ao Analytics

---

## 📈 Métricas Principais

### 1. **Receita Total (IA)**
- 💰 Valor total de vendas fechadas pela IA
- 📊 Comparação percentual com período anterior
- 🎯 Mostra apenas vendas confirmadas (API `enviar_pedido` acionada)

### 2. **Pedidos Fechados**
- 🛒 Quantidade de pedidos completados pela IA
- ✅ Pedidos onde o cliente confirmou e a IA enviou via API
- 📈 Taxa de crescimento vs período anterior

### 3. **Conversas Totais**
- 💬 Total de pessoas que falaram com a IA
- 👥 Inclui todas as conversas iniciadas
- 🔢 Tracking de leads únicos

### 4. **Taxa de Conversão**
- 🎯 % de conversas que viraram vendas
- 📊 Fórmula: (Pedidos Fechados / Conversas Totais) × 100
- 🏆 Benchmark de performance

---

## 🔥 Métricas Secundárias

### 5. **Ticket Médio**
- 💵 Valor médio por pedido fechado
- 📊 Indicador de qualidade das vendas
- 📈 Tendência de crescimento

### 6. **Negócios Fechados**
- ✅ Total de deals concluídos
- 🎉 Vendas confirmadas pelo cliente

### 7. **Leads Pendentes** ⚠️
- ❗ Clientes que INICIARAM mas NÃO completaram
- 📞 Requer ação humana (ligar)
- 💰 Valor potencial em risco

### 8. **Tempo de Resposta**
- ⚡ Velocidade média da IA
- 🚀 Em segundos
- 🎯 Meta: < 1 minuto

---

## 📊 Funil de Conversão

Visualização do pipeline de vendas:

1. **Conversas Iniciadas** (100%)
2. **Produtos Apresentados** (75%)
3. **Cotações Enviadas** (37%)
4. **Pedidos Fechados** (25%)

---

## 🏆 Top Produtos

Ranking dos 5 produtos mais vendidos pela IA:

- 🥇 1º lugar (medalha ouro)
- 🥈 2º lugar (medalha prata)
- 🥉 3º lugar (medalha bronze)
- 4º e 5º lugares

**Dados mostrados:**
- Nome do produto
- Quantidade vendida
- Receita total gerada

---

## 🔴 Leads Pendentes (Crítico)

### O que são?
Clientes que:
- ✅ Iniciaram conversa com a IA
- ✅ Demonstraram interesse
- ✅ Receberam cotação
- ❌ **NÃO completaram o pedido**

### Por que são importantes?
- 💰 Representam vendas potenciais
- 📞 Requerem follow-up humano
- 🎯 Alta taxa de conversão quando contatados

### Informações de cada lead:
- 👤 Nome do cliente
- 📱 Telefone
- 💬 Última mensagem enviada
- 💵 Valor estimado do pedido
- ⏰ Tempo desde última interação
- 📞 **Botão "Ligar Agora"**

### Ação Recomendada:
1. Verificar leads com maior valor
2. Priorizar os mais recentes (< 24h)
3. Ligar e completar a venda
4. Atualizar status no sistema

---

## 🎨 Filtros de Período

Visualize dados por:
- 📅 **Hoje**: Últimas 24 horas
- 📅 **7 dias**: Última semana
- 📅 **30 dias**: Último mês
- 📅 **Customizar**: Escolha datas específicas

---

## 💡 Insights de Performance

### Alta Performance
- 🎯 IA convertendo melhor que humanos
- 📊 Comparação automática
- ✅ Indicadores positivos

### Horário de Pico
- 🕐 Identifica horários de maior volume
- 📈 Sugere reforço humano
- ⏰ Otimização de recursos

### Recuperação de Leads
- 💰 Valor total em leads pendentes
- 📞 Quantidade de contatos necessários
- 🎯 Potencial de recuperação

---

## 🔄 Como a IA Alimenta o Dashboard

### 1. **Ao Confirmar Pedido**
```python
# Quando cliente confirma o pedido
response = await enviar_pedido(pedido_json)

if response["sucesso"]:
    # Dashboard automaticamente registra:
    # - +1 Pedido Fechado
    # - + R$ valor_total em Receita
    # - Atualiza Taxa de Conversão
    # - Adiciona produto ao Top Produtos
```

### 2. **Ao Iniciar Conversa**
```python
# Toda nova conversa incrementa
conversas_totais += 1
```

### 3. **Lead Pendente**
```python
# Quando cliente não completa após cotação
if cotacao_enviada and not pedido_confirmado:
    leads_pendentes.append({
        "nome": cliente_nome,
        "telefone": cliente_telefone,
        "valor_estimado": valor_cotacao,
        "ultima_mensagem": ultima_msg,
        "timestamp": agora
    })
```

### 4. **Produto Vendido**
```python
# Ao fechar venda
for produto in pedido["produtos"]:
    top_produtos.incrementar(
        nome=produto["nome"],
        quantidade=produto["quantidade"],
        receita=produto["valor_total"]
    )
```

---

## 📤 Exportação de Relatórios

Botão "Exportar" permite download de:
- 📊 Relatório PDF completo
- 📈 Excel com dados detalhados
- 📋 CSV para análises externas

---

## 🚀 Próximos Passos

### Para Integrar com Backend:

1. **Criar endpoint de métricas:**
```python
@app.get("/api/analytics/metrics")
async def get_analytics_metrics(
    period: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    # Retornar métricas do banco
    pass
```

2. **Criar endpoint de leads pendentes:**
```python
@app.get("/api/analytics/pending-leads")
async def get_pending_leads():
    # Buscar conversas sem pedido
    pass
```

3. **Webhook para atualizar em tempo real:**
```python
# Ao enviar pedido com sucesso
await analytics.registrar_venda(
    valor=valor_total,
    produtos=produtos,
    cliente_id=cliente_id
)
```

---

## 🎯 KPIs Recomendados

| Métrica | Meta | Status Atual |
|---------|------|--------------|
| Taxa de Conversão | > 20% | 25.4% ✅ |
| Tempo de Resposta | < 60s | 45s ✅ |
| Ticket Médio | > R$ 1.500 | R$ 1.675 ✅ |
| Leads Recuperados | > 70% | - |

---

**Criado por**: Alice Multiagente
**Versão**: 1.0.0
**Data**: 2025-10-17

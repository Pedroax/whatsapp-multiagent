# 🚨 COMANDOS DE EMERGÊNCIA - ALICE LC BATERIAS

Use estes comandos quando algo der errado em produção.

---

## 🔴 EMERGÊNCIA 1: Sistema Travou / Não Responde

### Sintomas:
- Alice não está respondendo mensagens
- Frontend não carrega
- Clientes reclamando que não recebem resposta

### Solução Rápida:

```bash
ssh root@138.68.13.174 "systemctl restart alice-backend"
```

Aguarde 10 segundos e teste novamente.

### Verificar se voltou:

```bash
ssh root@138.68.13.174 "systemctl status alice-backend"
```

✅ Deve aparecer: **active (running)**

---

## 🔴 EMERGÊNCIA 2: Ver o que está acontecendo AGORA

### Ver logs em tempo real:

```bash
ssh root@138.68.13.174
journalctl -u alice-backend -f
```

- Pressione **Ctrl+C** para parar
- Você verá todas as mensagens chegando e respostas sendo enviadas

---

## 🔴 EMERGÊNCIA 3: Cliente reclamou que não recebeu resposta

### Buscar logs desse cliente:

```bash
ssh root@138.68.13.174
journalctl -u alice-backend --since "30 minutes ago" --no-pager | grep "TELEFONE_AQUI"
```

Substitua `TELEFONE_AQUI` pelo número com DDI (ex: 556182563956)

### Exemplo:
```bash
journalctl -u alice-backend --since "30 minutes ago" --no-pager | grep "556182563956"
```

---

## 🔴 EMERGÊNCIA 4: Ver TODOS os erros recentes

```bash
ssh root@138.68.13.174
journalctl -u alice-backend -n 200 --no-pager | grep -E "ERROR|ERRO|❌|💥"
```

Isso mostra os últimos 200 logs e filtra só os erros.

---

## 🔴 EMERGÊNCIA 5: Pedido não foi enviado

### Ver tentativas de envio de pedidos:

```bash
ssh root@138.68.13.174
journalctl -u alice-backend --since "1 hour ago" --no-pager | grep -E "enviar_pedido|Timeout|Status Code"
```

### Ver se API está lenta:

```bash
journalctl -u alice-backend --since "1 hour ago" --no-pager | grep -E "Timeout|⏱️|demorou"
```

---

## 🔴 EMERGÊNCIA 6: Sistema caiu e não volta

### 1. Tentar reiniciar:

```bash
ssh root@138.68.13.174 "systemctl restart alice-backend"
```

### 2. Se não funcionar, ver o erro:

```bash
ssh root@138.68.13.174 "systemctl status alice-backend"
```

### 3. Ver logs do erro:

```bash
ssh root@138.68.13.174 "journalctl -u alice-backend -n 100 --no-pager"
```

### 4. Se nada funcionar, me chame! 📞

---

## 🔴 EMERGÊNCIA 7: Memória ou CPU alta

### Ver uso de recursos:

```bash
ssh root@138.68.13.174
systemctl status alice-backend
```

Procure por:
- **Memory:** Se estiver >500MB, pode ser problema
- **CPU:** Se estiver >80%, pode estar sobrecarregado

### Solução: Reiniciar

```bash
systemctl restart alice-backend
```

---

## 🔴 EMERGÊNCIA 8: Webhook parou de funcionar

### Verificar se backend está rodando:

```bash
ssh root@138.68.13.174 "systemctl is-active alice-backend"
```

Deve responder: **active**

### Testar webhook manualmente:

```bash
curl -X POST http://138.68.13.174/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'
```

Deve responder algo (não erro 502 ou 503).

---

## 🔴 EMERGÊNCIA 9: Limpar tudo e começar do zero

### ⚠️ CUIDADO: Isso apaga TODAS as sessões ativas!

```bash
ssh root@138.68.13.174
systemctl stop alice-backend
systemctl start alice-backend
```

Isso reinicia completamente o sistema.

---

## 🔴 EMERGÊNCIA 10: Ver últimas 50 mensagens processadas

```bash
ssh root@138.68.13.174
journalctl -u alice-backend -n 200 --no-pager | grep "Processando mensagem"
```

Mostra quais clientes a Alice atendeu recentemente.

---

## 📞 QUANDO ME CHAMAR:

Me chame se:
- ❌ Sistema não volta após reiniciar
- ❌ Erros que você não entende
- ❌ Cliente importante com problema urgente
- ❌ API da Fausoft com problema
- ❌ Perda de mensagens

### O que me enviar:
1. **Print/texto do erro** que apareceu
2. **Telefone do cliente** (se aplicável)
3. **Horário** que aconteceu
4. **O que você já tentou fazer**

---

## 🎯 COMANDOS RÁPIDOS (COPIAR E COLAR)

### Reiniciar:
```bash
ssh root@138.68.13.174 "systemctl restart alice-backend && sleep 5 && systemctl status alice-backend"
```

### Ver logs em tempo real:
```bash
ssh root@138.68.13.174 "journalctl -u alice-backend -f"
```

### Ver erros das últimas 2 horas:
```bash
ssh root@138.68.13.174 "journalctl -u alice-backend --since '2 hours ago' --no-pager | grep ERROR"
```

### Buscar por telefone:
```bash
ssh root@138.68.13.174 "journalctl -u alice-backend --since '1 hour ago' --no-pager | grep '5561XXXXXXXX'"
```

### Ver status:
```bash
ssh root@138.68.13.174 "systemctl status alice-backend --no-pager"
```

---

## 💡 DICAS IMPORTANTES

1. **Sempre olhe os logs primeiro** antes de reiniciar
2. **Anote o horário do problema** para buscar nos logs
3. **Copie o erro completo** se precisar da minha ajuda
4. **Reiniciar resolve 80% dos problemas**
5. **Logs ficam salvos por 7 dias** - não se perca!

---

## ✅ CHECKLIST DE DIAGNÓSTICO

Quando algo der errado, siga esta ordem:

- [ ] 1. Backend está rodando? (`systemctl status alice-backend`)
- [ ] 2. Tem erros recentes? (`grep ERROR`)
- [ ] 3. Cliente específico? Busque o telefone dele
- [ ] 4. Tentou reiniciar? (`systemctl restart`)
- [ ] 5. Problema persistiu? Me chame!

---

**Última atualização:** 28/10/2025

**Servidor:** 138.68.13.174
**Serviço:** alice-backend
**Webhook:** http://138.68.13.174/webhook/whatsapp

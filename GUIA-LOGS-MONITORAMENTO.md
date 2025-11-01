# 📋 Guia de Logs e Monitoramento - Alice LC Baterias

Este guia te ensina a monitorar e debugar o sistema Alice em produção.

## 🔐 Acesso ao Servidor

Primeiro, conecte-se ao servidor:

```bash
ssh root@138.68.13.174
```

---

## 📊 Comandos Essenciais

### 1. Ver Logs em Tempo Real
Acompanha tudo que está acontecendo AGORA:

```bash
journalctl -u alice-backend -f
```

- Os logs vão aparecer conforme chegam mensagens
- **Pressione Ctrl+C** para parar
- **Use isso para:** Ver se a Alice está respondendo em tempo real

---

### 2. Ver Últimas 100 Linhas
Mostra as 100 mensagens mais recentes:

```bash
journalctl -u alice-backend -n 100 --no-pager
```

- **Use isso para:** Ver rapidamente o que aconteceu

---

### 3. Buscar por Telefone Específico
Encontra todas as interações com um cliente:

```bash
journalctl -u alice-backend --no-pager | grep "556199660063"
```

Substitua `556199660063` pelo telefone que você quer investigar.

- **Use isso para:** Debugar problema de um cliente específico

---

### 4. Ver Apenas Erros
Filtra somente mensagens de erro:

```bash
journalctl -u alice-backend --no-pager | grep -E "ERROR|ERRO|❌|💥"
```

- **Use isso para:** Encontrar rapidamente o que deu errado

---

### 5. Ver Logs das Últimas 30 Minutos

```bash
journalctl -u alice-backend --since "30 minutes ago" --no-pager
```

Outras opções:
- `"1 hour ago"` - última hora
- `"2 hours ago"` - últimas 2 horas
- `"today"` - tudo de hoje

- **Use isso para:** Ver o que aconteceu recentemente

---

### 6. Ver Logs de Hoje

```bash
journalctl -u alice-backend --since today --no-pager
```

- **Use isso para:** Revisar tudo que aconteceu hoje

---

### 7. Buscar por Palavra-Chave
Encontra logs relacionados a uma função específica:

```bash
journalctl -u alice-backend --no-pager | grep "enviar_pedido"
```

Exemplos úteis:
- `grep "enviar_pedido"` - Ver tentativas de envio de pedidos
- `grep "verificar_cliente"` - Ver buscas de clientes
- `grep "consultar_baterias"` - Ver consultas de preços
- `grep "Timeout"` - Ver problemas de timeout na API

---

### 8. Combinar Filtros
Busca erros de um telefone específico:

```bash
journalctl -u alice-backend --no-pager | grep "556199660063" | grep "ERROR"
```

Busca pedidos das últimas 2 horas:

```bash
journalctl -u alice-backend --since "2 hours ago" --no-pager | grep "enviar_pedido"
```

---

## 🔧 Comandos de Manutenção

### Ver Status do Serviço

```bash
systemctl status alice-backend
```

Mostra:
- ✅ Se está rodando (active/running)
- ❌ Se está parado (inactive/dead)
- 💥 Se deu erro (failed)

---

### Reiniciar o Serviço
Se algo travou ou deu erro:

```bash
systemctl restart alice-backend
```

Aguarde 5 segundos e verifique se voltou:

```bash
systemctl status alice-backend
```

---

### Ver Uso de Memória/CPU

```bash
systemctl status alice-backend
```

Procure por:
- **Memory:** quanto de RAM está usando
- **CPU:** quanto de processamento está usando

---

## 🎯 Casos de Uso Práticos

### Caso 1: Cliente reclamou que a Alice não respondeu

```bash
# 1. Conecta no servidor
ssh root@138.68.13.174

# 2. Busca o telefone dele
journalctl -u alice-backend --since "1 hour ago" --no-pager | grep "5561XXXXXXXX"

# 3. Procura por erros nessa conversa
journalctl -u alice-backend --since "1 hour ago" --no-pager | grep "5561XXXXXXXX" | grep "ERROR"
```

---

### Caso 2: Pedido não foi para o sistema

```bash
# 1. Busca tentativas de envio de pedido
journalctl -u alice-backend --since "2 hours ago" --no-pager | grep "enviar_pedido"

# 2. Procura por timeouts ou erros
journalctl -u alice-backend --since "2 hours ago" --no-pager | grep -E "enviar_pedido|Timeout|Status Code"
```

---

### Caso 3: Sistema travou

```bash
# 1. Verifica se está rodando
systemctl status alice-backend

# 2. Se não estiver, reinicia
systemctl restart alice-backend

# 3. Monitora para ver se voltou
journalctl -u alice-backend -f
```

---

### Caso 4: Verificar se API do cliente está lenta

```bash
journalctl -u alice-backend --since "1 hour ago" --no-pager | grep -E "Timeout|⏱️|demorou"
```

---

## 📝 Salvando Logs para Análise

Se quiser salvar os logs num arquivo para analisar depois:

```bash
journalctl -u alice-backend --since today --no-pager > logs-hoje.txt
```

Baixa o arquivo para seu computador:

```bash
exit  # Sai do servidor
scp root@138.68.13.174:~/logs-hoje.txt .
```

---

## 🚨 Indicadores de Problema

Fique atento a estas mensagens nos logs:

### ❌ Erros Críticos
```
ERROR | ❌ | 💥
```

### ⏱️ Timeouts (API lenta)
```
Timeout | ⏱️ | demorou muito
```

### 🔧 Tool Failures
```
Tool enviar_pedido retornou conteúdo vazio
Erro ao registrar pedido
```

### 🔌 Problemas de Conexão
```
Connection refused
Failed to connect
Network unreachable
```

---

## 📞 Suporte

Se encontrar algo que não consegue resolver:

1. **Copie o erro completo** dos logs
2. **Anote o telefone do cliente** (se aplicável)
3. **Anote o horário** que aconteceu
4. Me envie essas informações

---

## 🎓 Dicas Extras

- **Logs são limpos automaticamente** após 7 dias
- **Use Ctrl+C** para parar qualquer comando
- **Use setas ↑↓** para navegar no histórico de comandos
- **Digite `exit`** para sair do servidor
- **Logs ficam em ordem cronológica** (mais antigo → mais recente)

---

**Última atualização:** 28/10/2025

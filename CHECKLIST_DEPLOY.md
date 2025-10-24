# ✅ CHECKLIST DE DEPLOY - ALICE LC BATERIAS

## 📋 STATUS ATUAL

### ✅ CONCLUÍDO
- [x] Tool `verificar_cliente` implementada e testada
- [x] Tool `buscar_baterias` implementada e testada
- [x] Tool `consultar_baterias` implementada e testada
- [x] Tool `enviar_pedido` implementada e testada
- [x] State management configurado
- [x] Prompt da Alice completo
- [x] Estrutura do projeto criada

### ❌ PENDENTE

#### 1. DEPENDÊNCIAS PYTHON
- [ ] Instalar anthropic
- [ ] Instalar fastapi + uvicorn
- [ ] Instalar langgraph
- [ ] Instalar redis (opcional)
- [ ] Instalar aiohttp
- [ ] Instalar pydantic-settings
- [ ] Verificar todas instalações

**Comando:**
```bash
pip install anthropic fastapi uvicorn langgraph redis aiohttp pydantic-settings
```

#### 2. CONFIGURAÇÃO DO .ENV
- [ ] Adicionar ANTHROPIC_API_KEY válida
- [ ] Verificar EVOLUTION_API_URL
- [ ] Verificar EVOLUTION_API_KEY
- [ ] Verificar EVOLUTION_INSTANCE_NAME
- [ ] Configurar REDIS_URL (ou deixar padrão)

**Arquivo:** `.env`

#### 3. TESTES LOCAIS
- [ ] Testar importação de todos módulos
- [ ] Executar `python main.py` e verificar se inicia
- [ ] Testar endpoint `http://localhost:8000/health`
- [ ] Verificar logs de inicialização

#### 4. REDIS (OPCIONAL)
- [ ] Verificar se Redis está rodando (localhost:6379)
- [ ] OU desabilitar Redis no código (usar apenas memória)

**Para verificar Redis:**
```bash
redis-cli ping
```

#### 5. EVOLUTION API
- [ ] Verificar se instância está conectada
- [ ] Configurar webhook para `http://SEU-IP:8000/webhook/whatsapp`
- [ ] Testar recebimento de mensagens

**Para verificar:**
```bash
curl http://localhost:8000/instance/status
```

#### 6. TESTE END-TO-END
- [ ] Enviar mensagem "Olá" via WhatsApp
- [ ] Verificar se Alice responde
- [ ] Testar fluxo completo de pedido
- [ ] Verificar logs em tempo real

#### 7. PRODUÇÃO (APÓS TESTES)
- [ ] Configurar servidor em nuvem
- [ ] Configurar HTTPS
- [ ] Configurar processo supervisor (PM2, systemd)
- [ ] Configurar backup de logs
- [ ] Monitoramento de erros

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

1. **Instalar dependências**
2. **Configurar ANTHROPIC_API_KEY**
3. **Testar servidor local**
4. **Configurar webhook**
5. **Teste de mensagem no WhatsApp**

---

## ⚠️ PROBLEMAS CONHECIDOS

### Dependências no Windows
- `numpy` requer compilador C++ no Windows
- Solução: Usar versão pré-compilada ou WSL

### Redis Opcional
- Sistema funciona sem Redis (usa memória)
- Para produção, recomendado usar Redis

---

## 📞 SUPORTE

Se encontrar erros, verifique:
1. Logs em `logs/alice_*.log` (se DEBUG=true)
2. Console do terminal
3. Response do endpoint `/health`

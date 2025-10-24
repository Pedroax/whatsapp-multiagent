# 🚀 Alice Multiagente - LC Baterias

Sistema completo de atendimento automatizado via WhatsApp com IA multiagente.

## 📋 INÍCIO RÁPIDO

### Windows
```bash
# Duplo clique em:
START_SERVER.bat
```

### Linux/Mac
```bash
chmod +x start_server.sh
./start_server.sh

# Para parar:
./stop_server.sh
```

## 🌐 Acessar Sistema

- **Frontend**: http://localhost:5174
- **Backend**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

**Login de teste**:
- Email: admin@lcbaterias.com
- Senha: admin123

## ✅ STATUS DO PROJETO

### 100% Implementado

✅ **Backend FastAPI**
- Alice Agent (IA conversacional)
- Sistema de Analytics integrado
- Controle inteligente de mensagens
- Sistema de transferência para departamentos
- Aprovação de mensagens
- Sistema de aprendizado

✅ **Frontend React**
- Dashboard de Analytics (conectado com IA)
- Gestão de conversas (Supabase Realtime)
- Controle de modo IA
- Fila de aprovação
- Simulador de conversas
- Estatísticas de aprendizado

✅ **Integrações**
- WhatsApp (Evolution API)
- Supabase (Database + Realtime)
- Anthropic Claude / OpenAI

## 📚 Documentação Completa

Ver arquivo: `DEPLOY_COMPLETO.md`

## 🔧 Configuração Necessária

1. **Executar SQLs no Supabase** (ver `database/` pasta)
2. **Configurar .env** com suas chaves
3. **Configurar webhook** da Evolution API
4. **Substituir APIs mock** por APIs reais da LC Baterias

## 📊 Funcionalidades Principais

### Para Super Admin
- Analytics completo com métricas da IA
- Controle global do modo IA
- Gestão de usuários e departamentos
- Simulador de conversas
- Estatísticas de aprendizado

### Para Departamentos
- Conversas filtradas por departamento
- Aprovação de mensagens da IA
- Envio manual de mensagens
- Notificações em tempo real

### IA Alice
- Atendimento automatizado 24/7
- Consulta de produtos
- Envio de cotações
- Fechamento de pedidos
- Transferência inteligente para humanos
- Aprendizado contínuo

## 🎯 Próximos Passos para Produção

1. Criar tabelas no Supabase (executar SQLs)
2. Configurar domínio e SSL
3. Apontar webhook WhatsApp
4. Substituir APIs mock por reais
5. Alterar senhas padrão
6. Configurar backup automático

## 📞 Suporte

- Logs: `logs/alice_*.log`
- Health check: `http://localhost:8000/health`
- Documentação: `DEPLOY_COMPLETO.md`

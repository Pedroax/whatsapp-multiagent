# Alice - Agente de Vendas LC Baterias 🤖

Sistema de IA conversacional para atendimento via WhatsApp da LC Baterias, construído com LangGraph e Claude.

## 🎯 Características

- ✅ **Gerenciamento de estado robusto** - Máquina de estados com 17 etapas controladas
- ✅ **Validação rigorosa** - Nunca perde dados críticos entre etapas
- ✅ **Debouncing inteligente** - Agrupa mensagens enviadas em sequência rápida
- ✅ **Simulação humana** - Split de mensagens longas com typing indicators
- ✅ **Persistência** - Sessões salvas em Redis com fallback em memória
- ✅ **5 ferramentas integradas** - APIs da LC Baterias
- ✅ **Webhook Evolution API** - Recebe mensagens do WhatsApp em tempo real

## 📁 Estrutura do Projeto

```
alice-lc/
├── alice/
│   ├── __init__.py
│   ├── agent.py              # Core do agente LangGraph
│   ├── state.py              # Gerenciamento de estados
│   ├── prompt.py             # System prompt completo
│   ├── tools.py              # 5 ferramentas (APIs)
│   └── session_manager.py    # Gerenciador de sessões
├── whatsapp/
│   ├── __init__.py
│   └── evolution_api.py      # Cliente Evolution API
├── utils/
│   ├── debouncer.py          # Debouncing de mensagens
│   └── message_splitter.py   # Split inteligente
├── config.py                 # Configurações
├── main.py                   # Aplicação FastAPI
├── requirements.txt
└── .env.example
```

## 🚀 Instalação

### 1. Clone e configure

```bash
cd alice-lc
cp .env.example .env
```

### 2. Configure as variáveis de ambiente

Edite o arquivo `.env`:

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-...

# Evolution API
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua_chave_aqui
EVOLUTION_INSTANCE_NAME=alice-instance

# LC Baterias APIs (você vai configurar depois)
LC_API_BASE_URL=https://api.lcbaterias.com.br
LC_API_KEY=sua_chave_aqui

# Redis (opcional)
REDIS_URL=redis://localhost:6379

# App
DEBUG=true
LOG_LEVEL=INFO
DEBOUNCE_SECONDS=5.0
```

### 3. Instale dependências

```bash
# Crie ambiente virtual
python -m venv venv

# Ative (Windows)
venv\Scripts\activate

# Ative (Linux/Mac)
source venv/bin/activate

# Instale
pip install -r requirements.txt
```

### 4. Rode a aplicação

```bash
python main.py
```

A aplicação estará rodando em `http://localhost:8000`

## 🔧 Configuração do WhatsApp

### Evolution API

1. Instale Evolution API: https://github.com/EvolutionAPI/evolution-api
2. Crie uma instância
3. Configure o webhook apontando para: `http://seu-servidor:8000/webhook/whatsapp`
4. Conecte o WhatsApp

## 📡 Endpoints

### Webhook (Evolution API)
```
POST /webhook/whatsapp
```

### Health Check
```
GET /health
```

### Resetar Sessão
```
POST /session/reset/{phone}
```

### Status da Instância
```
GET /instance/status
```

## 🛠️ Próximos Passos

### Implementar as Tools

As 5 tools estão criadas como **stubs** em [alice/tools.py](alice/tools.py:55):

1. **verificar_cliente** - Validar CNPJ
2. **buscar_baterias** - Buscar modelos
3. **consultar_baterias** - Consultar preços
4. **enviar_pedido** - Criar pedido
5. **transferir_para_humano** - Transferir atendimento

Você precisará substituir os mocks pelas chamadas reais às APIs da LC Baterias.

### Exemplo de implementação real:

```python
@tool(args_schema=VerificarClienteInput)
async def verificar_cliente(cnpj: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.lc_api_base_url}/api/v1/clientes/verificar",
            headers={
                "Authorization": f"Bearer {settings.lc_api_key}",
                "Content-Type": "application/json"
            },
            json={"cnpj": cnpj},
            timeout=10.0
        )

        return response.json()
```

## 🧪 Testes

Para testar localmente sem WhatsApp, você pode enviar mensagens direto via API:

```python
import httpx

# Simula webhook
payload = {
    "event": "messages.upsert",
    "data": {
        "key": {
            "remoteJid": "5561999999999@s.whatsapp.net",
            "fromMe": False
        },
        "message": {
            "conversation": "Olá!"
        }
    }
}

response = httpx.post("http://localhost:8000/webhook/whatsapp", json=payload)
print(response.json())
```

## 📊 Logs

Logs são salvos em `logs/alice_{timestamp}.log` quando `DEBUG=true`

## 🔒 Segurança

- Nunca commite o arquivo `.env`
- Use variáveis de ambiente em produção
- Configure HTTPS em produção
- Valide webhooks com assinaturas

## 🐛 Troubleshooting

### Alice não responde
- Verifique se `ANTHROPIC_API_KEY` está configurada
- Veja os logs em `logs/`
- Teste o endpoint `/health`

### Mensagens não chegam
- Verifique webhook da Evolution API
- Confirme que instância está conectada (`/instance/status`)
- Veja logs do Evolution API

### Redis não conecta
- Sistema funciona em memória se Redis falhar
- Verifique `REDIS_URL`
- Redis é opcional para desenvolvimento

## 📝 Licença

Propriedade da LC Baterias

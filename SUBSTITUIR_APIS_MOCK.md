# 🔄 GUIA: Substituir APIs Mock por APIs Reais

## 📍 Localização das APIs Mock

Todas as APIs mock estão no arquivo: `alice/tools.py`

## 🛠️ APIs que Precisam ser Substituídas

### 1. verificar_dados_cliente()
**Linha**: ~730
**O que faz**: Verifica se cliente já existe no sistema

**Mock atual**:
```python
async def verificar_dados_cliente(cpf_cnpj: str) -> Dict[str, Any]:
    # Simulação - SUBSTITUIR por API real
    if cpf_cnpj in ["12345678901", "12345678000190"]:
        return {
            "cliente_encontrado": True,
            "nome": "João Silva",
            "email": "joao@example.com",
            ...
        }
```

**Como substituir**:
```python
async def verificar_dados_cliente(cpf_cnpj: str) -> Dict[str, Any]:
    import httpx
    from config import settings

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.lc_api_base_url}/clientes/verificar",
                headers={
                    "Authorization": f"Bearer {settings.lc_api_key}",
                    "Content-Type": "application/json"
                },
                params={"cpf_cnpj": cpf_cnpj},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "cliente_encontrado": data.get("encontrado", False),
                    "nome": data.get("nome"),
                    "email": data.get("email"),
                    "telefone": data.get("telefone"),
                    "endereco": data.get("endereco"),
                    "credito_aprovado": data.get("credito_aprovado", False)
                }
            elif response.status_code == 404:
                return {"cliente_encontrado": False}
            else:
                logger.error(f"Erro API LC: {response.status_code}")
                return {"erro": "Erro ao consultar cliente"}

        except Exception as e:
            logger.error(f"Erro ao chamar API LC: {e}")
            return {"erro": str(e)}
```

---

### 2. buscar_baterias()
**Linha**: ~790
**O que faz**: Busca baterias por aplicação (veículo)

**Mock atual**:
```python
async def buscar_baterias(aplicacao: str) -> Dict[str, Any]:
    # Simulação - SUBSTITUIR
    return {
        "baterias_encontradas": [...]
    }
```

**Como substituir**:
```python
async def buscar_baterias(aplicacao: str) -> Dict[str, Any]:
    import httpx
    from config import settings

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.lc_api_base_url}/baterias/buscar",
                headers={"Authorization": f"Bearer {settings.lc_api_key}"},
                params={"aplicacao": aplicacao},
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"erro": "Baterias não encontradas"}

        except Exception as e:
            logger.error(f"Erro API buscar_baterias: {e}")
            return {"erro": str(e)}
```

---

### 3. consultar_baterias()
**Linha**: ~830
**O que faz**: Consulta disponibilidade e preço de baterias específicas

**Mock atual**:
```python
async def consultar_baterias(codigos: List[str]) -> Dict[str, Any]:
    # Simulação - SUBSTITUIR
    return {
        "produtos": [...]
    }
```

**Como substituir**:
```python
async def consultar_baterias(codigos: List[str]) -> Dict[str, Any]:
    import httpx
    from config import settings

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.lc_api_base_url}/baterias/consultar",
                headers={"Authorization": f"Bearer {settings.lc_api_key}"},
                json={"codigos": codigos},
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"erro": "Erro ao consultar baterias"}

        except Exception as e:
            logger.error(f"Erro API consultar_baterias: {e}")
            return {"erro": str(e)}
```

---

### 4. consultar_prazos_pagamento()
**Linha**: ~870
**O que faz**: Consulta formas de pagamento disponíveis

**Mock atual**:
```python
async def consultar_prazos_pagamento() -> Dict[str, Any]:
    # Simulação - SUBSTITUIR
    return {
        "formas_pagamento": [...]
    }
```

**Como substituir**:
```python
async def consultar_prazos_pagamento() -> Dict[str, Any]:
    import httpx
    from config import settings

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.lc_api_base_url}/pagamentos/formas",
                headers={"Authorization": f"Bearer {settings.lc_api_key}"},
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"erro": "Erro ao consultar formas de pagamento"}

        except Exception as e:
            logger.error(f"Erro API prazos: {e}")
            return {"erro": str(e)}
```

---

### 5. enviar_pedido() ⚠️ MAIS IMPORTANTE
**Linha**: ~900
**O que faz**: Envia pedido final para o sistema da LC Baterias

**Mock atual**:
```python
async def enviar_pedido(...) -> Dict[str, Any]:
    # Simulação - SUBSTITUIR
    numero_pedido = f"PED-{randint(10000, 99999)}"
    return {
        "pedido_criado": True,
        "numero_pedido": numero_pedido,
        ...
    }
```

**Como substituir**:
```python
async def enviar_pedido(
    cpf_cnpj: str,
    produtos: List[Dict],
    forma_pagamento: str,
    endereco_entrega: Dict,
    observacoes: str
) -> Dict[str, Any]:
    import httpx
    from config import settings

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "cliente": {"cpf_cnpj": cpf_cnpj},
                "produtos": produtos,
                "pagamento": {"forma": forma_pagamento},
                "entrega": endereco_entrega,
                "observacoes": observacoes
            }

            response = await client.post(
                f"{settings.lc_api_base_url}/pedidos",
                headers={
                    "Authorization": f"Bearer {settings.lc_api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0  # Timeout maior para criação de pedido
            )

            if response.status_code in [200, 201]:
                data = response.json()

                # ⚠️ IMPORTANTE: Só registrar analytics se pedido foi criado COM SUCESSO
                if data.get("pedido_criado"):
                    from alice.analytics import analytics_tracker
                    analytics_tracker.registrar_pedido_fechado(
                        phone=phone,  # Você precisa passar phone como parâmetro
                        numero_pedido=data.get("numero_pedido"),
                        valor_total=data.get("valor_total"),
                        produtos=produtos,
                        cliente_nome=data.get("cliente_nome", "Cliente")
                    )

                return data
            else:
                logger.error(f"Erro ao criar pedido: {response.status_code}")
                return {
                    "pedido_criado": False,
                    "erro": "Erro ao processar pedido"
                }

        except Exception as e:
            logger.error(f"Erro API enviar_pedido: {e}")
            return {
                "pedido_criado": False,
                "erro": str(e)
            }
```

---

## 🔑 Configurar Variáveis de Ambiente

Adicionar no `.env`:

```env
LC_API_BASE_URL=https://api.lcbaterias.com.br/v1
LC_API_KEY=sua-chave-api-aqui
```

E no `config.py`:

```python
class Settings(BaseSettings):
    # ... outras configs ...

    # LC Baterias API
    lc_api_base_url: str = "https://api.lcbaterias.com.br/v1"
    lc_api_key: str = "default-key"

    class Config:
        env_file = ".env"
```

---

## ✅ Checklist de Substituição

- [ ] verificar_dados_cliente() substituído
- [ ] buscar_baterias() substituído
- [ ] consultar_baterias() substituído
- [ ] consultar_prazos_pagamento() substituído
- [ ] enviar_pedido() substituído ⚠️ CRÍTICO
- [ ] Variáveis LC_API_BASE_URL e LC_API_KEY configuradas
- [ ] Testado em ambiente de desenvolvimento
- [ ] Testado em ambiente de produção

---

## 🧪 Como Testar

### 1. Testar manualmente cada função:

```python
# test_lc_api.py
import asyncio
from alice.tools import verificar_dados_cliente, buscar_baterias, consultar_baterias, enviar_pedido

async def test():
    # Testar verificação de cliente
    result = await verificar_dados_cliente("12345678901")
    print("Cliente:", result)

    # Testar busca de baterias
    result = await buscar_baterias("Honda Civic 2020")
    print("Baterias:", result)

    # ... etc

asyncio.run(test())
```

### 2. Testar via WhatsApp:
- Enviar mensagem para o bot
- Pedir cotação
- Finalizar pedido
- Verificar se pedido foi criado no sistema real da LC

---

## ⚠️ IMPORTANTE

**NÃO** substituir as APIs antes de:
1. Ter documentação completa da API da LC Baterias
2. Ter chave de API válida
3. Testar em ambiente de desenvolvimento primeiro
4. Validar formato de resposta esperado vs. retornado

**Manter mock enquanto estiver em desenvolvimento!**

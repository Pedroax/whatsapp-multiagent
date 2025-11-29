"""Tools/Ferramentas da Alice para integração com APIs"""
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import httpx
import hashlib
from datetime import datetime
from loguru import logger
from config import settings


# ============================================================================
# SCHEMAS DAS TOOLS
# ============================================================================

class VerificarClienteInput(BaseModel):
    """Schema para verificação de cliente"""
    cnpj: str = Field(description="CNPJ apenas com números (ex: 33164789000123)")


class BuscarBateriasInput(BaseModel):
    """Schema para busca de baterias"""
    termo: str = Field(description="Termo de busca exato que o cliente disse (ex: '60ah selada', 'CLP 60 VD')")


class ConsultarBateriasInput(BaseModel):
    """Schema para consulta de preços"""
    query: str = Field(
        description="Formato: 'CODIGO:QTD|SUCATA|EMP:X' (ex: 'CLP-60 VD:10|SIM|EMP:1')"
    )


class EnviarPedidoInput(BaseModel):
    """Schema para envio de pedido"""
    pedido_json: Dict[str, Any] = Field(
        description="JSON completo do pedido conforme especificação"
    )


class TransferirHumanoInput(BaseModel):
    """Schema para transferir para humano"""
    motivo: str = Field(description="Motivo da transferência")
    departamento: str = Field(
        description="Departamento para onde transferir: 'vendas', 'assistencia', 'financeiro', 'suporte' ou 'geral'"
    )


class ConsultarPrazosInput(BaseModel):
    """Schema para consultar prazos de pagamento disponíveis"""
    quantidade_total: int = Field(description="Quantidade total de baterias do pedido")
    valor_total: float = Field(description="Valor total do pedido em reais")


class ConsultarFormasPagamentoInput(BaseModel):
    """Schema para consultar formas de pagamento (Dinheiro, PIX, Cartão, Boleto)"""
    tipo_pagamento: str = Field(
        description="Tipo de pagamento: 'A VISTA' ou 'A PRAZO' (ou '1' para à vista, '2' para a prazo)"
    )


class ConsultarPrazosPorFormaInput(BaseModel):
    """Schema para consultar prazos baseado na forma de pagamento escolhida"""
    codigo_pagamento: int = Field(
        description="Código da forma de pagamento escolhida (ex: 1=Dinheiro, 4=PIX, 5=Boleto)"
    )
    quantidade_total: int = Field(
        description="Quantidade total de baterias do pedido"
    )


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def gerar_autenticacao() -> Dict[str, str]:
    """
    Gera timestamp e token SHA1 para autenticação na API Fausoft.

    Returns:
        Dict com timestamp e token
    """
    # Gerar timestamp no formato YmdHis
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # String secreta da API
    SECRET = "8baf9bcb5c12e2686a1367cc89c3e2d1da7555d0"

    # Gerar token SHA1
    string_para_hash = timestamp + SECRET
    token = hashlib.sha1(string_para_hash.encode()).hexdigest()

    logger.debug(f"🔐 Auth gerada - Timestamp: {timestamp}, Token: {token[:16]}...")

    return {
        "timestamp": timestamp,
        "token": token
    }


# ============================================================================
# IMPLEMENTAÇÃO DAS TOOLS
# ============================================================================

@tool(args_schema=VerificarClienteInput)
async def verificar_cliente(cnpj: str) -> Dict[str, Any]:
    """
    Verifica regularidade do cliente pelo CNPJ na API Fausoft.

    IMPORTANTE: A resposta desta tool contém dados críticos que devem ser salvos:
    - codigo_cliente: usar em todas as operações futuras
    - codigo_empresa: usar para consultar preços corretos (cada empresa tem tabela própria)
    - nome_empresa: nome da loja do cliente

    Args:
        cnpj: CNPJ apenas com números (14 dígitos)

    Returns:
        Dict com dados do cliente ou erro. Campos principais:
        - sucesso: bool indicando se a operação foi bem-sucedida
        - cliente_encontrado: bool indicando se cliente existe na base
        - codigo_cliente: código do cliente (GUARDAR NO STATE)
        - codigo_empresa: código da empresa do cliente (GUARDAR NO STATE - essencial para preços)
        - nome_loja: nome da empresa (GUARDAR NO STATE)
        - documento: CNPJ formatado
        - endereco_completo: endereço completo da loja
        - mensagem_para_ia: mensagem formatada para usar na resposta
    """
    logger.info(f"🔍 Verificando cliente: {cnpj}")

    try:
        # Limpar CNPJ (apenas números)
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))

        if len(cnpj_limpo) != 14:
            logger.warning(f"⚠️ CNPJ inválido: {cnpj_limpo} ({len(cnpj_limpo)} dígitos)")
            return {
                "sucesso": False,
                "cliente_encontrado": False,
                "erro": f"CNPJ deve conter 14 dígitos. Recebido: {len(cnpj_limpo)} dígitos",
                "cnpj_recebido": cnpj
            }

        # Gerar autenticação
        auth = gerar_autenticacao()

        # Montar payload
        payload = {
            "timestamp": auth["timestamp"],
            "token": auth["token"],
            "action": "select",
            "instance": "clientes",
            "filter": {
                "field": "documento",
                "value": cnpj_limpo
            }
        }

        logger.debug(f"📤 Payload: {payload}")

        # Chamar API Fausoft
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.grupolc.app.br/api/",
                json=payload,
                timeout=15.0
            )

            logger.debug(f"📥 Status Code: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP: {response.status_code}")
                return {
                    "sucesso": False,
                    "cliente_encontrado": False,
                    "erro": f"Erro HTTP {response.status_code}",
                    "cnpj_pesquisado": cnpj_limpo
                }

            data = response.json()
            logger.debug(f"📥 Resposta: {data}")

            # Verificar status da API
            if data.get("status") != "success":
                logger.error(f"❌ API retornou erro: {data.get('message', 'Erro desconhecido')}")
                return {
                    "sucesso": False,
                    "cliente_encontrado": False,
                    "erro": f"API retornou erro: {data.get('message', 'Erro desconhecido')}",
                    "resposta_api": data
                }

            # Verificar se encontrou cliente
            dataset = data.get("dataset", [])
            if not dataset or len(dataset) == 0:
                logger.warning(f"⚠️ Cliente não encontrado: {cnpj_limpo}")
                return {
                    "sucesso": True,
                    "cliente_encontrado": False,
                    "status_cliente": "nao_encontrado",
                    "mensagem": "Cliente não encontrado na base de dados",
                    "cnpj_pesquisado": cnpj_limpo
                }

            # Cliente encontrado
            cliente = dataset[0]

            resultado = {
                "sucesso": True,
                "cliente_encontrado": True,
                "status_cliente": "regular",

                # DADOS CRÍTICOS - DEVEM SER SALVOS NO STATE
                "codigo_cliente": cliente.get("codigo"),
                "codigo_empresa": cliente.get("empresa", "1"),  # Default empresa 1
                "nome_loja": cliente.get("nome"),

                # Dados complementares
                "documento": cliente.get("documento"),
                "endereco_completo": f"{cliente.get('endereco', '')}, {cliente.get('numero', '')} - {cliente.get('bairro', '')}",
                "cidade": cliente.get("cidade"),
                "estado": cliente.get("estado"),
                "cep": cliente.get("cep"),
                "telefone": cliente.get("telefone"),
                "celular": cliente.get("celular"),
                "email": cliente.get("email"),

                # Mensagem formatada para IA
                "mensagem_para_ia": f"Cliente identificado: {cliente.get('nome')}. Empresa: {cliente.get('empresa', '1')}",

                # Dados completos para debug
                "dados_completos": cliente,
                "timestamp_consulta": datetime.now().isoformat()
            }

            logger.success(f"✅ Cliente encontrado: {resultado['nome_loja']} (Empresa: {resultado['codigo_empresa']})")

            return resultado

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout ao verificar cliente: {cnpj}")
        return {
            "sucesso": False,
            "cliente_encontrado": False,
            "erro": "Timeout na conexão com a API",
            "cnpj_pesquisado": cnpj
        }
    except Exception as e:
        logger.error(f"💥 Erro ao verificar cliente: {str(e)}")
        return {
            "sucesso": False,
            "cliente_encontrado": False,
            "erro": f"Erro de comunicação: {str(e)}",
            "cnpj_pesquisado": cnpj
        }


@tool(args_schema=BuscarBateriasInput)
async def buscar_baterias(termo: str) -> Dict[str, Any]:
    """
    Busca modelos de baterias disponíveis na API de busca inteligente.

    Esta tool aceita diversos formatos de busca do cliente e a API interpreta automaticamente:
    - Por amperagem: "60", "100ah", "75"
    - Por tipo: "selada", "selada de 60"
    - Por marca: "cral", "moura"
    - Por linha: "prime", "top line"
    - Por garantia: "24 meses"
    - Combinações: "60 cral prime", "selada de 100"

    Args:
        termo: Termo de busca EXATO que o cliente disse (não modificar/interpretar)

    Returns:
        Dict com:
        - sucesso: bool
        - criterios: dict com critérios identificados pela API
        - resultado: string formatada com lista de baterias (cada linha = 1 bateria)
        - total: número total de baterias encontradas
        - timestamp: timestamp da consulta
    """
    logger.info(f"🔍 Buscando baterias: '{termo}'")

    try:
        # Chamar API de busca inteligente
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://72.60.137.243:5000/buscar",
                json={"modelo": termo},
                timeout=15.0
            )

            logger.debug(f"📥 Status Code: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP: {response.status_code}")
                return {
                    "sucesso": False,
                    "erro": f"Erro HTTP {response.status_code}",
                    "total": 0,
                    "resultado": "",
                    "termo_buscado": termo
                }

            data = response.json()
            logger.debug(f"📥 Resposta: {data}")

            # Verificar se retornou resultados
            total = data.get("total", 0)
            resultado = data.get("resultado", "")

            if total == 0 or not resultado:
                logger.warning(f"⚠️ Nenhuma bateria encontrada para: '{termo}'")
                return {
                    "sucesso": True,
                    "baterias_encontradas": False,
                    "total": 0,
                    "resultado": "",
                    "criterios": data.get("criterios", {}),
                    "termo_buscado": termo,
                    "mensagem": "Nenhuma bateria encontrada com esses critérios"
                }

            # Sucesso - baterias encontradas
            logger.success(f"✅ Encontradas {total} baterias para '{termo}'")

            return {
                "sucesso": True,
                "baterias_encontradas": True,
                "total": total,
                "resultado": resultado,  # String formatada com lista de baterias
                "criterios": data.get("criterios", {}),
                "termo_buscado": termo,
                "timestamp": data.get("timestamp", datetime.now().isoformat())
            }

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout ao buscar baterias: '{termo}'")
        return {
            "sucesso": False,
            "erro": "Timeout na conexão com a API de busca",
            "total": 0,
            "resultado": "",
            "termo_buscado": termo
        }
    except Exception as e:
        logger.error(f"💥 Erro ao buscar baterias: {str(e)}")
        return {
            "sucesso": False,
            "erro": f"Erro de comunicação: {str(e)}",
            "total": 0,
            "resultado": "",
            "termo_buscado": termo
        }


@tool(args_schema=ConsultarBateriasInput)
async def consultar_baterias(query: str) -> Dict[str, Any]:
    """
    Consulta preços de baterias na API Fausoft com cálculo automático.

    Formato obrigatório: "CODIGO:QTD|SUCATA|EMP:X"

    Exemplos:
    - "CLP-60 VD:10|SIM|EMP:1" (1 produto)
    - "CLP-60 VD:15,CL-45 VD:5|NAO|EMP:2" (múltiplos produtos)

    Args:
        query: String formatada: "CODIGO:QTD,CODIGO2:QTD2|SIM/NAO|EMP:X"

    Returns:
        Dict com:
        - sucesso: bool
        - produtos: lista com cada produto e seus valores
        - valor_total_geral: valor total da cotação
        - mensagem_formatada: mensagem pronta para enviar ao cliente
    """
    logger.info(f"💰 Consultando preços: '{query}'")

    try:
        # Parse da query: "CLP-60 VD:20|SIM|EMP:1"
        partes = query.split('|')

        if len(partes) < 3:
            logger.error(f"❌ Formato inválido: {query}")
            return {
                "sucesso": False,
                "erro": "Formato esperado: CODIGO:QTD|SIM/NAO|EMP:X",
                "query_recebida": query
            }

        produtos_str, sucata_str, empresa_str = partes

        # Extrair código da empresa
        import re
        empresa_match = re.search(r'EMP:(\d+)', empresa_str, re.IGNORECASE)
        if not empresa_match:
            logger.error(f"❌ Código da empresa não encontrado: {empresa_str}")
            return {
                "sucesso": False,
                "erro": "Código da empresa não encontrado (EMP:X)",
                "query_recebida": query
            }

        codigo_empresa = int(empresa_match.group(1))

        # Processar produtos
        produtos_pedido = []
        for item in produtos_str.split(','):
            if ':' not in item:
                continue
            codigo, qtd = item.split(':')
            produtos_pedido.append({
                "codigo": codigo.strip(),
                "quantidade": int(qtd.strip())
            })

        if not produtos_pedido:
            logger.error(f"❌ Nenhum produto encontrado: {produtos_str}")
            return {
                "sucesso": False,
                "erro": "Nenhum produto válido encontrado",
                "query_recebida": query
            }

        # Determinar sucata (1 = SIM, 0 = NAO)
        com_troca_sucata = sucata_str.upper().strip() == 'SIM'
        sucata_int = 1 if com_troca_sucata else 0

        logger.debug(f"📊 Produtos: {produtos_pedido}")
        logger.debug(f"📊 Com sucata: {com_troca_sucata} (valor: {sucata_int})")
        logger.debug(f"📊 Empresa: {codigo_empresa}")

        # Gerar autenticação
        auth = gerar_autenticacao()

        # Criar string com códigos separados por vírgula para filtro IN
        codigos_string = ', '.join([p["codigo"] for p in produtos_pedido])

        # Montar payload para API Fausoft
        payload = {
            "timestamp": auth["timestamp"],
            "token": auth["token"],
            "action": "select",
            "instance": "produtos",
            "filter": {
                "field": "nome_curto",
                "in": codigos_string
            }
        }

        logger.debug(f"📤 Payload: {payload}")

        # Chamar API Fausoft
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.grupolc.app.br/api/",
                json=payload,
                timeout=20.0
            )

            logger.debug(f"📥 Status Code: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP: {response.status_code}")
                return {
                    "sucesso": False,
                    "erro": f"Erro HTTP {response.status_code}",
                    "query_recebida": query
                }

            data = response.json()
            logger.debug(f"📥 Resposta: {data}")

            # Verificar status da API
            if data.get("status") != "success":
                logger.error(f"❌ API retornou erro")
                return {
                    "sucesso": False,
                    "erro": f"API retornou erro: {data.get('message', 'Erro desconhecido')}",
                    "resposta_api": data
                }

            # Processar dataset
            dataset = data.get("dataset", [])
            if not dataset:
                logger.warning(f"⚠️ Nenhum produto encontrado na API")
                return {
                    "sucesso": False,
                    "erro": "Nenhum produto encontrado",
                    "query_recebida": query
                }

            # Processar cada produto
            produtos_resultado = []
            valor_total_geral = 0.0

            for produto_pedido in produtos_pedido:
                codigo_busca = produto_pedido["codigo"]
                quantidade = produto_pedido["quantidade"]

                # Buscar produto no dataset
                produto_encontrado = None
                for prod in dataset:
                    if prod.get("nome_curto") == codigo_busca:
                        produto_encontrado = prod
                        break

                if not produto_encontrado:
                    logger.warning(f"⚠️ Produto não encontrado: {codigo_busca}")
                    produtos_resultado.append({
                        "sucesso": False,
                        "codigo": codigo_busca,
                        "erro": "Produto não encontrado",
                        "quantidade": quantidade
                    })
                    continue

                # Filtrar preço correto
                precos = produto_encontrado.get("precos", [])
                preco_correto = None

                for preco in precos:
                    # Verificar empresa
                    empresa_preco = preco.get("empresa", "0")
                    # Se empresa estiver vazia ou inválida, pular
                    if not empresa_preco or empresa_preco == "":
                        continue

                    try:
                        if int(empresa_preco) != codigo_empresa:
                            continue
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ Empresa inválida no preço: {empresa_preco}")
                        continue

                    # Verificar sucata
                    if int(preco.get("sucata", 0)) != sucata_int:
                        continue

                    # Verificar quantidade
                    qtd_min = int(preco.get("quantidade_minima", 0))
                    qtd_max = int(preco.get("quantidade_maxima", 999999))

                    if qtd_min <= quantidade <= qtd_max:
                        preco_correto = preco
                        break

                if not preco_correto:
                    logger.warning(
                        f"⚠️ Preço não encontrado para {codigo_busca}: "
                        f"empresa={codigo_empresa}, sucata={sucata_int}, qtd={quantidade}"
                    )
                    produtos_resultado.append({
                        "sucesso": False,
                        "codigo": codigo_busca,
                        "erro": "Preço não encontrado para essa combinação",
                        "quantidade": quantidade,
                        "empresa": codigo_empresa,
                        "com_troca_sucata": com_troca_sucata
                    })
                    continue

                # Calcular valores
                valor_unitario = float(preco_correto.get("valor_unitario", 0))
                valor_total = valor_unitario * quantidade
                valor_total_geral += valor_total

                produtos_resultado.append({
                    "sucesso": True,
                    "codigo": codigo_busca,
                    "nome_completo": produto_encontrado.get("nome_completo"),
                    "marca": produto_encontrado.get("marca"),
                    "quantidade": quantidade,
                    "valor_unitario": f"{valor_unitario:.2f}",
                    "valor_total": f"{valor_total:.2f}",
                    "empresa": codigo_empresa,
                    "com_troca_sucata": com_troca_sucata
                })

                logger.success(
                    f"✅ {codigo_busca}: {quantidade}x R$ {valor_unitario:.2f} = R$ {valor_total:.2f}"
                )

            # Formatar mensagem para IA
            mensagem_linhas = []
            if com_troca_sucata:
                mensagem_linhas.append("Cotação calculada (com troca de sucata):\n")
            else:
                mensagem_linhas.append("Cotação calculada (sem troca de sucata):\n")

            for idx, prod in enumerate([p for p in produtos_resultado if p.get("sucesso")], 1):
                mensagem_linhas.append(
                    f"{idx}. {prod['quantidade']}x {prod['codigo']} - {prod['marca']} = "
                    f"R$ {prod['valor_total']}"
                )

            mensagem_linhas.append(f"\nValor total geral: R$ {valor_total_geral:.2f}")

            mensagem_formatada = "\n".join(mensagem_linhas)

            resultado_final = {
                "sucesso": True,
                "produtos": produtos_resultado,
                "valor_total_geral": f"{valor_total_geral:.2f}",
                "mensagem_formatada": mensagem_formatada,
                "debug": {
                    "empresa_solicitada": codigo_empresa,
                    "criterios": {
                        "sucata": sucata_int
                    },
                    "total_produtos": len(produtos_pedido),
                    "processados_com_sucesso": len([p for p in produtos_resultado if p.get("sucesso")])
                }
            }

            logger.success(f"✅ Cotação total: R$ {valor_total_geral:.2f}")

            return resultado_final

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout ao consultar preços")
        return {
            "sucesso": False,
            "erro": "Timeout na conexão com a API",
            "query_recebida": query
        }
    except Exception as e:
        logger.error(f"💥 Erro ao consultar preços: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "sucesso": False,
            "erro": f"Erro de comunicação: {str(e)}",
            "query_recebida": query
        }


@tool
async def enviar_pedido(pedido_json: str) -> Dict[str, Any]:
    """
    Envia pedido para a API Fausoft com normalização robusta de produtos.

    NORMALIZAÇÃO AUTOMÁTICA:
    - Aceita produtos como array, objeto único, ou string JSON
    - Garante que API sempre receba array válido
    - Converte tipos automaticamente (int, float, string)
    - Trata campos opcionais (prazo_sucata, parcelas_cartao)

    Args:
        pedido_json: Dict com campos:
            - codigo_cliente: int (obrigatório)
            - codigo_empresa: int (obrigatório)
            - produtos: array/object (obrigatório)
            - base_troca: int 0/1 (obrigatório)
            - tipo_pagamento: int (obrigatório)
            - forma_pagamento: int (obrigatório)
            - prazo_pedido: string (obrigatório)
            - prazo_sucata: string (opcional, só se base_troca=1)
            - parcelas_cartao: int (opcional, só se for Cartão de Crédito - valores: 1, 2 ou 3)

    Returns:
        Dict com:
        - sucesso: bool
        - numero_pedido: int (se sucesso)
        - status_pedido: string (faturamento/financeiro)
    """
    logger.info(f"📤 Enviando pedido...")
    logger.info(f"📥 Tipo recebido: {type(pedido_json)}")
    logger.debug(f"📥 Dados recebidos: {pedido_json}")

    try:
        # Converter string para dict se necessário
        if isinstance(pedido_json, str):
            import json
            pedido_json = json.loads(pedido_json)
        elif not isinstance(pedido_json, dict):
            logger.error(f"❌ Tipo inválido: {type(pedido_json)}")
            return {
                "sucesso": False,
                "erro": f"Esperado dict ou string JSON, recebido {type(pedido_json).__name__}"
            }

        logger.info(f"✅ Dados convertidos para dict com sucesso")
        # ===================================================================
        # NORMALIZAÇÃO DE PRODUTOS (À PROVA DE FALHAS)
        # ===================================================================

        produtos_raw = pedido_json.get('produtos')

        if not produtos_raw:
            logger.error("❌ Campo 'produtos' não encontrado")
            return {
                "sucesso": False,
                "erro": "Campo 'produtos' é obrigatório",
                "dados_recebidos": pedido_json
            }

        # Normalizar produtos para array
        produtos_array = []

        # Caso 1: Já é uma lista
        if isinstance(produtos_raw, list):
            produtos_array = produtos_raw
            logger.debug(f"✓ Produtos já em formato array: {len(produtos_array)} itens")

        # Caso 2: É um dict (objeto único)
        elif isinstance(produtos_raw, dict):
            produtos_array = [produtos_raw]
            logger.debug(f"✓ Produto único convertido para array")

        # Caso 3: É uma string JSON
        elif isinstance(produtos_raw, str):
            try:
                import json
                parsed = json.loads(produtos_raw)
                if isinstance(parsed, list):
                    produtos_array = parsed
                elif isinstance(parsed, dict):
                    produtos_array = [parsed]
                else:
                    raise ValueError(f"String JSON não resultou em array/object válido")
                logger.debug(f"✓ String JSON parseada: {len(produtos_array)} itens")
            except Exception as e:
                logger.error(f"❌ Erro ao parsear produtos como JSON: {e}")
                return {
                    "sucesso": False,
                    "erro": f"Erro ao parsear produtos: {str(e)}",
                    "produtos_recebidos": produtos_raw
                }

        # Caso 4: Tipo inválido
        else:
            logger.error(f"❌ Tipo inválido para produtos: {type(produtos_raw)}")
            return {
                "sucesso": False,
                "erro": f"Produtos deve ser array, object ou string JSON. Recebido: {type(produtos_raw).__name__}",
                "produtos_recebidos": produtos_raw
            }

        # Validar que temos pelo menos 1 produto
        if not produtos_array:
            logger.error("❌ Array de produtos está vazio")
            return {
                "sucesso": False,
                "erro": "Array de produtos não pode estar vazio"
            }

        # Normalizar cada produto
        produtos_formatados = []
        for idx, produto in enumerate(produtos_array, 1):
            if not isinstance(produto, dict):
                logger.error(f"❌ Produto {idx} não é um objeto: {produto}")
                return {
                    "sucesso": False,
                    "erro": f"Produto {idx} deve ser um objeto",
                    "produto_invalido": produto
                }

            # Extrair nome do produto (aceita múltiplos nomes de campo)
            nome_produto = (
                produto.get('nome_produto') or
                produto.get('codigo_produto') or
                produto.get('codigo') or
                produto.get('nome')
            )

            if not nome_produto:
                logger.error(f"❌ Produto {idx} sem identificador")
                return {
                    "sucesso": False,
                    "erro": f"Produto {idx} precisa ter 'nome_produto', 'codigo_produto' ou 'codigo'",
                    "produto_invalido": produto
                }

            # Extrair quantidade
            quantidade = produto.get('quantidade')
            if quantidade is None:
                logger.error(f"❌ Produto {idx} sem quantidade")
                return {
                    "sucesso": False,
                    "erro": f"Produto {idx} precisa ter 'quantidade'",
                    "produto_invalido": produto
                }

            # Extrair valor unitário
            valor_unitario = produto.get('valor_unitario')
            if valor_unitario is None:
                logger.error(f"❌ Produto {idx} sem valor_unitario")
                return {
                    "sucesso": False,
                    "erro": f"Produto {idx} precisa ter 'valor_unitario'",
                    "produto_invalido": produto
                }

            # Formatar produto com tipos corretos
            produtos_formatados.append({
                "nome_produto": str(nome_produto),
                "quantidade": int(quantidade),
                "valor_unitario": float(valor_unitario)
            })

            logger.debug(f"✓ Produto {idx}: {nome_produto} x{quantidade} @ R$ {valor_unitario}")

        logger.success(f"✅ {len(produtos_formatados)} produtos normalizados com sucesso")

        # ===================================================================
        # VALIDAÇÃO DE CAMPOS OBRIGATÓRIOS
        # ===================================================================

        campos_obrigatorios = {
            'codigo_cliente': int,
            'codigo_empresa': int,
            'base_troca': int,
            'tipo_pagamento': int,
            'forma_pagamento': int,
            'prazo_pedido': str
        }

        dataset = {}

        for campo, tipo_esperado in campos_obrigatorios.items():
            valor = pedido_json.get(campo)

            if valor is None:
                logger.error(f"❌ Campo obrigatório ausente: {campo}")
                return {
                    "sucesso": False,
                    "erro": f"Campo '{campo}' é obrigatório",
                    "dados_recebidos": pedido_json
                }

            # Converter para tipo correto
            try:
                dataset[campo] = tipo_esperado(valor)
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Erro ao converter {campo}: {e}")
                return {
                    "sucesso": False,
                    "erro": f"Campo '{campo}' deve ser {tipo_esperado.__name__}",
                    "valor_recebido": valor
                }

        # Adicionar produtos formatados
        dataset['produtos'] = produtos_formatados

        # ===================================================================
        # TRATAMENTO CONDICIONAL DO PRAZO_SUCATA
        # ===================================================================

        # Só adiciona prazo_sucata se base_troca = 1
        if dataset['base_troca'] == 1:
            prazo_sucata = pedido_json.get('prazo_sucata')
            if prazo_sucata:
                dataset['prazo_sucata'] = str(prazo_sucata)
                logger.debug(f"✓ Prazo sucata incluído: {prazo_sucata}")
            else:
                logger.warning("⚠️ base_troca=1 mas prazo_sucata não fornecido")
        else:
            logger.debug("✓ Sem troca de sucata, prazo_sucata não incluído")

        # ===================================================================
        # TRATAMENTO CONDICIONAL DO PARCELAS_CARTAO (CARTÃO DE CRÉDITO)
        # ===================================================================

        # Se tiver parcelas_cartao (Cartão de Crédito), adicionar ao dataset
        parcelas_cartao = pedido_json.get('parcelas_cartao')
        if parcelas_cartao:
            try:
                dataset['parcelas_cartao'] = int(parcelas_cartao)
                logger.debug(f"✓ Parcelas do cartão incluídas: {parcelas_cartao}x")
            except (ValueError, TypeError):
                logger.warning(f"⚠️ parcelas_cartao inválido: {parcelas_cartao}")
        else:
            logger.debug("✓ Sem parcelas de cartão (não é Cartão de Crédito)")

        # ===================================================================
        # GERAR AUTENTICAÇÃO E PAYLOAD
        # ===================================================================

        auth = gerar_autenticacao()

        payload = {
            "timestamp": auth["timestamp"],
            "token": auth["token"],
            "action": "insert",
            "instance": "pedidos",
            "dataset": dataset
        }

        logger.debug(f"📤 Payload final: {payload}")

        # ===================================================================
        # ENVIAR PARA API FAUSOFT
        # ===================================================================

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.grupolc.app.br/api/",
                json=payload,
                timeout=60.0  # Aumentado para 60s pois a API está lenta
            )

            logger.debug(f"📥 Status Code: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP: {response.status_code}")
                response_text = response.text[:500] if response.text else "Sem resposta"
                return {
                    "sucesso": False,
                    "erro": f"Erro HTTP {response.status_code}",
                    "resposta": response_text
                }

            data = response.json()
            logger.debug(f"📥 Resposta: {data}")

            # Verificar status da API
            if data.get("status") != "success":
                logger.error(f"❌ API retornou erro")
                return {
                    "sucesso": False,
                    "erro": f"API retornou erro: {data.get('message', 'Erro desconhecido')}",
                    "resposta_api": data
                }

            # Sucesso!
            numero_pedido = data.get("numero_pedido")
            status_pedido = data.get("status_pedido", "desconhecido")

            logger.success(f"✅ Pedido criado: #{numero_pedido} (status: {status_pedido})")

            return {
                "sucesso": True,
                "numero_pedido": numero_pedido,
                "status_pedido": status_pedido,
                "mensagem": f"Pedido #{numero_pedido} criado com sucesso! Status: {status_pedido}",
                "resposta_completa": data
            }

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout ao enviar pedido (60s)")
        return {
            "sucesso": False,
            "erro": "A API demorou muito para responder (timeout de 60s). Pode estar com lentidão. Tente novamente ou peça ao cliente aguardar um momento.",
            "tipo_erro": "timeout"
        }
    except Exception as e:
        logger.error(f"💥 Erro ao enviar pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "sucesso": False,
            "erro": f"Erro de comunicação: {str(e)}"
        }


@tool(args_schema=TransferirHumanoInput)
async def transferir_para_humano(motivo: str, departamento: str) -> Dict[str, Any]:
    """
    Transfere atendimento para humano de um departamento específico.

    QUANDO USAR:
    - Cliente pede para falar com departamento específico
    - Cliente menciona: "quero falar com o financeiro", "preciso de assistência técnica", etc.
    - IA não consegue resolver o problema

    DEPARTAMENTOS DISPONÍVEIS:
    - 'vendas': Vendas e cotações
    - 'assistencia': Assistência técnica
    - 'financeiro': Questões financeiras, pagamentos, boletos
    - 'suporte': Suporte técnico/TI
    - 'geral': Transferência genérica (super admin)

    Args:
        motivo: Motivo da transferência
        departamento: Departamento destino

    Returns:
        Confirmação de transferência com departamento
    """
    # Normalizar departamento
    departamento_map = {
        "vendas": "vendas",
        "venda": "vendas",
        "comercial": "vendas",

        "assistencia": "assistencia-tecnica",
        "assistência": "assistencia-tecnica",
        "tecnica": "assistencia-tecnica",
        "técnica": "assistencia-tecnica",

        "financeiro": "financeiro",
        "pagamento": "financeiro",
        "boleto": "financeiro",
        "cobrança": "financeiro",

        "suporte": "suporte-ti",
        "ti": "suporte-ti",
        "tecnologia": "suporte-ti",

        "geral": "geral",
        "super": "geral",
        "admin": "geral"
    }

    dept_normalizado = departamento_map.get(departamento.lower(), "geral")

    logger.warning(f"👤 Transferindo para {dept_normalizado}: {motivo}")

    # Retornar dados estruturados para o agente processar
    return {
        "status": "transferido",
        "departamento": dept_normalizado,
        "motivo": motivo,
        "mensagem": f"Atendimento transferido para {dept_normalizado.replace('-', ' ').title()}",
        "notificar": True  # Flag para backend enviar notificação
    }


@tool(args_schema=ConsultarPrazosInput)
async def consultar_prazos_pagamento(quantidade_total: int, valor_total: float) -> Dict[str, Any]:
    """
    Consulta prazos de pagamento disponíveis na API Fausoft baseado na quantidade e valor total.

    QUANDO USAR:
    - Após o cliente confirmar os produtos e a cotação
    - ANTES de perguntar sobre forma de pagamento
    - Sempre que precisar mostrar opções de prazo disponíveis

    IMPORTANTE:
    - Esta tool DEVE ser chamada antes de perguntar ao cliente sobre pagamento
    - Os prazos retornados são específicos para a quantidade e valor informados
    - Não pergunte "à vista ou à prazo?" antes de chamar esta tool
    - Mostre as opções retornadas pela API para o cliente escolher

    Args:
        quantidade_total: Soma total de baterias do pedido (ex: 10 unidades)
        valor_total: Valor total da cotação em reais (ex: 680.50)

    Returns:
        Dict com:
        - sucesso: bool
        - prazos: lista de prazos disponíveis, cada um com:
            - codigo: código do prazo (usar ao enviar pedido)
            - condicao: "A VISTA" ou "A PRAZO"
            - prazo: descrição do prazo (ex: "A VISTA", "7 DD", "30/45 DD")
        - mensagem_formatada: mensagem pronta para apresentar ao cliente
    """
    logger.info(f"💳 Consultando prazos: {quantidade_total} baterias, R$ {valor_total:.2f}")

    try:
        # Gerar autenticação
        auth = gerar_autenticacao()

        # Montar payload
        payload = {
            "timestamp": auth["timestamp"],
            "token": auth["token"],
            "action": "select",
            "instance": "prazos",
            "dataset": {
                "quantidade_total": int(quantidade_total),
                "valor_total": float(valor_total)
            }
        }

        logger.debug(f"📤 Payload: {payload}")

        # Chamar API Fausoft
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.grupolc.app.br/api/",
                json=payload,
                timeout=15.0
            )

            logger.debug(f"📥 Status Code: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP: {response.status_code}")
                return {
                    "sucesso": False,
                    "erro": f"Erro HTTP {response.status_code}",
                    "quantidade": quantidade_total,
                    "valor": valor_total
                }

            data = response.json()
            logger.debug(f"📥 Resposta: {data}")

            # Verificar status da API
            if data.get("status") != "success":
                logger.error(f"❌ API retornou erro: {data.get('message', 'Erro desconhecido')}")
                return {
                    "sucesso": False,
                    "erro": f"API retornou erro: {data.get('message', 'Erro desconhecido')}",
                    "resposta_api": data
                }

            # Processar dataset de prazos
            dataset = data.get("dataset", [])

            if not dataset or len(dataset) == 0:
                logger.warning(f"⚠️ Nenhum prazo disponível")
                return {
                    "sucesso": False,
                    "erro": "Nenhum prazo de pagamento disponível",
                    "quantidade": quantidade_total,
                    "valor": valor_total
                }

            # Formatar prazos
            prazos_formatados = []
            for idx, prazo in enumerate(dataset, 1):
                prazos_formatados.append({
                    "codigo": prazo.get("codigo"),
                    "condicao": prazo.get("condicao"),
                    "prazo": prazo.get("prazo")
                })

            # Separar à vista e à prazo
            prazos_avista = [p for p in prazos_formatados if p["condicao"] == "A VISTA"]
            prazos_aprazo = [p for p in prazos_formatados if p["condicao"] == "A PRAZO"]

            # Formatar mensagem para o cliente
            mensagem_linhas = ["📋 Opções de pagamento disponíveis:\n"]

            if prazos_avista:
                mensagem_linhas.append("💰 À VISTA:")
                for p in prazos_avista:
                    mensagem_linhas.append(f"  • {p['prazo']}")

            if prazos_aprazo:
                if prazos_avista:
                    mensagem_linhas.append("")
                mensagem_linhas.append("📅 À PRAZO:")
                for p in prazos_aprazo:
                    mensagem_linhas.append(f"  • {p['prazo']}")

            mensagem_linhas.append("\nQual opção você prefere?")
            mensagem_formatada = "\n".join(mensagem_linhas)

            logger.success(f"✅ {len(prazos_formatados)} prazos encontrados")

            return {
                "sucesso": True,
                "total_prazos": len(prazos_formatados),
                "prazos": prazos_formatados,
                "prazos_avista": prazos_avista,
                "prazos_aprazo": prazos_aprazo,
                "mensagem_formatada": mensagem_formatada,
                "quantidade_consultada": quantidade_total,
                "valor_consultado": valor_total
            }

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout ao consultar prazos")
        return {
            "sucesso": False,
            "erro": "Timeout na conexão com a API",
            "quantidade": quantidade_total,
            "valor": valor_total
        }
    except Exception as e:
        logger.error(f"💥 Erro ao consultar prazos: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "sucesso": False,
            "erro": f"Erro de comunicação: {str(e)}",
            "quantidade": quantidade_total,
            "valor": valor_total
        }


@tool(args_schema=ConsultarFormasPagamentoInput)
async def consultar_formas_pagamento(tipo_pagamento: str) -> Dict[str, Any]:
    """
    Consulta as FORMAS de pagamento disponíveis (Dinheiro, PIX, Cartão, Boleto)
    para um tipo específico (À VISTA ou A PRAZO) na API Fausoft.

    IMPORTANTE: Esta é a PRIMEIRA consulta de pagamento. Depois desta, você deve
    chamar consultar_prazos_por_forma com o código da forma escolhida.

    Args:
        tipo_pagamento: "A VISTA", "1", "à vista" OU "A PRAZO", "2", "a prazo"

    Returns:
        Dict com lista de formas de pagamento (cada uma com código, descricao)

    Exemplo de uso no fluxo:
    1. Cliente confirma cotação: "sim"
    2. IA pergunta: "É à vista ou a prazo? 1️⃣ À vista / 2️⃣ A prazo"
    3. Cliente: "1" ou "à vista"
    4. IA chama: consultar_formas_pagamento("A VISTA")
    5. API retorna: [{"codigo": 4, "descricao": "PIX"}, {"codigo": 1, "descricao": "Dinheiro"}]
    6. IA mostra opções e aguarda escolha
    """
    try:
        # Normalizar entrada
        tipo_normalizado = tipo_pagamento.strip().upper()

        # Mapear respostas do cliente para formato da API
        if tipo_normalizado in ["1", "À VISTA", "A VISTA", "VISTA", "AVISTA"]:
            condicao = "A VISTA"
        elif tipo_normalizado in ["2", "À PRAZO", "A PRAZO", "PRAZO", "APRAZO"]:
            condicao = "A PRAZO"
        else:
            return {
                "sucesso": False,
                "erro": f"Tipo de pagamento inválido: {tipo_pagamento}. Use 'A VISTA' ou 'A PRAZO'"
            }

        logger.info(f"🔍 Consultando condições de pagamento: {condicao}")

        # Gerar autenticação
        auth = gerar_autenticacao()

        # Montar payload
        payload = {
            "timestamp": auth["timestamp"],
            "token": auth["token"],
            "action": "select",
            "instance": "pagamentos",
            "dataset": {
                "condicao_pagamento": condicao
            }
        }

        logger.debug(f"📤 Payload: {payload}")

        # Fazer requisição
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.grupolc.app.br/api/",
                json=payload,
                timeout=15.0
            )

        logger.debug(f"📥 Status Code: {response.status_code}")

        # Processar resposta
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"📥 Resposta: {data}")

            if data.get("status") == "success":
                condicoes = data.get("dataset", [])

                if not condicoes:
                    return {
                        "sucesso": False,
                        "erro": f"Nenhuma condição de pagamento encontrada para {condicao}"
                    }

                # Formatar condições para exibição
                condicoes_formatadas = []
                for idx, cond in enumerate(condicoes, 1):
                    condicoes_formatadas.append({
                        "numero": idx,
                        "descricao": cond.get("pagamento", ""),  # Campo correto da API
                        "codigo": cond.get("codigo", ""),
                        "tipo": condicao
                    })

                logger.success(f"✅ Encontradas {len(condicoes_formatadas)} formas de pagamento para {condicao}")

                return {
                    "sucesso": True,
                    "tipo_pagamento": condicao,
                    "formas": condicoes_formatadas,  # Renomeado de "condicoes" para "formas"
                    "total_formas": len(condicoes_formatadas)
                }
            else:
                error_msg = data.get("message", "Erro desconhecido")
                logger.error(f"❌ Erro na API: {error_msg}")
                return {
                    "sucesso": False,
                    "erro": error_msg
                }
        else:
            logger.error(f"❌ HTTP {response.status_code}: {response.text}")
            return {
                "sucesso": False,
                "erro": f"Erro HTTP {response.status_code}"
            }

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout ao consultar condições de pagamento")
        return {
            "sucesso": False,
            "erro": "Timeout na conexão com a API"
        }
    except Exception as e:
        logger.error(f"💥 Erro ao consultar condições: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "sucesso": False,
            "erro": f"Erro de comunicação: {str(e)}"
        }


@tool(args_schema=ConsultarPrazosPorFormaInput)
async def consultar_prazos_por_forma(codigo_pagamento: int, quantidade_total: int) -> Dict[str, Any]:
    """
    Consulta os PRAZOS disponíveis baseado na FORMA de pagamento escolhida
    e quantidade de baterias na API Fausoft.

    IMPORTANTE: Esta é a SEGUNDA consulta de pagamento, após o cliente escolher
    a forma (PIX, Dinheiro, Boleto, etc).

    Args:
        codigo_pagamento: Código da forma escolhida (ex: 1=Dinheiro, 4=PIX, 5=Boleto)
        quantidade_total: Total de baterias do pedido

    Returns:
        Dict com lista de prazos disponíveis (cada prazo com codigo, descricao)

    Exemplo de uso no fluxo:
    1. Cliente escolheu forma: "1" (PIX, código 4)
    2. IA chama: consultar_prazos_por_forma(codigo_pagamento=4, quantidade_total=10)
    3. API retorna: [{"codigo": "11", "prazo": "7 DD"}, {"codigo": "12", "prazo": "14 DD"}]
    4. IA mostra opções e aguarda escolha
    """
    try:
        logger.info(f"🔍 Consultando prazos: forma={codigo_pagamento}, qtd={quantidade_total}")

        # Gerar autenticação
        auth = gerar_autenticacao()

        # Montar payload
        payload = {
            "timestamp": auth["timestamp"],
            "token": auth["token"],
            "action": "select",
            "instance": "prazos",
            "dataset": {
                "codigo_pagamento": codigo_pagamento,
                "quantidade_total": quantidade_total
            }
        }

        logger.debug(f"📤 Payload: {payload}")

        # Fazer requisição
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.grupolc.app.br/api/",
                json=payload,
                timeout=15.0
            )

        logger.debug(f"📥 Status Code: {response.status_code}")

        # Processar resposta
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"📥 Resposta: {data}")

            if data.get("status") == "success":
                prazos = data.get("dataset", [])

                if not prazos:
                    return {
                        "sucesso": False,
                        "erro": f"Nenhum prazo encontrado para forma {codigo_pagamento} e quantidade {quantidade_total}"
                    }

                # Formatar prazos para exibição
                prazos_formatados = []
                for idx, prazo in enumerate(prazos, 1):
                    prazos_formatados.append({
                        "numero": idx,
                        "descricao": prazo.get("prazo", prazo.get("descricao", "")),
                        "codigo": prazo.get("codigo", ""),
                        "condicao": prazo.get("condicao", "")
                    })

                logger.success(f"✅ Encontrados {len(prazos_formatados)} prazos para forma {codigo_pagamento}")

                return {
                    "sucesso": True,
                    "codigo_pagamento": codigo_pagamento,
                    "quantidade_total": quantidade_total,
                    "prazos": prazos_formatados,
                    "total_prazos": len(prazos_formatados)
                }
            else:
                error_msg = data.get("message", "Erro desconhecido")
                logger.error(f"❌ Erro na API: {error_msg}")
                return {
                    "sucesso": False,
                    "erro": error_msg
                }
        else:
            logger.error(f"❌ HTTP {response.status_code}: {response.text}")
            return {
                "sucesso": False,
                "erro": f"Erro HTTP {response.status_code}"
            }

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout ao consultar prazos por forma")
        return {
            "sucesso": False,
            "erro": "Timeout na conexão com a API"
        }
    except Exception as e:
        logger.error(f"💥 Erro ao consultar prazos por forma: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "sucesso": False,
            "erro": f"Erro de comunicação: {str(e)}"
        }


# ============================================================================
# LISTA DE TOOLS PARA O AGENTE
# ============================================================================

ALICE_TOOLS = [
    verificar_cliente,
    buscar_baterias,
    consultar_baterias,
    consultar_prazos_pagamento,  # Mantida por compatibilidade (pode remover depois)
    consultar_formas_pagamento,  # API 1: Retorna formas (PIX, Dinheiro, etc)
    consultar_prazos_por_forma,  # API 2: Retorna prazos baseado na forma
    enviar_pedido,
    transferir_para_humano
]

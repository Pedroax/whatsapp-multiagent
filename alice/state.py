"""Gerenciamento de estado da conversa"""
from typing import Annotated, TypedDict, Optional, List, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from enum import Enum


class FlowState(str, Enum):
    """Estados do fluxo de atendimento"""
    INICIO = "inicio"
    AGUARDANDO_NOME = "aguardando_nome"
    AGUARDANDO_CNPJ = "aguardando_cnpj"
    VERIFICANDO_CLIENTE = "verificando_cliente"
    AGUARDANDO_INTERESSE = "aguardando_interesse"
    AGUARDANDO_MODELO = "aguardando_modelo"
    APRESENTANDO_OPCOES = "apresentando_opcoes"
    AGUARDANDO_ESCOLHA = "aguardando_escolha"
    AGUARDANDO_TERMINAL = "aguardando_terminal"
    AGUARDANDO_QUANTIDADE = "aguardando_quantidade"
    AGUARDANDO_TROCA_SUCATA = "aguardando_troca_sucata"
    CONSULTANDO_PRECOS = "consultando_precos"
    CONFIRMANDO_COTACAO = "confirmando_cotacao"
    AGUARDANDO_TIPO_PAGAMENTO = "aguardando_tipo_pagamento"
    AGUARDANDO_PRAZO_PAGAMENTO = "aguardando_prazo_pagamento"
    AGUARDANDO_PRAZO_SUCATA = "aguardando_prazo_sucata"
    ENVIANDO_PEDIDO = "enviando_pedido"
    FINALIZADO = "finalizado"
    ERRO = "erro"


class ProdutoEscolhido(BaseModel):
    """Produto escolhido pelo cliente"""
    codigo: str
    nome_completo: str
    quantidade: Optional[int] = None
    valor_unitario: Optional[float] = None
    garantia: Optional[int] = None


class ConversationState(TypedDict):
    """Estado da conversa com o cliente"""

    # Mensagens
    messages: Annotated[List[BaseMessage], add_messages]

    # Estado do fluxo
    current_state: FlowState

    # Dados do cliente
    nome_cliente: Optional[str]
    cnpj: Optional[str]
    codigo_cliente: Optional[int]
    codigo_empresa: Optional[int]
    nome_empresa: Optional[str]

    # Dados da busca
    termo_busca: Optional[str]
    baterias_encontradas: Optional[List[Dict[str, Any]]]

    # Produtos escolhidos
    produtos_escolhidos: List[ProdutoEscolhido]
    produto_pendente_terminal: Optional[Dict[str, Any]]

    # Dados da cotação
    com_troca_sucata: Optional[bool]
    cotacao_detalhada: Optional[Dict[str, Any]]
    valor_total: Optional[float]

    # Dados do pedido
    tipo_pagamento: Optional[int]  # 1=vista, 2=prazo
    forma_pagamento: Optional[int]  # 1=boleto, 4=pix, 5=duplicata, 6=cartao
    prazo_pedido: Optional[str]
    prazo_sucata: Optional[str]

    # Transferência para departamento
    notificar_departamento: Optional[str]
    transferido_para: Optional[str]
    motivo_transferencia: Optional[str]

    # Memória de longo prazo (dados históricos do cliente)
    historico_interacoes: Optional[int]  # Número de conversas anteriores
    ultimo_pedido: Optional[Dict[str, Any]]  # Dados do último pedido

    # Controle
    tentativas_erro: int
    ultima_mensagem_usuario: Optional[str]


def create_initial_state(phone: str) -> ConversationState:
    """Cria estado inicial da conversa"""
    return ConversationState(
        messages=[],
        current_state=FlowState.INICIO,
        nome_cliente=None,
        cnpj=None,
        codigo_cliente=None,
        codigo_empresa=None,
        nome_empresa=None,
        termo_busca=None,
        baterias_encontradas=None,
        produtos_escolhidos=[],
        produto_pendente_terminal=None,
        com_troca_sucata=None,
        cotacao_detalhada=None,
        valor_total=None,
        tipo_pagamento=None,
        forma_pagamento=None,
        prazo_pedido=None,
        prazo_sucata=None,
        notificar_departamento=None,
        transferido_para=None,
        motivo_transferencia=None,
        historico_interacoes=None,
        ultimo_pedido=None,
        tentativas_erro=0,
        ultima_mensagem_usuario=None
    )

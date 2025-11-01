"""Agente Alice - Core do sistema"""
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from loguru import logger

from config import settings
from alice.state import ConversationState, FlowState, create_initial_state
from alice.tools import ALICE_TOOLS
from alice.prompt import ALICE_SYSTEM_PROMPT
from alice.analytics import analytics_tracker


class AliceAgent:
    """Agente Alice - Vendedora virtual da LC Baterias"""

    def __init__(self):
        """Inicializa o agente Alice"""

        # LLM principal (GPT-4)
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1,  # Baixa temperatura para respostas mais consistentes
            max_tokens=4096
        )

        # LLM com tools
        self.llm_with_tools = self.llm.bind_tools(ALICE_TOOLS)

        # Tool node para executar ferramentas
        self.tool_node = ToolNode(ALICE_TOOLS)

        # Grafo de estados
        self.graph = self._create_graph()

        logger.info("✅ Alice Agent inicializada")

    def _create_graph(self) -> StateGraph:
        """Cria o grafo de estados do agente"""

        workflow = StateGraph(ConversationState)

        # Nós
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("process_tool_results", self._process_tool_results_node)

        # Entry point
        workflow.set_entry_point("agent")

        # Edges condicionais
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )

        # Após executar tools, processa resultados
        workflow.add_edge("tools", "process_tool_results")

        # Volta para agent após processar resultados
        workflow.add_edge("process_tool_results", "agent")

        return workflow.compile()

    def _agent_node(self, state: ConversationState) -> Dict[str, Any]:
        """Nó principal do agente - processa mensagem e decide próxima ação"""

        # Monta mensagens do contexto
        messages = [
            SystemMessage(content=ALICE_SYSTEM_PROMPT)
        ]

        # Adiciona contexto do estado atual
        context_info = self._build_context_from_state(state)
        if context_info:
            messages.append(SystemMessage(content=f"CONTEXTO ATUAL:\n{context_info}"))

        # Adiciona histórico de mensagens (apenas últimas 10 para evitar erros de tool_call_id)
        recent_messages = state["messages"][-10:] if len(state["messages"]) > 10 else state["messages"]
        messages.extend(recent_messages)

        # Chama LLM
        logger.info(f"🤖 Alice processando mensagem (estado: {state['current_state']})")
        response = self.llm_with_tools.invoke(messages)

        # Atualiza mensagens
        return {"messages": [response]}

    def _build_context_from_state(self, state: ConversationState) -> str:
        """Constrói contexto estruturado do estado atual"""

        context_parts = []

        # Estado do fluxo
        context_parts.append(f"ESTADO DO FLUXO: {state['current_state']}")

        # Dados do cliente
        if state.get("nome_cliente"):
            context_parts.append(f"NOME: {state['nome_cliente']}")
        if state.get("cnpj"):
            context_parts.append(f"CNPJ: {state['cnpj']}")
        if state.get("codigo_cliente") and state.get("codigo_empresa"):
            context_parts.append(
                f"CÓDIGOS MEMORIZADOS: codigo_cliente={state['codigo_cliente']}, "
                f"codigo_empresa={state['codigo_empresa']}"
            )
        if state.get("nome_empresa"):
            context_parts.append(f"EMPRESA: {state['nome_empresa']}")

        # Busca de produtos
        if state.get("baterias_encontradas"):
            num_baterias = len(state["baterias_encontradas"])
            context_parts.append(f"BATERIAS ENCONTRADAS: {num_baterias} opções")

        # Produtos escolhidos
        if state.get("produtos_escolhidos"):
            context_parts.append(f"PRODUTOS ESCOLHIDOS: {len(state['produtos_escolhidos'])} itens")
            for idx, prod in enumerate(state["produtos_escolhidos"], 1):
                context_parts.append(
                    f"  {idx}. {prod['codigo']} - Qtd: {prod.get('quantidade', 'pendente')}"
                )

        # Troca de sucata
        if state.get("com_troca_sucata") is not None:
            context_parts.append(f"TROCA SUCATA: {'SIM' if state['com_troca_sucata'] else 'NÃO'}")

        # Cotação
        if state.get("valor_total"):
            context_parts.append(f"VALOR TOTAL: R$ {state['valor_total']:.2f}")

        # Dados de pagamento
        if state.get("tipo_pagamento"):
            tipo = "À VISTA" if state["tipo_pagamento"] == 1 else "À PRAZO"
            context_parts.append(f"TIPO PAGAMENTO: {tipo}")
        if state.get("prazo_pedido"):
            context_parts.append(f"PRAZO PEDIDO: {state['prazo_pedido']}")

        return "\n".join(context_parts)

    def _process_tool_results_node(self, state: ConversationState) -> Dict[str, Any]:
        """
        Processa resultados das tools e extrai dados críticos para o state.

        Este nó é executado após cada chamada de tool e é responsável por:
        - Extrair dados da tool verificar_cliente e salvar no state
        - Registrar métricas de analytics
        - Extrair dados de outras tools conforme necessário
        """
        # Pega a última mensagem (resultado da tool)
        last_message = state["messages"][-1]

        # Se não é uma ToolMessage, não faz nada
        if not hasattr(last_message, "content"):
            return {}

        updates = {}
        phone = state.get("phone", "")

        # Verifica se foi chamada a tool verificar_cliente
        if hasattr(last_message, "name") and last_message.name == "verificar_cliente":
            try:
                import json
                # Tenta parsear o conteúdo da tool
                if isinstance(last_message.content, str):
                    tool_result = json.loads(last_message.content)
                else:
                    tool_result = last_message.content

                # Se cliente foi encontrado, salva dados críticos no state
                if tool_result.get("cliente_encontrado"):
                    updates["codigo_cliente"] = int(tool_result.get("codigo_cliente", 0))
                    updates["codigo_empresa"] = int(tool_result.get("codigo_empresa", 1))
                    updates["nome_empresa"] = tool_result.get("nome_loja")

                    logger.success(
                        f"💾 Dados salvos no state: "
                        f"codigo_cliente={updates['codigo_cliente']}, "
                        f"codigo_empresa={updates['codigo_empresa']}, "
                        f"nome_empresa={updates['nome_empresa']}"
                    )
            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar resultado da tool: {str(e)}")

        # Analytics: Registrar busca de baterias
        elif hasattr(last_message, "name") and last_message.name == "buscar_baterias":
            try:
                import json
                tool_result = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content

                if tool_result.get("sucesso") and tool_result.get("baterias_encontradas"):
                    analytics_tracker.registrar_produtos_apresentados(phone, [])
            except:
                pass

        # Analytics: Registrar cotação enviada
        elif hasattr(last_message, "name") and last_message.name == "consultar_baterias":
            try:
                import json
                tool_result = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content

                if tool_result.get("sucesso"):
                    valor_total = float(tool_result.get("valor_total_geral", 0))
                    produtos = tool_result.get("produtos", [])
                    analytics_tracker.registrar_cotacao_enviada(phone, valor_total, produtos)
            except:
                pass

        # Analytics: Registrar pedido fechado (SUCESSO!)
        elif hasattr(last_message, "name") and last_message.name == "enviar_pedido":
            try:
                import json
                tool_result = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content

                if tool_result.get("sucesso"):
                    # PEDIDO CONFIRMADO! Registrar no analytics
                    numero_pedido = tool_result.get("numero_pedido", "")

                    # Pegar dados do state
                    valor_total = state.get("valor_total", 0)
                    produtos = state.get("produtos_escolhidos", [])
                    cliente_nome = state.get("nome_cliente", "Cliente")

                    analytics_tracker.registrar_pedido_fechado(
                        phone=phone,
                        numero_pedido=str(numero_pedido),
                        valor_total=float(valor_total),
                        produtos=produtos,
                        cliente_nome=cliente_nome
                    )

                    # Remover de leads pendentes (se estava lá)
                    analytics_tracker.remover_lead_pendente(phone)
            except Exception as e:
                logger.error(f"❌ Erro ao registrar pedido no analytics: {e}")

        # Transferência para humano: Registrar departamento e notificar
        elif hasattr(last_message, "name") and last_message.name == "transferir_para_humano":
            try:
                import json
                tool_result = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content

                if tool_result.get("status") == "transferido":
                    departamento = tool_result.get("departamento", "geral")
                    motivo = tool_result.get("motivo", "")

                    # Salvar no state
                    updates["transferido_para"] = departamento
                    updates["motivo_transferencia"] = motivo
                    updates["current_state"] = "transferido_humano"

                    logger.warning(f"🔔 Transferência detectada para {departamento}: {motivo}")

                    # Flag para enviar notificação (será processada no main.py)
                    updates["notificar_departamento"] = departamento
            except Exception as e:
                logger.error(f"❌ Erro ao processar transferência: {e}")

        return updates

    def _should_continue(self, state: ConversationState) -> str:
        """Decide se deve executar tools ou finalizar"""

        last_message = state["messages"][-1]

        # Se a última mensagem tem tool_calls, executa
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info(f"🔧 Executando {len(last_message.tool_calls)} tool(s)")
            return "continue"

        # Caso contrário, finaliza
        return "end"

    async def process_message(
        self,
        phone: str,
        message: str,
        state: ConversationState
    ) -> tuple[str, ConversationState]:
        """
        Processa mensagem do usuário e retorna resposta

        Args:
            phone: Telefone do usuário
            message: Mensagem recebida
            state: Estado atual da conversa

        Returns:
            Tupla (resposta_texto, novo_estado)
        """
        logger.info(f"📩 Processando mensagem de {phone}: '{message[:50]}...'")

        # Analytics: Registrar conversa iniciada (apenas na primeira mensagem)
        if len(state.get("messages", [])) == 0:
            analytics_tracker.registrar_conversa_iniciada(phone)

        # Adiciona mensagem do usuário ao estado
        state["messages"].append(HumanMessage(content=message))
        state["ultima_mensagem_usuario"] = message

        try:
            # Executa o grafo
            result = await self.graph.ainvoke(state)

            # Extrai resposta da Alice
            last_message = result["messages"][-1]
            response_text = last_message.content

            logger.success(f"✅ Alice respondeu: '{response_text[:50]}...'")

            return response_text, result

        except Exception as e:
            logger.error(f"💥 Erro ao processar mensagem: {str(e)}")

            # Incrementa tentativas de erro
            state["tentativas_erro"] = state.get("tentativas_erro", 0) + 1

            # Se muitos erros, transfere para humano
            if state["tentativas_erro"] >= 3:
                error_response = (
                    "Desculpe, estou enfrentando dificuldades técnicas. "
                    "Vou transferir você para um atendente humano."
                )
                state["current_state"] = FlowState.ERRO
            else:
                error_response = (
                    "Desculpe, tive um problema ao processar sua mensagem. "
                    "Pode repetir, por favor?"
                )

            return error_response, state

    def create_new_session(self, phone: str) -> ConversationState:
        """Cria nova sessão de conversa"""
        logger.info(f"🆕 Nova sessão criada para {phone}")
        return create_initial_state(phone)

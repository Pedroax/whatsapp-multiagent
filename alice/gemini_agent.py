"""Agente Alice com Gemini - Versão experimental"""
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from loguru import logger

from config import settings
from alice.state import ConversationState, FlowState, create_initial_state
from alice.tools import ALICE_TOOLS
from alice.prompt import ALICE_SYSTEM_PROMPT
from alice.analytics import analytics_tracker


class GeminiAgent:
    """Agente Alice usando Gemini 2.0 Flash - Versão experimental"""

    def __init__(self):
        """Inicializa o agente Alice com Gemini"""

        # LLM Gemini 2.0 Flash
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.google_api_key,
            temperature=0.1,
            max_output_tokens=8192,
            convert_system_message_to_human=True  # CRÍTICO: converte SystemMessage para HumanMessage
        )

        # LLM com tools
        self.llm_with_tools = self.llm.bind_tools(ALICE_TOOLS)

        # Tool node para executar ferramentas
        self.tool_node = ToolNode(ALICE_TOOLS)

        # Grafo de estados
        self.graph = self._create_graph()

        logger.info("✅ Gemini Agent inicializada (experimental)")

    def _create_graph(self) -> StateGraph:
        """Cria o grafo de estados do agente"""

        workflow = StateGraph(ConversationState)

        # Nós
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("process_tool_results", self._process_tool_results_node)
        workflow.add_node("extract_info", self._extract_info_node)

        # Entry point
        workflow.set_entry_point("agent")

        # Edges condicionais
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "extract": "extract_info"
            }
        )

        # Após executar tools, processa resultados
        workflow.add_edge("tools", "process_tool_results")

        # Volta para agent após processar resultados
        workflow.add_edge("process_tool_results", "agent")

        # Após extrair info, finaliza
        workflow.add_edge("extract_info", END)

        return workflow.compile()

    def _agent_node(self, state: ConversationState) -> Dict[str, Any]:
        """Nó principal do agente - processa mensagem e decide próxima ação"""

        # Gemini não aceita SystemMessage, então criamos um HumanMessage especial
        # apenas na PRIMEIRA mensagem da conversa
        messages = []

        # Se é a primeira interação (sem mensagens ainda), adiciona o system prompt
        if len(state["messages"]) == 0:
            # Cria uma mensagem inicial combinando system prompt + mensagem do usuário
            system_context = f"""Você é Alice, agente de vendas da LC Baterias.

INSTRUÇÕES DO SISTEMA:
{ALICE_SYSTEM_PROMPT}

---
MENSAGEM DO CLIENTE:
{state.get('ultima_mensagem_usuario', '')}"""

            messages.append(HumanMessage(content=system_context))
        else:
            # Para mensagens seguintes, adiciona contexto estruturado se necessário
            context_info = self._build_context_from_state(state)

            # Se tem contexto importante, injeta como primeira mensagem
            if context_info and len(state["messages"]) > 0:
                # Pega a última mensagem do usuário e adiciona contexto
                last_user_msg = None
                for msg in reversed(state["messages"]):
                    if isinstance(msg, HumanMessage):
                        last_user_msg = msg.content
                        break

                if last_user_msg:
                    enhanced_msg = f"""CONTEXTO ATUAL:
{context_info}

MENSAGEM DO CLIENTE:
{last_user_msg}"""

                    # Adiciona histórico menos a última mensagem
                    messages.extend(state["messages"][:-1])
                    messages.append(HumanMessage(content=enhanced_msg))
                else:
                    messages.extend(state["messages"])
            else:
                # Adiciona histórico completo
                messages.extend(state["messages"])

        # Chama LLM
        logger.info(f"🤖 Gemini processando mensagem (estado: {state['current_state']})")

        try:
            response = self.llm_with_tools.invoke(messages)
        except Exception as e:
            logger.error(f"❌ Erro Gemini: {e}")
            # Fallback: tentar sem tools
            response = self.llm.invoke(messages)

        return {"messages": [response]}

    def _build_context_from_state(self, state: ConversationState) -> str:
        """Constrói contexto estruturado do estado atual"""

        context_parts = []

        # Estado do fluxo
        context_parts.append(f"Estado atual: {state['current_state']}")

        # Dados do cliente
        if state.get("nome_cliente"):
            context_parts.append(f"Nome: {state['nome_cliente']}")
        if state.get("cnpj"):
            context_parts.append(f"CNPJ: {state['cnpj']}")
        if state.get("codigo_cliente") and state.get("codigo_empresa"):
            context_parts.append(
                f"Códigos: cliente={state['codigo_cliente']}, empresa={state['codigo_empresa']}"
            )

        # Produtos
        if state.get("produtos_escolhidos"):
            context_parts.append(f"Produtos escolhidos: {len(state['produtos_escolhidos'])} itens")

        # Troca de sucata
        if state.get("com_troca_sucata") is not None:
            context_parts.append(f"Troca sucata: {'SIM' if state['com_troca_sucata'] else 'NÃO'}")

        # Valor total
        if state.get("valor_total"):
            context_parts.append(f"Valor total: R$ {state['valor_total']:.2f}")

        return "\n".join(context_parts) if context_parts else ""

    def _process_tool_results_node(self, state: ConversationState) -> Dict[str, Any]:
        """Processa resultados das tools - reutiliza lógica do AliceAgent"""
        from alice.agent import AliceAgent

        # Cria instância temporária para usar o método
        temp_agent = AliceAgent.__new__(AliceAgent)
        return temp_agent._process_tool_results_node(state)

    def _extract_info_node(self, state: ConversationState) -> Dict[str, Any]:
        """Extrai informações da conversa - reutiliza lógica do AliceAgent"""
        from alice.agent import AliceAgent

        temp_agent = AliceAgent.__new__(AliceAgent)
        extracted_info = temp_agent._extract_info_from_conversation(state)

        # Se não extraiu nada, retorna campo dummy para não dar erro
        if not extracted_info:
            return {"tentativas_erro": state.get("tentativas_erro", 0)}

        return extracted_info

    def _should_continue(self, state: ConversationState) -> str:
        """Decide se deve executar tools ou extrair info e finalizar"""

        last_message = state["messages"][-1]

        # Se a última mensagem tem tool_calls, executa tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info(f"🔧 Executando {len(last_message.tool_calls)} tool(s)")
            return "continue"

        # Caso contrário, extrai info e finaliza
        return "extract"

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
        logger.info(f"📩 [GEMINI] Processando mensagem de {phone}: '{message[:50]}...'")

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

            logger.success(f"✅ [GEMINI] Alice respondeu: '{response_text[:50]}...'")

            return response_text, result

        except Exception as e:
            logger.error(f"💥 [GEMINI] Erro ao processar mensagem: {str(e)}")

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
        logger.info(f"🆕 [GEMINI] Nova sessão criada para {phone}")
        return create_initial_state(phone)

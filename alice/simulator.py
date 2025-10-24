"""
Simulador/Sandbox de Conversas
Permite testar respostas da IA sem enviar para clientes reais
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from supabase import create_client, Client
from config import settings


class ConversationSimulator:
    """Simulador de conversas para testes seguros"""

    def __init__(self, empresa_id: str = "emp1"):
        self.empresa_id = empresa_id
        self.supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
        logger.info("✅ ConversationSimulator inicializado")

    async def criar_simulacao(
        self,
        nome: str,
        descricao: Optional[str] = None,
        mensagens_iniciais: Optional[List[Dict[str, str]]] = None,
        contexto_inicial: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cria uma nova simulação

        Args:
            nome: Nome da simulação
            descricao: Descrição opcional
            mensagens_iniciais: Lista de mensagens [{role: 'user'|'assistant', content: '...'}]
            contexto_inicial: Contexto simulado (CNPJ, estado, etc)

        Returns:
            ID da simulação criada
        """
        try:
            response = self.supabase.table("simulacoes").insert({
                "empresa_id": self.empresa_id,
                "nome_simulacao": nome,
                "descricao": descricao,
                "mensagens": mensagens_iniciais or [],
                "contexto_simulado": contexto_inicial or {},
                "status": "rascunho"
            }).execute()

            simulacao_id = response.data[0]["id"]
            logger.info(f"📋 Simulação criada: {simulacao_id}")
            return simulacao_id

        except Exception as e:
            logger.error(f"❌ Erro ao criar simulação: {e}")
            return None

    async def executar_simulacao(
        self,
        simulacao_id: str,
        mensagem_usuario: str,
        contexto_extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executa uma simulação e retorna o resultado

        Args:
            simulacao_id: ID da simulação
            mensagem_usuario: Nova mensagem do usuário para simular
            contexto_extra: Contexto adicional

        Returns:
            Resultado com resposta_ia, confiança, intenção, decisão
        """
        try:
            # Importar aqui para evitar circular import
            from alice.agent import AliceAgent
            from alice.intelligent_controller import IntelligentController

            # Buscar simulação
            simulacao = self.supabase.table("simulacoes")\
                .select("*")\
                .eq("id", simulacao_id)\
                .single()\
                .execute()

            if not simulacao.data:
                raise ValueError(f"Simulação {simulacao_id} não encontrada")

            sim_data = simulacao.data
            mensagens_anteriores = sim_data.get("mensagens", [])
            contexto_simulado = sim_data.get("contexto_simulado", {})

            # Mesclar contexto
            if contexto_extra:
                contexto_simulado.update(contexto_extra)

            # Criar contexto completo para o agente
            from alice.state import FlowState

            contexto_completo = {
                "messages": mensagens_anteriores,
                "current_state": FlowState.INICIO,  # Estado inicial padrão
                "cnpj": contexto_simulado.get("cnpj"),
                "produtos_interesse": contexto_simulado.get("produtos_interesse", []),
                **contexto_simulado
            }

            # Executar agente IA
            alice = AliceAgent()
            phone_simulado = f"sim_{simulacao_id[:8]}"

            # IMPORTANTE: Modo SANDBOX - não salva sessão
            resposta_ia, novo_estado = await alice.process_message(
                phone=phone_simulado,
                message=mensagem_usuario,
                state=contexto_completo
            )

            # Analisar com IntelligentController
            controller = IntelligentController()
            confianca, intencao, metadados = await controller.analisar_confianca(
                mensagem_usuario=mensagem_usuario,
                resposta_ia=resposta_ia,
                contexto=novo_estado
            )

            # Determinar decisão (sem executar de verdade)
            decisao = await self._simular_decisao(confianca, intencao)

            logger.success(f"✅ Simulação executada: {simulacao_id}")

            # RETORNAR APENAS DADOS SIMPLES - SEM SALVAR NO BANCO
            return {
                "success": True,
                "simulacao_id": simulacao_id,
                "mensagem_usuario": mensagem_usuario,
                "resposta_ia": resposta_ia,
                "confianca": float(confianca),
                "intencao": intencao,
                "decisao": decisao
            }

        except Exception as e:
            logger.error(f"❌ Erro ao executar simulação: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _simular_decisao(self, confianca: float, intencao: str) -> str:
        """
        Simula qual seria a decisão do sistema (sem executar)

        Args:
            confianca: Score de confiança
            intencao: Intenção detectada

        Returns:
            'enviar_direto', 'aguardar_aprovacao', ou 'bloquear'
        """
        from alice.ia_controller import ia_controller

        # Buscar modo atual
        modo = await ia_controller.get_modo_ia(self.empresa_id)

        if modo == "desligado":
            return "bloquear"
        elif modo == "atencao":
            return "aguardar_aprovacao"
        elif modo == "ligado":
            # Buscar config
            config = await ia_controller._get_config_ia(self.empresa_id)
            limiar = config.get("limiar_confianca", 0.95)

            if config.get("auto_aprovar_alta_confianca") and confianca >= limiar:
                return "enviar_direto"
            else:
                return "aguardar_aprovacao"

        return "aguardar_aprovacao"

    async def listar_simulacoes(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista simulações criadas

        Args:
            status: Filtro por status ('rascunho', 'executado', 'arquivado')

        Returns:
            Lista de simulações
        """
        try:
            query = self.supabase.table("simulacoes")\
                .select("*")\
                .eq("empresa_id", self.empresa_id)\
                .order("created_at", desc=True)

            if status:
                query = query.eq("status", status)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"❌ Erro ao listar simulações: {e}")
            return []

    async def excluir_simulacao(self, simulacao_id: str) -> bool:
        """Exclui uma simulação"""
        try:
            self.supabase.table("simulacoes")\
                .delete()\
                .eq("id", simulacao_id)\
                .execute()

            logger.info(f"🗑️ Simulação excluída: {simulacao_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao excluir simulação: {e}")
            return False

    async def executar_rapido(
        self,
        mensagem: str,
        contexto: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executa simulação rápida sem salvar

        Args:
            mensagem: Mensagem do usuário
            contexto: Contexto opcional

        Returns:
            Resultado da simulação
        """
        # Criar simulação temporária
        sim_id = await self.criar_simulacao(
            nome=f"Teste Rápido - {datetime.now().strftime('%H:%M:%S')}",
            descricao="Simulação rápida sem persistência",
            mensagens_iniciais=[],
            contexto_inicial=contexto or {}
        )

        if not sim_id:
            return {"success": False, "error": "Não foi possível criar simulação"}

        # Executar
        resultado = await self.executar_simulacao(sim_id, mensagem, contexto)

        # Excluir (opcional - pode manter para histórico)
        # await self.excluir_simulacao(sim_id)

        return resultado

    def _serializar_estado(self, estado: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte estado com objetos LangChain para JSON serializável

        Args:
            estado: Estado da conversa com objetos LangChain

        Returns:
            Estado serializado em formato JSON
        """
        from langchain_core.messages import BaseMessage
        from alice.state import FlowState

        estado_json = {}

        for key, value in estado.items():
            if key == "messages":
                # Converter mensagens LangChain para dict
                estado_json[key] = [
                    {
                        "role": msg.type if hasattr(msg, "type") else "unknown",
                        "content": msg.content if hasattr(msg, "content") else str(msg)
                    }
                    for msg in value
                    if isinstance(msg, BaseMessage)
                ]
            elif key == "current_state":
                # Converter enum FlowState para string
                estado_json[key] = value.value if isinstance(value, FlowState) else str(value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                # Tipos básicos
                estado_json[key] = value
            elif isinstance(value, list):
                # Listas - tentar serializar itens
                estado_json[key] = [
                    item if isinstance(item, (str, int, float, bool, type(None))) else str(item)
                    for item in value
                ]
            elif isinstance(value, dict):
                # Dicts recursivos
                estado_json[key] = self._serializar_estado(value)
            else:
                # Outros objetos - converter para string
                estado_json[key] = str(value)

        return estado_json


# Singleton
simulator = ConversationSimulator()

"""
Controlador de IA - Gerencia modos de operação e aprovação de mensagens
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, time as dt_time
from loguru import logger
from supabase import create_client, Client
from config import settings
import pytz


class IAController:
    """
    Gerencia o controle da IA: LIGADO, DESLIGADO, ATENÇÃO
    e sistema de aprovação de mensagens
    """

    def __init__(self):
        """Inicializa o controlador"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        logger.info("✅ IAController inicializado")

    # ========================================================================
    # CONTROLE DE MODO DA IA
    # ========================================================================

    async def get_modo_ia(self, empresa_id: str) -> str:
        """
        Obtém o modo atual da IA para uma empresa

        Args:
            empresa_id: ID da empresa

        Returns:
            'ligado', 'atencao' ou 'desligado'
        """
        try:
            # Buscar configuração
            response = self.supabase.table("config_ia")\
                .select("modo_global, agendamento_ativo")\
                .eq("empresa_id", empresa_id)\
                .single()\
                .execute()

            if not response.data:
                logger.warning(f"⚠️ Config não encontrada para empresa {empresa_id}")
                return "atencao"  # modo padrão

            config = response.data
            modo_base = config.get("modo_global", "atencao")

            # Se agendamento está ativo, verificar se deve sobrescrever
            if config.get("agendamento_ativo"):
                modo_agendado = await self._get_modo_por_agendamento(empresa_id)
                if modo_agendado:
                    logger.debug(f"📅 Modo da IA sobrescrito por agendamento: {modo_agendado}")
                    return modo_agendado

            return modo_base

        except Exception as e:
            logger.error(f"❌ Erro ao obter modo da IA: {e}")
            return "atencao"  # fallback seguro

    async def set_modo_ia(
        self,
        empresa_id: str,
        modo: str,
        usuario_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Define o modo da IA manualmente

        Args:
            empresa_id: ID da empresa
            modo: 'ligado', 'atencao' ou 'desligado'
            usuario_id: ID do usuário que fez a alteração

        Returns:
            Configuração atualizada
        """
        try:
            if modo not in ['ligado', 'atencao', 'desligado']:
                raise ValueError(f"Modo inválido: {modo}")

            # Atualizar configuração
            response = self.supabase.table("config_ia")\
                .update({
                    "modo_global": modo,
                    "updated_at": datetime.utcnow().isoformat(),
                    "updated_by": usuario_id
                })\
                .eq("empresa_id", empresa_id)\
                .execute()

            # Registrar evento de auditoria
            await self._registrar_evento(
                empresa_id=empresa_id,
                tipo="modo_ia_alterado",
                categoria="ia",
                titulo=f"Modo da IA alterado para: {modo.upper()}",
                dados={"modo_anterior": await self.get_modo_ia(empresa_id), "modo_novo": modo},
                usuario_id=usuario_id
            )

            logger.success(f"✅ Modo da IA alterado para '{modo}' (empresa: {empresa_id})")

            return response.data[0] if response.data else {}

        except Exception as e:
            logger.error(f"❌ Erro ao definir modo da IA: {e}")
            raise

    async def _get_modo_por_agendamento(self, empresa_id: str) -> Optional[str]:
        """
        Verifica se existe agendamento ativo e retorna o modo apropriado

        Args:
            empresa_id: ID da empresa

        Returns:
            Modo da IA conforme agendamento ou None se não houver
        """
        try:
            # Obter agendamentos ativos
            response = self.supabase.table("agendamentos_ia")\
                .select("*")\
                .eq("empresa_id", empresa_id)\
                .eq("ativo", True)\
                .order("prioridade", desc=True)\
                .execute()

            if not response.data:
                return None

            # Verificar qual agendamento se aplica agora
            agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
            dia_semana_atual = agora.weekday() + 1  # 1=segunda, 7=domingo
            hora_atual = agora.time()

            for agendamento in response.data:
                # Verificar se hoje está nos dias ativos
                dias_semana = agendamento.get("dias_semana", [])
                if dia_semana_atual not in dias_semana:
                    continue

                # Verificar exceções (feriados, etc)
                excecoes = agendamento.get("excecoes", [])
                data_hoje = agora.date().isoformat()
                if any(exc.get("data") == data_hoje and not exc.get("ativo", True) for exc in excecoes):
                    logger.debug(f"📅 Hoje é exceção no agendamento: {agendamento['nome']}")
                    continue

                # Verificar se estamos dentro do horário
                hora_ligar = datetime.strptime(agendamento["hora_ligar"], "%H:%M:%S").time()
                hora_desligar = datetime.strptime(agendamento["hora_desligar"], "%H:%M:%S").time()

                if hora_ligar <= hora_atual <= hora_desligar:
                    # Dentro do horário
                    return agendamento.get("modo_dentro_horario", "atencao")
                else:
                    # Fora do horário
                    return agendamento.get("modo_fora_horario", "desligado")

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao verificar agendamento: {e}")
            return None

    # ========================================================================
    # SISTEMA DE APROVAÇÃO DE MENSAGENS
    # ========================================================================

    async def criar_mensagem_pendente(
        self,
        empresa_id: str,
        conversa_id: str,
        lead_id: str,
        lead_nome: str,
        lead_telefone: str,
        mensagem_recebida: str,
        resposta_ia: str,
        confianca_ia: float = 0.0,
        intencao_detectada: Optional[str] = None,
        contexto_ia: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Cria uma mensagem pendente de aprovação

        Args:
            empresa_id: ID da empresa
            conversa_id: ID da conversa
            lead_id: ID do lead
            lead_nome: Nome do lead
            lead_telefone: Telefone do lead
            mensagem_recebida: Mensagem enviada pelo lead
            resposta_ia: Resposta gerada pela IA
            confianca_ia: Nível de confiança da IA (0.0 a 1.0)
            intencao_detectada: Intenção detectada pela IA
            contexto_ia: Contexto adicional da IA

        Returns:
            Mensagem pendente criada
        """
        try:
            # Verificar se deve auto-aprovar (alta confiança)
            config = await self._get_config_ia(empresa_id)
            auto_aprovar = config.get("auto_aprovar_alta_confianca", False)
            limiar = config.get("limiar_confianca", 0.95)

            if auto_aprovar and confianca_ia >= limiar:
                logger.info(
                    f"✨ Auto-aprovando mensagem (confiança: {confianca_ia:.2%} >= {limiar:.2%})"
                )
                # Criar como já aprovada
                status_inicial = "aprovada"
                enviada_inicial = True
                enviada_em = datetime.utcnow().isoformat()
            else:
                status_inicial = "pendente"
                enviada_inicial = False
                enviada_em = None

            # Criar registro
            response = self.supabase.table("mensagens_pendentes")\
                .insert({
                    "empresa_id": empresa_id,
                    "conversa_id": conversa_id,
                    "lead_id": lead_id,
                    "lead_nome": lead_nome,
                    "lead_telefone": lead_telefone,
                    "mensagem_recebida": mensagem_recebida,
                    "resposta_ia": resposta_ia,
                    "confianca_ia": confianca_ia,
                    "intencao_detectada": intencao_detectada,
                    "contexto_ia": contexto_ia or {},
                    "status": status_inicial,
                    "enviada": enviada_inicial,
                    "enviada_em": enviada_em
                })\
                .execute()

            mensagem_criada = response.data[0] if response.data else {}

            logger.success(
                f"✅ Mensagem pendente criada (status: {status_inicial}): {mensagem_criada.get('id')}"
            )

            # Notificar usuários se necessário
            if status_inicial == "pendente":
                await self._notificar_nova_mensagem_pendente(empresa_id, mensagem_criada)

            return mensagem_criada

        except Exception as e:
            logger.error(f"❌ Erro ao criar mensagem pendente: {e}")
            raise

    async def aprovar_mensagem(
        self,
        mensagem_id: str,
        usuario_id: str,
        texto_editado: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aprova (e opcionalmente edita) uma mensagem pendente

        Args:
            mensagem_id: ID da mensagem
            usuario_id: ID do usuário que aprovou
            texto_editado: Texto editado (None = sem edição)

        Returns:
            Mensagem aprovada com texto final
        """
        try:
            # Buscar mensagem original
            msg_response = self.supabase.table("mensagens_pendentes")\
                .select("*")\
                .eq("id", mensagem_id)\
                .single()\
                .execute()

            if not msg_response.data:
                raise ValueError(f"Mensagem {mensagem_id} não encontrada")

            mensagem = msg_response.data
            resposta_ia_original = mensagem["resposta_ia"]

            # Determinar se foi editada
            foi_editada = texto_editado is not None and texto_editado != resposta_ia_original
            status_final = "editada" if foi_editada else "aprovada"
            texto_final = texto_editado if foi_editada else resposta_ia_original

            # Atualizar via função SQL (garante atomicidade)
            self.supabase.rpc(
                "aprovar_mensagem",
                {
                    "p_mensagem_id": mensagem_id,
                    "p_usuario_id": usuario_id,
                    "p_texto_final": texto_final if foi_editada else None
                }
            ).execute()

            logger.success(
                f"✅ Mensagem {status_final}: {mensagem_id} "
                f"(editada: {foi_editada})"
            )

            return {
                "id": mensagem_id,
                "status": status_final,
                "texto_final": texto_final,
                "lead_telefone": mensagem["lead_telefone"]
            }

        except Exception as e:
            logger.error(f"❌ Erro ao aprovar mensagem: {e}")
            raise

    async def recusar_mensagem(
        self,
        mensagem_id: str,
        usuario_id: str,
        motivo: Optional[str] = None
    ) -> bool:
        """
        Recusa uma mensagem pendente

        Args:
            mensagem_id: ID da mensagem
            usuario_id: ID do usuário que recusou
            motivo: Motivo da recusa

        Returns:
            True se recusada com sucesso
        """
        try:
            self.supabase.rpc(
                "recusar_mensagem",
                {
                    "p_mensagem_id": mensagem_id,
                    "p_usuario_id": usuario_id,
                    "p_motivo": motivo
                }
            ).execute()

            logger.info(f"🚫 Mensagem recusada: {mensagem_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao recusar mensagem: {e}")
            raise

    async def get_fila_aprovacao(self, empresa_id: str) -> List[Dict[str, Any]]:
        """
        Obtém fila de mensagens pendentes de aprovação

        Args:
            empresa_id: ID da empresa

        Returns:
            Lista de mensagens pendentes
        """
        try:
            response = self.supabase.table("mensagens_pendentes")\
                .select("*")\
                .eq("empresa_id", empresa_id)\
                .execute()

            return response.data or []

        except Exception as e:
            logger.error(f"❌ Erro ao buscar fila de aprovação: {e}")
            return []

    # ========================================================================
    # AGENDAMENTOS
    # ========================================================================

    async def criar_agendamento(
        self,
        empresa_id: str,
        nome: str,
        hora_ligar: str,  # "08:00"
        hora_desligar: str,  # "18:00"
        dias_semana: List[int],  # [1,2,3,4,5]
        modo_dentro_horario: str = "atencao",
        modo_fora_horario: str = "desligado",
        mensagem_auto_fora_horario: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo agendamento de horários

        Args:
            empresa_id: ID da empresa
            nome: Nome do agendamento
            hora_ligar: Hora de ligar (HH:MM)
            hora_desligar: Hora de desligar (HH:MM)
            dias_semana: Dias da semana [1=seg, 7=dom]
            modo_dentro_horario: Modo quando dentro do horário
            modo_fora_horario: Modo quando fora do horário
            mensagem_auto_fora_horario: Mensagem automática fora do horário

        Returns:
            Agendamento criado
        """
        try:
            response = self.supabase.table("agendamentos_ia")\
                .insert({
                    "empresa_id": empresa_id,
                    "nome": nome,
                    "hora_ligar": f"{hora_ligar}:00",
                    "hora_desligar": f"{hora_desligar}:00",
                    "dias_semana": dias_semana,
                    "modo_dentro_horario": modo_dentro_horario,
                    "modo_fora_horario": modo_fora_horario,
                    "mensagem_auto_fora_horario": mensagem_auto_fora_horario,
                    "ativo": True
                })\
                .execute()

            logger.success(f"✅ Agendamento criado: {nome}")
            return response.data[0] if response.data else {}

        except Exception as e:
            logger.error(f"❌ Erro ao criar agendamento: {e}")
            raise

    # ========================================================================
    # HELPERS
    # ========================================================================

    async def _get_config_ia(self, empresa_id: str) -> Dict[str, Any]:
        """Busca configuração da IA"""
        response = self.supabase.table("config_ia")\
            .select("*")\
            .eq("empresa_id", empresa_id)\
            .single()\
            .execute()
        return response.data or {}

    async def _notificar_nova_mensagem_pendente(
        self,
        empresa_id: str,
        mensagem: Dict[str, Any]
    ):
        """Notifica usuários sobre nova mensagem pendente"""
        # TODO: Implementar notificações (push, email, websocket)
        logger.debug(f"🔔 Notificação: Nova mensagem pendente de {mensagem['lead_nome']}")

    async def _registrar_evento(
        self,
        empresa_id: str,
        tipo: str,
        categoria: str,
        titulo: str,
        dados: Dict,
        usuario_id: Optional[str] = None
    ):
        """Registra evento de auditoria"""
        try:
            self.supabase.table("eventos")\
                .insert({
                    "empresa_id": empresa_id,
                    "tipo": tipo,
                    "categoria": categoria,
                    "titulo": titulo,
                    "dados": dados,
                    "usuario_id": usuario_id
                })\
                .execute()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao registrar evento: {e}")


# Instância global
ia_controller = IAController()

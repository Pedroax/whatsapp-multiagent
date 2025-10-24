"""
Sistema de Aprendizado Inteligente
Aprende com decisões humanas e ajusta pesos automaticamente
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from loguru import logger
from supabase import create_client, Client
from config import settings


class LearningSystem:
    """Sistema de aprendizado que melhora decisões ao longo do tempo"""

    def __init__(self, empresa_id: str = "emp1"):
        self.empresa_id = empresa_id
        self.supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
        logger.info("✅ LearningSystem inicializado")

    async def registrar_decisao(
        self,
        mensagem_usuario: str,
        resposta_ia: str,
        intencao: str,
        confianca_inicial: float,
        contexto: Dict[str, Any],
        decisao_sistema: str
    ) -> str:
        """
        Registra uma decisão do sistema para futuro aprendizado

        Args:
            mensagem_usuario: Mensagem do cliente
            resposta_ia: Resposta gerada pela IA
            intencao: Intenção detectada
            confianca_inicial: Score de confiança calculado
            contexto: Contexto completo da conversa
            decisao_sistema: 'enviar_direto', 'aguardar_aprovacao', 'bloquear'

        Returns:
            ID da decisão registrada
        """
        try:
            estado_fluxo = contexto.get("state", "unknown")
            tem_cnpj = bool(contexto.get("cnpj"))
            tamanho_historico = len(contexto.get("messages", []))

            response = self.supabase.table("historico_decisoes").insert({
                "empresa_id": self.empresa_id,
                "mensagem_usuario": mensagem_usuario,
                "resposta_ia": resposta_ia,
                "intencao_detectada": intencao,
                "confianca_inicial": float(confianca_inicial),
                "estado_fluxo": estado_fluxo,
                "tem_cnpj": tem_cnpj,
                "tamanho_historico": tamanho_historico,
                "metadados_contexto": contexto,
                "decisao_sistema": decisao_sistema
            }).execute()

            decisao_id = response.data[0]["id"]
            logger.info(f"📝 Decisão registrada: {decisao_id}")
            return decisao_id

        except Exception as e:
            logger.error(f"❌ Erro ao registrar decisão: {e}")
            return None

    async def registrar_feedback(
        self,
        decisao_id: str,
        decisao_humana: str,
        texto_editado: Optional[str] = None,
        motivo_recusa: Optional[str] = None,
        tempo_decisao_segundos: Optional[int] = None
    ) -> bool:
        """
        Registra feedback humano sobre uma decisão

        Args:
            decisao_id: ID da decisão original
            decisao_humana: 'aprovado', 'aprovado_editado', 'recusado'
            texto_editado: Texto editado (se aplicável)
            motivo_recusa: Motivo da recusa (se aplicável)
            tempo_decisao_segundos: Tempo que levou para decidir

        Returns:
            True se registrado com sucesso
        """
        try:
            # Buscar decisão original
            decisao = self.supabase.table("historico_decisoes")\
                .select("*")\
                .eq("id", decisao_id)\
                .single()\
                .execute()

            if not decisao.data:
                logger.warning(f"⚠️ Decisão {decisao_id} não encontrada")
                return False

            decisao_data = decisao.data
            decisao_sistema = decisao_data["decisao_sistema"]

            # Determinar se a decisão do sistema foi correta
            foi_correto = self._avaliar_decisao(decisao_sistema, decisao_humana)

            # Atualizar registro com feedback
            self.supabase.table("historico_decisoes").update({
                "decisao_humana": decisao_humana,
                "texto_editado": texto_editado,
                "motivo_recusa": motivo_recusa,
                "tempo_decisao_segundos": tempo_decisao_segundos,
                "foi_correto": foi_correto,
                "feedback_at": datetime.utcnow().isoformat()
            }).eq("id", decisao_id).execute()

            logger.success(f"✅ Feedback registrado: {decisao_id} - {'CORRETO' if foi_correto else 'INCORRETO'}")

            # Disparar aprendizado se decisão incorreta
            if not foi_correto:
                await self._ajustar_pesos(decisao_data, decisao_humana)

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao registrar feedback: {e}")
            return False

    def _avaliar_decisao(self, decisao_sistema: str, decisao_humana: str) -> bool:
        """
        Avalia se a decisão do sistema foi correta com base no feedback humano

        Regras:
        - enviar_direto + aprovado = CORRETO
        - aguardar_aprovacao + aprovado = CORRETO (conservador, mas aceitável)
        - aguardar_aprovacao + recusado = CORRETO (evitou erro)
        - enviar_direto + recusado = INCORRETO (enviou algo errado!)
        - enviar_direto + aprovado_editado = INCORRETO (precisava edição)
        """
        if decisao_sistema == "enviar_direto":
            return decisao_humana == "aprovado"
        elif decisao_sistema == "aguardar_aprovacao":
            # Aguardar aprovação é sempre seguro
            return True
        elif decisao_sistema == "bloquear":
            return decisao_humana == "recusado"

        return False

    async def _ajustar_pesos(self, decisao_data: Dict[str, Any], decisao_humana: str):
        """
        Ajusta pesos do algoritmo com base em decisão incorreta

        Estratégia:
        - Se enviou direto mas deveria esperar: REDUZ pesos positivos
        - Se esperou mas poderia enviar: AUMENTA pesos positivos (levemente)
        """
        try:
            # Buscar pesos atuais
            pesos = self.supabase.table("pesos_aprendizado")\
                .select("*")\
                .eq("empresa_id", self.empresa_id)\
                .single()\
                .execute()

            if not pesos.data:
                logger.warning("⚠️ Pesos não encontrados, criando padrão")
                return

            pesos_atuais = pesos.data
            decisao_sistema = decisao_data["decisao_sistema"]
            confianca = decisao_data["confianca_inicial"]

            # Determinar ajuste
            fator_ajuste = 0.02  # Ajuste gradual de 2%

            novos_pesos = {}

            # Se enviou direto mas foi recusado/editado = estava muito confiante
            if decisao_sistema == "enviar_direto" and decisao_humana in ["recusado", "aprovado_editado"]:
                logger.warning(f"⚠️ IA muito confiante ({confianca:.2f}) - REDUZINDO pesos positivos")

                # Reduzir pesos positivos
                novos_pesos["peso_cnpj_validado"] = max(0.05, pesos_atuais["peso_cnpj_validado"] - fator_ajuste)
                novos_pesos["peso_fluxo_estruturado"] = max(0.05, pesos_atuais["peso_fluxo_estruturado"] - fator_ajuste)
                novos_pesos["peso_dados_estruturados"] = max(0.02, pesos_atuais["peso_dados_estruturados"] - fator_ajuste)

                # Aumentar penalidades
                novos_pesos["peso_primeira_msg"] = min(-0.10, pesos_atuais["peso_primeira_msg"] - fator_ajuste)
                novos_pesos["peso_msg_longa"] = min(-0.05, pesos_atuais["peso_msg_longa"] - fator_ajuste)

                # Aumentar limiar de confiança
                novos_pesos["limiar_confianca_alta"] = min(0.99, pesos_atuais["limiar_confianca_alta"] + 0.01)

            # Se aguardou mas foi aprovado sem edição = poderia ter enviado direto
            elif decisao_sistema == "aguardar_aprovacao" and decisao_humana == "aprovado" and confianca > 0.85:
                logger.info(f"📈 IA conservadora demais ({confianca:.2f}) - AUMENTANDO pesos levemente")

                # Aumentar pesos positivos levemente
                novos_pesos["peso_cnpj_validado"] = min(0.25, pesos_atuais["peso_cnpj_validado"] + fator_ajuste/2)
                novos_pesos["peso_fluxo_estruturado"] = min(0.15, pesos_atuais["peso_fluxo_estruturado"] + fator_ajuste/2)

                # Reduzir limiar de confiança levemente
                novos_pesos["limiar_confianca_alta"] = max(0.90, pesos_atuais["limiar_confianca_alta"] - 0.005)

            # Aplicar ajustes
            if novos_pesos:
                novos_pesos["updated_at"] = datetime.utcnow().isoformat()
                novos_pesos["versao"] = pesos_atuais["versao"] + 1

                self.supabase.table("pesos_aprendizado")\
                    .update(novos_pesos)\
                    .eq("empresa_id", self.empresa_id)\
                    .execute()

                logger.success(f"✅ Pesos ajustados (versão {novos_pesos['versao']})")

        except Exception as e:
            logger.error(f"❌ Erro ao ajustar pesos: {e}")

    async def get_pesos_atuais(self) -> Dict[str, Any]:
        """Retorna os pesos atuais de aprendizado"""
        try:
            response = self.supabase.table("pesos_aprendizado")\
                .select("*")\
                .eq("empresa_id", self.empresa_id)\
                .single()\
                .execute()

            return response.data or {}

        except Exception as e:
            logger.error(f"❌ Erro ao buscar pesos: {e}")
            return {}

    async def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas de aprendizado"""
        try:
            # Pesos e taxa de acerto
            pesos = await self.get_pesos_atuais()

            # Últimas 100 decisões
            decisoes = self.supabase.table("historico_decisoes")\
                .select("*")\
                .eq("empresa_id", self.empresa_id)\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()

            total = len(decisoes.data)
            com_feedback = len([d for d in decisoes.data if d.get("foi_correto") is not None])
            corretas = len([d for d in decisoes.data if d.get("foi_correto") is True])

            return {
                "total_decisoes": pesos.get("total_decisoes", 0),
                "total_corretas": pesos.get("total_corretas", 0),
                "total_incorretas": pesos.get("total_incorretas", 0),
                "taxa_acerto": float(pesos.get("taxa_acerto", 0.0)),
                "versao_pesos": pesos.get("versao", 1),
                "ultimas_100": {
                    "total": total,
                    "com_feedback": com_feedback,
                    "corretas": corretas,
                    "taxa_recente": corretas / com_feedback if com_feedback > 0 else 0.0
                }
            }

        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas: {e}")
            return {}


# Singleton
learning_system = LearningSystem()

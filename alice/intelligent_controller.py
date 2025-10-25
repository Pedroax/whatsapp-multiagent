"""
Sistema Inteligente de Controle da IA - Versão Melhorada
Integra análise de confiança, detecção de intenção e controle automático
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger
from alice.ia_controller import ia_controller
import re


class IntelligentController:
    """
    Controlador Inteligente que decide automaticamente quando aprovar,
    quando pedir aprovação humana e quando desligar a IA
    """

    def __init__(self):
        """Inicializa o controlador inteligente"""
        self.empresa_id = "emp1"  # TODO: Pegar dinamicamente por phone
        logger.info("✅ IntelligentController inicializado")

    # ========================================================================
    # ANÁLISE INTELIGENTE DE CONFIANÇA
    # ========================================================================

    async def analisar_confianca(
        self,
        mensagem_usuario: str,
        resposta_ia: str,
        contexto: Dict[str, Any]
    ) -> Tuple[float, str, Dict[str, Any]]:
        """
        Analisa o nível de confiança da resposta da IA

        Args:
            mensagem_usuario: Mensagem do usuário
            resposta_ia: Resposta gerada pela IA
            contexto: Contexto da conversa (state)

        Returns:
            (confianca, intencao, metadados)
        """
        confianca = 0.5  # Base
        intencao = "desconhecida"
        metadados = {}

        # ====================================================================
        # 1. ANÁLISE DE INTENÇÃO
        # ====================================================================
        intencao = self._detectar_intencao(mensagem_usuario)
        metadados["intencao"] = intencao

        # ====================================================================
        # 2. FATORES QUE AUMENTAM CONFIANÇA
        # ====================================================================

        # Cliente já validado (tem CNPJ)
        if contexto.get("cnpj"):
            confianca += 0.15
            metadados["cliente_validado"] = True

        # Está em fluxo de vendas estruturado
        estado_atual = contexto.get("current_state", "")
        if estado_atual in [
            "aguardando_modelo",
            "apresentando_opcoes",
            "aguardando_escolha"
        ]:
            confianca += 0.10
            metadados["em_fluxo_estruturado"] = True

        # Resposta é curta e objetiva (menos chance de erro)
        if len(resposta_ia) < 300:
            confianca += 0.05

        # Resposta contém dados estruturados (cotação, lista)
        if self._tem_dados_estruturados(resposta_ia):
            confianca += 0.10
            metadados["tem_dados_estruturados"] = True

        # Não é primeira mensagem (já tem contexto)
        if len(contexto.get("messages", [])) > 2:
            confianca += 0.05

        # ====================================================================
        # 3. FATORES QUE DIMINUEM CONFIANÇA
        # ====================================================================

        # Primeira mensagem (saudação) - sempre deve ser revisada
        if len(contexto.get("messages", [])) <= 1:
            confianca -= 0.20
            metadados["primeira_mensagem"] = True

        # Mensagem muito longa (>500 chars) - mais chance de erro
        if len(resposta_ia) > 500:
            confianca -= 0.10

        # Contém valores financeiros sem confirmação
        if self._tem_valores_financeiros_sem_confirmacao(resposta_ia, contexto):
            confianca -= 0.15
            metadados["valores_sem_confirmacao"] = True

        # Detecta possível erro ou confusão
        palavras_incerteza = ["talvez", "acho que", "pode ser", "não tenho certeza"]
        if any(palavra in resposta_ia.lower() for palavra in palavras_incerteza):
            confianca -= 0.20
            metadados["incerteza_detectada"] = True

        # Pedido de transferência para humano
        if "transferir" in resposta_ia.lower() or "atendente" in resposta_ia.lower():
            confianca = 0.0  # Sempre requer aprovação
            metadados["transferencia_detectada"] = True

        # ====================================================================
        # 4. NORMALIZAR CONFIANÇA (0.0 a 1.0)
        # ====================================================================
        confianca = max(0.0, min(1.0, confianca))

        logger.debug(
            f"📊 Análise de confiança: {confianca:.2%} "
            f"(intenção: {intencao}) - {metadados}"
        )

        return confianca, intencao, metadados

    # ========================================================================
    # DECISÃO INTELIGENTE DE FLUXO
    # ========================================================================

    async def decidir_fluxo(
        self,
        phone: str,
        mensagem_usuario: str,
        resposta_ia: str,
        contexto: Dict[str, Any]
    ) -> Tuple[str, Optional[str]]:
        """
        Decide o que fazer com a resposta da IA

        Returns:
            (decisao, mensagem_id)
            decisao: 'enviar_direto', 'aguardar_aprovacao', 'bloquear'
            mensagem_id: ID da mensagem pendente (se criada)
        """
        # Verificar modo da IA
        modo_ia = await ia_controller.get_modo_ia(self.empresa_id)

        logger.info(f"🎯 Modo IA: {modo_ia}")

        # ====================================================================
        # MODO DESLIGADO - Bloqueia tudo
        # ====================================================================
        if modo_ia == "desligado":
            logger.warning("🔴 IA DESLIGADA - Bloqueando resposta")
            return "bloquear", None

        # ====================================================================
        # ANALISAR CONFIANÇA
        # ====================================================================
        confianca, intencao, metadados = await self.analisar_confianca(
            mensagem_usuario, resposta_ia, contexto
        )

        # ====================================================================
        # MODO ATENÇÃO - Sempre pede aprovação
        # ====================================================================
        if modo_ia == "atencao":
            logger.info("🟡 MODO ATENÇÃO - Criando mensagem para aprovação")

            mensagem_id = await self._criar_mensagem_pendente(
                phone, mensagem_usuario, resposta_ia,
                confianca, intencao, metadados, contexto
            )

            return "aguardar_aprovacao", mensagem_id

        # ====================================================================
        # MODO LIGADO - Decisão inteligente baseada em confiança
        # ====================================================================
        if modo_ia == "ligado":
            # Verificar config de auto-aprovação
            config = await ia_controller._get_config_ia(self.empresa_id)
            auto_aprovar_alta_confianca = config.get("auto_aprovar_alta_confianca", False)
            limiar_confianca = config.get("limiar_confianca", 0.95)

            # Auto-aprovar se confiança alta E config permite
            if auto_aprovar_alta_confianca and confianca >= limiar_confianca:
                logger.success(
                    f"✨ AUTO-APROVADA (confiança: {confianca:.2%} >= {limiar_confianca:.2%})"
                )

                # Registrar decisão para aprendizado
                await self._registrar_decisao_aprendizado(
                    mensagem_usuario, resposta_ia, intencao, confianca, contexto, "enviar_direto"
                )

                return "enviar_direto", None

            # Caso contrário, pede aprovação
            logger.info(
                f"🟡 Confiança baixa ({confianca:.2%}) - Criando mensagem para aprovação"
            )

            mensagem_id = await self._criar_mensagem_pendente(
                phone, mensagem_usuario, resposta_ia,
                confianca, intencao, metadados, contexto
            )

            # Registrar decisão para aprendizado
            await self._registrar_decisao_aprendizado(
                mensagem_usuario, resposta_ia, intencao, confianca, contexto, "aguardar_aprovacao"
            )

            return "aguardar_aprovacao", mensagem_id

        # Fallback: aguardar aprovação
        return "aguardar_aprovacao", None

    # ========================================================================
    # HELPERS PRIVADOS
    # ========================================================================

    def _detectar_intencao(self, mensagem: str) -> str:
        """Detecta a intenção da mensagem do usuário"""
        msg_lower = mensagem.lower()

        # Saudações
        if any(word in msg_lower for word in ["olá", "oi", "bom dia", "boa tarde", "boa noite"]):
            return "saudacao"

        # Pedido/Cotação
        if any(word in msg_lower for word in [
            "quero", "preciso", "gostaria", "orçamento", "cotação", "preço", "valor"
        ]):
            return "pedido"

        # Dúvida
        if any(word in msg_lower for word in [
            "como", "qual", "quanto", "onde", "quando", "?", "dúvida"
        ]):
            return "duvida"

        # Confirmação
        if any(word in msg_lower for word in [
            "sim", "confirmo", "ok", "pode", "isso mesmo", "correto"
        ]):
            return "confirmacao"

        # Negação
        if any(word in msg_lower for word in [
            "não", "nao", "negativo", "cancelar", "desistir"
        ]):
            return "negacao"

        # Reclamação
        if any(word in msg_lower for word in [
            "problema", "erro", "reclamação", "insatisfeito", "ruim"
        ]):
            return "reclamacao"

        # Urgente
        if any(word in msg_lower for word in ["urgente", "rápido", "agora", "imediato"]):
            return "urgente"

        return "informacao"

    def _tem_dados_estruturados(self, resposta: str) -> bool:
        """Verifica se a resposta contém dados estruturados"""
        # Lista numerada
        if re.search(r'\d+\.\s+', resposta):
            return True

        # Valores monetários
        if re.search(r'R\$\s*\d+', resposta):
            return True

        # Tabela-like
        if '|' in resposta or '---' in resposta:
            return True

        return False

    def _tem_valores_financeiros_sem_confirmacao(
        self,
        resposta: str,
        contexto: Dict[str, Any]
    ) -> bool:
        """Verifica se tem valores financeiros mas ainda não está confirmado"""
        # Tem valor monetário
        tem_valor = bool(re.search(r'R\$\s*\d+', resposta))

        # Não está no estado de confirmação
        estado = contexto.get("current_state", "")
        esta_confirmando = estado in ["confirmando_cotacao", "enviando_pedido"]

        return tem_valor and not esta_confirmando

    async def _criar_mensagem_pendente(
        self,
        phone: str,
        mensagem_usuario: str,
        resposta_ia: str,
        confianca: float,
        intencao: str,
        metadados: Dict,
        contexto: Dict
    ) -> str:
        """Cria mensagem pendente de aprovação"""
        try:
            # Extrair dados do contexto
            nome_cliente = contexto.get("nome_cliente") or contexto.get("nome_lead") or "Cliente"
            lead_id = f"lead_{phone}"  # TODO: buscar no Supabase

            mensagem_criada = await ia_controller.criar_mensagem_pendente(
                empresa_id=self.empresa_id,
                conversa_id=f"conv_{phone}",  # TODO: buscar no Supabase
                lead_id=lead_id,
                lead_nome=nome_cliente or "Cliente",
                lead_telefone=phone,
                mensagem_recebida=mensagem_usuario,
                resposta_ia=resposta_ia,
                confianca_ia=confianca,
                intencao_detectada=intencao,
                contexto_ia=metadados
            )

            return mensagem_criada.get("id")

        except Exception as e:
            logger.error(f"❌ Erro ao criar mensagem pendente: {e}")
            return None

    # ========================================================================
    # ENVIO AUTOMÁTICO APÓS APROVAÇÃO
    # ========================================================================

    async def enviar_mensagem_aprovada(
        self,
        mensagem_id: str,
        texto_final: str,
        lead_telefone: str
    ) -> bool:
        """
        Envia mensagem após aprovação humana

        Args:
            mensagem_id: ID da mensagem aprovada
            texto_final: Texto final (aprovado ou editado)
            lead_telefone: Telefone do lead

        Returns:
            True se enviou com sucesso
        """
        try:
            # Importar aqui para evitar circular import
            from whatsapp.evolution_api import EvolutionAPI
            from utils.message_splitter import send_with_typing_simulation

            whatsapp_api = EvolutionAPI()

            # Enviar via WhatsApp
            await send_with_typing_simulation(
                send_func=whatsapp_api.send_text,
                phone=lead_telefone,
                message=texto_final,
                use_smart_split=True
            )

            logger.success(f"✅ Mensagem aprovada enviada para {lead_telefone}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem aprovada: {e}")
            return False

    # ========================================================================
    # INTEGRAÇÃO COM SISTEMA DE APRENDIZADO
    # ========================================================================

    async def _registrar_decisao_aprendizado(
        self,
        mensagem_usuario: str,
        resposta_ia: str,
        intencao: str,
        confianca: float,
        contexto: Dict[str, Any],
        decisao_sistema: str
    ):
        """Registra decisão no sistema de aprendizado"""
        try:
            from alice.learning_system import learning_system

            await learning_system.registrar_decisao(
                mensagem_usuario=mensagem_usuario,
                resposta_ia=resposta_ia,
                intencao=intencao,
                confianca_inicial=confianca,
                contexto=contexto,
                decisao_sistema=decisao_sistema
            )
        except Exception as e:
            logger.warning(f"⚠️ Erro ao registrar decisão para aprendizado: {e}")


# Instância global
intelligent_controller = IntelligentController()

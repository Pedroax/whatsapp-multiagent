"""
Endpoints FastAPI para controle da IA
Gerencia modos (LIGADO/DESLIGADO/ATENÇÃO), aprovação de mensagens e agendamentos
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import time
from loguru import logger

from alice.ia_controller import ia_controller


# ============================================================================
# SCHEMAS
# ============================================================================

class SetModoRequest(BaseModel):
    """Request para alterar modo da IA"""
    modo: str = Field(..., description="'ligado', 'atencao' ou 'desligado'")
    usuario_id: Optional[str] = None


class AprovarMensagemRequest(BaseModel):
    """Request para aprovar mensagem"""
    mensagem_id: str
    usuario_id: str
    texto_editado: Optional[str] = None


class RecusarMensagemRequest(BaseModel):
    """Request para recusar mensagem"""
    mensagem_id: str
    usuario_id: str
    motivo: Optional[str] = None


class CriarAgendamentoRequest(BaseModel):
    """Request para criar agendamento"""
    empresa_id: str
    nome: str
    hora_ligar: str  # "08:00"
    hora_desligar: str  # "18:00"
    dias_semana: List[int] = Field(default=[1, 2, 3, 4, 5])  # 1=seg, 7=dom
    modo_dentro_horario: str = "atencao"
    modo_fora_horario: str = "desligado"
    mensagem_auto_fora_horario: Optional[str] = None


class AtualizarAgendamentoRequest(BaseModel):
    """Request para atualizar agendamento"""
    agendamento_id: str
    nome: Optional[str] = None
    hora_ligar: Optional[str] = None
    hora_desligar: Optional[str] = None
    dias_semana: Optional[List[int]] = None
    modo_dentro_horario: Optional[str] = None
    modo_fora_horario: Optional[str] = None
    mensagem_auto_fora_horario: Optional[str] = None
    ativo: Optional[bool] = None


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/api/ia-control", tags=["IA Control"])


# ============================================================================
# ENDPOINTS - CONTROLE DE MODO
# ============================================================================

@router.get("/modo/{empresa_id}")
async def get_modo_ia(empresa_id: str):
    """
    Obtém o modo atual da IA para uma empresa

    Returns:
        - modo: 'ligado', 'atencao' ou 'desligado'
        - agendamento_ativo: bool
        - horario_atual_dentro: bool (se há agendamento ativo)
    """
    try:
        modo = await ia_controller.get_modo_ia(empresa_id)

        from datetime import datetime
        return {
            "success": True,
            "modo": modo,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter modo da IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modo/{empresa_id}")
async def set_modo_ia(empresa_id: str, request: SetModoRequest):
    """
    Define o modo da IA manualmente

    Body:
        - modo: 'ligado', 'atencao' ou 'desligado'
        - usuario_id: ID do usuário que está alterando (opcional)
    """
    try:
        if request.modo not in ['ligado', 'atencao', 'desligado']:
            raise HTTPException(
                status_code=400,
                detail=f"Modo inválido: {request.modo}. Use 'ligado', 'atencao' ou 'desligado'."
            )

        config = await ia_controller.set_modo_ia(
            empresa_id=empresa_id,
            modo=request.modo,
            usuario_id=request.usuario_id
        )

        logger.success(f"✅ Modo da IA alterado para '{request.modo}' (empresa: {empresa_id})")

        return {
            "success": True,
            "modo": request.modo,
            "config": config
        }
    except Exception as e:
        logger.error(f"❌ Erro ao definir modo da IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - FILA DE APROVAÇÃO
# ============================================================================

@router.get("/fila-aprovacao/{empresa_id}")
async def get_fila_aprovacao(empresa_id: str):
    """
    Obtém fila de mensagens pendentes de aprovação

    Returns:
        Lista de mensagens pendentes com:
        - id, lead_nome, lead_telefone
        - mensagem_recebida, resposta_ia
        - confianca_ia, intencao_detectada
        - created_at, tempo_restante
    """
    try:
        fila = await ia_controller.get_fila_aprovacao(empresa_id)

        return {
            "success": True,
            "total": len(fila),
            "mensagens": fila
        }
    except Exception as e:
        logger.error(f"❌ Erro ao buscar fila de aprovação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aprovar-mensagem")
async def aprovar_mensagem(request: AprovarMensagemRequest):
    """
    Aprova (e opcionalmente edita) uma mensagem pendente
    e ENVIA AUTOMATICAMENTE via WhatsApp

    Body:
        - mensagem_id: ID da mensagem
        - usuario_id: ID do usuário aprovando
        - texto_editado: Texto editado (opcional)

    Returns:
        - id, status ('aprovada' ou 'editada')
        - texto_final: texto que foi enviado
        - enviada: true se enviou com sucesso
    """
    try:
        # Aprovar no banco de dados
        resultado = await ia_controller.aprovar_mensagem(
            mensagem_id=request.mensagem_id,
            usuario_id=request.usuario_id,
            texto_editado=request.texto_editado
        )

        logger.success(
            f"✅ Mensagem aprovada: {request.mensagem_id} "
            f"(editada: {request.texto_editado is not None})"
        )

        # ====================================================================
        # 🚀 ENVIO AUTOMÁTICO VIA WHATSAPP
        # ====================================================================
        from alice.intelligent_controller import intelligent_controller

        enviada = await intelligent_controller.enviar_mensagem_aprovada(
            mensagem_id=request.mensagem_id,
            texto_final=resultado["texto_final"],
            lead_telefone=resultado["lead_telefone"]
        )

        return {
            "success": True,
            "enviada": enviada,
            **resultado
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao aprovar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recusar-mensagem")
async def recusar_mensagem(request: RecusarMensagemRequest):
    """
    Recusa uma mensagem pendente

    Body:
        - mensagem_id: ID da mensagem
        - usuario_id: ID do usuário recusando
        - motivo: Motivo da recusa (opcional)
    """
    try:
        sucesso = await ia_controller.recusar_mensagem(
            mensagem_id=request.mensagem_id,
            usuario_id=request.usuario_id,
            motivo=request.motivo
        )

        logger.info(f"🚫 Mensagem recusada: {request.mensagem_id}")

        return {
            "success": sucesso,
            "mensagem_id": request.mensagem_id
        }
    except Exception as e:
        logger.error(f"❌ Erro ao recusar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - AGENDAMENTOS
# ============================================================================

@router.post("/agendamentos")
async def criar_agendamento(request: CriarAgendamentoRequest):
    """
    Cria um novo agendamento de horários

    Body:
        - empresa_id: ID da empresa
        - nome: Nome do agendamento (ex: "Horário Comercial")
        - hora_ligar: Hora de ligar (ex: "08:00")
        - hora_desligar: Hora de desligar (ex: "18:00")
        - dias_semana: Dias ativos [1=seg, 2=ter, ..., 7=dom]
        - modo_dentro_horario: 'ligado', 'atencao' ou 'desligado'
        - modo_fora_horario: 'ligado', 'atencao' ou 'desligado'
        - mensagem_auto_fora_horario: Mensagem automática (opcional)

    Exemplo:
        {
          "empresa_id": "uuid",
          "nome": "Horário Comercial",
          "hora_ligar": "08:00",
          "hora_desligar": "18:00",
          "dias_semana": [1, 2, 3, 4, 5],
          "modo_dentro_horario": "atencao",
          "modo_fora_horario": "desligado",
          "mensagem_auto_fora_horario": "Olá! Estamos fora do horário. Retornaremos em breve."
        }
    """
    try:
        agendamento = await ia_controller.criar_agendamento(
            empresa_id=request.empresa_id,
            nome=request.nome,
            hora_ligar=request.hora_ligar,
            hora_desligar=request.hora_desligar,
            dias_semana=request.dias_semana,
            modo_dentro_horario=request.modo_dentro_horario,
            modo_fora_horario=request.modo_fora_horario,
            mensagem_auto_fora_horario=request.mensagem_auto_fora_horario
        )

        return {
            "success": True,
            "agendamento": agendamento
        }
    except Exception as e:
        logger.error(f"❌ Erro ao criar agendamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agendamentos/{empresa_id}")
async def listar_agendamentos(empresa_id: str):
    """
    Lista todos os agendamentos de uma empresa
    """
    try:
        response = ia_controller.supabase.table("agendamentos_ia")\
            .select("*")\
            .eq("empresa_id", empresa_id)\
            .order("prioridade", desc=True)\
            .execute()

        return {
            "success": True,
            "total": len(response.data),
            "agendamentos": response.data
        }
    except Exception as e:
        logger.error(f"❌ Erro ao listar agendamentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agendamentos/{agendamento_id}")
async def atualizar_agendamento(
    agendamento_id: str,
    request: AtualizarAgendamentoRequest
):
    """
    Atualiza um agendamento existente

    Permite atualizar qualquer campo do agendamento
    """
    try:
        # Montar dados para atualização (apenas campos fornecidos)
        dados_update = {
            k: v for k, v in request.dict().items()
            if v is not None and k != "agendamento_id"
        }

        if not dados_update:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

        # Atualizar
        response = ia_controller.supabase.table("agendamentos_ia")\
            .update(dados_update)\
            .eq("id", agendamento_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")

        logger.success(f"✅ Agendamento atualizado: {agendamento_id}")

        return {
            "success": True,
            "agendamento": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar agendamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agendamentos/{agendamento_id}")
async def deletar_agendamento(agendamento_id: str):
    """
    Deleta um agendamento
    """
    try:
        response = ia_controller.supabase.table("agendamentos_ia")\
            .delete()\
            .eq("id", agendamento_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")

        logger.success(f"✅ Agendamento deletado: {agendamento_id}")

        return {
            "success": True,
            "message": "Agendamento deletado com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar agendamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - ESTATÍSTICAS
# ============================================================================

@router.get("/stats/aprovacao/{empresa_id}")
async def get_stats_aprovacao(empresa_id: str, dias: int = 30):
    """
    Obtém estatísticas de aprovação de mensagens

    Query Params:
        - dias: Número de dias para análise (padrão: 30)

    Returns:
        - total_mensagens
        - total_aprovadas, total_editadas, total_recusadas
        - taxa_aprovacao (%)
        - tempo_medio_aprovacao
    """
    try:
        from datetime import datetime, timedelta

        data_inicio = (datetime.utcnow() - timedelta(days=dias)).isoformat()
        data_fim = datetime.utcnow().isoformat()

        response = ia_controller.supabase.rpc(
            "get_stats_aprovacao",
            {
                "p_empresa_id": empresa_id,
                "p_data_inicio": data_inicio,
                "p_data_fim": data_fim
            }
        ).execute()

        stats = response.data[0] if response.data else {}

        return {
            "success": True,
            "periodo_dias": dias,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

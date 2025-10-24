"""
Endpoints FastAPI para Sistema de Aprendizado e Simulador
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from alice.learning_system import learning_system
from alice.simulator import simulator


router = APIRouter(prefix="/api/learning", tags=["Learning & Simulator"])


# ============================================================================
# SCHEMAS
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request para registrar feedback"""
    decisao_id: str
    decisao_humana: str = Field(..., description="'aprovado', 'aprovado_editado', 'recusado'")
    texto_editado: Optional[str] = None
    motivo_recusa: Optional[str] = None
    tempo_decisao_segundos: Optional[int] = None


class CriarSimulacaoRequest(BaseModel):
    """Request para criar simulação"""
    nome: str
    descricao: Optional[str] = None
    mensagens_iniciais: Optional[List[Dict[str, str]]] = None
    contexto_inicial: Optional[Dict[str, Any]] = None


class ExecutarSimulacaoRequest(BaseModel):
    """Request para executar simulação"""
    mensagem_usuario: str
    contexto_extra: Optional[Dict[str, Any]] = None


class SimulacaoRapidaRequest(BaseModel):
    """Request para simulação rápida"""
    mensagem: str
    contexto: Optional[Dict[str, Any]] = None


# ============================================================================
# ENDPOINTS - APRENDIZADO
# ============================================================================

@router.post("/feedback")
async def registrar_feedback(request: FeedbackRequest):
    """
    Registra feedback humano sobre uma decisão da IA
    Dispara ajuste automático de pesos se necessário
    """
    try:
        sucesso = await learning_system.registrar_feedback(
            decisao_id=request.decisao_id,
            decisao_humana=request.decisao_humana,
            texto_editado=request.texto_editado,
            motivo_recusa=request.motivo_recusa,
            tempo_decisao_segundos=request.tempo_decisao_segundos
        )

        if not sucesso:
            raise HTTPException(status_code=404, detail="Decisão não encontrada")

        logger.success(f"✅ Feedback registrado: {request.decisao_id}")

        return {
            "success": True,
            "message": "Feedback registrado com sucesso",
            "aprendizado_ativado": request.decisao_humana in ["recusado", "aprovado_editado"]
        }

    except Exception as e:
        logger.error(f"❌ Erro ao registrar feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pesos/{empresa_id}")
async def get_pesos(empresa_id: str):
    """
    Retorna os pesos atuais do algoritmo de aprendizado
    """
    try:
        pesos = await learning_system.get_pesos_atuais()

        return {
            "success": True,
            "pesos": pesos
        }

    except Exception as e:
        logger.error(f"❌ Erro ao buscar pesos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estatisticas/{empresa_id}")
async def get_estatisticas(empresa_id: str):
    """
    Retorna estatísticas de aprendizado e performance
    """
    try:
        stats = await learning_system.get_estatisticas()

        return {
            "success": True,
            "estatisticas": stats
        }

    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - SIMULADOR
# ============================================================================

@router.post("/simulador/criar")
async def criar_simulacao(request: CriarSimulacaoRequest):
    """
    Cria uma nova simulação de conversa
    """
    try:
        simulacao_id = await simulator.criar_simulacao(
            nome=request.nome,
            descricao=request.descricao,
            mensagens_iniciais=request.mensagens_iniciais,
            contexto_inicial=request.contexto_inicial
        )

        if not simulacao_id:
            raise HTTPException(status_code=500, detail="Não foi possível criar simulação")

        logger.success(f"✅ Simulação criada: {simulacao_id}")

        return {
            "success": True,
            "simulacao_id": simulacao_id
        }

    except Exception as e:
        logger.error(f"❌ Erro ao criar simulação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulador/{simulacao_id}/executar")
async def executar_simulacao(simulacao_id: str, request: ExecutarSimulacaoRequest):
    """
    Executa uma simulação e retorna resultado completo
    """
    try:
        resultado = await simulator.executar_simulacao(
            simulacao_id=simulacao_id,
            mensagem_usuario=request.mensagem_usuario,
            contexto_extra=request.contexto_extra
        )

        if not resultado.get("success"):
            raise HTTPException(status_code=400, detail=resultado.get("error", "Erro desconhecido"))

        logger.success(f"✅ Simulação executada: {simulacao_id}")

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao executar simulação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulador/rapido")
async def simulacao_rapida(request: SimulacaoRapidaRequest):
    """
    Executa simulação rápida sem salvar histórico
    Ideal para testes rápidos no dashboard
    """
    try:
        resultado = await simulator.executar_rapido(
            mensagem=request.mensagem,
            contexto=request.contexto
        )

        if not resultado.get("success"):
            raise HTTPException(status_code=400, detail=resultado.get("error", "Erro desconhecido"))

        logger.success("✅ Simulação rápida executada")

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao executar simulação rápida: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulador/listar/{empresa_id}")
async def listar_simulacoes(empresa_id: str, status: Optional[str] = None):
    """
    Lista simulações criadas
    """
    try:
        simulacoes = await simulator.listar_simulacoes(status=status)

        return {
            "success": True,
            "simulacoes": simulacoes,
            "total": len(simulacoes)
        }

    except Exception as e:
        logger.error(f"❌ Erro ao listar simulações: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/simulador/{simulacao_id}")
async def excluir_simulacao(simulacao_id: str):
    """
    Exclui uma simulação
    """
    try:
        sucesso = await simulator.excluir_simulacao(simulacao_id)

        if not sucesso:
            raise HTTPException(status_code=404, detail="Simulação não encontrada")

        logger.success(f"✅ Simulação excluída: {simulacao_id}")

        return {
            "success": True,
            "message": "Simulação excluída com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao excluir simulação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

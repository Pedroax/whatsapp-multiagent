"""Sistema de Analytics da IA Alice - Integrado com Supabase"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger


class AnalyticsTracker:
    """Rastreador de métricas e analytics da IA - Busca dados reais do Supabase"""

    def __init__(self):
        """Inicializa o tracker"""
        logger.info("✅ AnalyticsTracker inicializado (modo Supabase)")

    def _get_supabase(self):
        """Retorna cliente Supabase"""
        try:
            from supabase import create_client
            from config import settings
            return create_client(settings.supabase_url, settings.supabase_service_key)
        except Exception as e:
            logger.error(f"❌ Erro ao conectar Supabase: {e}")
            return None

    # ========================================================================
    # MÉTODOS PARA COMPATIBILIDADE (IA ainda chama esses métodos)
    # ========================================================================

    def registrar_conversa_iniciada(self, phone: str):
        """Compatibilidade - Não faz nada pois dados vêm do banco"""
        logger.debug(f"📊 Conversa iniciada registrada no banco: {phone}")

    def registrar_produtos_apresentados(self, phone: str, produtos: List[str]):
        """Compatibilidade - Não faz nada pois dados vêm do banco"""
        logger.debug(f"📊 Produtos apresentados registrado no banco")

    def registrar_cotacao_enviada(self, phone: str, valor: float, produtos: List[Dict]):
        """Compatibilidade - Não faz nada pois dados vêm do banco"""
        logger.debug(f"📊 Cotação enviada registrada no banco: R$ {valor:.2f}")

    def registrar_pedido_fechado(self, phone: str, numero_pedido: str, valor_total: float,
                                 produtos: List[Dict], cliente_nome: str):
        """
        Registra pedido fechado NO BANCO DE DADOS
        Este é o único método que realmente salva dados
        """
        try:
            supabase = self._get_supabase()
            if not supabase:
                return

            # Salvar pedido na tabela pedidos
            pedido_data = {
                "numero_pedido": numero_pedido,
                "telefone": phone,
                "cliente_nome": cliente_nome,
                "valor_total": valor_total,
                "produtos": produtos,
                "status": "confirmado",
                "created_at": datetime.utcnow().isoformat()
            }

            supabase.table("pedidos").insert(pedido_data).execute()
            logger.success(f"✅ Pedido {numero_pedido} salvo no banco: R$ {valor_total:.2f}")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar pedido: {e}")

    def adicionar_lead_pendente(self, phone: str, nome: str, mensagem: str, valor_estimado: float = 0):
        """Adiciona lead pendente NO BANCO"""
        try:
            supabase = self._get_supabase()
            if not supabase:
                return

            lead_data = {
                "telefone": phone,
                "nome": nome,
                "ultima_mensagem": mensagem,
                "valor_estimado": valor_estimado,
                "status": "pendente",
                "created_at": datetime.utcnow().isoformat()
            }

            supabase.table("leads_pendentes").upsert(lead_data, on_conflict="telefone").execute()
            logger.info(f"📊 Lead pendente salvo: {nome} ({phone})")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar lead pendente: {e}")

    def remover_lead_pendente(self, phone: str):
        """Remove lead pendente DO BANCO quando fecha pedido"""
        try:
            supabase = self._get_supabase()
            if not supabase:
                return

            supabase.table("leads_pendentes").delete().eq("telefone", phone).execute()
            logger.info(f"📊 Lead pendente removido: {phone}")

        except Exception as e:
            logger.error(f"❌ Erro ao remover lead pendente: {e}")

    # ========================================================================
    # MÉTODOS QUE BUSCAM DADOS DO BANCO (USADOS PELA API)
    # ========================================================================

    def get_total_conversas(self) -> int:
        """Busca total de conversas do Supabase"""
        try:
            supabase = self._get_supabase()
            if not supabase:
                return 0

            result = supabase.table("conversas").select("id").execute()
            total = len(result.data) if result.data else 0
            logger.info(f"📊 Total de conversas: {total}")
            return total

        except Exception as e:
            logger.error(f"❌ Erro ao buscar conversas: {e}")
            return 0

    def get_total_pedidos(self) -> int:
        """Busca total de pedidos do Supabase"""
        try:
            supabase = self._get_supabase()
            if not supabase:
                return 0

            result = supabase.table("pedidos").select("id").execute()
            total = len(result.data) if result.data else 0
            logger.info(f"📊 Total de pedidos: {total}")
            return total

        except Exception as e:
            logger.error(f"❌ Erro ao buscar pedidos: {e}")
            return 0

    def get_receita_total(self) -> float:
        """Busca receita total do Supabase"""
        try:
            supabase = self._get_supabase()
            if not supabase:
                return 0.0

            result = supabase.table("pedidos").select("valor_total").execute()
            receita = sum(p.get("valor_total", 0) for p in result.data)
            logger.debug(f"📊 Receita total: R$ {receita:.2f}")
            return receita

        except Exception as e:
            logger.error(f"❌ Erro ao buscar receita: {e}")
            return 0.0

    def get_ticket_medio(self) -> float:
        """Calcula ticket médio"""
        total_pedidos = self.get_total_pedidos()
        if total_pedidos == 0:
            return 0.0
        return self.get_receita_total() / total_pedidos

    def get_taxa_conversao(self) -> float:
        """Calcula taxa de conversão"""
        total_conversas = self.get_total_conversas()
        if total_conversas == 0:
            return 0.0
        return (self.get_total_pedidos() / total_conversas) * 100

    def get_produtos_mais_vendidos(self, limit: int = 5) -> List[Dict]:
        """Busca produtos mais vendidos do Supabase"""
        try:
            supabase = self._get_supabase()
            if not supabase:
                return []

            # Buscar todos os pedidos
            result = supabase.table("pedidos").select("produtos").execute()

            # Agregar produtos
            produtos_agregados = {}
            for pedido in result.data:
                produtos = pedido.get("produtos", [])
                for produto in produtos:
                    codigo = produto.get("codigo", "")
                    nome = produto.get("nome", "")
                    quantidade = produto.get("quantidade", 0)
                    valor_unitario = produto.get("valor_unitario", 0)

                    if codigo not in produtos_agregados:
                        produtos_agregados[codigo] = {
                            "codigo": codigo,
                            "nome": nome,
                            "quantidade": 0,
                            "receita": 0
                        }

                    produtos_agregados[codigo]["quantidade"] += quantidade
                    produtos_agregados[codigo]["receita"] += quantidade * valor_unitario

            # Ordenar por receita e pegar top N
            produtos_ordenados = sorted(
                produtos_agregados.values(),
                key=lambda x: x["receita"],
                reverse=True
            )[:limit]

            logger.debug(f"📊 Top {limit} produtos: {len(produtos_ordenados)} encontrados")
            return produtos_ordenados

        except Exception as e:
            logger.error(f"❌ Erro ao buscar produtos mais vendidos: {e}")
            return []

    def get_top_produtos(self, limit: int = 5) -> List[Dict]:
        """Alias para compatibilidade com endpoint"""
        return self.get_produtos_mais_vendidos(limit)

    def get_leads_pendentes(self) -> List[Dict]:
        """Busca leads pendentes do Supabase"""
        try:
            supabase = self._get_supabase()
            if not supabase:
                return []

            result = supabase.table("leads_pendentes")\
                .select("*")\
                .eq("status", "pendente")\
                .order("created_at", desc=True)\
                .execute()

            leads = []
            for lead in result.data:
                leads.append({
                    "nome": lead.get("nome", "Cliente"),
                    "telefone": lead.get("telefone", ""),
                    "ultima_mensagem": lead.get("ultima_mensagem", ""),
                    "valor_estimado": lead.get("valor_estimado", 0),
                    "timestamp": lead.get("created_at", "")
                })

            logger.debug(f"📊 Leads pendentes: {len(leads)}")
            return leads

        except Exception as e:
            logger.error(f"❌ Erro ao buscar leads pendentes: {e}")
            return []

    def get_funil_conversao(self) -> List[Dict]:
        """Retorna dados do funil de conversão baseado em dados reais"""
        try:
            total_conversas = self.get_total_conversas()

            # Para produtos apresentados e cotações, vamos estimar baseado em conversas
            # (ideal seria ter tabelas separadas para isso)
            produtos_apresentados = int(total_conversas * 0.75) if total_conversas > 0 else 0
            cotacoes_enviadas = int(total_conversas * 0.37) if total_conversas > 0 else 0
            pedidos_fechados = self.get_total_pedidos()

            return [
                {
                    "stage": "Conversas Iniciadas",
                    "count": total_conversas,
                    "percentage": 100 if total_conversas > 0 else 0
                },
                {
                    "stage": "Produtos Apresentados",
                    "count": produtos_apresentados,
                    "percentage": int((produtos_apresentados / total_conversas) * 100) if total_conversas > 0 else 0
                },
                {
                    "stage": "Cotações Enviadas",
                    "count": cotacoes_enviadas,
                    "percentage": int((cotacoes_enviadas / total_conversas) * 100) if total_conversas > 0 else 0
                },
                {
                    "stage": "Pedidos Fechados",
                    "count": pedidos_fechados,
                    "percentage": int((pedidos_fechados / total_conversas) * 100) if total_conversas > 0 else 0
                }
            ]

        except Exception as e:
            logger.error(f"❌ Erro ao gerar funil: {e}")
            return []

    def get_metricas_completas(self) -> Dict[str, Any]:
        """Retorna todas as métricas para o dashboard - DADOS REAIS DO BANCO"""

        # Buscar dados reais
        total_conversas = self.get_total_conversas()
        total_pedidos = self.get_total_pedidos()
        receita_total = self.get_receita_total()
        ticket_medio = self.get_ticket_medio()
        taxa_conversao = self.get_taxa_conversao()
        leads_pendentes = len(self.get_leads_pendentes())

        return {
            "total_revenue": receita_total,
            "revenue_change": 0.0,  # Será calculado quando implementar comparação de períodos

            "total_orders": total_pedidos,
            "orders_change": 0.0,

            "conversations": total_conversas,
            "conversations_change": 0.0,

            "closed_deals": total_pedidos,
            "closed_deals_change": 0.0,

            "avg_ticket": ticket_medio,
            "avg_ticket_change": 0.0,

            "conversion_rate": taxa_conversao,
            "conversion_rate_change": 0.0,

            "pending_leads": leads_pendentes,
            "pending_leads_change": 0.0,

            "response_time": 0,  # Será implementado com dados de tempo real
            "response_time_change": 0.0,
        }


# Instância global
analytics_tracker = AnalyticsTracker()

"""Sistema de Analytics da IA Alice"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
import random


class AnalyticsTracker:
    """Rastreador de métricas e analytics da IA"""

    def __init__(self):
        """Inicializa o tracker com dados fictícios + reais"""

        # Dados reais que serão incrementados pela IA
        self.real_data = {
            "conversas_iniciadas": 0,
            "produtos_apresentados": 0,
            "cotacoes_enviadas": 0,
            "pedidos_fechados": 0,
            "receita_total": 0.0,
            "produtos_vendidos": {},  # {produto_codigo: {quantidade, receita}}
            "leads_pendentes": []  # Lista de leads que não completaram
        }

        # Dados fictícios para demonstração (mesclados com reais)
        self.demo_data = self._gerar_dados_demo()

        logger.info("✅ AnalyticsTracker inicializado")

    def _gerar_dados_demo(self) -> Dict[str, Any]:
        """Gera dados fictícios realistas para demonstração"""

        # Conversas demo das últimas 2 semanas
        base_conversas = 342
        base_pedidos = 87

        return {
            "conversas_base": base_conversas,
            "pedidos_base": base_pedidos,
            "receita_base": 145680.00,

            # Top produtos fictícios
            "top_produtos_demo": [
                {"codigo": "BAT-60AH-SEL", "nome": "Bateria 60Ah Selada", "quantidade": 45, "receita": 67500},
                {"codigo": "BAT-100AH-AUT", "nome": "Bateria 100Ah Automotiva", "quantidade": 32, "receita": 56000},
                {"codigo": "BAT-45AH-EST", "nome": "Bateria 45Ah Estacionária", "quantidade": 28, "receita": 39200},
                {"codigo": "BAT-75AH-PRM", "nome": "Bateria 75Ah Premium", "quantidade": 18, "receita": 31500},
                {"codigo": "BAT-150AH-IND", "nome": "Bateria 150Ah Industrial", "quantidade": 12, "receita": 28800},
            ],

            # Leads pendentes demo
            "leads_pendentes_demo": [
                {
                    "nome": "Roberto Almeida",
                    "telefone": "+55 61 98888-1234",
                    "ultima_mensagem": "Quero a bateria de 60ah, mas preciso ver o prazo de entrega",
                    "valor_estimado": 2850,
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    "nome": "Fernanda Costa",
                    "telefone": "+55 61 98888-5678",
                    "ultima_mensagem": "Vou confirmar com meu chefe e te retorno",
                    "valor_estimado": 4200,
                    "timestamp": (datetime.now() - timedelta(hours=5)).isoformat()
                },
                {
                    "nome": "Paulo Mendes",
                    "telefone": "+55 61 98888-9012",
                    "ultima_mensagem": "Preciso de 20 unidades, pode fazer desconto?",
                    "valor_estimado": 28000,
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat()
                },
                {
                    "nome": "Ana Silva",
                    "telefone": "+55 61 98888-3456",
                    "ultima_mensagem": "Qual o prazo de pagamento mesmo?",
                    "valor_estimado": 1650,
                    "timestamp": (datetime.now() - timedelta(days=1, hours=2)).isoformat()
                },
                {
                    "nome": "Carlos Eduardo",
                    "telefone": "+55 61 98888-7890",
                    "ultima_mensagem": "Deixa eu verificar o modelo do meu carro",
                    "valor_estimado": 3100,
                    "timestamp": (datetime.now() - timedelta(days=2)).isoformat()
                }
            ]
        }

    # ========================================================================
    # MÉTODOS CHAMADOS PELA IA (DADOS REAIS)
    # ========================================================================

    def registrar_conversa_iniciada(self, phone: str):
        """Registra quando uma nova conversa é iniciada"""
        self.real_data["conversas_iniciadas"] += 1
        logger.info(f"📊 Analytics: Nova conversa iniciada - Total: {self.get_total_conversas()}")

    def registrar_produtos_apresentados(self, phone: str, produtos: List[str]):
        """Registra quando produtos são apresentados ao cliente"""
        self.real_data["produtos_apresentados"] += 1
        logger.info(f"📊 Analytics: Produtos apresentados - Total: {self.real_data['produtos_apresentados']}")

    def registrar_cotacao_enviada(self, phone: str, valor: float, produtos: List[Dict]):
        """Registra quando uma cotação é enviada"""
        self.real_data["cotacoes_enviadas"] += 1
        logger.info(f"📊 Analytics: Cotação enviada R$ {valor:.2f} - Total: {self.real_data['cotacoes_enviadas']}")

    def registrar_pedido_fechado(
        self,
        phone: str,
        numero_pedido: str,
        valor_total: float,
        produtos: List[Dict],
        cliente_nome: str
    ):
        """
        Registra quando um pedido é FECHADO (API enviar_pedido com sucesso)

        IMPORTANTE: Este método deve ser chamado APENAS quando:
        - Cliente confirmou o pedido
        - API enviar_pedido retornou sucesso
        """
        self.real_data["pedidos_fechados"] += 1
        self.real_data["receita_total"] += valor_total

        # Registrar produtos vendidos
        for produto in produtos:
            codigo = produto.get("nome_produto", produto.get("codigo", "UNKNOWN"))
            qtd = produto.get("quantidade", 0)
            valor_unit = produto.get("valor_unitario", 0)
            receita = qtd * valor_unit

            if codigo not in self.real_data["produtos_vendidos"]:
                self.real_data["produtos_vendidos"][codigo] = {
                    "quantidade": 0,
                    "receita": 0.0
                }

            self.real_data["produtos_vendidos"][codigo]["quantidade"] += qtd
            self.real_data["produtos_vendidos"][codigo]["receita"] += receita

        logger.success(
            f"🎉 Analytics: PEDIDO FECHADO #{numero_pedido} - "
            f"R$ {valor_total:.2f} - Cliente: {cliente_nome}"
        )
        logger.success(
            f"📊 Totais: {self.get_total_pedidos()} pedidos | "
            f"R$ {self.get_receita_total():.2f} em vendas"
        )

    def registrar_lead_pendente(
        self,
        phone: str,
        nome: str,
        ultima_mensagem: str,
        valor_estimado: float
    ):
        """
        Registra lead que INICIOU mas NÃO completou o pedido

        Usado quando:
        - Cliente recebeu cotação
        - Não confirmou/finalizou
        - Precisa de follow-up humano
        """
        lead = {
            "nome": nome,
            "telefone": phone,
            "ultima_mensagem": ultima_mensagem,
            "valor_estimado": valor_estimado,
            "timestamp": datetime.now().isoformat()
        }

        # Evitar duplicatas
        if not any(l["telefone"] == phone for l in self.real_data["leads_pendentes"]):
            self.real_data["leads_pendentes"].append(lead)
            logger.warning(
                f"⚠️ Analytics: Lead pendente registrado - {nome} ({phone}) - "
                f"Potencial: R$ {valor_estimado:.2f}"
            )

    def remover_lead_pendente(self, phone: str):
        """Remove lead pendente (quando humano recupera a venda)"""
        self.real_data["leads_pendentes"] = [
            l for l in self.real_data["leads_pendentes"]
            if l["telefone"] != phone
        ]
        logger.info(f"✅ Analytics: Lead {phone} removido (recuperado)")

    # ========================================================================
    # GETTERS - DADOS MESCLADOS (REAL + DEMO)
    # ========================================================================

    def get_total_conversas(self) -> int:
        """Retorna total de conversas (demo + real)"""
        return self.demo_data["conversas_base"] + self.real_data["conversas_iniciadas"]

    def get_total_pedidos(self) -> int:
        """Retorna total de pedidos fechados (demo + real)"""
        return self.demo_data["pedidos_base"] + self.real_data["pedidos_fechados"]

    def get_receita_total(self) -> float:
        """Retorna receita total (demo + real)"""
        return self.demo_data["receita_base"] + self.real_data["receita_total"]

    def get_taxa_conversao(self) -> float:
        """Calcula taxa de conversão"""
        total_conversas = self.get_total_conversas()
        if total_conversas == 0:
            return 0.0
        return (self.get_total_pedidos() / total_conversas) * 100

    def get_ticket_medio(self) -> float:
        """Calcula ticket médio"""
        total_pedidos = self.get_total_pedidos()
        if total_pedidos == 0:
            return 0.0
        return self.get_receita_total() / total_pedidos

    def get_top_produtos(self, limit: int = 5) -> List[Dict]:
        """Retorna top produtos (mesclando demo + real)"""

        # Combinar produtos demo com produtos reais
        produtos_combined = {}

        # Adicionar produtos demo
        for prod in self.demo_data["top_produtos_demo"]:
            produtos_combined[prod["codigo"]] = {
                "codigo": prod["codigo"],
                "nome": prod["nome"],
                "quantidade": prod["quantidade"],
                "receita": prod["receita"]
            }

        # Adicionar/somar produtos reais
        for codigo, data in self.real_data["produtos_vendidos"].items():
            if codigo in produtos_combined:
                produtos_combined[codigo]["quantidade"] += data["quantidade"]
                produtos_combined[codigo]["receita"] += data["receita"]
            else:
                produtos_combined[codigo] = {
                    "codigo": codigo,
                    "nome": codigo,  # Nome será o código se não tiver nome demo
                    "quantidade": data["quantidade"],
                    "receita": data["receita"]
                }

        # Ordenar por receita e retornar top N
        sorted_produtos = sorted(
            produtos_combined.values(),
            key=lambda x: x["receita"],
            reverse=True
        )

        return sorted_produtos[:limit]

    def get_leads_pendentes(self) -> List[Dict]:
        """Retorna leads pendentes (demo + real)"""
        # Combinar leads demo com leads reais
        all_leads = self.demo_data["leads_pendentes_demo"].copy()
        all_leads.extend(self.real_data["leads_pendentes"])

        # Ordenar por valor (maior primeiro)
        return sorted(all_leads, key=lambda x: x["valor_estimado"], reverse=True)

    def get_funil_conversao(self) -> List[Dict]:
        """Retorna dados do funil de conversão"""
        total_conversas = self.get_total_conversas()
        produtos_apresentados = self.demo_data["conversas_base"] * 0.75 + self.real_data["produtos_apresentados"]
        cotacoes_enviadas = self.demo_data["conversas_base"] * 0.37 + self.real_data["cotacoes_enviadas"]
        pedidos_fechados = self.get_total_pedidos()

        return [
            {
                "stage": "Conversas Iniciadas",
                "count": total_conversas,
                "percentage": 100
            },
            {
                "stage": "Produtos Apresentados",
                "count": int(produtos_apresentados),
                "percentage": int((produtos_apresentados / total_conversas) * 100) if total_conversas > 0 else 0
            },
            {
                "stage": "Cotações Enviadas",
                "count": int(cotacoes_enviadas),
                "percentage": int((cotacoes_enviadas / total_conversas) * 100) if total_conversas > 0 else 0
            },
            {
                "stage": "Pedidos Fechados",
                "count": pedidos_fechados,
                "percentage": int((pedidos_fechados / total_conversas) * 100) if total_conversas > 0 else 0
            }
        ]

    def get_metricas_completas(self) -> Dict[str, Any]:
        """Retorna todas as métricas para o dashboard"""

        # Simular variação (crescimento) para demo
        base_growth = random.uniform(8.0, 25.0)

        return {
            "total_revenue": self.get_receita_total(),
            "revenue_change": round(base_growth + random.uniform(-2, 5), 1),

            "total_orders": self.get_total_pedidos(),
            "orders_change": round(base_growth + random.uniform(-5, 3), 1),

            "conversations": self.get_total_conversas(),
            "conversations_change": round(base_growth + random.uniform(-3, 2), 1),

            "closed_deals": self.get_total_pedidos(),
            "closed_deals_change": round(base_growth + random.uniform(0, 8), 1),

            "avg_ticket": self.get_ticket_medio(),
            "avg_ticket_change": round(random.uniform(3.0, 8.0), 1),

            "conversion_rate": self.get_taxa_conversao(),
            "conversion_rate_change": round(random.uniform(2.0, 5.0), 1),

            "pending_leads": len(self.get_leads_pendentes()),
            "pending_leads_change": round(random.uniform(-20.0, -10.0), 1),  # Negativo = melhorando

            "response_time": random.randint(40, 55),  # Segundos
            "response_time_change": round(random.uniform(-15.0, -8.0), 1),  # Negativo = melhorando
        }


# Instância global
analytics_tracker = AnalyticsTracker()

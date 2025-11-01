"""Monitor de saúde do sistema Alice"""
import asyncio
import psutil
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger
from config import settings


class HealthMonitor:
    """Monitora saúde do sistema e dispara alertas críticos"""

    def __init__(self, alert_phone: str = "5561982563956"):
        """
        Args:
            alert_phone: Número do WhatsApp para enviar alertas (com DDI)
        """
        self.alert_phone = alert_phone
        self.alertas_enviados: Dict[str, datetime] = {}  # Controla quais alertas já foram enviados
        self.error_counters: Dict[str, int] = {}  # Conta erros consecutivos

        # Thresholds
        self.MAX_MEMORY_PERCENT = 90
        self.MAX_CPU_PERCENT = 90
        self.MAX_CONSECUTIVE_ERRORS = 5
        self.ALERT_COOLDOWN_HOURS = 1  # Só re-alerta após 1h do mesmo erro resolvido

    async def check_system_health(self) -> Dict[str, Any]:
        """
        Verifica saúde geral do sistema

        Returns:
            Dict com status de todos os componentes
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "backend": await self._check_backend(),
            "evolution_api": await self._check_evolution_api(),
            "lc_erp_api": await self._check_lc_erp_api(),
            "supabase": await self._check_supabase(),
            "system_resources": self._check_system_resources(),
            "gemini_health": self._check_model_health("gemini"),
            "gpt_health": self._check_model_health("gpt-4o")
        }

        # Verifica se há problemas críticos
        await self._check_critical_issues(health_status)

        return health_status

    async def _check_backend(self) -> Dict[str, Any]:
        """Verifica se backend está respondendo"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/health")
                return {
                    "status": "healthy" if response.status_code == 200 else "degraded",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        except Exception as e:
            await self._send_alert(
                "backend_offline",
                "🚨 Backend Offline",
                f"Backend não está respondendo.\n\nErro: {str(e)}\n\n🔧 Ação: Reiniciar serviço alice-backend"
            )
            return {"status": "offline", "error": str(e)}

    async def _check_evolution_api(self) -> Dict[str, Any]:
        """Verifica se Evolution API está acessível"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.evolution_api_url}/instance/fetchInstances",
                    headers={"apikey": settings.evolution_api_key}
                )
                return {
                    "status": "healthy" if response.status_code == 200 else "degraded",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        except Exception as e:
            await self._send_alert(
                "evolution_api_offline",
                "🚨 Evolution API Offline",
                f"Não consegue enviar mensagens no WhatsApp.\n\nErro: {str(e)}\n\n🔧 Ação: Verificar Evolution API"
            )
            return {"status": "offline", "error": str(e)}

    async def _check_lc_erp_api(self) -> Dict[str, Any]:
        """Verifica se LC ERP API está acessível"""
        try:
            # Tenta apenas uma requisição leve de ping
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Usa endpoint de autenticação que é mais leve
                from alice.tools import gerar_autenticacao
                auth = gerar_autenticacao()

                response = await client.post(
                    "https://b.appeletronicos.com.br/ws/ws.rule",
                    json={
                        "timestamp": auth["timestamp"],
                        "token": auth["token"],
                        "action": "select",
                        "instance": "bateria",
                        "dataset": {},
                        "filter": {"codigo": 1},  # Busca simples
                        "sort": {"codigo": "asc"},
                        "limit": 1
                    },
                    timeout=10.0
                )

                return {
                    "status": "healthy" if response.status_code == 200 else "degraded",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        except Exception as e:
            await self._send_alert(
                "lc_erp_offline",
                "🚨 LC ERP API Offline",
                f"Não consegue buscar preços/criar pedidos.\n\nErro: {str(e)}\n\n🔧 Ação: Verificar API LC"
            )
            return {"status": "offline", "error": str(e)}

    async def _check_supabase(self) -> Dict[str, Any]:
        """Verifica se Supabase está acessível"""
        try:
            from supabase import create_client
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)

            # Tenta uma query simples
            result = supabase.table("chat_sessions").select("phone").limit(1).execute()

            return {
                "status": "healthy",
                "records_accessible": len(result.data) if result.data else 0
            }
        except Exception as e:
            await self._send_alert(
                "supabase_offline",
                "🚨 Supabase (Banco de Dados) Offline",
                f"Não consegue salvar/carregar conversas.\n\nErro: {str(e)}\n\n🔧 Ação: Verificar Supabase"
            )
            return {"status": "offline", "error": str(e)}

    def _check_system_resources(self) -> Dict[str, Any]:
        """Verifica uso de CPU e memória"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        resources = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "disk_percent": disk.percent,
            "status": "healthy"
        }

        # Alerta se recursos críticos
        if memory.percent > self.MAX_MEMORY_PERCENT:
            asyncio.create_task(self._send_alert(
                "high_memory",
                "⚠️ Memória Crítica",
                f"Memória em {memory.percent:.1f}% (limite: {self.MAX_MEMORY_PERCENT}%)\n\n"
                f"Usado: {memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB\n\n"
                f"🔧 Ação: Reiniciar servidor ou escalar"
            ))
            resources["status"] = "critical"

        if cpu_percent > self.MAX_CPU_PERCENT:
            asyncio.create_task(self._send_alert(
                "high_cpu",
                "⚠️ CPU Crítica",
                f"CPU em {cpu_percent:.1f}% (limite: {self.MAX_CPU_PERCENT}%)\n\n"
                f"🔧 Ação: Verificar processos ou escalar"
            ))
            resources["status"] = "critical"

        return resources

    def _check_model_health(self, model_name: str) -> Dict[str, Any]:
        """
        Verifica saúde de um modelo (Gemini ou GPT-4o)
        Baseado em contadores de erro mantidos em memória
        """
        error_count = self.error_counters.get(f"{model_name}_errors", 0)

        return {
            "model": model_name,
            "consecutive_errors": error_count,
            "status": "healthy" if error_count < self.MAX_CONSECUTIVE_ERRORS else "failing"
        }

    def increment_model_error(self, model_name: str):
        """Incrementa contador de erros de um modelo"""
        key = f"{model_name}_errors"
        self.error_counters[key] = self.error_counters.get(key, 0) + 1

        # Se atingir threshold, envia alerta
        if self.error_counters[key] == self.MAX_CONSECUTIVE_ERRORS:
            suggestion = "Trocar webhook para GPT-4o" if model_name == "gemini" else "Verificar créditos OpenAI"

            asyncio.create_task(self._send_alert(
                f"{model_name}_failing",
                f"🚨 {model_name.upper()} com Falhas",
                f"Modelo {model_name} falhou {self.MAX_CONSECUTIVE_ERRORS}x seguidas.\n\n"
                f"🔧 Ação sugerida: {suggestion}"
            ))

    def reset_model_errors(self, model_name: str):
        """Reseta contador quando modelo volta a funcionar"""
        key = f"{model_name}_errors"
        if key in self.error_counters:
            # Se tinha erros antes, limpa o alerta também
            if self.error_counters[key] >= self.MAX_CONSECUTIVE_ERRORS:
                alert_key = f"{model_name}_failing"
                if alert_key in self.alertas_enviados:
                    del self.alertas_enviados[alert_key]

            self.error_counters[key] = 0

    async def _check_critical_issues(self, health_status: Dict[str, Any]):
        """Analisa status geral e identifica problemas críticos adicionais"""

        # Verifica se tanto Gemini quanto GPT estão falhando
        gemini_failing = health_status["gemini_health"]["status"] == "failing"
        gpt_failing = health_status["gpt_health"]["status"] == "failing"

        if gemini_failing and gpt_failing:
            await self._send_alert(
                "all_models_failing",
                "🚨🚨 CRÍTICO: Todos os Modelos Falhando",
                "Tanto Gemini quanto GPT-4o estão com erros!\n\n"
                "Alice NÃO ESTÁ RESPONDENDO clientes.\n\n"
                "🔧 Ação URGENTE: Verificar APIs OpenAI e Google"
            )

    async def _send_alert(self, alert_key: str, titulo: str, mensagem: str):
        """
        Envia alerta via WhatsApp (apenas uma vez por tipo de erro)

        Args:
            alert_key: Identificador único do alerta
            titulo: Título do alerta
            mensagem: Corpo da mensagem
        """
        # Verifica se já enviou este alerta
        if alert_key in self.alertas_enviados:
            last_sent = self.alertas_enviados[alert_key]

            # Só re-envia se passou o cooldown (significa que erro voltou)
            if datetime.now() - last_sent < timedelta(hours=self.ALERT_COOLDOWN_HOURS):
                logger.debug(f"⏳ Alerta '{alert_key}' já enviado recentemente, ignorando...")
                return

        try:
            # Formata mensagem final
            full_message = f"""🤖 *ALICE - SISTEMA DE MONITORAMENTO*

{titulo}

{mensagem}

⏰ Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

📊 Painel: https://lcbaterias.automatexia.com.br/monitor
"""

            # Envia via Evolution API
            from whatsapp.evolution_api import EvolutionAPI
            whatsapp = EvolutionAPI()

            await whatsapp.send_text(self.alert_phone, full_message)

            # Marca como enviado
            self.alertas_enviados[alert_key] = datetime.now()

            logger.warning(f"🚨 Alerta enviado para {self.alert_phone}: {titulo}")

        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta: {e}")

    def clear_alert(self, alert_key: str):
        """
        Remove um alerta do histórico (usado quando problema é resolvido)
        Permite re-alertar se problema voltar
        """
        if alert_key in self.alertas_enviados:
            del self.alertas_enviados[alert_key]
            logger.info(f"✅ Alerta '{alert_key}' limpo - pode alertar novamente se necessário")


# Instância global
health_monitor = HealthMonitor(alert_phone="5561982563956")

"""
Utilitário para dividir mensagens longas em partes menores
Similar ao Split Out do n8n
"""

import asyncio
import random
from typing import List
from dataclasses import dataclass


@dataclass
class SplitMessage:
    """Mensagem dividida com delay"""
    text: str
    delay: float  # segundos


def split_message(message: str) -> List[SplitMessage]:
    """
    Divide mensagem em partes baseado em quebras de linha
    Simula comportamento humano de enviar mensagens picadas

    Args:
        message: Mensagem completa da IA

    Returns:
        Lista de mensagens divididas com delays
    """
    # Remove espaços extras e normaliza quebras de linha
    normalized = message.strip()
    normalized = '\n\n'.join(line for line in normalized.split('\n\n') if line.strip())

    # Divide por quebras de linha
    parts = [part.strip() for part in normalized.split('\n') if part.strip()]

    if not parts:
        return [SplitMessage(text=message, delay=0)]

    # Mapeia cada parte com um delay calculado
    result = []
    for i, part in enumerate(parts):
        # Primeiro fragmento: sem delay
        if i == 0:
            result.append(SplitMessage(text=part, delay=0))
        else:
            # Delay baseado no tamanho do texto anterior
            previous_text = parts[i - 1]
            typing_time = calculate_typing_time(previous_text)
            result.append(SplitMessage(text=part, delay=typing_time))

    return result


def calculate_typing_time(text: str) -> float:
    """
    Calcula tempo de digitação simulado baseado no comprimento do texto

    Args:
        text: Texto anterior digitado

    Returns:
        Tempo em segundos
    """
    base_delay = 0.8  # delay mínimo (segundos)
    chars_per_second = 15  # velocidade de digitação média

    text_length = len(text)
    typing_time = text_length / chars_per_second

    # Adiciona variação aleatória (±20%) para parecer mais natural
    variation = typing_time * 0.2
    random_variation = (random.random() - 0.5) * variation

    return max(base_delay, typing_time + random_variation)


def smart_split(message: str) -> List[SplitMessage]:
    """
    Divide mensagem de forma inteligente, respeitando contexto
    Agrupa linhas relacionadas (ex: perguntas com contexto)

    Args:
        message: Mensagem completa da IA

    Returns:
        Lista de mensagens divididas com delays
    """
    # Remove espaços extras
    normalized = message.strip()
    lines = [line.strip() for line in normalized.split('\n') if line.strip()]

    groups = []
    current_group = []

    for i, line in enumerate(lines):
        current_group.append(line)

        # Verifica se deve continuar agrupando
        next_line = lines[i + 1] if i + 1 < len(lines) else None
        should_continue = next_line and (
            # Próxima linha é muito curta (provável continuação)
            len(next_line) < 20 or
            # Linha atual termina com vírgula ou "e"
            line.endswith(',') or
            line.endswith(' e')
        )

        if not should_continue:
            groups.append('\n'.join(current_group))
            current_group = []

    # Adiciona último grupo se existir
    if current_group:
        groups.append('\n'.join(current_group))

    # Mapeia para SplitMessage com delays
    result = []
    for i, text in enumerate(groups):
        if i == 0:
            result.append(SplitMessage(text=text, delay=0))
        else:
            delay_time = calculate_typing_time(groups[i - 1])
            result.append(SplitMessage(text=text, delay=delay_time))

    return result


async def send_with_typing_simulation(
    send_func,
    phone: str,
    message: str,
    use_smart_split: bool = True
) -> List[dict]:
    """
    Envia mensagem com simulação de digitação (typing)

    Args:
        send_func: Função async para enviar mensagem (ex: evolution_api.send_text)
        phone: Número do telefone
        message: Mensagem completa
        use_smart_split: Se True, usa smart_split; caso contrário split_message

    Returns:
        Lista de respostas de cada envio
    """
    # Divide mensagem
    parts = smart_split(message) if use_smart_split else split_message(message)

    results = []

    for part in parts:
        # Aguarda delay (simula digitação)
        if part.delay > 0:
            await asyncio.sleep(part.delay)

        # Envia mensagem
        result = await send_func(phone, part.text)
        results.append(result)

    return results

import { useEffect, useRef } from 'react'
import { notificationService } from '@/lib/notifications'
import type { NotificationType } from '@/lib/notifications'
import type { Conversa } from '@/types'

interface UseNotificationsOptions {
  enabled?: boolean
  conversas: Conversa[]
}

export function useNotifications({ enabled = true, conversas }: UseNotificationsOptions) {
  const conversasAntigasRef = useRef<Conversa[]>([])

  useEffect(() => {
    if (!enabled) return

    const conversasAntigas = conversasAntigasRef.current

    conversas.forEach(conversa => {
      const antiga = conversasAntigas.find(c => c.id === conversa.id)

      if (!antiga) {
        if (conversa.nao_lidas > 0) {
          notificationService.notificar(
            'nova_mensagem',
            `Nova mensagem de ${conversa.lead.nome}`,
            conversa.ultima_mensagem?.conteudo
          )
        }
        return
      }

      if (conversa.nao_lidas > antiga.nao_lidas) {
        const novasMensagens = conversa.nao_lidas - antiga.nao_lidas

        let tipo: NotificationType = 'nova_mensagem'

        if (conversa.prioridade === 'urgente') {
          tipo = 'urgente'
        } else if (conversa.departamento && !antiga.departamento) {
          tipo = 'transferencia'
        }

        notificationService.notificar(
          tipo,
          `${novasMensagens} nova(s) mensagem(ns) de ${conversa.lead.nome}`,
          conversa.ultima_mensagem?.conteudo
        )
      }

      if (conversa.departamento && !antiga.departamento) {
        notificationService.notificar(
          'transferencia',
          `Conversa transferida: ${conversa.lead.nome}`,
          `Departamento: ${conversa.departamento.nome}`
        )
      }

      if (conversa.prioridade === 'urgente' && antiga.prioridade !== 'urgente') {
        notificationService.notificar(
          'urgente',
          `🚨 URGENTE: ${conversa.lead.nome}`,
          conversa.ultima_mensagem?.conteudo
        )
      }
    })

    conversasAntigasRef.current = conversas

  }, [conversas, enabled])

  return {
    notificar: (tipo: NotificationType, titulo: string, mensagem?: string) => {
      if (enabled) {
        notificationService.notificar(tipo, titulo, mensagem)
      }
    },
    tocarSom: (tipo: NotificationType) => {
      if (enabled) {
        notificationService.tocarSom(tipo)
      }
    },
    solicitarPermissao: () => notificationService.solicitarPermissao()
  }
}

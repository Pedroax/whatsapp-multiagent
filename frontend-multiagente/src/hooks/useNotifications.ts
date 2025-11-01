import { useEffect, useRef } from 'react'
import { notificationService } from '@/lib/notifications'
import type { NotificationType } from '@/lib/notifications'
import type { Conversa } from '@/types'

interface UseNotificationsOptions {
  enabled?: boolean
  conversas: Conversa[]
  userDepartamento?: string  // Departamento do usuário logado
  userRole?: string  // Role do usuário
}

export function useNotifications({ enabled = true, conversas, userDepartamento, userRole }: UseNotificationsOptions) {
  const conversasAntigasRef = useRef<Conversa[]>([])

  useEffect(() => {
    if (!enabled) return

    // Super admin não recebe notificações de transferência (muito barulho)
    const isAdmin = userRole === 'super_admin'

    const conversasAntigas = conversasAntigasRef.current

    conversas.forEach(conversa => {
      const antiga = conversasAntigas.find(c => c.id === conversa.id)

      // Nova conversa apareceu na lista
      if (!antiga) {
        // Se é departamento (não super admin) e a conversa acabou de chegar
        if (!isAdmin && userDepartamento && conversa.departamento_slug === userDepartamento) {
          notificationService.notificar(
            'transferencia',
            `📥 Nova conversa transferida`,
            `${conversa.lead.nome} - ${conversa.lead.telefone}`
          )
        } else if (conversa.nao_lidas > 0) {
          notificationService.notificar(
            'nova_mensagem',
            `Nova mensagem de ${conversa.lead.nome}`,
            conversa.ultima_mensagem?.conteudo
          )
        }
        return
      }

      // Novas mensagens
      if (conversa.nao_lidas > antiga.nao_lidas) {
        const novasMensagens = conversa.nao_lidas - antiga.nao_lidas

        let tipo: NotificationType = 'nova_mensagem'

        if (conversa.prioridade === 'urgente') {
          tipo = 'urgente'
        }

        notificationService.notificar(
          tipo,
          `${novasMensagens} nova(s) mensagem(ns) de ${conversa.lead.nome}`,
          conversa.ultima_mensagem?.conteudo
        )
      }

      // Conversa foi transferida PARA este departamento
      // Só notifica departamentos (não super admin)
      if (!isAdmin && userDepartamento) {
        const antigaDepartamento = antiga.departamento_slug
        const novoDepartamento = conversa.departamento_slug

        // Conversa chegou neste departamento
        if (novoDepartamento === userDepartamento && antigaDepartamento !== userDepartamento) {
          notificationService.notificar(
            'transferencia',
            `📥 Conversa transferida para você`,
            `${conversa.lead.nome} - ${conversa.lead.telefone}`
          )
        }
      }

      // Urgente
      if (conversa.prioridade === 'urgente' && antiga.prioridade !== 'urgente') {
        notificationService.notificar(
          'urgente',
          `🚨 URGENTE: ${conversa.lead.nome}`,
          conversa.ultima_mensagem?.conteudo
        )
      }
    })

    conversasAntigasRef.current = conversas

  }, [conversas, enabled, userDepartamento, userRole])

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

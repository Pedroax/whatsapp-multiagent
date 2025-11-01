import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import type { Conversa, Mensagem } from '@/types'
import { useAuth } from './useAuth'

export function useConversas() {
  console.log('🚀 useConversas INICIADO')

  const [conversas, setConversas] = useState<Conversa[]>([])
  const [mensagens, setMensagens] = useState<Record<string, Mensagem[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { usuario } = useAuth()

  console.log('👤 Usuário:', usuario)

  useEffect(() => {
    if (usuario) {
      // Carga inicial com loading
      fetchConversas(true)

      // Subscription para atualizações em tempo real - CONVERSAS
      const conversasSubscription = supabase
        .channel('conversas-realtime')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'conversas' }, (payload) => {
          console.log('🔄 Mudança em conversas:', payload)
          // Atualiza SEM loading para não perder estado
          fetchConversas(false)
        })
        .subscribe()

      // Subscription para atualizações em tempo real - MENSAGENS
      const mensagensSubscription = supabase
        .channel('mensagens-realtime')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'mensagens' }, (payload) => {
          console.log('🔄 Mudança em mensagens:', payload)
          // Atualiza SEM loading para não perder estado
          fetchConversas(false)
        })
        .subscribe()

      return () => {
        conversasSubscription.unsubscribe()
        mensagensSubscription.unsubscribe()
      }
    }
  }, [usuario])

  async function fetchConversas(isInitialLoad = false) {
    try {
      // Só mostra loading na primeira carga, não em atualizações
      if (isInitialLoad) {
        setLoading(true)
      }

      if (!usuario) {
        setConversas([])
        setMensagens({})
        setLoading(false)
        return
      }

      // Buscar conversas COM mensagens do backend
      const API_URL = import.meta.env.VITE_API_URL || 'https://lcbaterias.automatexia.com.br'
      console.log('🔍 Buscando conversas de:', `${API_URL}/api/conversas`)

      const response = await fetch(`${API_URL}/api/conversas`)

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('📦 Dados recebidos do backend:', data)

      const conversasData = data.conversas || []

      // Mapear conversas
      const conversasFormatadas: Conversa[] = conversasData.map((c: any) => ({
        id: c.id,
        empresa_id: c.empresa_id,
        lead_id: c.id,
        lead: {
          id: c.id,
          empresa_id: c.empresa_id,
          nome: c.nome_lead || 'Cliente',
          telefone: c.phone,
          tags: []
        },
        departamento_slug: c.departamento_slug,  // ADICIONAR campo para filtro
        status: 'aberta',
        modo_ia: c.modo_ia || 'ativo',
        prioridade: 'normal',
        nao_lidas: 0,
        created_at: c.created_at,
        updated_at: c.updated_at
      }))

      // Mapear mensagens
      const mensagensMap: Record<string, Mensagem[]> = {}

      conversasData.forEach((c: any) => {
        if (c.mensagens && Array.isArray(c.mensagens)) {
          mensagensMap[c.id] = c.mensagens.map((m: any) => ({
            id: m.id,
            conversa_id: m.conversa_id,
            tipo: m.remetente === 'usuario' ? 'entrada' : 'saida',
            conteudo: m.conteudo,
            enviado_por_ia: m.remetente === 'assistente',
            lida: m.lida || false,
            created_at: m.enviada_em || m.created_at
          }))
        }
      })

      console.log('✅ Conversas formatadas:', conversasFormatadas.length)
      console.log('✅ Mensagens mapeadas:', Object.keys(mensagensMap).length, 'conversas')
      Object.entries(mensagensMap).forEach(([id, msgs]) => {
        console.log(`  Conversa ${id}: ${msgs.length} mensagens`)
        msgs.forEach(m => console.log(`    - ${m.tipo}: ${m.conteudo.substring(0, 50)}...`))
      })

      setConversas(conversasFormatadas)
      setMensagens(mensagensMap)
      setError(null)
    } catch (err: any) {
      console.error('❌ Erro ao buscar conversas:', err)
      setError(err.message)
    } finally {
      // Só desativa loading se foi carga inicial
      if (isInitialLoad) {
        setLoading(false)
      }
    }
  }

  return { conversas, mensagens, loading, error, refetch: fetchConversas }
}

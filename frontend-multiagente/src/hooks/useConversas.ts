import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import type { Conversa, Mensagem } from '@/types'
import { useAuth } from './useAuth'

export function useConversas() {
  const [conversas, setConversas] = useState<Conversa[]>([])
  const [mensagens, setMensagens] = useState<Record<string, Mensagem[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { usuario } = useAuth()

  useEffect(() => {
    if (usuario) {
      fetchConversas()

      // Subscription para atualizações em tempo real
      const conversasSubscription = supabase
        .channel('conversas-changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'conversas' }, () => {
          fetchConversas()
        })
        .subscribe()

      const mensagensSubscription = supabase
        .channel('mensagens-changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'mensagens' }, () => {
          fetchConversas()
        })
        .subscribe()

      return () => {
        conversasSubscription.unsubscribe()
        mensagensSubscription.unsubscribe()
      }
    }
  }, [usuario])

  async function fetchConversas() {
    try {
      setLoading(true)

      if (!usuario) {
        setConversas([])
        setMensagens({})
        setLoading(false)
        return
      }

      // Construir query baseada no usuário
      let query = supabase.from('conversas').select('*')

      // Filtrar por departamento se não for super_admin
      if (usuario.role !== 'super_admin' && !usuario.pode_ver_todos_departamentos) {
        if (usuario.departamento_slug) {
          query = query.eq('departamento_slug', usuario.departamento_slug)
        }
      }

      // Buscar conversas
      const { data: conversasData, error: conversasError } = await query
        .order('updated_at', { ascending: false })

      if (conversasError) throw conversasError

      // Transformar dados do Supabase para o formato esperado
      const conversasFormatadas: Conversa[] = (conversasData || []).map(c => ({
        id: c.id,
        empresa_id: c.empresa_id,
        lead_id: c.lead_id || c.id,
        lead: {
          id: c.lead_id || c.id,
          empresa_id: c.empresa_id,
          nome: c.nome_lead || 'Cliente',
          telefone: c.phone,
          email: c.email_lead,
          tags: c.tags || []
        },
        departamento_id: c.departamento_slug,
        departamento: c.departamento_slug ? {
          id: c.departamento_slug,
          empresa_id: c.empresa_id,
          nome: c.departamento_nome || c.departamento_slug,
          slug: c.departamento_slug,
          cor_primaria: '#3B82F6',
          icone: 'briefcase',
          ordem: 1,
          ativo: true
        } : undefined,
        status: c.status || 'aberta',
        modo_ia: c.modo_ia || 'ligado',
        prioridade: c.prioridade || 'normal',
        nao_lidas: c.nao_lidas || 0,
        ultima_mensagem: c.ultima_mensagem ? {
          id: 'last',
          conversa_id: c.id,
          tipo: 'entrada',
          conteudo: c.ultima_mensagem,
          enviado_por_ia: false,
          lida: false,
          created_at: c.ultima_mensagem_em || c.updated_at
        } : undefined,
        created_at: c.created_at,
        updated_at: c.updated_at
      }))

      setConversas(conversasFormatadas)

      // Buscar mensagens para cada conversa
      const mensagensMap: Record<string, Mensagem[]> = {}
      
      for (const conversa of conversasFormatadas) {
        const { data: mensagensData } = await supabase
          .from('mensagens')
          .select('*')
          .eq('conversa_id', conversa.id)
          .order('created_at', { ascending: true })

        mensagensMap[conversa.id] = (mensagensData || []).map(m => ({
          id: m.id,
          conversa_id: m.conversa_id,
          tipo: m.tipo,
          conteudo: m.conteudo,
          enviado_por_ia: m.enviado_por_ia || false,
          enviado_por_user_id: m.enviado_por_user_id,
          departamento_origem: m.departamento_origem,
          lida: m.lida || false,
          entregue: m.entregue || false,
          metadata: m.metadata,
          created_at: m.created_at
        }))
      }

      setMensagens(mensagensMap)
      setError(null)
    } catch (err: any) {
      console.error('Erro ao buscar conversas:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return { conversas, mensagens, loading, error, refetch: fetchConversas }
}

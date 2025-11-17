import { X, Mail, Phone, Tag, Calendar, MessageSquare, Clock, CheckCircle2, Flame, Snowflake } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Conversa } from '../types/index'
import { useState, useEffect } from 'react'
import { PipelineStage, type EstagioType } from './PipelineStage'

interface ContactInfoProps {
  conversa?: Conversa
  onClose: () => void
}


export function ContactInfo({ conversa, onClose }: ContactInfoProps) {
  const [resolvendoConversa, setResolvendoConversa] = useState(false)
  const [qualificacao, setQualificacao] = useState<string | null>(conversa?.qualificacao || null)
  const [atualizandoQualificacao, setAtualizandoQualificacao] = useState(false)

  // 🎯 NOVO: State para Pipeline
  const [estagioPipeline, setEstagioPipeline] = useState<EstagioType | null>((conversa as any)?.estagio_pipeline || null)
  const [atualizandoPipeline, setAtualizandoPipeline] = useState(false)

  // 🚨 FIX: Atualizar qualificação quando conversa mudar
  useEffect(() => {
    // Só atualiza se a qualificação local for diferente da que veio do servidor
    // Isso evita resetar enquanto o usuário está qualificando
    if (conversa?.qualificacao !== qualificacao) {
      setQualificacao(conversa?.qualificacao || null)
    }
  }, [conversa?.id, conversa?.qualificacao]) // Monitora mudança de conversa E qualificação

  // 🎯 NOVO: Sincronizar pipeline quando conversa mudar
  useEffect(() => {
    const novoEstagio = (conversa as any)?.estagio_pipeline || null
    if (novoEstagio !== estagioPipeline) {
      setEstagioPipeline(novoEstagio)
    }
  }, [conversa?.id, (conversa as any)?.estagio_pipeline])

  if (!conversa) {
    return null
  }

  const formatDate = (date: string) => {
    const d = new Date(date)
    return d.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleResolverConversa = async () => {
    if (!confirm('Tem certeza que deseja marcar como resolvido e reativar a IA?')) {
      return
    }

    setResolvendoConversa(true)

    try {
      const phone = conversa.lead.telefone.replace(/\D/g, '')

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://clinicacaru.automatexia.com.br'}/api/resolver-conversa/${phone}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: 'current-user-id',
          nota: 'Atendimento concluído via dashboard'
        })
      })

      if (response.ok) {
        alert('✅ Conversa resolvida! A IA voltará a atender automaticamente.')
        window.location.reload()
      } else {
        throw new Error('Erro ao resolver conversa')
      }
    } catch (error) {
      console.error('Erro:', error)
      alert('❌ Erro ao resolver conversa. Tente novamente.')
    } finally {
      setResolvendoConversa(false)
    }
  }

  const handleAtualizarQualificacao = async (novaQualificacao: string | null) => {
    // 🚀 OPTIMISTIC UPDATE: Atualiza imediatamente na UI
    const qualificacaoAnterior = qualificacao
    setQualificacao(novaQualificacao)
    setAtualizandoQualificacao(true)

    try {
      const phone = conversa.lead.telefone.replace(/\D/g, '')

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/conversas/${phone}/qualificacao`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          qualificacao: novaQualificacao
        })
      })

      if (response.ok) {
        // Sucesso - já atualizamos otimisticamente
        console.log(`✅ Lead qualificado como ${novaQualificacao === 'quente' ? 'QUENTE 🔥' : novaQualificacao === 'frio' ? 'FRIO ❄️' : 'SEM QUALIFICAÇÃO'}`)
      } else {
        throw new Error('Erro ao atualizar qualificação')
      }
    } catch (error) {
      // ❌ ROLLBACK: Se der erro, volta para qualificação anterior
      console.error('Erro:', error)
      setQualificacao(qualificacaoAnterior)
      alert('❌ Erro ao atualizar qualificação. Tente novamente.')
    } finally {
      setAtualizandoQualificacao(false)
    }
  }

  // 🎯 NOVO: Função para atualizar estágio do pipeline
  const handleAtualizarPipeline = async (novoEstagio: EstagioType) => {
    // 🚀 OPTIMISTIC UPDATE
    const estagioAnterior = estagioPipeline
    setEstagioPipeline(novoEstagio)
    setAtualizandoPipeline(true)

    try {
      const phone = conversa.lead.telefone.replace(/\D/g, '')

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/conversas/${phone}/pipeline`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          estagio: novoEstagio
        })
      })

      if (response.ok) {
        console.log(`✅ Estágio do pipeline atualizado: ${novoEstagio}`)
      } else {
        throw new Error('Erro ao atualizar pipeline')
      }
    } catch (error) {
      // ❌ ROLLBACK
      console.error('Erro:', error)
      setEstagioPipeline(estagioAnterior)
      alert('❌ Erro ao atualizar estágio. Tente novamente.')
    } finally {
      setAtualizandoPipeline(false)
    }
  }


  return (
    <div className="flex flex-col h-full bg-white border-l">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="font-semibold">Informações do Contato</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          {/* Avatar and Name */}
          <div className="flex flex-col items-center text-center">
            <Avatar className="h-20 w-20 mb-3">
              <AvatarImage src={conversa.lead.avatar_url} />
              <AvatarFallback className="bg-blue-500 text-white text-2xl">
                {conversa.lead.nome.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <h3 className="font-bold text-lg">{conversa.lead.nome}</h3>
            <p className="text-sm text-gray-500">Lead</p>
          </div>

          {/* Contact Details */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm text-gray-700">Detalhes de Contato</h4>

            <div className="space-y-2">
              <div className="flex items-center gap-3 text-sm">
                <Phone className="h-4 w-4 text-gray-500" />
                <span>{conversa.lead.telefone}</span>
              </div>

              {conversa.lead.email && (
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="h-4 w-4 text-gray-500" />
                  <span>{conversa.lead.email}</span>
                </div>
              )}
            </div>
          </div>

          {/* Tags */}
          {conversa.tags && conversa.tags.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-gray-500" />
                <h4 className="font-semibold text-sm text-gray-700">Tags</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {conversa.tags.map((tag) => {
                  // Definir cor baseado no tipo de tag
                  let colorClass = 'bg-gray-100 text-gray-700 border-gray-300'

                  // Tags por médica
                  if (tag.includes('dra_')) {
                    colorClass = 'bg-purple-100 text-purple-700 border-purple-300'
                  }
                  // Tags por categoria
                  else if (['estetica', 'dermatologia', 'capilar', 'gineco_estetica'].includes(tag)) {
                    colorClass = 'bg-blue-100 text-blue-700 border-blue-300'
                  }
                  // Tags de status
                  else if (['novo_paciente', 'retorno'].includes(tag)) {
                    colorClass = 'bg-green-100 text-green-700 border-green-300'
                  }
                  // Tags de procedimentos específicos
                  else if (['botox', 'preenchimento', 'harmonizacao'].includes(tag.toLowerCase())) {
                    colorClass = 'bg-pink-100 text-pink-700 border-pink-300'
                  }
                  else if (['limpeza', 'peeling', 'laser'].includes(tag.toLowerCase())) {
                    colorClass = 'bg-amber-100 text-amber-700 border-amber-300'
                  }
                  else if (['melasma', 'acne', 'manchas'].includes(tag.toLowerCase())) {
                    colorClass = 'bg-orange-100 text-orange-700 border-orange-300'
                  }
                  // Tags de teste (vip, urgente, etc)
                  else if (tag === 'vip') {
                    colorClass = 'bg-yellow-100 text-yellow-800 border-yellow-400'
                  }
                  else if (tag === 'urgente') {
                    colorClass = 'bg-red-100 text-red-700 border-red-300'
                  }
                  else if (tag === 'interessado') {
                    colorClass = 'bg-teal-100 text-teal-700 border-teal-300'
                  }

                  return (
                    <Badge
                      key={tag}
                      variant="outline"
                      className={`${colorClass} font-medium border`}
                    >
                      {tag.replace(/_/g, ' ')}
                    </Badge>
                  )
                })}
              </div>
            </div>
          )}

          {/* Conversation Info */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm text-gray-700">Informações da Conversa</h4>

            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <MessageSquare className="h-4 w-4 text-gray-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Status</p>
                  <Badge variant="outline" className="mt-1 capitalize">
                    {conversa.status}
                  </Badge>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Calendar className="h-4 w-4 text-gray-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Criada em</p>
                  <p className="text-sm mt-1">{formatDate(conversa.created_at)}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Clock className="h-4 w-4 text-gray-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Última atualização</p>
                  <p className="text-sm mt-1">{formatDate(conversa.updated_at)}</p>
                </div>
              </div>
            </div>
          </div>


          {/* AI Status */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm text-gray-700">Status da IA</h4>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm">Modo Atual</span>
                <Badge
                  className={
                    conversa.modo_ia === 'ativo' || conversa.modo_ia === 'ligado'
                      ? 'bg-green-500'
                      : conversa.modo_ia === 'pausado'
                      ? 'bg-yellow-500'
                      : 'bg-gray-500'
                  }
                >
                  {conversa.modo_ia}
                </Badge>
              </div>
            </div>
          </div>

          {/* Priority */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm text-gray-700">Prioridade</h4>
            <Badge
              variant={
                conversa.prioridade === 'urgente' || conversa.prioridade === 'alta'
                  ? 'destructive'
                  : 'outline'
              }
              className="capitalize"
            >
              {conversa.prioridade}
            </Badge>
          </div>

          {/* Estágio do Pipeline */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm text-gray-700">Estágio do Pipeline</h4>
            <PipelineStage
              estagio={estagioPipeline}
              onChangeEstagio={handleAtualizarPipeline}
              loading={atualizandoPipeline}
            />
          </div>

          {/* Qualificação do Lead */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm text-gray-700">Qualificação do Lead</h4>

            {/* Botões de Qualificação */}
            <div className="grid grid-cols-3 gap-2">
              {/* Botão Frio */}
              <Button
                onClick={() => handleAtualizarQualificacao('frio')}
                disabled={atualizandoQualificacao}
                variant="outline"
                style={qualificacao === 'frio' ? {
                  background: 'linear-gradient(to bottom right, rgb(59 130 246), rgb(37 99 235))',
                  color: 'white',
                  borderColor: 'rgb(37 99 235)',
                  boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.3)',
                  transform: 'scale(1.05)'
                } : {}}
                className="flex flex-col items-center gap-1.5 h-auto py-4 transition-all hover:scale-105"
                onMouseEnter={(e) => {
                  if (qualificacao !== 'frio') {
                    e.currentTarget.style.backgroundColor = 'rgb(239 246 255)'
                    e.currentTarget.style.borderColor = 'rgb(147 197 253)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (qualificacao !== 'frio') {
                    e.currentTarget.style.backgroundColor = ''
                    e.currentTarget.style.borderColor = ''
                  }
                }}
              >
                <Snowflake className={`h-6 w-6 ${qualificacao === 'frio' ? 'animate-pulse' : ''}`} />
                <span className="text-xs font-semibold">Frio</span>
              </Button>

              {/* Botão Quente */}
              <Button
                onClick={() => handleAtualizarQualificacao('quente')}
                disabled={atualizandoQualificacao}
                variant="outline"
                style={qualificacao === 'quente' ? {
                  background: 'linear-gradient(to bottom right, rgb(239 68 68), rgb(220 38 38))',
                  color: 'white',
                  borderColor: 'rgb(220 38 38)',
                  boxShadow: '0 10px 15px -3px rgba(239, 68, 68, 0.3)',
                  transform: 'scale(1.05)'
                } : {}}
                className="flex flex-col items-center gap-1.5 h-auto py-4 transition-all hover:scale-105"
                onMouseEnter={(e) => {
                  if (qualificacao !== 'quente') {
                    e.currentTarget.style.backgroundColor = 'rgb(254 242 242)'
                    e.currentTarget.style.borderColor = 'rgb(252 165 165)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (qualificacao !== 'quente') {
                    e.currentTarget.style.backgroundColor = ''
                    e.currentTarget.style.borderColor = ''
                  }
                }}
              >
                <Flame className={`h-6 w-6 ${qualificacao === 'quente' ? 'animate-pulse' : ''}`} />
                <span className="text-xs font-semibold">Quente</span>
              </Button>

              {/* Botão Limpar */}
              <Button
                onClick={() => handleAtualizarQualificacao(null)}
                disabled={atualizandoQualificacao}
                variant="outline"
                className="flex flex-col items-center gap-1.5 h-auto py-4 hover:bg-gray-100 hover:border-gray-400 transition-all hover:scale-105"
              >
                <X className="h-6 w-6" />
                <span className="text-xs font-semibold">Limpar</span>
              </Button>
            </div>

            {/* Status atual - Card bonito */}
            {qualificacao && (
              <div
                className="p-3 rounded-lg border-2 text-center"
                style={qualificacao === 'quente' ? {
                  background: 'linear-gradient(to bottom right, rgb(254 242 242), rgb(254 226 226))',
                  borderColor: 'rgb(252 165 165)'
                } : {
                  background: 'linear-gradient(to bottom right, rgb(239 246 255), rgb(219 234 254))',
                  borderColor: 'rgb(147 197 253)'
                }}
              >
                <div className="flex items-center justify-center gap-2">
                  {qualificacao === 'quente' ? (
                    <Flame className="h-5 w-5 text-red-600 animate-pulse" />
                  ) : (
                    <Snowflake className="h-5 w-5 text-blue-600" />
                  )}
                  <span className={`text-sm font-bold ${
                    qualificacao === 'quente' ? 'text-red-700' : 'text-blue-700'
                  }`}>
                    LEAD {qualificacao.toUpperCase()}
                  </span>
                  {qualificacao === 'quente' ? (
                    <Flame className="h-5 w-5 text-red-600 animate-pulse" />
                  ) : (
                    <Snowflake className="h-5 w-5 text-blue-600" />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </ScrollArea>

      {/* Actions */}
      <div className="p-4 border-t space-y-2">
        {/* Botão Reativar IA - Aparece quando IA está pausada ou desligada */}
        {(conversa.modo_ia === 'desligado' || conversa.modo_ia === 'pausado') && (
          <Button
            onClick={handleResolverConversa}
            disabled={resolvendoConversa}
            className="w-full bg-green-600 hover:bg-green-700 text-white"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            {resolvendoConversa ? 'Reativando...' : 'Encerrar e Reativar IA'}
          </Button>
        )}

      </div>
    </div>
  )
}

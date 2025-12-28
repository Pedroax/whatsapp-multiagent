import { X, Mail, Phone, Tag, Calendar, MessageSquare, Clock, CheckCircle2, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Conversa } from '../types/index'
import { useState } from 'react'

interface ContactInfoProps {
  conversa?: Conversa
  onClose: () => void
}

const DEPARTAMENTOS = [
  { value: 'vendas', label: '💼 Vendas' },
  { value: 'financeiro', label: '💰 Financeiro' },
  { value: 'assistencia-tecnica', label: '🔧 Assistência Técnica' },
  { value: 'suporte-ti', label: '💻 Suporte TI' },
]

export function ContactInfo({ conversa, onClose }: ContactInfoProps) {
  const [resolvendoConversa, setResolvendoConversa] = useState(false)
  const [transferindo, setTransferindo] = useState(false)

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

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://lcbaterias.automatexia.com.br'}/api/resolver-conversa/${phone}`, {
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

  const handleTransferirConversa = async () => {
    // Exibir opções de departamento
    const departamentoTexto = DEPARTAMENTOS.map((d, i) => `${i + 1}. ${d.label}`).join('\n')
    const escolha = prompt(`Selecione o departamento:\n\n${departamentoTexto}\n\nDigite o número:`)

    if (!escolha) return

    const index = parseInt(escolha) - 1
    if (index < 0 || index >= DEPARTAMENTOS.length) {
      alert('Departamento inválido')
      return
    }

    const departamentoSelecionado = DEPARTAMENTOS[index].value
    const motivo = prompt('Motivo da transferência (opcional):') || 'Transferência manual via dashboard'

    setTransferindo(true)

    try {
      const phone = conversa.lead.telefone.replace(/\D/g, '')

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://lcbaterias.automatexia.com.br'}/api/transferir-conversa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          phone,
          departamento: departamentoSelecionado,
          motivo,
          user_id: 'current-user-id'
        })
      })

      if (response.ok) {
        alert('✅ Conversa transferida com sucesso! A IA foi pausada.')
        window.location.reload()
      } else {
        throw new Error('Erro ao transferir conversa')
      }
    } catch (error) {
      console.error('Erro:', error)
      alert('❌ Erro ao transferir conversa. Tente novamente.')
    } finally {
      setTransferindo(false)
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
            <div className="h-20 w-20 mb-3 shrink-0 rounded-full bg-blue-500 text-white flex items-center justify-center font-semibold text-2xl">
              {conversa.lead.nome.charAt(0).toUpperCase()}
            </div>
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
          {conversa.lead.tags && conversa.lead.tags.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-gray-500" />
                <h4 className="font-semibold text-sm text-gray-700">Tags</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {conversa.lead.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
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

          {/* Department Info */}
          {conversa.departamento && (
            <div className="space-y-3">
              <h4 className="font-semibold text-sm text-gray-700">Departamento</h4>
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: conversa.departamento.cor_primaria }}
                />
                <span className="text-sm font-medium">{conversa.departamento.nome}</span>
              </div>

              {conversa.usuario_atribuido && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 mb-2">Atendente Responsável</p>
                  <div className="flex items-center gap-2">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-green-500 text-white text-xs">
                        {conversa.usuario_atribuido.nome_completo.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="text-sm font-medium">{conversa.usuario_atribuido.nome_completo}</p>
                      <p className="text-xs text-gray-500">{conversa.usuario_atribuido.email}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

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
        </div>
      </ScrollArea>

      {/* Actions */}
      <div className="p-4 border-t space-y-2">
        {/* Botão Resolvido - Só aparece quando conversa está transferida (modo_ia = desligado) */}
        {conversa.modo_ia === 'desligado' && (
          <Button
            onClick={handleResolverConversa}
            disabled={resolvendoConversa}
            className="w-full bg-green-600 hover:bg-green-700 text-white"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" />
            {resolvendoConversa ? 'Resolvendo...' : 'Encerrar e Reativar IA'}
          </Button>
        )}

        <Button
          variant="outline"
          className="w-full"
          onClick={handleTransferirConversa}
          disabled={transferindo}
        >
          <Users className="h-4 w-4 mr-2" />
          {transferindo ? 'Transferindo...' : 'Transferir Conversa'}
        </Button>
      </div>
    </div>
  )
}

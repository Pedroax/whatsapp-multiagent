import { useState } from 'react'
import { Send, Paperclip, Mic, MoreVertical, Bot, User, CheckCircle2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Conversa, Mensagem } from '../types/index'
import { cn } from '@/lib/utils'

interface MessageAreaProps {
  conversa?: Conversa
  mensagens: Mensagem[]
  onEnviarMensagem: (conteudo: string) => void
}

export function MessageArea({ conversa, mensagens, onEnviarMensagem }: MessageAreaProps) {
  const [novaMensagem, setNovaMensagem] = useState('')
  const [resolvendoConversa, setResolvendoConversa] = useState(false)

  const handleEnviar = () => {
    if (novaMensagem.trim()) {
      onEnviarMensagem(novaMensagem)
      setNovaMensagem('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleEnviar()
    }
  }

  const handleResolverConversa = async () => {
    if (!conversa) return

    if (!confirm('Tem certeza que deseja marcar como resolvido e reativar a IA?')) {
      return
    }

    setResolvendoConversa(true)

    try {
      const phone = conversa.lead.telefone.replace(/\D/g, '') // Remove formatação

      const response = await fetch(`http://localhost:8000/api/resolver-conversa/${phone}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: 'user123', // TODO: Pegar do contexto/auth
          nota: 'Atendimento concluído via dashboard'
        })
      })

      if (response.ok) {
        alert('✅ Conversa resolvida! A IA foi reativada e atenderá o próximo contato do cliente.')
        // Recarregar página ou atualizar estado
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

  if (!conversa) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <p className="text-gray-500">Selecione uma conversa para começar</p>
        </div>
      </div>
    )
  }

  const formatMessageTime = (date: string) => {
    const d = new Date(date)
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={conversa.lead.avatar_url} />
              <AvatarFallback className="bg-blue-500 text-white">
                {conversa.lead.nome.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>

            <div>
              <h2 className="font-bold text-lg">{conversa.lead.nome}</h2>
              <p className="text-sm text-gray-500">{conversa.lead.telefone}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {conversa.modo_ia === 'ativo' && (
              <Badge className="bg-green-500">
                <Bot className="h-3 w-3 mr-1" />
                IA Ativa
              </Badge>
            )}
            {conversa.modo_ia === 'pausado' && (
              <Badge className="bg-yellow-500">
                <User className="h-3 w-3 mr-1" />
                Modo Humano
              </Badge>
            )}
            {conversa.modo_ia === 'desligado' && (
              <>
                <Badge variant="secondary">IA Desligada</Badge>

                {/* Botão RESOLVIDO - Só aparece quando IA está desligada (transferido para humano) */}
                <Button
                  onClick={handleResolverConversa}
                  disabled={resolvendoConversa}
                  className="bg-green-600 hover:bg-green-700 text-white"
                  size="sm"
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  {resolvendoConversa ? 'Resolvendo...' : 'Resolvido'}
                </Button>
              </>
            )}

            <Button variant="ghost" size="icon">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Departamento Header */}
        {conversa.departamento && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: conversa.departamento.cor_primaria }}
              />
              <span className="font-bold">{conversa.departamento.nome}</span>
              {conversa.usuario_atribuido && (
                <span className="text-sm text-gray-500">
                  • Atendido por {conversa.usuario_atribuido.nome_completo}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {mensagens.map((mensagem) => (
            <div
              key={mensagem.id}
              className={cn(
                "flex gap-2",
                mensagem.tipo === 'saida' ? 'justify-end' : 'justify-start'
              )}
            >
              {mensagem.tipo === 'entrada' && (
                <Avatar className="h-8 w-8">
                  <AvatarImage src={conversa.lead.avatar_url} />
                  <AvatarFallback className="bg-gray-400 text-white text-xs">
                    {conversa.lead.nome.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              )}

              <div
                className={cn(
                  "max-w-[70%] rounded-lg px-4 py-2",
                  mensagem.tipo === 'saida'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white border'
                )}
              >
                {/* Label do departamento (se mensagem foi enviada por humano após transferência) */}
                {mensagem.departamento_origem && mensagem.tipo === 'saida' && !mensagem.enviado_por_ia && (
                  <div className="flex items-center gap-1 text-xs font-semibold opacity-90 mb-2 pb-2 border-b border-white/20">
                    {mensagem.departamento_origem === 'vendas' && '💼 Vendas:'}
                    {mensagem.departamento_origem === 'assistencia-tecnica' && '🔧 Assistência Técnica:'}
                    {mensagem.departamento_origem === 'financeiro' && '💰 Financeiro:'}
                    {mensagem.departamento_origem === 'suporte-ti' && '💻 Suporte TI:'}
                    {!['vendas', 'assistencia-tecnica', 'financeiro', 'suporte-ti'].includes(mensagem.departamento_origem) && '👤 Atendente:'}
                  </div>
                )}

                {mensagem.enviado_por_ia && mensagem.tipo === 'saida' && (
                  <div className="flex items-center gap-1 text-xs opacity-75 mb-1">
                    <Bot className="h-3 w-3" />
                    <span>Alice (IA)</span>
                  </div>
                )}

                <p className="text-sm whitespace-pre-wrap">{mensagem.conteudo}</p>

                <div className={cn(
                  "text-xs mt-1",
                  mensagem.tipo === 'saida' ? 'text-blue-100' : 'text-gray-500'
                )}>
                  {formatMessageTime(mensagem.created_at)}
                </div>
              </div>

              {mensagem.tipo === 'saida' && mensagem.enviado_por_usuario && (
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-green-500 text-white text-xs">
                    {mensagem.enviado_por_usuario.nome_completo.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="bg-white border-t p-4">
        <div className="flex items-end gap-2">
          <Button variant="outline" size="icon">
            <Paperclip className="h-5 w-5" />
          </Button>

          <div className="flex-1">
            <Input
              placeholder="Digite sua mensagem..."
              value={novaMensagem}
              onChange={(e) => setNovaMensagem(e.target.value)}
              onKeyPress={handleKeyPress}
              className="resize-none"
            />
          </div>

          <Button variant="outline" size="icon">
            <Mic className="h-5 w-5" />
          </Button>

          <Button onClick={handleEnviar}>
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  )
}

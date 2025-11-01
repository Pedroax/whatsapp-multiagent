import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Mic, MoreVertical, Bot, User, CheckCircle2, X, FileText, Image as ImageIcon, Video, Music, File, Download, Play, Pause, Loader2 } from 'lucide-react'
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
  onEnviarMensagem: (conteudo: string, arquivo?: File) => void
  onMensagensAtualizadas?: () => void
}

export function MessageArea({ conversa, mensagens, onEnviarMensagem, onMensagensAtualizadas }: MessageAreaProps) {
  const [novaMensagem, setNovaMensagem] = useState('')
  const [resolvendoConversa, setResolvendoConversa] = useState(false)
  const [arquivoSelecionado, setArquivoSelecionado] = useState<File | null>(null)
  const [gravandoAudio, setGravandoAudio] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [aliceDigitando, setAliceDigitando] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const lastMessageCountRef = useRef(mensagens.length)
  const userIsScrollingRef = useRef(false)
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  console.log('💬 MessageArea - Conversa:', conversa?.lead.nome)
  console.log('💬 MessageArea - Total de mensagens:', mensagens.length)
  console.log('💬 MessageArea - Mensagens:', mensagens)

  // Detectar quando usuário faz scroll manual
  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    const scrollViewport = container.closest('[data-radix-scroll-area-viewport]') as HTMLElement
    if (!scrollViewport) return

    const handleScroll = () => {
      // Marca que usuário está fazendo scroll
      userIsScrollingRef.current = true

      // Limpa timeout anterior
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current)
      }

      // Após 3 segundos sem scroll, libera auto-scroll novamente
      scrollTimeoutRef.current = setTimeout(() => {
        userIsScrollingRef.current = false
      }, 3000)
    }

    scrollViewport.addEventListener('scroll', handleScroll)
    return () => {
      scrollViewport.removeEventListener('scroll', handleScroll)
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current)
      }
    }
  }, [])

  // Auto-scroll para o final APENAS se usuário NÃO estiver fazendo scroll manual
  useEffect(() => {
    // Se usuário está fazendo scroll manual, não interfere
    if (userIsScrollingRef.current) {
      return
    }

    const container = scrollContainerRef.current
    if (!container) return

    // Encontra o elemento scrollável (viewport do ScrollArea)
    const scrollViewport = container.closest('[data-radix-scroll-area-viewport]') as HTMLElement
    if (!scrollViewport) {
      // Fallback: sempre faz scroll se não encontrar viewport
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      return
    }

    // Verifica se usuário está perto do final (tolerância de 200px)
    const isNearBottom =
      scrollViewport.scrollHeight - scrollViewport.scrollTop - scrollViewport.clientHeight < 200

    // Só faz scroll automático se usuário estiver perto do final
    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [mensagens])

  // Polling para buscar novas mensagens a cada 2 segundos
  useEffect(() => {
    if (!conversa || !onMensagensAtualizadas) return

    const interval = setInterval(() => {
      onMensagensAtualizadas()
    }, 2000) // Atualiza a cada 2 segundos

    return () => clearInterval(interval)
  }, [conversa, onMensagensAtualizadas])

  // Detectar quando Alice está "digitando" (nova mensagem chegou)
  useEffect(() => {
    if (mensagens.length > lastMessageCountRef.current) {
      const ultimaMensagem = mensagens[mensagens.length - 1]
      if (ultimaMensagem.tipo === 'saida' && ultimaMensagem.enviado_por_ia) {
        setAliceDigitando(false)
      }
    }
    lastMessageCountRef.current = mensagens.length
  }, [mensagens])

  const handleEnviar = () => {
    // Mostra indicador de "digitando..." quando usuário envia mensagem
    if (conversa?.modo_ia === 'ativo' || conversa?.modo_ia === 'ligado') {
      setAliceDigitando(true)
      // Remove indicador após 30 segundos (timeout de segurança)
      setTimeout(() => setAliceDigitando(false), 30000)
    }
    if (audioBlob) {
      // Enviar áudio
      const audioFile = new File([audioBlob], 'audio.ogg', { type: 'audio/ogg' })
      onEnviarMensagem('Áudio', audioFile)
      setAudioBlob(null)
    } else if (arquivoSelecionado) {
      // Enviar arquivo
      const mensagem = novaMensagem.trim() || getFileDescription(arquivoSelecionado)
      onEnviarMensagem(mensagem, arquivoSelecionado)
      setArquivoSelecionado(null)
      setNovaMensagem('')
    } else if (novaMensagem.trim()) {
      // Enviar texto
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

  const getFileDescription = (file: File): string => {
    if (file.type.startsWith('image/')) return 'Imagem'
    if (file.type.startsWith('video/')) return 'Vídeo'
    if (file.type.startsWith('audio/')) return 'Áudio'
    if (file.type.includes('pdf')) return 'Documento PDF'
    return 'Arquivo'
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setArquivoSelecionado(file)
    }
  }

  const handleRemoveFile = () => {
    setArquivoSelecionado(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/ogg; codecs=opus' })
        setAudioBlob(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setGravandoAudio(true)
    } catch (error) {
      console.error('Erro ao acessar microfone:', error)
      alert('Não foi possível acessar o microfone. Verifique as permissões.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
      setGravandoAudio(false)
    }
  }

  const cancelAudio = () => {
    if (gravandoAudio) {
      stopRecording()
    }
    setAudioBlob(null)
    audioChunksRef.current = []
  }

  const getFileIcon = (tipo?: string) => {
    switch (tipo) {
      case 'imagem': return <ImageIcon className="h-4 w-4" />
      case 'video': return <Video className="h-4 w-4" />
      case 'audio': return <Music className="h-4 w-4" />
      case 'documento': return <FileText className="h-4 w-4" />
      default: return <File className="h-4 w-4" />
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

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://lcbaterias.automatexia.com.br'}/api/resolver-conversa/${phone}`, {
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
        <div className="space-y-4" ref={scrollContainerRef}>
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

                {/* Exibição de mídia */}
                {mensagem.tipo_midia === 'imagem' && mensagem.midia_url && (
                  <div className="mb-2">
                    <img
                      src={mensagem.midia_url}
                      alt="Imagem"
                      className="max-w-full rounded-lg cursor-pointer hover:opacity-90"
                      onClick={() => window.open(mensagem.midia_url, '_blank')}
                    />
                  </div>
                )}

                {mensagem.tipo_midia === 'audio' && mensagem.midia_url && (
                  <div className="mb-2">
                    <audio controls className="w-full max-w-sm">
                      <source src={mensagem.midia_url} type="audio/ogg" />
                      <source src={mensagem.midia_url} type="audio/mpeg" />
                      Seu navegador não suporta áudio.
                    </audio>
                  </div>
                )}

                {mensagem.tipo_midia === 'video' && mensagem.midia_url && (
                  <div className="mb-2">
                    <video controls className="max-w-full rounded-lg">
                      <source src={mensagem.midia_url} type="video/mp4" />
                      Seu navegador não suporta vídeo.
                    </video>
                  </div>
                )}

                {mensagem.tipo_midia === 'documento' && mensagem.midia_url && (
                  <div className="mb-2">
                    <a
                      href={mensagem.midia_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(
                        "flex items-center gap-2 p-2 rounded",
                        mensagem.tipo === 'saida'
                          ? 'bg-blue-600 hover:bg-blue-700'
                          : 'bg-gray-100 hover:bg-gray-200'
                      )}
                    >
                      {getFileIcon('documento')}
                      <span className="text-sm">Baixar documento</span>
                      <Download className="h-4 w-4 ml-auto" />
                    </a>
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

          {/* Indicador "Alice digitando..." */}
          {aliceDigitando && (
            <div className="flex gap-2 justify-start">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-blue-500 text-white text-xs">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="bg-white border rounded-lg px-4 py-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                <span className="text-sm text-gray-600">Alice está digitando...</span>
              </div>
            </div>
          )}

          {/* Referência para auto-scroll */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="bg-white border-t p-4">
        {/* Preview de arquivo selecionado */}
        {arquivoSelecionado && (
          <div className="mb-3 p-3 bg-gray-50 rounded-lg border flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getFileIcon(getFileDescription(arquivoSelecionado).toLowerCase())}
              <div>
                <p className="text-sm font-medium">{arquivoSelecionado.name}</p>
                <p className="text-xs text-gray-500">
                  {(arquivoSelecionado.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRemoveFile}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Preview de áudio gravado */}
        {audioBlob && (
          <div className="mb-3 p-3 bg-gray-50 rounded-lg border">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Music className="h-4 w-4" />
                <span className="text-sm font-medium">Áudio gravado</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={cancelAudio}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <audio controls className="w-full">
              <source src={URL.createObjectURL(audioBlob)} type="audio/ogg" />
            </audio>
          </div>
        )}

        {/* Indicador de gravação */}
        {gravandoAudio && (
          <div className="mb-3 p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium text-red-700">Gravando áudio...</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={stopRecording}
                className="text-red-700 hover:text-red-800"
              >
                Parar
              </Button>
            </div>
          </div>
        )}

        <div className="flex items-end gap-2">
          {/* Botão de anexo */}
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx"
          />
          <Button
            variant="outline"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={gravandoAudio || audioBlob !== null}
          >
            <Paperclip className="h-5 w-5" />
          </Button>

          <div className="flex-1">
            <Input
              placeholder="Digite sua mensagem..."
              value={novaMensagem}
              onChange={(e) => setNovaMensagem(e.target.value)}
              onKeyPress={handleKeyPress}
              className="resize-none"
              disabled={gravandoAudio}
            />
          </div>

          {/* Botão de gravação de áudio */}
          <Button
            variant="outline"
            size="icon"
            onClick={gravandoAudio ? stopRecording : startRecording}
            disabled={arquivoSelecionado !== null || audioBlob !== null}
            className={gravandoAudio ? 'bg-red-100 border-red-300' : ''}
          >
            <Mic className={cn("h-5 w-5", gravandoAudio && "text-red-600")} />
          </Button>

          {/* Botão de enviar */}
          <Button
            onClick={handleEnviar}
            disabled={!novaMensagem.trim() && !arquivoSelecionado && !audioBlob}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  )
}

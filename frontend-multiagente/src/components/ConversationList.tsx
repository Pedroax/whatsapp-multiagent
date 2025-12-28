import { useState, useMemo, useEffect } from 'react'
import { Search, Filter, X, Calendar, Tag, AlertCircle } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Conversa } from '../types/index'
import { cn } from '@/lib/utils'

interface ConversationListProps {
  conversas: Conversa[]
  conversaSelecionada?: string
  onSelectConversa: (conversaId: string) => void
}

const STORAGE_KEY = 'alice_conversation_filters'

export function ConversationList({ conversas, conversaSelecionada, onSelectConversa }: ConversationListProps) {
  const [buscaTexto, setBuscaTexto] = useState('')
  const [mostrarFiltros, setMostrarFiltros] = useState(false)

  // Carregar filtros do localStorage
  const [filtros, setFiltros] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : {
        status: '',
        prioridade: '',
        departamento: '',
        dataInicio: '',
        dataFim: ''
      }
    } catch {
      return {
        status: '',
        prioridade: '',
        departamento: '',
        dataInicio: '',
        dataFim: ''
      }
    }
  })

  // Salvar filtros no localStorage quando mudarem
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtros))
  }, [filtros])

  // Aplicar filtros e busca
  const conversasFiltradas = useMemo(() => {
    return conversas.filter(conversa => {
      // Filtro de busca por texto
      if (buscaTexto) {
        const textoBusca = buscaTexto.toLowerCase()
        const matchNome = conversa.lead.nome.toLowerCase().includes(textoBusca)
        const matchMensagem = conversa.ultima_mensagem?.conteudo.toLowerCase().includes(textoBusca)
        if (!matchNome && !matchMensagem) return false
      }

      // Filtro de status
      if (filtros.status && conversa.status !== filtros.status) return false

      // Filtro de prioridade
      if (filtros.prioridade && conversa.prioridade !== filtros.prioridade) return false

      // Filtro de departamento
      if (filtros.departamento && conversa.departamento?.slug !== filtros.departamento) return false

      // Filtro de data
      if (filtros.dataInicio || filtros.dataFim) {
        const dataConversa = conversa.ultima_mensagem ? new Date(conversa.ultima_mensagem.created_at) : new Date(conversa.created_at)

        if (filtros.dataInicio) {
          const inicio = new Date(filtros.dataInicio)
          if (dataConversa < inicio) return false
        }

        if (filtros.dataFim) {
          const fim = new Date(filtros.dataFim)
          fim.setHours(23, 59, 59)
          if (dataConversa > fim) return false
        }
      }

      return true
    })
  }, [conversas, buscaTexto, filtros])

  const limparFiltros = () => {
    setFiltros({
      status: '',
      prioridade: '',
      departamento: '',
      dataInicio: '',
      dataFim: ''
    })
  }

  const filtrosAtivos = Object.values(filtros).filter(v => v !== '').length
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'nova': return 'bg-blue-500'
      case 'aberta': return 'bg-green-500'
      case 'pendente': return 'bg-yellow-500'
      case 'resolvida': return 'bg-purple-500'
      case 'fechada': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const formatTime = (date: string) => {
    const d = new Date(date)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))

    if (hours < 1) return 'Agora'
    if (hours < 24) return `${hours}h`
    return `${Math.floor(hours / 24)}d`
  }

  return (
    <div className="flex flex-col h-full bg-white border-r">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-lg font-semibold">Conversas</h2>
          <Badge variant="secondary">{conversasFiltradas.length}</Badge>
          {filtrosAtivos > 0 && (
            <Badge className="bg-blue-600">{filtrosAtivos} filtros</Badge>
          )}
        </div>

        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Buscar conversa..."
              className="pl-9"
              value={buscaTexto}
              onChange={(e) => setBuscaTexto(e.target.value)}
            />
          </div>
          <Button
            variant={mostrarFiltros ? "default" : "outline"}
            size="icon"
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
          >
            <Filter className="h-4 w-4" />
          </Button>
        </div>

        {/* Painel de Filtros */}
        {mostrarFiltros && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Filtros Avançados</span>
              {filtrosAtivos > 0 && (
                <Button variant="ghost" size="sm" onClick={limparFiltros} className="h-7 text-xs">
                  Limpar tudo
                </Button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              {/* Status */}
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Status</label>
                <select
                  value={filtros.status}
                  onChange={(e) => setFiltros({ ...filtros, status: e.target.value })}
                  className="w-full h-8 px-2 text-sm border rounded-md bg-white"
                >
                  <option value="">Todos</option>
                  <option value="nova">Nova</option>
                  <option value="aberta">Aberta</option>
                  <option value="pendente">Pendente</option>
                  <option value="resolvida">Resolvida</option>
                  <option value="fechada">Fechada</option>
                </select>
              </div>

              {/* Prioridade */}
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Prioridade</label>
                <select
                  value={filtros.prioridade}
                  onChange={(e) => setFiltros({ ...filtros, prioridade: e.target.value })}
                  className="w-full h-8 px-2 text-sm border rounded-md bg-white"
                >
                  <option value="">Todas</option>
                  <option value="baixa">Baixa</option>
                  <option value="media">Média</option>
                  <option value="alta">Alta</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>

              {/* Departamento */}
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Departamento</label>
                <select
                  value={filtros.departamento}
                  onChange={(e) => setFiltros({ ...filtros, departamento: e.target.value })}
                  className="w-full h-8 px-2 text-sm border rounded-md bg-white"
                >
                  <option value="">Todos</option>
                  <option value="vendas">Vendas</option>
                  <option value="assistencia-tecnica">Assistência Técnica</option>
                  <option value="financeiro">Financeiro</option>
                  <option value="suporte-ti">Suporte TI</option>
                </select>
              </div>

              {/* Data Início */}
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Data Início</label>
                <input
                  type="date"
                  value={filtros.dataInicio}
                  onChange={(e) => setFiltros({ ...filtros, dataInicio: e.target.value })}
                  className="w-full h-8 px-2 text-sm border rounded-md bg-white"
                />
              </div>

              {/* Data Fim */}
              <div className="col-span-2">
                <label className="text-xs text-gray-600 mb-1 block">Data Fim</label>
                <input
                  type="date"
                  value={filtros.dataFim}
                  onChange={(e) => setFiltros({ ...filtros, dataFim: e.target.value })}
                  className="w-full h-8 px-2 text-sm border rounded-md bg-white"
                />
              </div>
            </div>

            {/* Filtros Ativos */}
            {filtrosAtivos > 0 && (
              <div className="flex flex-wrap gap-1 pt-2 border-t">
                {filtros.status && (
                  <Badge variant="secondary" className="text-xs">
                    {filtros.status}
                    <X className="h-3 w-3 ml-1 cursor-pointer" onClick={() => setFiltros({ ...filtros, status: '' })} />
                  </Badge>
                )}
                {filtros.prioridade && (
                  <Badge variant="secondary" className="text-xs">
                    {filtros.prioridade}
                    <X className="h-3 w-3 ml-1 cursor-pointer" onClick={() => setFiltros({ ...filtros, prioridade: '' })} />
                  </Badge>
                )}
                {filtros.departamento && (
                  <Badge variant="secondary" className="text-xs">
                    {filtros.departamento}
                    <X className="h-3 w-3 ml-1 cursor-pointer" onClick={() => setFiltros({ ...filtros, departamento: '' })} />
                  </Badge>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Conversation List */}
      <ScrollArea className="flex-1">
        {conversasFiltradas.map((conversa) => (
          <div
            key={conversa.id}
            onClick={() => onSelectConversa(conversa.id)}
            className={cn(
              "p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors",
              conversaSelecionada === conversa.id && "bg-blue-50 border-l-4 border-l-blue-500"
            )}
          >
            <div className="flex items-start gap-3">
              <Avatar className="h-10 w-10">
                <AvatarImage src={conversa.lead.avatar_url} />
                <AvatarFallback className="bg-gradient-to-br from-orange-500 to-red-600 text-white">
                  {conversa.lead.nome.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-semibold text-sm truncate">
                    {conversa.lead.nome}
                  </h3>
                  <span className="text-xs text-gray-500">
                    {conversa.ultima_mensagem && formatTime(conversa.ultima_mensagem.created_at)}
                  </span>
                </div>

                {conversa.ultima_mensagem && (
                  <p className="text-sm text-gray-600 truncate">
                    {conversa.ultima_mensagem.conteudo}
                  </p>
                )}

                <div className="flex items-center gap-2 mt-2">
                  <div className={cn("w-2 h-2 rounded-full", getStatusColor(conversa.status))} />
                  <span className="text-xs text-gray-500 capitalize">{conversa.status}</span>

                  {conversa.nao_lidas > 0 && (
                    <Badge variant="default" className="ml-auto">
                      {conversa.nao_lidas}
                    </Badge>
                  )}

                  {conversa.departamento && (
                    <Badge variant="outline" className="text-xs">
                      {conversa.departamento.nome}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </ScrollArea>
    </div>
  )
}

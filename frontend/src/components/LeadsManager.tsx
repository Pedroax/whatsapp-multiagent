import { useState, useEffect } from 'react'
import { X, Download, Search, Filter, Calendar, Snowflake, Flame, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { PipelineStage, PipelineBadge, type EstagioType } from './PipelineStage'

interface Lead {
  id: string
  nome: string
  telefone: string
  tags: string[]
  qualificacao: 'frio' | 'quente' | null
  estagio_pipeline?: EstagioType
  status: string
  prioridade: string
  primeira_mensagem: string
  ultima_interacao: string
  total_mensagens: number
}

interface LeadsManagerProps {
  onClose: () => void
}

export function LeadsManager({ onClose }: LeadsManagerProps) {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(false)
  const [filtros, setFiltros] = useState({
    periodo: 'mes',
    qualificacao: '',
    pipeline: '',
    tag: '',
    busca: ''
  })

  const [mostrarFiltros, setMostrarFiltros] = useState(false)

  // Buscar leads
  const buscarLeads = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('periodo', filtros.periodo)
      if (filtros.qualificacao) params.append('qualificacao', filtros.qualificacao)
      if (filtros.pipeline) params.append('pipeline', filtros.pipeline)
      if (filtros.tag) params.append('tag', filtros.tag)

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/leads?${params}`)
      const data = await response.json()

      if (data.success) {
        setLeads(data.leads)
      }
    } catch (error) {
      console.error('Erro ao buscar leads:', error)
      alert('Erro ao buscar leads')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    buscarLeads()
  }, [filtros.periodo, filtros.qualificacao, filtros.pipeline, filtros.tag])

  // Filtro de busca local
  const leadsFiltrados = leads.filter(lead => {
    if (!filtros.busca) return true
    const busca = filtros.busca.toLowerCase()
    return (
      lead.nome.toLowerCase().includes(busca) ||
      lead.telefone.includes(busca) ||
      lead.tags.some(t => t.toLowerCase().includes(busca))
    )
  })

  // Atualizar pipeline de um lead
  const atualizarPipeline = async (telefone: string, novoEstagio: EstagioType) => {
    try {
      const phone = telefone.replace(/\D/g, '')
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/conversas/${phone}/pipeline`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estagio: novoEstagio })
      })

      if (response.ok) {
        // Atualizar lead localmente
        setLeads(leads.map(lead =>
          lead.telefone === telefone
            ? { ...lead, estagio_pipeline: novoEstagio }
            : lead
        ))
      } else {
        alert('Erro ao atualizar estágio do pipeline')
      }
    } catch (error) {
      console.error('Erro ao atualizar pipeline:', error)
      alert('Erro ao atualizar estágio do pipeline')
    }
  }

  // Exportar para CSV
  const exportarCSV = () => {
    const csv = [
      ['Nome', 'Telefone', 'Qualificação', 'Tags', 'Status', 'Prioridade', 'Primeira Mensagem', 'Última Interação'],
      ...leadsFiltrados.map(lead => [
        lead.nome,
        lead.telefone,
        lead.qualificacao || 'Sem qualificação',
        lead.tags.join(', '),
        lead.status,
        lead.prioridade,
        new Date(lead.primeira_mensagem).toLocaleString('pt-BR'),
        new Date(lead.ultima_interacao).toLocaleString('pt-BR')
      ])
    ].map(row => row.join(';')).join('\n')

    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `leads_${filtros.periodo}_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  // Estatísticas
  const stats = {
    total: leadsFiltrados.length,
    quentes: leadsFiltrados.filter(l => l.qualificacao === 'quente').length,
    frios: leadsFiltrados.filter(l => l.qualificacao === 'frio').length,
    semQualificacao: leadsFiltrados.filter(l => !l.qualificacao).length
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Users className="h-6 w-6 text-blue-600" />
              Gerenciamento de Leads
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Lista completa de leads que interagiram com a IA
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="p-6 border-b bg-gray-50">
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-600">Total de Leads</div>
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <Flame className="h-4 w-4 text-red-500" />
                Leads Quentes
              </div>
              <div className="text-2xl font-bold text-red-600">{stats.quentes}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <Snowflake className="h-4 w-4 text-blue-500" />
                Leads Frios
              </div>
              <div className="text-2xl font-bold text-blue-600">{stats.frios}</div>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-600">Sem Qualificação</div>
              <div className="text-2xl font-bold text-gray-600">{stats.semQualificacao}</div>
            </div>
          </div>
        </div>

        {/* Filtros */}
        <div className="p-6 border-b">
          <div className="flex gap-3 flex-wrap items-center">
            {/* Busca */}
            <div className="flex-1 min-w-[250px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Buscar por nome, telefone ou tag..."
                  className="pl-9"
                  value={filtros.busca}
                  onChange={(e) => setFiltros({ ...filtros, busca: e.target.value })}
                />
              </div>
            </div>

            {/* Período */}
            <select
              value={filtros.periodo}
              onChange={(e) => setFiltros({ ...filtros, periodo: e.target.value })}
              className="px-3 py-2 border rounded-md bg-white text-sm"
            >
              <option value="hoje">Hoje</option>
              <option value="7dias">Últimos 7 dias</option>
              <option value="mes">Este mês</option>
              <option value="tudo">Todos os períodos</option>
            </select>

            {/* Qualificação */}
            <select
              value={filtros.qualificacao}
              onChange={(e) => setFiltros({ ...filtros, qualificacao: e.target.value })}
              className="px-3 py-2 border rounded-md bg-white text-sm"
            >
              <option value="">Todas qualificações</option>
              <option value="quente">🔥 Quentes</option>
              <option value="frio">❄️ Frios</option>
              <option value="sem_qualificacao">Sem qualificação</option>
            </select>

            {/* Pipeline */}
            <select
              value={filtros.pipeline}
              onChange={(e) => setFiltros({ ...filtros, pipeline: e.target.value })}
              className="px-3 py-2 border rounded-md bg-white text-sm"
            >
              <option value="">Todos os estágios</option>
              <option value="novo">🔵 Novo</option>
              <option value="em_contato">💬 Em Contato</option>
              <option value="aguardando_resposta">⏳ Aguardando Resposta</option>
              <option value="interessado">⭐ Interessado</option>
              <option value="agendamento_solicitado">📅 Agendamento Solicitado</option>
              <option value="agendado">✅ Agendado</option>
              <option value="compareceu">🎉 Compareceu</option>
              <option value="nao_compareceu">❌ Não Compareceu</option>
              <option value="convertido">💚 Convertido</option>
              <option value="perdido">🚫 Perdido</option>
            </select>

            {/* Tag */}
            <Input
              placeholder="Filtrar por tag..."
              className="w-48"
              value={filtros.tag}
              onChange={(e) => setFiltros({ ...filtros, tag: e.target.value })}
            />

            {/* Botão Exportar */}
            <Button onClick={exportarCSV} className="bg-green-600 hover:bg-green-700">
              <Download className="h-4 w-4 mr-2" />
              Exportar CSV
            </Button>

            {/* Botão Atualizar */}
            <Button onClick={buscarLeads} variant="outline">
              Atualizar
            </Button>
          </div>
        </div>

        {/* Lista de Leads */}
        <ScrollArea className="flex-1 p-6">
          {loading ? (
            <div className="text-center py-12 text-gray-500">
              Carregando leads...
            </div>
          ) : leadsFiltrados.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              Nenhum lead encontrado com os filtros aplicados
            </div>
          ) : (
            <div className="space-y-3">
              {leadsFiltrados.map(lead => (
                <div
                  key={lead.id}
                  className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <h3 className="font-semibold text-lg">{lead.nome}</h3>
                        {lead.qualificacao === 'quente' && (
                          <Badge className="bg-red-100 text-red-700 border-red-300">
                            <Flame className="h-3 w-3 mr-1" />
                            Quente
                          </Badge>
                        )}
                        {lead.qualificacao === 'frio' && (
                          <Badge className="bg-blue-100 text-blue-700 border-blue-300">
                            <Snowflake className="h-3 w-3 mr-1" />
                            Frio
                          </Badge>
                        )}
                      </div>

                      <div className="text-sm text-gray-600 mb-3">
                        <span className="font-mono">{lead.telefone}</span>
                      </div>

                      {/* Tags */}
                      {lead.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-3">
                          {lead.tags.map((tag, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {tag.replace(/_/g, ' ')}
                            </Badge>
                          ))}
                        </div>
                      )}

                      <div className="flex gap-4 text-xs text-gray-500">
                        <span>
                          <Calendar className="h-3 w-3 inline mr-1" />
                          Primeiro contato: {new Date(lead.primeira_mensagem).toLocaleDateString('pt-BR')}
                        </span>
                        <span>
                          Última interação: {new Date(lead.ultima_interacao).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      {/* Pipeline Stage - Editável e Compacto */}
                      <PipelineStage
                        estagio={lead.estagio_pipeline || 'novo'}
                        onChangeEstagio={(novoEstagio) => atualizarPipeline(lead.telefone, novoEstagio)}
                        loading={false}
                        compact={true}
                      />

                      {/* Status badge */}
                      <Badge variant="secondary" className="text-xs">
                        {lead.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}

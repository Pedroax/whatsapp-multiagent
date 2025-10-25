import { useState, useEffect } from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  MessageSquare,
  ShoppingCart,
  CheckCircle,
  XCircle,
  Clock,
  Phone,
  Bot,
  Calendar,
  Download,
  Filter,
  AlertCircle,
  FileText,
  Table
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import * as XLSX from 'xlsx'

const API_BASE_URL = '${import.meta.env.VITE_API_URL || "http://localhost:8000"}'

interface MetricCardProps {
  title: string
  value: string | number
  change: number
  changeLabel: string
  icon: React.ElementType
  color: string
  prefix?: string
  suffix?: string
}

function MetricCard({ title, value, change, changeLabel, icon: Icon, color, prefix = '', suffix = '' }: MetricCardProps) {
  const isPositive = change >= 0

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <Badge variant={isPositive ? 'default' : 'destructive'} className="flex items-center gap-1">
          {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          {Math.abs(change)}%
        </Badge>
      </div>
      <div>
        <p className="text-sm text-gray-600 mb-1">{title}</p>
        <p className="text-3xl font-bold text-gray-900">
          {prefix}{typeof value === 'number' ? value.toLocaleString('pt-BR') : value}{suffix}
        </p>
        <p className="text-xs text-gray-500 mt-1">{changeLabel}</p>
      </div>
    </div>
  )
}

interface ConversionFunnelProps {
  data: {
    stage: string
    count: number
    percentage: number
  }[]
}

function ConversionFunnel({ data }: ConversionFunnelProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-6">Funil de Conversão</h3>
      <div className="space-y-4">
        {data.map((item, index) => (
          <div key={index}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">{item.stage}</span>
              <span className="text-sm font-bold text-gray-900">{item.count} ({item.percentage}%)</span>
            </div>
            <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={cn(
                  "absolute inset-y-0 left-0 rounded-full transition-all",
                  index === 0 ? "bg-blue-500" :
                  index === 1 ? "bg-blue-400" :
                  index === 2 ? "bg-green-500" :
                  "bg-green-600"
                )}
                style={{ width: `${item.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

interface TopProductProps {
  products: {
    codigo?: string
    nome: string
    quantidade: number
    receita: number
  }[]
}

function TopProducts({ products }: TopProductProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Produtos Mais Vendidos pela IA</h3>
      <div className="space-y-3">
        {products.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="font-medium">Nenhum produto vendido ainda</p>
            <p className="text-sm">Aguarde as primeiras vendas da IA</p>
          </div>
        ) : (
          products.map((product, index) => (
            <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white",
                  index === 0 ? "bg-yellow-500" :
                  index === 1 ? "bg-gray-400" :
                  index === 2 ? "bg-orange-600" :
                  "bg-gray-300"
                )}>
                  {index + 1}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{product.nome}</p>
                  <p className="text-sm text-gray-500">{product.quantidade} unidades</p>
                </div>
              </div>
              <p className="font-bold text-green-600">R$ {product.receita.toLocaleString('pt-BR')}</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

interface PendingLeadProps {
  leads: {
    nome: string
    telefone: string
    ultima_mensagem: string
    valor_estimado: number
    timestamp: string
  }[]
  onCall: (phone: string) => void
}

// Helper function to format timestamp
function formatTimeAgo(timestamp: string): string {
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 60) return `${diffMins}min atrás`
  if (diffHours < 24) return `${diffHours}h atrás`
  return `${diffDays}d atrás`
}

function PendingLeads({ leads, onCall }: PendingLeadProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">Leads Pendentes (Requer Ação)</h3>
        <Badge variant="destructive">{leads.length}</Badge>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Clientes que iniciaram mas não completaram o pedido. Ligue para recuperar a venda!
      </p>
      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        {leads.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
            <p className="font-medium">Nenhum lead pendente!</p>
            <p className="text-sm">Todos os clientes foram atendidos</p>
          </div>
        ) : (
          leads.map((lead, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">{lead.nome}</p>
                  <p className="text-sm text-gray-500">{lead.telefone}</p>
                </div>
                <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatTimeAgo(lead.timestamp)}
                </Badge>
              </div>
              <p className="text-sm text-gray-600 mb-3 italic">"{lead.ultima_mensagem}"</p>
              <div className="flex items-center justify-between">
                <p className="font-bold text-green-600">Valor estimado: R$ {lead.valor_estimado.toLocaleString('pt-BR')}</p>
                <Button
                  size="sm"
                  onClick={() => onCall(lead.telefone)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Phone className="h-4 w-4 mr-1" />
                  Ligar Agora
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export function AnalyticsDashboard() {
  const [period, setPeriod] = useState<'today' | 'week' | 'month' | 'custom'>('week')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Estado para dados da API
  const [metrics, setMetrics] = useState<any>(null)
  const [funnelData, setFunnelData] = useState<any[]>([])
  const [topProducts, setTopProducts] = useState<any[]>([])
  const [pendingLeads, setPendingLeads] = useState<any[]>([])

  // Fetch data from API
  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true)
      setError(null)

      try {
        const [metricsRes, funnelRes, productsRes, leadsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/analytics/metrics`),
          fetch(`${API_BASE_URL}/api/analytics/funil`),
          fetch(`${API_BASE_URL}/api/analytics/top-products?limit=5`),
          fetch(`${API_BASE_URL}/api/analytics/pending-leads`)
        ])

        // Check if all requests succeeded
        if (!metricsRes.ok || !funnelRes.ok || !productsRes.ok || !leadsRes.ok) {
          throw new Error('Erro ao buscar dados da API')
        }

        const [metricsData, funnelData, productsData, leadsData] = await Promise.all([
          metricsRes.json(),
          funnelRes.json(),
          productsRes.json(),
          leadsRes.json()
        ])

        // Update state with API data
        if (metricsData.success) {
          setMetrics(metricsData.metrics)
        }

        if (funnelData.success) {
          setFunnelData(funnelData.funnel || [])
        }

        if (productsData.success) {
          setTopProducts(productsData.products || [])
        }

        if (leadsData.success) {
          setPendingLeads(leadsData.leads || [])
        }

      } catch (err: any) {
        console.error('Error fetching analytics:', err)
        const errorMsg = err.message || 'Erro desconhecido'
        setError(`Erro ao carregar dados do analytics: ${errorMsg}. Verifique se o backend está rodando em ${API_BASE_URL}`)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [period]) // Refetch when period changes

  const handleCall = (phone: string) => {
    console.log('Ligando para:', phone)
    alert(`Iniciando ligação para ${phone}`)
  }

  const exportToPDF = () => {
    const doc = new jsPDF()

    // Título
    doc.setFontSize(20)
    doc.text('Relatório de Analytics - Alice IA', 14, 20)

    doc.setFontSize(10)
    doc.text(`Período: ${period === 'today' ? 'Hoje' : period === 'week' ? '7 dias' : period === 'month' ? '30 dias' : 'Customizado'}`, 14, 28)
    doc.text(`Gerado em: ${new Date().toLocaleDateString('pt-BR')} às ${new Date().toLocaleTimeString('pt-BR')}`, 14, 33)

    // Métricas principais
    doc.setFontSize(14)
    doc.text('Métricas Principais', 14, 45)

    autoTable(doc, {
      startY: 50,
      head: [['Métrica', 'Valor', 'Variação']],
      body: [
        ['Receita Total', `R$ ${metrics?.total_revenue?.toLocaleString('pt-BR')}`, `${metrics?.revenue_change >= 0 ? '+' : ''}${metrics?.revenue_change}%`],
        ['Pedidos Fechados', metrics?.total_orders, `${metrics?.orders_change >= 0 ? '+' : ''}${metrics?.orders_change}%`],
        ['Conversas Totais', metrics?.total_conversations, `${metrics?.conversations_change >= 0 ? '+' : ''}${metrics?.conversations_change}%`],
        ['Taxa de Conversão', `${metrics?.conversion_rate?.toFixed(2)}%`, `${metrics?.conversion_growth >= 0 ? '+' : ''}${metrics?.conversion_growth}%`],
        ['Ticket Médio', `R$ ${metrics?.avg_ticket?.toLocaleString('pt-BR')}`, `${metrics?.ticket_growth >= 0 ? '+' : ''}${metrics?.ticket_growth}%`],
        ['Leads Pendentes', metrics?.pending_leads, `${metrics?.leads_growth >= 0 ? '+' : ''}${metrics?.leads_growth}%`],
      ]
    })

    // Funil de Conversão
    const finalY = (doc as any).lastAutoTable.finalY || 100
    doc.setFontSize(14)
    doc.text('Funil de Conversão', 14, finalY + 15)

    autoTable(doc, {
      startY: finalY + 20,
      head: [['Etapa', 'Quantidade', 'Percentual']],
      body: funnelData.map(item => [item.stage, item.count, `${item.percentage}%`])
    })

    // Top Produtos
    const finalY2 = (doc as any).lastAutoTable.finalY || 150
    doc.setFontSize(14)
    doc.text('Top 5 Produtos Mais Vendidos', 14, finalY2 + 15)

    autoTable(doc, {
      startY: finalY2 + 20,
      head: [['Produto', 'Quantidade', 'Receita']],
      body: topProducts.map(p => [p.nome, p.quantidade, `R$ ${p.receita.toLocaleString('pt-BR')}`])
    })

    // Leads Pendentes
    if (pendingLeads.length > 0) {
      const finalY3 = (doc as any).lastAutoTable.finalY || 200
      doc.addPage()
      doc.setFontSize(14)
      doc.text('Leads Pendentes', 14, 20)

      autoTable(doc, {
        startY: 25,
        head: [['Nome', 'Telefone', 'Valor Estimado', 'Última Mensagem']],
        body: pendingLeads.map(l => [
          l.nome,
          l.telefone,
          `R$ ${l.valor_estimado.toLocaleString('pt-BR')}`,
          l.ultima_mensagem.substring(0, 50) + '...'
        ])
      })
    }

    doc.save(`analytics-alice-${new Date().toISOString().split('T')[0]}.pdf`)
  }

  const exportToExcel = () => {
    // Métricas
    const metricsData = [
      ['RELATÓRIO DE ANALYTICS - ALICE IA'],
      [`Período: ${period === 'today' ? 'Hoje' : period === 'week' ? '7 dias' : period === 'month' ? '30 dias' : 'Customizado'}`],
      [`Gerado em: ${new Date().toLocaleString('pt-BR')}`],
      [],
      ['MÉTRICAS PRINCIPAIS'],
      ['Métrica', 'Valor', 'Variação'],
      ['Receita Total', `R$ ${metrics?.total_revenue?.toLocaleString('pt-BR')}`, `${metrics?.revenue_change}%`],
      ['Pedidos Fechados', metrics?.total_orders, `${metrics?.orders_change}%`],
      ['Conversas Totais', metrics?.total_conversations, `${metrics?.conversations_change}%`],
      ['Taxa de Conversão', `${metrics?.conversion_rate?.toFixed(2)}%`, `${metrics?.conversion_growth}%`],
      ['Ticket Médio', `R$ ${metrics?.avg_ticket?.toLocaleString('pt-BR')}`, `${metrics?.ticket_growth}%`],
      ['Leads Pendentes', metrics?.pending_leads, `${metrics?.leads_growth}%`],
      [],
      ['FUNIL DE CONVERSÃO'],
      ['Etapa', 'Quantidade', 'Percentual'],
      ...funnelData.map(item => [item.stage, item.count, `${item.percentage}%`]),
      [],
      ['TOP 5 PRODUTOS'],
      ['Produto', 'Quantidade', 'Receita'],
      ...topProducts.map(p => [p.nome, p.quantidade, `R$ ${p.receita.toLocaleString('pt-BR')}`]),
    ]

    if (pendingLeads.length > 0) {
      metricsData.push(
        [],
        ['LEADS PENDENTES'],
        ['Nome', 'Telefone', 'Valor Estimado', 'Última Mensagem'],
        ...pendingLeads.map(l => [
          l.nome,
          l.telefone,
          `R$ ${l.valor_estimado.toLocaleString('pt-BR')}`,
          l.ultima_mensagem
        ])
      )
    }

    const ws = XLSX.utils.aoa_to_sheet(metricsData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Analytics')

    XLSX.writeFile(wb, `analytics-alice-${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  const [showExportMenu, setShowExportMenu] = useState(false)

  // Loading state
  if (loading) {
    return (
      <div className="h-full overflow-y-auto bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Bot className="h-12 w-12 text-blue-600 animate-pulse mx-auto mb-4" />
          <p className="text-lg font-semibold text-gray-700">Carregando analytics...</p>
          <p className="text-sm text-gray-500">Aguarde enquanto buscamos os dados</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="h-full overflow-y-auto bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <p className="text-lg font-semibold text-gray-900 mb-2">Erro ao carregar dados</p>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()} className="bg-blue-600 hover:bg-blue-700">
            Tentar Novamente
          </Button>
        </div>
      </div>
    )
  }

  // No data state
  if (!metrics) {
    return (
      <div className="h-full overflow-y-auto bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
          <p className="text-lg font-semibold text-gray-700">Nenhum dado disponível</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Bot className="h-7 w-7 text-blue-600" />
              Analytics da IA
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Dashboard exclusivo para Super Administrador
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Period Filter */}
            <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-1">
              <Button
                size="sm"
                variant={period === 'today' ? 'default' : 'ghost'}
                onClick={() => setPeriod('today')}
                className="text-xs"
              >
                Hoje
              </Button>
              <Button
                size="sm"
                variant={period === 'week' ? 'default' : 'ghost'}
                onClick={() => setPeriod('week')}
                className="text-xs"
              >
                7 dias
              </Button>
              <Button
                size="sm"
                variant={period === 'month' ? 'default' : 'ghost'}
                onClick={() => setPeriod('month')}
                className="text-xs"
              >
                30 dias
              </Button>
              <Button
                size="sm"
                variant={period === 'custom' ? 'default' : 'ghost'}
                onClick={() => setPeriod('custom')}
                className="text-xs"
              >
                <Calendar className="h-3 w-3 mr-1" />
                Customizar
              </Button>
            </div>

            {/* Export Dropdown */}
            <div className="relative">
              <Button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Download className="h-4 w-4 mr-2" />
                Exportar
              </Button>

              {showExportMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                  <button
                    onClick={() => {
                      exportToPDF()
                      setShowExportMenu(false)
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 rounded-t-lg transition-colors"
                  >
                    <FileText className="h-4 w-4 text-red-600" />
                    <div>
                      <p className="font-medium text-sm text-gray-900">Exportar PDF</p>
                      <p className="text-xs text-gray-500">Relatório em PDF</p>
                    </div>
                  </button>
                  <button
                    onClick={() => {
                      exportToExcel()
                      setShowExportMenu(false)
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 rounded-b-lg transition-colors border-t"
                  >
                    <Table className="h-4 w-4 text-green-600" />
                    <div>
                      <p className="font-medium text-sm text-gray-900">Exportar Excel</p>
                      <p className="text-xs text-gray-500">Planilha editável</p>
                    </div>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Receita Total (IA)"
            value={metrics.total_revenue}
            change={metrics.revenue_growth}
            changeLabel="vs período anterior"
            icon={DollarSign}
            color="bg-green-500"
            prefix="R$ "
          />
          <MetricCard
            title="Pedidos Fechados"
            value={metrics.total_orders}
            change={metrics.orders_growth}
            changeLabel="vs período anterior"
            icon={ShoppingCart}
            color="bg-blue-500"
          />
          <MetricCard
            title="Conversas Totais"
            value={metrics.total_conversations}
            change={metrics.conversations_growth}
            changeLabel="vs período anterior"
            icon={MessageSquare}
            color="bg-purple-500"
          />
          <MetricCard
            title="Taxa de Conversão"
            value={metrics.conversion_rate}
            change={metrics.conversion_growth}
            changeLabel="vs período anterior"
            icon={TrendingUp}
            color="bg-orange-500"
            suffix="%"
          />
        </div>

        {/* Secondary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Ticket Médio"
            value={metrics.avg_ticket}
            change={metrics.ticket_growth}
            changeLabel="vs período anterior"
            icon={DollarSign}
            color="bg-teal-500"
            prefix="R$ "
          />
          <MetricCard
            title="Negócios Fechados"
            value={metrics.closed_deals}
            change={metrics.deals_growth}
            changeLabel="vs período anterior"
            icon={CheckCircle}
            color="bg-green-600"
          />
          <MetricCard
            title="Leads Pendentes"
            value={metrics.pending_leads}
            change={metrics.leads_growth}
            changeLabel="vs período anterior"
            icon={XCircle}
            color="bg-red-500"
          />
          <MetricCard
            title="Tempo Resposta (IA)"
            value={metrics.avg_response_time}
            change={metrics.response_growth}
            changeLabel="vs período anterior"
            icon={Clock}
            color="bg-indigo-500"
            suffix="s"
          />
        </div>

        {/* Charts and Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ConversionFunnel data={funnelData} />
          <TopProducts products={topProducts} />
        </div>

        {/* Pending Leads - Full Width */}
        <PendingLeads leads={pendingLeads} onCall={handleCall} />

        {/* Performance Insights */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Insights de Performance</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                <p className="font-semibold text-blue-900">Alta Performance</p>
              </div>
              <p className="text-sm text-blue-700">
                A IA está convertendo <strong>23% a mais</strong> que a média humana nas últimas 2 semanas
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-5 w-5 text-yellow-600" />
                <p className="font-semibold text-yellow-900">Horário de Pico</p>
              </div>
              <p className="text-sm text-yellow-700">
                Maior volume de conversas entre <strong>14h-18h</strong>. Considere reforço humano neste período.
              </p>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-5 w-5 text-green-600" />
                <p className="font-semibold text-green-900">Recuperação de Leads</p>
              </div>
              <p className="text-sm text-green-700">
                <strong>{pendingLeads.length} leads</strong> aguardam contato humano. Potencial de R$ {pendingLeads.reduce((sum, lead) => sum + lead.valor_estimado, 0).toLocaleString('pt-BR')} em vendas.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

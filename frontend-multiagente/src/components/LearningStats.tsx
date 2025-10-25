import { useState, useEffect } from 'react'
import { Brain, TrendingUp, CheckCircle, XCircle, Activity } from 'lucide-react'

interface LearningStatsProps {
  empresaId: string
}

interface Estatisticas {
  total_decisoes: number
  total_corretas: number
  total_incorretas: number
  taxa_acerto: number
  versao_pesos: number
  ultimas_100: {
    total: number
    com_feedback: number
    corretas: number
    taxa_recente: number
  }
}

export function LearningStats({ empresaId }: LearningStatsProps) {
  const [stats, setStats] = useState<Estatisticas | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 30000) // Atualizar a cada 30s
    return () => clearInterval(interval)
  }, [empresaId])

  const fetchStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "${API_URL}"}/api/learning/estatisticas/${empresaId}`)
      const data = await response.json()
      if (data.success) {
        setStats(data.estatisticas)
      }
    } catch (error) {
      console.error('Erro ao buscar estatísticas:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6">
        <p className="text-gray-500">Nenhuma estatística disponível ainda.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-purple-500" />
          <h2 className="text-xl font-bold text-gray-800">Sistema de Aprendizado</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Activity className="w-4 h-4" />
          <span>v{stats.versao_pesos}</span>
        </div>
      </div>

      {/* Métricas Principais */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Total de Decisões */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">Total de Decisões</span>
            <TrendingUp className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-blue-900">{stats.total_decisoes}</p>
        </div>

        {/* Decisões Corretas */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-green-900">Corretas</span>
            <CheckCircle className="w-4 h-4 text-green-600" />
          </div>
          <p className="text-3xl font-bold text-green-900">{stats.total_corretas}</p>
        </div>

        {/* Decisões Incorretas */}
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-red-900">Incorretas</span>
            <XCircle className="w-4 h-4 text-red-600" />
          </div>
          <p className="text-3xl font-bold text-red-900">{stats.total_incorretas}</p>
        </div>
      </div>

      {/* Taxa de Acerto Geral */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Taxa de Acerto Geral</h3>
          <span className={`text-3xl font-bold ${
            stats.taxa_acerto >= 0.9 ? 'text-green-600' :
            stats.taxa_acerto >= 0.7 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {(stats.taxa_acerto * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all ${
              stats.taxa_acerto >= 0.9 ? 'bg-green-500' :
              stats.taxa_acerto >= 0.7 ? 'bg-yellow-500' :
              'bg-red-500'
            }`}
            style={{ width: `${stats.taxa_acerto * 100}%` }}
          />
        </div>
      </div>

      {/* Últimas 100 Decisões */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Últimas 100 Decisões</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">Com Feedback</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.ultimas_100.com_feedback} <span className="text-sm font-normal text-gray-500">/ {stats.ultimas_100.total}</span>
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Taxa Recente</p>
            <p className={`text-2xl font-bold ${
              stats.ultimas_100.taxa_recente >= 0.9 ? 'text-green-600' :
              stats.ultimas_100.taxa_recente >= 0.7 ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {(stats.ultimas_100.taxa_recente * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </div>

      {/* Explicação */}
      <div className="mt-4 bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-purple-900 mb-2">🧠 Como funciona:</h4>
        <p className="text-sm text-purple-800">
          O sistema aprende com suas aprovações e recusas. Quando você recusa uma mensagem ou a edita,
          a IA ajusta automaticamente seus pesos para melhorar nas próximas decisões.
          Quanto maior a taxa de acerto, menos mensagens precisarão de aprovação manual!
        </p>
      </div>
    </div>
  )
}

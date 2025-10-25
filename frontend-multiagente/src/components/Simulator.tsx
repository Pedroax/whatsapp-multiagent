import { useState, useEffect } from 'react'
import { Send, Sparkles, TrendingUp, AlertCircle, CheckCircle, XCircle } from 'lucide-react'

interface SimulatorProps {
  empresaId: string
}

interface SimulationResult {
  success: boolean
  resposta_ia: string
  confianca: number
  intencao: string
  decisao: string
  metadados?: any
  error?: string
}

export function Simulator({ empresaId }: SimulatorProps) {
  const [mensagem, setMensagem] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState<SimulationResult | null>(null)
  const [contexto, setContexto] = useState({
    cnpj: '',
    state: 'inicio',
    produtos_interesse: []
  })

  const executarSimulacao = async () => {
    if (!mensagem.trim()) return

    setLoading(true)
    try {
      const response = await fetch('${import.meta.env.VITE_API_URL || "${API_URL}"}/api/learning/simulador/rapido', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mensagem: mensagem.trim(),
          contexto: {
            ...contexto,
            state: contexto.state || 'inicio'
          }
        })
      })

      const data = await response.json()
      setResultado(data)
    } catch (error) {
      console.error('Erro na simulação:', error)
      setResultado({
        success: false,
        error: 'Erro ao executar simulação',
        resposta_ia: '',
        confianca: 0,
        intencao: '',
        decisao: ''
      })
    } finally {
      setLoading(false)
    }
  }

  const getDecisaoColor = (decisao: string) => {
    switch (decisao) {
      case 'enviar_direto':
        return 'text-green-600 bg-green-50'
      case 'aguardar_aprovacao':
        return 'text-yellow-600 bg-yellow-50'
      case 'bloquear':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getDecisaoIcon = (decisao: string) => {
    switch (decisao) {
      case 'enviar_direto':
        return <CheckCircle className="w-5 h-5" />
      case 'aguardar_aprovacao':
        return <AlertCircle className="w-5 h-5" />
      case 'bloquear':
        return <XCircle className="w-5 h-5" />
      default:
        return null
    }
  }

  const getDecisaoTexto = (decisao: string) => {
    switch (decisao) {
      case 'enviar_direto':
        return 'ENVIAR DIRETO'
      case 'aguardar_aprovacao':
        return 'AGUARDAR APROVAÇÃO'
      case 'bloquear':
        return 'BLOQUEADO'
      default:
        return decisao
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <div className="flex items-center gap-3 mb-6">
        <Sparkles className="w-6 h-6 text-purple-500" />
        <h2 className="text-xl font-bold text-gray-800">Simulador de Conversa</h2>
      </div>

      <div className="space-y-6">
        {/* Contexto Opcional */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Contexto (Opcional)
          </label>
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="CNPJ (opcional)"
              value={contexto.cnpj}
              onChange={(e) => setContexto({ ...contexto, cnpj: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <select
              value={contexto.state}
              onChange={(e) => setContexto({ ...contexto, state: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="inicio">Início</option>
              <option value="aguardando_produto">Aguardando Produto</option>
              <option value="aguardando_modelo">Aguardando Modelo</option>
              <option value="finalizado">Finalizado</option>
            </select>
          </div>
        </div>

        {/* Mensagem do Cliente */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Mensagem do Cliente
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Digite uma mensagem para simular..."
              value={mensagem}
              onChange={(e) => setMensagem(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && executarSimulacao()}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              onClick={executarSimulacao}
              disabled={loading || !mensagem.trim()}
              className="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Simulando...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Simular
                </>
              )}
            </button>
          </div>
        </div>

        {/* Resultado */}
        {resultado && (
          <div className="space-y-4 border-t border-gray-200 pt-6">
            {resultado.success ? (
              <>
                {/* Resposta da IA */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-blue-900 mb-2 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    Resposta da IA:
                  </h3>
                  <p className="text-gray-800">{resultado.resposta_ia}</p>
                </div>

                {/* Métricas */}
                <div className="grid grid-cols-3 gap-4">
                  {/* Confiança */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-600">Confiança</span>
                      <TrendingUp className="w-4 h-4 text-blue-500" />
                    </div>
                    <div className="flex items-end gap-2">
                      <span className="text-3xl font-bold text-gray-900">
                        {(resultado.confianca * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          resultado.confianca >= 0.9
                            ? 'bg-green-500'
                            : resultado.confianca >= 0.7
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${resultado.confianca * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Intenção */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-600">Intenção</span>
                      <AlertCircle className="w-4 h-4 text-purple-500" />
                    </div>
                    <p className="text-lg font-semibold text-gray-900 capitalize">
                      {resultado.intencao.replace('_', ' ')}
                    </p>
                  </div>

                  {/* Decisão */}
                  <div className={`border rounded-lg p-4 ${getDecisaoColor(resultado.decisao)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Decisão</span>
                      {getDecisaoIcon(resultado.decisao)}
                    </div>
                    <p className="text-lg font-bold">
                      {getDecisaoTexto(resultado.decisao)}
                    </p>
                  </div>
                </div>

                {/* Explicação */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">O que isso significa?</h4>
                  <p className="text-sm text-gray-600">
                    {resultado.decisao === 'enviar_direto' && (
                      <>
                        ✅ <strong>Alta confiança!</strong> A IA enviaria essa mensagem automaticamente para o cliente.
                      </>
                    )}
                    {resultado.decisao === 'aguardar_aprovacao' && (
                      <>
                        ⚠️ <strong>Aprovação necessária.</strong> Essa mensagem apareceria na fila para você aprovar antes de enviar.
                      </>
                    )}
                    {resultado.decisao === 'bloquear' && (
                      <>
                        🔴 <strong>IA desligada.</strong> Nenhuma mensagem seria enviada (modo OFF).
                      </>
                    )}
                  </p>
                </div>
              </>
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">
                  ❌ Erro: {resultado.error || 'Erro desconhecido'}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Dicas */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-purple-900 mb-2">💡 Dicas:</h4>
          <ul className="text-sm text-purple-800 space-y-1">
            <li>• Teste diferentes mensagens para ver como a IA responde</li>
            <li>• Simule cenários com/sem CNPJ para ver a diferença na confiança</li>
            <li>• Use antes de ativar a IA para garantir respostas adequadas</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

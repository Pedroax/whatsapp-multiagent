import { useState } from 'react'
import {
  User,
  MessageCircle,
  Clock,
  Heart,
  CalendarCheck,
  CalendarClock,
  CheckCircle2,
  XCircle,
  Trophy,
  AlertCircle,
  ChevronDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

// Definição dos estágios do pipeline
export const ESTAGIOS_PIPELINE = {
  novo: {
    label: 'Novo',
    icon: User,
    color: 'bg-blue-500',
    colorLight: 'bg-blue-100',
    colorText: 'text-blue-700',
    colorBorder: 'border-blue-300',
    description: 'Lead novo que acabou de chegar'
  },
  em_contato: {
    label: 'Em Contato',
    icon: MessageCircle,
    color: 'bg-cyan-500',
    colorLight: 'bg-cyan-100',
    colorText: 'text-cyan-700',
    colorBorder: 'border-cyan-300',
    description: 'Primeira interação acontecendo'
  },
  aguardando_resposta: {
    label: 'Aguardando Resposta',
    icon: Clock,
    color: 'bg-orange-500',
    colorLight: 'bg-orange-100',
    colorText: 'text-orange-700',
    colorBorder: 'border-orange-300',
    description: 'Lead não respondeu ainda'
  },
  interessado: {
    label: 'Interessado',
    icon: Heart,
    color: 'bg-pink-500',
    colorLight: 'bg-pink-100',
    colorText: 'text-pink-700',
    colorBorder: 'border-pink-300',
    description: 'Demonstrou interesse'
  },
  agendamento_solicitado: {
    label: 'Agendamento Solicitado',
    icon: CalendarClock,
    color: 'bg-purple-500',
    colorLight: 'bg-purple-100',
    colorText: 'text-purple-700',
    colorBorder: 'border-purple-300',
    description: 'Pediu para agendar'
  },
  agendado: {
    label: 'Agendado',
    icon: CalendarCheck,
    color: 'bg-indigo-500',
    colorLight: 'bg-indigo-100',
    colorText: 'text-indigo-700',
    colorBorder: 'border-indigo-300',
    description: 'Consulta já marcada'
  },
  compareceu: {
    label: 'Compareceu',
    icon: CheckCircle2,
    color: 'bg-green-500',
    colorLight: 'bg-green-100',
    colorText: 'text-green-700',
    colorBorder: 'border-green-300',
    description: 'Passou na consulta'
  },
  nao_compareceu: {
    label: 'Não Compareceu',
    icon: XCircle,
    color: 'bg-red-500',
    colorLight: 'bg-red-100',
    colorText: 'text-red-700',
    colorBorder: 'border-red-300',
    description: 'Faltou à consulta'
  },
  convertido: {
    label: 'Convertido',
    icon: Trophy,
    color: 'bg-yellow-500',
    colorLight: 'bg-yellow-100',
    colorText: 'text-yellow-700',
    colorBorder: 'border-yellow-300',
    description: 'Fechou tratamento'
  },
  perdido: {
    label: 'Perdido',
    icon: AlertCircle,
    color: 'bg-gray-500',
    colorLight: 'bg-gray-100',
    colorText: 'text-gray-700',
    colorBorder: 'border-gray-300',
    description: 'Desistiu/não tem interesse'
  }
} as const

export type EstagioType = keyof typeof ESTAGIOS_PIPELINE

interface PipelineStageProps {
  estagio: EstagioType | null
  onChangeEstagio: (novoEstagio: EstagioType) => void
  loading?: boolean
}

export function PipelineStage({ estagio, onChangeEstagio, loading }: PipelineStageProps) {
  const [mostrarDropdown, setMostrarDropdown] = useState(false)

  const estagioAtual = estagio ? ESTAGIOS_PIPELINE[estagio] : null
  const Icon = estagioAtual?.icon || User

  return (
    <div className="relative">
      {/* Badge atual - clicável para abrir dropdown */}
      <Button
        variant="outline"
        className={`w-full justify-between ${estagioAtual ? estagioAtual.colorLight + ' ' + estagioAtual.colorBorder : 'bg-gray-50'}`}
        onClick={() => setMostrarDropdown(!mostrarDropdown)}
        disabled={loading}
      >
        <div className="flex items-center gap-2">
          {estagioAtual && <Icon className={`h-4 w-4 ${estagioAtual.colorText}`} />}
          <span className={estagioAtual ? estagioAtual.colorText : 'text-gray-500'}>
            {estagioAtual?.label || 'Selecione o estágio'}
          </span>
        </div>
        <ChevronDown className={`h-4 w-4 transition-transform ${mostrarDropdown ? 'rotate-180' : ''}`} />
      </Button>

      {/* Dropdown com todos os estágios */}
      {mostrarDropdown && (
        <>
          {/* Overlay para fechar ao clicar fora */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setMostrarDropdown(false)}
          />

          {/* Lista de opções */}
          <div className="absolute top-full left-0 right-0 mt-2 bg-white border rounded-lg shadow-xl z-20 max-h-96 overflow-y-auto">
            {Object.entries(ESTAGIOS_PIPELINE).map(([key, config]) => {
              const EstagioIcon = config.icon
              const isSelected = estagio === key

              return (
                <button
                  key={key}
                  onClick={() => {
                    onChangeEstagio(key as EstagioType)
                    setMostrarDropdown(false)
                  }}
                  className={`w-full px-4 py-3 flex items-start gap-3 hover:bg-gray-50 transition-colors border-b last:border-b-0 ${
                    isSelected ? config.colorLight : ''
                  }`}
                >
                  <div className={`p-2 rounded-full ${config.colorLight} flex-shrink-0`}>
                    <EstagioIcon className={`h-5 w-5 ${config.colorText}`} />
                  </div>
                  <div className="flex-1 text-left">
                    <div className={`font-semibold ${config.colorText}`}>
                      {config.label}
                      {isSelected && (
                        <CheckCircle2 className="inline h-4 w-4 ml-2" />
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {config.description}
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

// Badge simples para mostrar o estágio (sem edição)
interface PipelineBadgeProps {
  estagio: EstagioType | null
  size?: 'sm' | 'md' | 'lg'
}

export function PipelineBadge({ estagio, size = 'md' }: PipelineBadgeProps) {
  if (!estagio) return null

  const config = ESTAGIOS_PIPELINE[estagio]
  const Icon = config.icon

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2'
  }

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  }

  return (
    <Badge
      className={`${config.colorLight} ${config.colorText} ${config.colorBorder} border ${sizeClasses[size]} font-semibold`}
    >
      <Icon className={`${iconSizes[size]} mr-1.5`} />
      {config.label}
    </Badge>
  )
}

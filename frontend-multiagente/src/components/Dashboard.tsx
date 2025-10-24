import { useState, useEffect } from 'react'
import {
  MessageSquare,
  BarChart3,
  Settings,
  Users,
  Bot,
  LogOut,
  Menu,
  X,
  Bell,
  Search,
  Volume2
} from 'lucide-react'
import { useNotifications } from '@/hooks/useNotifications'
import { useAuth } from '@/hooks/useAuth'
import { ConversationList } from './ConversationList'
import { MessageArea } from './MessageArea'
import { ContactInfo } from './ContactInfo'
import { AnalyticsDashboard } from './AnalyticsDashboard'
import { IAModeControl } from './IAModeControl'
import { ApprovalQueue } from './ApprovalQueue'
import { ScheduleManager } from './ScheduleManager'
import { Simulator } from './Simulator'
import { LearningStats } from './LearningStats'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { PulsingBadge } from '@/components/ui/pulsing-badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import type { Conversa, Mensagem } from '../types/index'

interface DashboardProps {
  conversas: Conversa[]
  mensagens: Record<string, Mensagem[]>
  onLogout: () => void
  userRole?: 'super_admin' | 'vendas' | 'assistencia-tecnica' | 'financeiro' | 'suporte-ti'
  userDepartamento?: string // slug do departamento do usuário
}

export function Dashboard({
  conversas,
  mensagens,
  onLogout,
  userRole = 'super_admin',
  userDepartamento
}: DashboardProps) {
  const { usuario } = useAuth()
  const [conversaSelecionada, setConversaSelecionada] = useState<string>()
  const [mostrarInfo, setMostrarInfo] = useState(true)
  const [sidebarAberta, setSidebarAberta] = useState(true)
  const [activeTab, setActiveTab] = useState('conversas')
  const [notificacoesAtivadas, setNotificacoesAtivadas] = useState(true)

  // Filtrar conversas baseado no departamento do usuário
  const conversasFiltradas = userRole === 'super_admin'
    ? conversas
    : conversas.filter(c => c.departamento?.slug === userDepartamento)

  // Hook de notificações
  const { notificar, tocarSom, solicitarPermissao } = useNotifications({
    enabled: notificacoesAtivadas,
    conversas: conversasFiltradas
  })

  // Solicitar permissão ao carregar
  useEffect(() => {
    solicitarPermissao()
  }, [])

  const conversa = conversas.find(c => c.id === conversaSelecionada)
  const mensagensConversa = conversaSelecionada ? mensagens[conversaSelecionada] || [] : []

  const handleEnviarMensagem = (conteudo: string) => {
    console.log('Enviando mensagem:', conteudo)
  }

  const menuItems = [
    {
      id: 'conversas',
      icon: MessageSquare,
      label: 'Conversas',
      badge: conversasFiltradas.filter(c => c.nao_lidas > 0).length
    },
    ...(userRole === 'super_admin' ? [
      { id: 'analytics', icon: BarChart3, label: 'Analytics' },
      { id: 'agentes', icon: Users, label: 'Agentes' },
      { id: 'ia', icon: Bot, label: 'Config IA' },
      { id: 'settings', icon: Settings, label: 'Configurações' },
    ] : [])
  ]

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarAberta ? 'w-64' : 'w-20'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300`}>
        {/* Logo */}
        <div className="h-16 border-b border-gray-200 flex items-center justify-between px-4">
          {sidebarAberta ? (
            <>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-sm font-bold text-gray-900">Alice</h1>
                  <p className="text-xs text-gray-500">Multiagente</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarAberta(false)}
                className="h-8 w-8"
              >
                <Menu className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarAberta(true)}
              className="mx-auto h-8 w-8"
            >
              <Menu className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Menu Items */}
        <nav className="flex-1 p-3 space-y-1">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                activeTab === item.id
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {sidebarAberta && (
                <>
                  <span className="text-sm font-medium flex-1 text-left">{item.label}</span>
                  {item.badge && item.badge > 0 && (
                    <PulsingBadge pulse={item.badge > 0}>
                      {item.badge}
                    </PulsingBadge>
                  )}
                </>
              )}
            </button>
          ))}
        </nav>

        {/* User Profile */}
        <div className="border-t border-gray-200 p-3">
          <div className={`flex items-center gap-3 px-3 py-2 ${sidebarAberta ? '' : 'justify-center'}`}>
            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-blue-600 text-white text-sm">
                {usuario?.nome_completo?.charAt(0).toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            {sidebarAberta && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{usuario?.nome_completo || 'Usuário'}</p>
                <p className="text-xs text-gray-500 truncate">{usuario?.email || ''}</p>
              </div>
            )}
          </div>
          {sidebarAberta && (
            <Button
              variant="ghost"
              onClick={onLogout}
              className="w-full mt-2 justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sair
            </Button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {activeTab === 'conversas' && 'Conversas'}
              {activeTab === 'analytics' && 'Analytics'}
              {activeTab === 'agentes' && 'Agentes'}
              {activeTab === 'ia' && 'Configurações de IA'}
              {activeTab === 'settings' && 'Configurações'}
            </h2>
            <p className="text-sm text-gray-500">
              {activeTab === 'conversas' && `${conversas.length} conversas ativas`}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Botão Testar Som */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                console.log('Tocando som...')
                tocarSom('nova_mensagem')
              }}
              className="gap-2"
            >
              <Volume2 className="h-4 w-4" />
              <span className="hidden sm:inline">Testar Som</span>
            </Button>

            {/* Notifications Toggle */}
            <Button
              variant={notificacoesAtivadas ? 'default' : 'outline'}
              size="sm"
              onClick={() => {
                const novoEstado = !notificacoesAtivadas
                console.log('Notificações:', novoEstado ? 'ATIVADAS' : 'DESATIVADAS')
                setNotificacoesAtivadas(novoEstado)
                if (novoEstado) {
                  solicitarPermissao()
                }
              }}
              className="gap-2"
            >
              <Bell className="h-4 w-4" />
              <span className="hidden sm:inline">
                {notificacoesAtivadas ? 'Notificações ON' : 'Notificações OFF'}
              </span>
            </Button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {activeTab === 'conversas' && (
            <>
              <div className="w-[350px] border-r border-gray-200">
                <ConversationList
                  conversas={conversasFiltradas}
                  conversaSelecionada={conversaSelecionada}
                  onSelectConversa={setConversaSelecionada}
                />
              </div>

              <div className="flex-1">
                <MessageArea
                  conversa={conversa}
                  mensagens={mensagensConversa}
                  onEnviarMensagem={handleEnviarMensagem}
                />
              </div>

              {mostrarInfo && conversa && (
                <div className="w-[320px] border-l border-gray-200">
                  <ContactInfo
                    conversa={conversa}
                    onClose={() => setMostrarInfo(false)}
                  />
                </div>
              )}
            </>
          )}

          {activeTab === 'analytics' && (
            userRole === 'super_admin' ? (
              <AnalyticsDashboard />
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-semibold text-gray-700 mb-2">Acesso Restrito</p>
                  <p className="text-gray-500">Apenas Super Administradores podem acessar Analytics</p>
                </div>
              </div>
            )
          )}

          {activeTab === 'agentes' && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Gerenciamento de agentes em desenvolvimento</p>
              </div>
            </div>
          )}

          {activeTab === 'ia' && (
            <div className="flex-1 overflow-y-auto p-6">
              <div className="max-w-7xl mx-auto space-y-6">
                {/* Grid principal */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Coluna esquerda - Controle e Agendamentos */}
                  <div className="lg:col-span-1 space-y-6">
                    <IAModeControl empresaId="emp1" />
                    <ScheduleManager empresaId="emp1" />
                  </div>

                  {/* Coluna direita - Fila de Aprovação */}
                  <div className="lg:col-span-2">
                    <ApprovalQueue empresaId="emp1" />
                  </div>
                </div>

                {/* Simulador e Estatísticas de Aprendizado */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                  <Simulator empresaId="emp1" />
                  <LearningStats empresaId="emp1" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Settings className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Configurações em desenvolvimento</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

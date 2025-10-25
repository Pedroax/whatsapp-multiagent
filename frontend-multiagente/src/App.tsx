import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Login } from './pages/Login'
import { Dashboard } from './components/Dashboard'
import { useConversas } from './hooks/useConversas'
import { useAuth } from './hooks/useAuth'
import type { Conversa, Mensagem } from './types/index'

// Mock data para demonstração
const mockConversas: Conversa[] = [
  {
    id: '1',
    empresa_id: 'emp1',
    lead_id: 'lead1',
    lead: {
      id: 'lead1',
      empresa_id: 'emp1',
      nome: 'João Silva',
      telefone: '+55 61 99999-1234',
      email: 'joao@example.com',
      tags: ['cliente', 'vendas']
    },
    departamento_id: 'dep1',
    departamento: {
      id: 'dep1',
      empresa_id: 'emp1',
      nome: 'Vendas',
      slug: 'vendas',
      cor_primaria: '#3B82F6',
      icone: 'shopping-cart',
      ordem: 1,
      ativo: true
    },
    status: 'aberta',
    modo_ia: 'ativo',
    prioridade: 'normal',
    nao_lidas: 2,
    ultima_mensagem: {
      id: 'msg1',
      conversa_id: '1',
      tipo: 'entrada',
      conteudo: 'Olá, gostaria de saber mais sobre baterias automotivas',
      enviado_por_ia: false,
      lida: false,
      created_at: new Date().toISOString()
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: '2',
    empresa_id: 'emp1',
    lead_id: 'lead2',
    lead: {
      id: 'lead2',
      empresa_id: 'emp1',
      nome: 'Maria Santos',
      telefone: '+55 61 99999-5678',
      tags: ['assistencia']
    },
    departamento_id: 'dep2',
    departamento: {
      id: 'dep2',
      empresa_id: 'emp1',
      nome: 'Assistência Técnica',
      slug: 'assistencia-tecnica',
      cor_primaria: '#F59E0B',
      icone: 'wrench',
      ordem: 2,
      ativo: true
    },
    status: 'pendente',
    modo_ia: 'pausado',
    prioridade: 'alta',
    nao_lidas: 0,
    ultima_mensagem: {
      id: 'msg2',
      conversa_id: '2',
      tipo: 'saida',
      conteudo: 'Entendi seu problema. Vou transferir para a assistência técnica.',
      enviado_por_ia: true,
      lida: true,
      created_at: new Date(Date.now() - 3600000).toISOString()
    },
    created_at: new Date(Date.now() - 7200000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: '3',
    empresa_id: 'emp1',
    lead_id: 'lead3',
    lead: {
      id: 'lead3',
      empresa_id: 'emp1',
      nome: 'Carlos Oliveira',
      telefone: '+55 61 99999-9999',
      tags: ['vip', 'vendas']
    },
    status: 'nova',
    modo_ia: 'ativo',
    prioridade: 'urgente',
    nao_lidas: 5,
    ultima_mensagem: {
      id: 'msg3',
      conversa_id: '3',
      tipo: 'entrada',
      conteudo: 'Preciso de uma cotação urgente',
      enviado_por_ia: false,
      lida: false,
      created_at: new Date(Date.now() - 120000).toISOString()
    },
    created_at: new Date(Date.now() - 180000).toISOString(),
    updated_at: new Date(Date.now() - 120000).toISOString()
  }
]

const mockMensagens: Record<string, Mensagem[]> = {
  '1': [
    {
      id: 'msg1-1',
      conversa_id: '1',
      tipo: 'entrada',
      conteudo: 'Olá!',
      enviado_por_ia: false,
      lida: true,
      created_at: new Date(Date.now() - 600000).toISOString()
    },
    {
      id: 'msg1-2',
      conversa_id: '1',
      tipo: 'saida',
      conteudo: 'Olá! Seja bem-vindo à LC Baterias. Como posso ajudá-lo hoje?',
      enviado_por_ia: true,
      lida: true,
      created_at: new Date(Date.now() - 540000).toISOString()
    },
    {
      id: 'msg1-3',
      conversa_id: '1',
      tipo: 'entrada',
      conteudo: 'Gostaria de saber mais sobre baterias automotivas',
      enviado_por_ia: false,
      lida: false,
      created_at: new Date(Date.now() - 120000).toISOString()
    },
    {
      id: 'msg1-4',
      conversa_id: '1',
      tipo: 'saida',
      conteudo: 'Claro! Temos várias opções de baterias automotivas. Para qual tipo de veículo você precisa?',
      enviado_por_ia: true,
      lida: false,
      created_at: new Date().toISOString()
    }
  ],
  '2': [
    {
      id: 'msg2-1',
      conversa_id: '2',
      tipo: 'entrada',
      conteudo: 'Minha bateria está com problema',
      enviado_por_ia: false,
      lida: true,
      created_at: new Date(Date.now() - 7200000).toISOString()
    },
    {
      id: 'msg2-2',
      conversa_id: '2',
      tipo: 'saida',
      conteudo: 'Entendi seu problema. Vou transferir para a assistência técnica que poderá te ajudar melhor.',
      enviado_por_ia: true,
      lida: true,
      created_at: new Date(Date.now() - 3600000).toISOString()
    }
  ],
  '3': [
    {
      id: 'msg3-1',
      conversa_id: '3',
      tipo: 'entrada',
      conteudo: 'Preciso de uma cotação urgente',
      enviado_por_ia: false,
      lida: false,
      created_at: new Date(Date.now() - 120000).toISOString()
    }
  ]
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, checkAuth } = useAuth()

  useEffect(() => {
    checkAuth()
  }, [])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  const { isAuthenticated, usuario, logout } = useAuth()
  const { conversas, mensagens, loading, error } = useConversas()

  // Verificar autenticação ao carregar
  useEffect(() => {
    const { checkAuth } = useAuth.getState()
    checkAuth()
  }, [])

  return (
    <Router>
      <Routes>
        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/" replace /> : <Login />
        } />

        <Route path="/" element={
          <ProtectedRoute>
            {loading ? (
              <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Carregando conversas...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                  <p className="text-red-600 mb-4">Erro ao carregar conversas: {error}</p>
                  <p className="text-sm text-gray-500">Verifique a conexão com o Supabase</p>
                </div>
              </div>
            ) : (
              <Dashboard
                conversas={conversas.length > 0 ? conversas : mockConversas}
                mensagens={Object.keys(mensagens).length > 0 ? mensagens : mockMensagens}
                onLogout={logout}
                userRole={usuario?.role as 'super_admin' | 'vendas' | 'assistencia-tecnica' | 'financeiro' | 'suporte-ti' || 'super_admin'}
                userDepartamento={usuario?.departamento_slug || undefined}
              />
            )}
          </ProtectedRoute>
        } />
      </Routes>
    </Router>
  )
}

export default App

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { supabase } from '../lib/supabase'

interface Usuario {
  id: string
  email: string
  nome_completo: string
  role: 'super_admin' | 'admin' | 'agente'
  departamento_slug: string | null
  pode_ver_todos_departamentos: boolean
}

interface AuthState {
  usuario: Usuario | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      usuario: null,
      token: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        try {
          // Fazer login no Supabase Auth
          const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
            email,
            password,
          })

          if (authError) {
            throw new Error(authError.message)
          }

          if (!authData.user || !authData.session) {
            throw new Error('Erro ao fazer login')
          }

          // Buscar dados do usuário na tabela usuarios
          const { data: usuarioData, error: usuarioError } = await supabase
            .from('usuarios')
            .select('*')
            .eq('id', authData.user.id)
            .single()

          if (usuarioError || !usuarioData) {
            throw new Error('Usuário não encontrado na base de dados')
          }

          set({
            usuario: usuarioData,
            token: authData.session.access_token,
            isAuthenticated: true,
          })
        } catch (error: any) {
          console.error('Erro no login:', error)
          throw error
        }
      },

      logout: async () => {
        try {
          await supabase.auth.signOut()
        } catch (error) {
          console.error('Erro ao fazer logout:', error)
        }

        set({
          usuario: null,
          token: null,
          isAuthenticated: false,
        })
      },

      checkAuth: async () => {
        try {
          const { data: { session } } = await supabase.auth.getSession()

          if (!session) {
            set({ isAuthenticated: false, usuario: null, token: null })
            return
          }

          // Buscar dados do usuário na tabela usuarios
          const { data: usuarioData, error: usuarioError } = await supabase
            .from('usuarios')
            .select('*')
            .eq('id', session.user.id)
            .single()

          if (usuarioError || !usuarioData) {
            set({ isAuthenticated: false, usuario: null, token: null })
            return
          }

          set({
            usuario: usuarioData,
            token: session.access_token,
            isAuthenticated: true,
          })
        } catch (error) {
          console.error('Erro ao verificar autenticação:', error)
          set({
            usuario: null,
            token: null,
            isAuthenticated: false,
          })
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)

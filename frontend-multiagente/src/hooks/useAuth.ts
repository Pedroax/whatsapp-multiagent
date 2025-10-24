import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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
  logout: () => void
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
          const response = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
          })

          if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Erro ao fazer login')
          }

          const data = await response.json()

          set({
            usuario: data.usuario,
            token: data.token,
            isAuthenticated: true,
          })
        } catch (error: any) {
          console.error('Erro no login:', error)
          throw error
        }
      },

      logout: () => {
        const { token } = get()

        // Chamar endpoint de logout no backend
        if (token) {
          fetch('http://localhost:8000/api/auth/logout', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }).catch(console.error)
        }

        set({
          usuario: null,
          token: null,
          isAuthenticated: false,
        })
      },

      checkAuth: async () => {
        const { token } = get()

        if (!token) {
          set({ isAuthenticated: false, usuario: null })
          return
        }

        try {
          const response = await fetch('http://localhost:8000/api/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          })

          if (!response.ok) {
            throw new Error('Token inválido')
          }

          const usuario = await response.json()

          set({
            usuario,
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

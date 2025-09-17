import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/api/client'

interface User {
  id: string
  email: string
  username: string
  role: string
  first_name?: string
  last_name?: string
}

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: { username: string; password: string }) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isLoading: false,
      isAuthenticated: false,

      login: async (credentials) => {
        set({ isLoading: true })
        try {
          // В реальном приложении здесь будет API вызов
          // const response = await api.post('/auth/login/', credentials)
          // const { user, token } = response.data
          
          // Пока используем мок данные
          const mockUser = {
            id: '1',
            email: credentials.username,
            username: credentials.username,
            role: 'Подрядчик',
            first_name: 'Тест',
            last_name: 'Пользователь'
          }
          
          set({ 
            user: mockUser, 
            isAuthenticated: true, 
            isLoading: false 
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        set({ 
          user: null, 
          isAuthenticated: false 
        })
        // Очищаем токен из localStorage
        localStorage.removeItem('auth-storage')
      },

      checkAuth: async () => {
        set({ isLoading: true })
        try {
          // Проверяем есть ли сохраненный пользователь
          const state = get()
          if (state.user) {
            set({ 
              isAuthenticated: true, 
              isLoading: false 
            })
            return
          }

          // В реальном приложении здесь будет проверка токена
          // const response = await api.get('/auth/me/')
          // set({ user: response.data, isAuthenticated: true })
          
          set({ isLoading: false })
        } catch (error) {
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false 
          })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)

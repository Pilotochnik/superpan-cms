import { Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import Layout from '@/components/Layout'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Projects from '@/pages/Projects'
import Kanban from '@/pages/Kanban'
import Warehouse from '@/pages/Warehouse'
import Profile from '@/pages/Profile'
import { useAuthStore } from '@/hooks/useAuthStore'

function App() {
  const [isLoading, setIsLoading] = useState(true)
  const { user, checkAuth } = useAuthStore()

  useEffect(() => {
    const initAuth = async () => {
      await checkAuth()
      setIsLoading(false)
    }
    initAuth()
  }, [checkAuth])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Login />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="kanban/:projectId" element={<Kanban />} />
          <Route path="warehouse" element={<Warehouse />} />
          <Route path="profile" element={<Profile />} />
        </Route>
      </Routes>
      
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            style: {
              background: '#28a745',
            },
          },
          error: {
            style: {
              background: '#dc3545',
            },
          },
        }}
      />
    </div>
  )
}

export default App

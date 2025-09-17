import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  Users, 
  FolderOpen, 
  Package, 
  Calendar,
  ArrowUpRight,
  Activity
} from 'lucide-react'

interface DashboardStats {
  totalProjects: number
  activeProjects: number
  totalUsers: number
  warehouseItems: number
  pendingTasks: number
  completedThisWeek: number
}

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    activeProjects: 0,
    totalUsers: 0,
    warehouseItems: 0,
    pendingTasks: 0,
    completedThisWeek: 0
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Имитация загрузки данных
    const loadStats = async () => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setStats({
        totalProjects: 12,
        activeProjects: 8,
        totalUsers: 45,
        warehouseItems: 156,
        pendingTasks: 23,
        completedThisWeek: 18
      })
      setIsLoading(false)
    }
    loadStats()
  }, [])

  const statCards = [
    {
      title: 'Всего проектов',
      value: stats.totalProjects,
      change: '+12%',
      icon: FolderOpen,
      color: 'blue',
      bgColor: 'bg-blue-500',
      textColor: 'text-blue-600'
    },
    {
      title: 'Активные проекты',
      value: stats.activeProjects,
      change: '+5%',
      icon: Activity,
      color: 'green',
      bgColor: 'bg-green-500',
      textColor: 'text-green-600'
    },
    {
      title: 'Пользователи',
      value: stats.totalUsers,
      change: '+8%',
      icon: Users,
      color: 'purple',
      bgColor: 'bg-purple-500',
      textColor: 'text-purple-600'
    },
    {
      title: 'Товары на складе',
      value: stats.warehouseItems,
      change: '-2%',
      icon: Package,
      color: 'orange',
      bgColor: 'bg-orange-500',
      textColor: 'text-orange-600'
    },
    {
      title: 'Задачи в работе',
      value: stats.pendingTasks,
      change: '+15%',
      icon: Calendar,
      color: 'red',
      bgColor: 'bg-red-500',
      textColor: 'text-red-600'
    },
    {
      title: 'Завершено на неделе',
      value: stats.completedThisWeek,
      change: '+22%',
      icon: TrendingUp,
      color: 'indigo',
      bgColor: 'bg-indigo-500',
      textColor: 'text-indigo-600'
    }
  ]

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-20 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Добро пожаловать!
          </h1>
          <p className="text-gray-600 mt-1">
            Обзор ваших проектов и активностей
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Сегодня</p>
          <p className="text-lg font-semibold text-gray-900">
            {new Date().toLocaleDateString('ru-RU', {
              day: 'numeric',
              month: 'long',
              year: 'numeric'
            })}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div key={index} className="card hover:shadow-lg transition-all duration-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">
                    {stat.title}
                  </p>
                  <p className="text-3xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                  <div className="flex items-center mt-2">
                    <ArrowUpRight 
                      size={16} 
                      className={`mr-1 ${
                        stat.change.startsWith('+') ? 'text-green-500' : 'text-red-500'
                      }`} 
                    />
                    <span 
                      className={`text-sm font-medium ${
                        stat.change.startsWith('+') ? 'text-green-500' : 'text-red-500'
                      }`}
                    >
                      {stat.change}
                    </span>
                    <span className="text-sm text-gray-500 ml-1">с прошлой недели</span>
                  </div>
                </div>
                <div className={`w-12 h-12 ${stat.bgColor} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Быстрые действия
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <a
            href="/projects"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FolderOpen className="w-8 h-8 text-primary-500 mb-2" />
            <span className="text-sm font-medium text-gray-700">Проекты</span>
          </a>
          <a
            href="/kanban"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Activity className="w-8 h-8 text-primary-500 mb-2" />
            <span className="text-sm font-medium text-gray-700">Канбан</span>
          </a>
          <a
            href="/warehouse"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Package className="w-8 h-8 text-primary-500 mb-2" />
            <span className="text-sm font-medium text-gray-700">Склад</span>
          </a>
          <a
            href="/profile"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Users className="w-8 h-8 text-primary-500 mb-2" />
            <span className="text-sm font-medium text-gray-700">Профиль</span>
          </a>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

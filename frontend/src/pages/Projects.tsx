import { useState, useEffect } from 'react'
import { Plus, Search, Filter, MoreVertical } from 'lucide-react'

interface Project {
  id: string
  name: string
  description: string
  status: 'planning' | 'in_progress' | 'completed' | 'on_hold'
  budget: number
  created_at: string
  progress: number
}

const Projects = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    // Имитация загрузки проектов
    const loadProjects = async () => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setProjects([
        {
          id: '1',
          name: 'Жилой комплекс "Солнечный"',
          description: 'Строительство многоэтажного жилого комплекса',
          status: 'in_progress',
          budget: 15000000,
          created_at: '2024-01-15',
          progress: 65
        },
        {
          id: '2',
          name: 'Торговый центр "Мегаполис"',
          description: 'Строительство торгового центра',
          status: 'planning',
          budget: 8000000,
          created_at: '2024-02-01',
          progress: 25
        },
        {
          id: '3',
          name: 'Офисное здание "Бизнес-центр"',
          description: 'Строительство офисного здания',
          status: 'completed',
          budget: 12000000,
          created_at: '2023-11-20',
          progress: 100
        }
      ])
      setIsLoading(false)
    }
    loadProjects()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'planning':
        return 'bg-yellow-100 text-yellow-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'on_hold':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'in_progress':
        return 'В работе'
      case 'planning':
        return 'Планирование'
      case 'completed':
        return 'Завершен'
      case 'on_hold':
        return 'Приостановлен'
      default:
        return status
    }
  }

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded animate-pulse" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-24 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Проекты</h1>
          <p className="text-gray-600 mt-1">Управление строительными проектами</p>
        </div>
        <button className="btn-primary flex items-center space-x-2 touch-target">
          <Plus size={20} />
          <span>Создать проект</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Поиск проектов..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
        <button className="btn-secondary flex items-center space-x-2">
          <Filter size={20} />
          <span>Фильтры</span>
        </button>
      </div>

      {/* Projects List */}
      <div className="space-y-4">
        {filteredProjects.map((project) => (
          <div key={project.id} className="card hover:shadow-lg transition-all duration-200">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {project.name}
                  </h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                    {getStatusText(project.status)}
                  </span>
                </div>
                <p className="text-gray-600 mb-3">{project.description}</p>
                
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">Прогресс</span>
                      <span className="text-sm font-medium text-gray-900">{project.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${project.progress}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Бюджет: {project.budget.toLocaleString()} ₽</span>
                    <span>Создан: {new Date(project.created_at).toLocaleDateString('ru-RU')}</span>
                  </div>
                </div>
              </div>
              
              <button className="ml-4 p-2 text-gray-400 hover:text-gray-600 transition-colors">
                <MoreVertical size={20} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Проекты не найдены</h3>
          <p className="text-gray-600">
            {searchTerm ? 'Попробуйте изменить поисковый запрос' : 'Создайте свой первый проект'}
          </p>
        </div>
      )}
    </div>
  )
}

export default Projects

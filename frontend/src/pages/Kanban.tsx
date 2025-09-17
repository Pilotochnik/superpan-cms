import { useState } from 'react'
import { Plus, MoreHorizontal } from 'lucide-react'

interface Task {
  id: string
  title: string
  description: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high'
  assignee?: string
  dueDate?: string
}

const Kanban = () => {
  const [tasks, setTasks] = useState<Task[]>([
    {
      id: '1',
      title: 'Заливка фундамента',
      description: 'Залить бетон для фундамента блока А',
      status: 'todo',
      priority: 'high',
      assignee: 'Иван Петров',
      dueDate: '2024-03-15'
    },
    {
      id: '2',
      title: 'Установка опалубки',
      description: 'Собрать опалубку для стен',
      status: 'in_progress',
      priority: 'medium',
      assignee: 'Петр Сидоров'
    },
    {
      id: '3',
      title: 'Проверка качества',
      description: 'Проверить качество выполненных работ',
      status: 'review',
      priority: 'high',
      assignee: 'Мария Козлова'
    },
    {
      id: '4',
      title: 'Документация',
      description: 'Оформить акты выполненных работ',
      status: 'done',
      priority: 'low'
    }
  ])

  const columns = [
    { id: 'todo', title: 'К выполнению', color: 'bg-gray-100' },
    { id: 'in_progress', title: 'В работе', color: 'bg-blue-100' },
    { id: 'review', title: 'На проверке', color: 'bg-yellow-100' },
    { id: 'done', title: 'Выполнено', color: 'bg-green-100' }
  ]

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'Высокий'
      case 'medium':
        return 'Средний'
      case 'low':
        return 'Низкий'
      default:
        return priority
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Канбан доска</h1>
          <p className="text-gray-600 mt-1">Управление задачами проекта</p>
        </div>
        <button className="btn-primary flex items-center space-x-2 touch-target">
          <Plus size={20} />
          <span>Добавить задачу</span>
        </button>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {columns.map((column) => {
          const columnTasks = tasks.filter(task => task.status === column.id)
          
          return (
            <div key={column.id} className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">{column.title}</h3>
                <span className="bg-gray-200 text-gray-600 px-2 py-1 rounded-full text-sm">
                  {columnTasks.length}
                </span>
              </div>
              
              <div className="space-y-3">
                {columnTasks.map((task) => (
                  <div key={task.id} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900 text-sm">{task.title}</h4>
                      <button className="text-gray-400 hover:text-gray-600">
                        <MoreHorizontal size={16} />
                      </button>
                    </div>
                    
                    <p className="text-gray-600 text-xs mb-3 line-clamp-2">{task.description}</p>
                    
                    <div className="flex items-center justify-between">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                        {getPriorityText(task.priority)}
                      </span>
                      
                      {task.assignee && (
                        <div className="flex items-center space-x-1">
                          <div className="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-xs font-medium">
                              {task.assignee.split(' ').map(n => n[0]).join('')}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {task.dueDate && (
                      <div className="mt-2 text-xs text-gray-500">
                        Срок: {new Date(task.dueDate).toLocaleDateString('ru-RU')}
                      </div>
                    )}
                  </div>
                ))}
                
                <button className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors touch-target">
                  <Plus size={20} className="mx-auto" />
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Kanban

import { useState, useEffect } from 'react'
import { Plus, Search, Package, TrendingUp, TrendingDown } from 'lucide-react'

interface WarehouseItem {
  id: string
  name: string
  description: string
  item_type: 'MATERIAL' | 'EQUIPMENT'
  current_quantity: number
  min_quantity: number
  unit: string
  last_transaction: string
}

const Warehouse = () => {
  const [items, setItems] = useState<WarehouseItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    const loadItems = async () => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setItems([
        {
          id: '1',
          name: 'Цемент М400',
          description: 'Портландцемент для бетонных работ',
          item_type: 'MATERIAL',
          current_quantity: 150,
          min_quantity: 50,
          unit: 'кг',
          last_transaction: '2024-03-10'
        },
        {
          id: '2',
          name: 'Бетономешалка',
          description: 'Переносная бетономешалка 200л',
          item_type: 'EQUIPMENT',
          current_quantity: 3,
          min_quantity: 2,
          unit: 'шт',
          last_transaction: '2024-03-08'
        },
        {
          id: '3',
          name: 'Арматура А500',
          description: 'Стальная арматура диаметром 12мм',
          item_type: 'MATERIAL',
          current_quantity: 25,
          min_quantity: 100,
          unit: 'т',
          last_transaction: '2024-03-05'
        }
      ])
      setIsLoading(false)
    }
    loadItems()
  }, [])

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getItemTypeColor = (type: string) => {
    return type === 'MATERIAL' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
  }

  const getItemTypeText = (type: string) => {
    return type === 'MATERIAL' ? 'Материал' : 'Оборудование'
  }

  const getStockStatus = (current: number, min: number) => {
    if (current <= min) return { color: 'text-red-600', icon: TrendingDown }
    if (current <= min * 2) return { color: 'text-yellow-600', icon: TrendingUp }
    return { color: 'text-green-600', icon: TrendingUp }
  }

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
          <h1 className="text-3xl font-bold text-gray-900">Склад</h1>
          <p className="text-gray-600 mt-1">Управление материалами и оборудованием</p>
        </div>
        <button className="btn-primary flex items-center space-x-2 touch-target">
          <Plus size={20} />
          <span>Добавить товар</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
              <Package className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Всего товаров</p>
              <p className="text-2xl font-bold text-gray-900">{items.length}</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">В наличии</p>
              <p className="text-2xl font-bold text-gray-900">
                {items.filter(item => item.current_quantity > item.min_quantity).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mr-4">
              <TrendingDown className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Нужно пополнить</p>
              <p className="text-2xl font-bold text-gray-900">
                {items.filter(item => item.current_quantity <= item.min_quantity).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
        <input
          type="text"
          placeholder="Поиск товаров..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Items List */}
      <div className="space-y-4">
        {filteredItems.map((item) => {
          const stockStatus = getStockStatus(item.current_quantity, item.min_quantity)
          const StockIcon = stockStatus.icon
          
          return (
            <div key={item.id} className="card hover:shadow-lg transition-all duration-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{item.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getItemTypeColor(item.item_type)}`}>
                      {getItemTypeText(item.item_type)}
                    </span>
                  </div>
                  
                  <p className="text-gray-600 mb-3">{item.description}</p>
                  
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <StockIcon className={`w-4 h-4 ${stockStatus.color}`} />
                        <span className={`text-sm font-medium ${stockStatus.color}`}>
                          {item.current_quantity} {item.unit}
                        </span>
                      </div>
                      
                      <span className="text-sm text-gray-500">
                        Мин: {item.min_quantity} {item.unit}
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-500">
                      Последняя транзакция: {new Date(item.last_transaction).toLocaleDateString('ru-RU')}
                    </div>
                  </div>
                </div>
                
                <div className="ml-4 flex flex-col items-end">
                  <div className={`w-3 h-3 rounded-full mb-2 ${
                    item.current_quantity <= item.min_quantity ? 'bg-red-500' :
                    item.current_quantity <= item.min_quantity * 2 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`} />
                  
                  <button className="btn-secondary text-sm px-3 py-1 touch-target">
                    Детали
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Товары не найдены</h3>
          <p className="text-gray-600">
            {searchTerm ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первый товар на склад'}
          </p>
        </div>
      )}
    </div>
  )
}

export default Warehouse

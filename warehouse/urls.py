from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    # Главная страница склада
    path('', views.warehouse_dashboard, name='dashboard'),
    
    # Товары склада
    path('items/', views.warehouse_items_list, name='items_list'),
    path('items/create/', views.warehouse_item_create, name='item_create'),
    path('items/<int:item_id>/', views.warehouse_item_detail, name='item_detail'),
    path('items/<int:item_id>/edit/', views.warehouse_item_edit, name='item_edit'),
    
    # Транзакции
    path('transactions/', views.warehouse_transactions_list, name='transactions_list'),
    path('transactions/create/', views.warehouse_transaction_create, name='transaction_create'),
    
    # Категории
    path('categories/', views.warehouse_categories_list, name='categories_list'),
    path('categories/create/', views.warehouse_category_create, name='category_create'),
    
    # Оборудование проектов
    path('projects/<uuid:project_id>/equipment/', views.project_equipment_list, name='project_equipment_list'),
    path('projects/<uuid:project_id>/equipment/add/', views.project_equipment_add, name='project_equipment_add'),
    path('equipment/<int:equipment_id>/update-photo/', views.update_equipment_photo, name='update_equipment_photo'),
]

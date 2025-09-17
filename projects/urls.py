from django.urls import path
from . import views
from . import estimate_views

app_name = 'projects'

urlpatterns = [
    # Основные страницы
    path('', views.dashboard, name='dashboard'),
    path('list/', views.ProjectListView.as_view(), name='list'),
    path('create/', views.create_project, name='create'),
    
    # Детали проекта
    path('<uuid:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.edit_project, name='edit'),
    path('<uuid:pk>/members/', views.project_members, name='members'),
    path('<uuid:pk>/estimate/', views.project_estimate, name='estimate'),
    
    # API для работы с проектами
    path('<uuid:pk>/generate-key/', views.generate_access_key, name='generate_key'),
    path('<uuid:pk>/create-estimate/', views.create_estimate, name='create_estimate'),
    
    # Сметы и расценки
    path('estimates/rates/', estimate_views.estimate_rates_list, name='estimate_rates_list'),
    path('estimates/rates/<int:pk>/', estimate_views.estimate_rate_detail, name='estimate_rate_detail'),
    path('estimates/calculate/', estimate_views.calculate_estimate_cost, name='calculate_estimate_cost'),
    path('<uuid:pk>/estimate/detailed/', estimate_views.project_estimate_detailed, name='estimate_detailed'),
    path('<uuid:pk>/estimate/add-item/', estimate_views.add_estimate_item, name='add_estimate_item'),
    path('<uuid:pk>/estimate/remove-item/<int:item_id>/', estimate_views.remove_estimate_item, name='remove_estimate_item'),
    path('<uuid:pk>/estimate/import/', estimate_views.estimate_import, name='estimate_import'),
    path('<uuid:pk>/estimate/export/', estimate_views.estimate_export, name='estimate_export'),
    
    # Шаблоны смет
    path('estimates/templates/', estimate_views.estimate_templates_list, name='estimate_templates_list'),
    path('estimates/templates/<int:pk>/', estimate_views.estimate_template_detail, name='estimate_template_detail'),
    path('<uuid:pk>/estimate/apply-template/<int:template_id>/', estimate_views.apply_template_to_project, name='apply_template'),
]

from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.users_list, name='users_list'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:pk>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('users/register-telegram/', views.register_telegram_user, name='register_telegram_user'),
    path('users/<int:pk>/telegram-link/', views.telegram_link, name='telegram_link'),
    path('users/<int:pk>/telegram-unlink/', views.telegram_unlink, name='telegram_unlink'),
    path('projects/', views.projects_list, name='projects_list'),
    path('projects/<uuid:pk>/members/', views.project_members, name='project_members'),
    path('projects/<uuid:pk>/access-keys/', views.project_access_keys, name='project_access_keys'),
    path('access-keys/create/', views.create_access_key, name='create_access_key'),
    path('access-keys/<int:pk>/toggle/', views.toggle_access_key, name='toggle_access_key'),
    path('expenses/', views.expenses_overview, name='expenses_overview'),
    path('reports/', views.reports, name='reports'),
    path('reports/financial/', views.financial_reports, name='financial_reports'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('devices/', views.device_management, name='device_management'),
    path('devices/reset/<int:user_id>/', views.reset_device_binding, name='reset_device_binding'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TaskViewSet, WarehouseItemViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'warehouse', WarehouseItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

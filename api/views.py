from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Case, When, IntegerField
from projects.models import Project
from kanban.models import ExpenseItem
from warehouse.models import WarehouseItem

User = get_user_model()


# @extend_schema_view(  # Временно отключено
#     list=extend_schema(
#         summary="Список проектов",
#         description="Получить список всех доступных проектов пользователя"
#     ),
#     retrieve=extend_schema(
#         summary="Детали проекта",
#         description="Получить подробную информацию о проекте"
#     ),
#     create=extend_schema(
#         summary="Создать проект",
#         description="Создать новый проект"
#     ),
#     update=extend_schema(
#         summary="Обновить проект",
#         description="Обновить информацию о проекте"
#     ),
#     destroy=extend_schema(
#         summary="Удалить проект",
#         description="Удалить проект"
#     ),
#     stats=extend_schema(
#         summary="Статистика проекта",
#         description="Получить статистику по задачам проекта"
#     )
# )
class ProjectViewSet(viewsets.ModelViewSet):
    """API для управления проектами"""
    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.filter(
            members__user=self.request.user,
            members__is_active=True
        ).distinct()
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Статистика проекта"""
        project = self.get_object()
        
        # Оптимизированный запрос с агрегацией
        
        stats = project.expense_items.aggregate(
            total_tasks=Count('id'),
            completed_tasks=Count(Case(When(status='done', then=1), output_field=IntegerField())),
            in_progress_tasks=Count(Case(When(status='in_progress', then=1), output_field=IntegerField())),
            pending_tasks=Count(Case(When(status='todo', then=1), output_field=IntegerField())),
        )
        
        return Response(stats)


class TaskViewSet(viewsets.ModelViewSet):
    """API для управления задачами"""
    queryset = ExpenseItem.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ExpenseItem.objects.filter(
            project__members__user=self.request.user,
            project__members__is_active=True
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Перемещение задачи между колонками"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in [choice[0] for choice in ExpenseItem.Status.choices]:
            task.status = new_status
            task.save()
            return Response({'status': 'success'})
        
        return Response({'status': 'error', 'message': 'Invalid status'}, status=400)


class WarehouseItemViewSet(viewsets.ModelViewSet):
    """API для управления складом"""
    queryset = WarehouseItem.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        """Обновление количества товара"""
        item = self.get_object()
        quantity = request.data.get('quantity')
        operation = request.data.get('operation')  # 'in' or 'out'
        
        if operation == 'in':
            item.current_quantity += quantity
        elif operation == 'out':
            if item.current_quantity >= quantity:
                item.current_quantity -= quantity
            else:
                return Response({'status': 'error', 'message': 'Insufficient stock'}, status=400)
        
        item.save()
        return Response({
            'status': 'success',
            'new_quantity': item.current_quantity
        })

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from projects.models import Project
from kanban.models import ExpenseItem
from warehouse.models import WarehouseItem

User = get_user_model()


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
        return Response({
            'total_tasks': project.expense_items.count(),
            'completed_tasks': project.expense_items.filter(status='done').count(),
            'in_progress_tasks': project.expense_items.filter(status='in_progress').count(),
            'pending_tasks': project.expense_items.filter(status='todo').count(),
        })


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

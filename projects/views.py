from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count
from django_ratelimit.decorators import ratelimit
from decimal import Decimal
import logging

from .models import Project, ProjectMember, ProjectActivity, ProjectDocument, ProjectEstimate
from .forms import ProjectForm, ProjectMemberForm, ProjectDocumentForm
from accounts.models import ProjectAccessKey, User

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Главная панель управления проектами"""
    user = request.user
    
    # Доступ только для суперпользователей
    if not user.is_superuser:
        messages.error(request, 'Доступ запрещен. Только суперпользователи могут просматривать главную панель.')
        return redirect('accounts:profile')
    
    # Получаем проекты в зависимости от роли пользователя
    projects = user.get_accessible_projects()
    
    # Статистика
    total_projects = projects.count()
    active_projects = projects.filter(status='in_progress').count()
    total_budget = projects.aggregate(Sum('budget'))['budget__sum'] or Decimal('0')
    total_spent = projects.aggregate(Sum('spent_amount'))['spent_amount__sum'] or Decimal('0')
    
    # Последние активности
    recent_activities = ProjectActivity.objects.filter(
        project__in=projects
    ).select_related('project', 'user')[:10]
    
    context = {
        'user': user,
        'projects': projects[:6],  # Показываем только первые 6 проектов
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'remaining_budget': total_budget - total_spent,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'projects/dashboard.html', context)


class ProjectListView(LoginRequiredMixin, ListView):
    """Список проектов"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        user = self.request.user
        queryset = user.get_accessible_projects()
        
        # Поиск
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        
        # Фильтр по статусу
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('created_by', 'foreman').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Project.Status.choices
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """Детальный вид проекта"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_object(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        
        # Проверяем доступ пользователя к проекту
        if not project.can_user_access(self.request.user):
            raise PermissionError("У вас нет доступа к этому проекту")
        
        return project
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        
        # Участники проекта
        context['members'] = project.members.filter(is_active=True).select_related('user')
        
        # Последние активности
        context['recent_activities'] = project.activities.select_related('user')[:10]
        
        # Документы
        context['documents'] = project.documents.select_related('uploaded_by')[:5]
        
        # Статистика расходов (будет реализована в kanban приложении)
        context['can_manage'] = (
            self.request.user.can_edit_projects() or
            project.created_by == self.request.user or
            project.foreman == self.request.user
        )
        
        return context


@login_required
def create_project(request):
    """Создание нового проекта"""
    if not request.user.can_create_projects():
        messages.error(request, 'У вас нет прав для создания проектов.')
        return redirect('projects:dashboard')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            
            # Добавляем создателя как участника проекта с ролью admin
            ProjectMember.objects.create(
                project=project,
                user=request.user,
                role='admin',
                is_active=True
            )
            
            # Создаем активность
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                activity_type='project_created',
                description=f'Проект "{project.name}" создан'
            )
            
            messages.success(request, f'Проект "{project.name}" успешно создан.')
            return redirect('projects:detail', pk=project.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Создать проект'})


@login_required
def edit_project(request, pk):
    """Редактирование проекта"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем права на редактирование
    if not (request.user.is_admin_role() or 
            project.created_by == request.user or 
            project.foreman == request.user):
        messages.error(request, 'У вас нет прав для редактирования этого проекта.')
        return redirect('projects:detail', pk=pk)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            old_budget = project.budget
            project = form.save()
            
            # Создаем активность при изменении бюджета
            if old_budget != project.budget:
                ProjectActivity.objects.create(
                    project=project,
                    user=request.user,
                    activity_type='budget_updated',
                    description=f'Бюджет изменен с {old_budget} на {project.budget}'
                )
            
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                activity_type='project_updated',
                description=f'Проект "{project.name}" обновлен'
            )
            
            messages.success(request, 'Проект успешно обновлен.')
            return redirect('projects:detail', pk=pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {
        'form': form, 
        'project': project,
        'title': f'Редактировать проект "{project.name}"'
    })


@login_required
@ratelimit(key='user', rate='10/h', method='POST', block=True)
@require_http_methods(["POST"])
def generate_access_key(request, pk):
    """Генерация ключа доступа к проекту"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем права
    if not (request.user.is_admin_role() or 
            project.created_by == request.user or 
            project.foreman == request.user):
        return JsonResponse({'error': 'Недостаточно прав'}, status=403)
    
    try:
        data = json.loads(request.body)
        user_email = data.get('user_email')
        expires_days = data.get('expires_days', 30)
        
        # Находим пользователя
        try:
            assigned_user = User.objects.get(email=user_email) if user_email else None
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        # Создаем или получаем существующий ключ доступа
        if assigned_user:
            # Проверяем, есть ли уже активный ключ для этого пользователя
            existing_key = ProjectAccessKey.objects.filter(
                project_id=project.id,
                assigned_to=assigned_user,
                is_active=True
            ).first()
            
            if existing_key:
                return JsonResponse({
                    'error': f'У пользователя {assigned_user.get_full_name()} уже есть активный ключ доступа к этому проекту'
                }, status=400)
        
        # Создаем новый ключ доступа
        access_key = ProjectAccessKey.objects.create(
            project_id=project.id,
            created_by=request.user,
            assigned_to=assigned_user,
            expires_at=timezone.now() + timezone.timedelta(days=expires_days) if expires_days else None
        )
        
        # Создаем активность
        if assigned_user:
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                activity_type='member_added',
                description=f'Создан ключ доступа для {assigned_user.get_full_name()}'
            )
        
        return JsonResponse({
            'success': True,
            'key': str(access_key.key),
            'expires_at': access_key.expires_at.isoformat() if access_key.expires_at else None
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректные данные'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при создании ключа доступа: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@login_required
def project_members(request, pk):
    """Управление участниками проекта"""
    project = get_object_or_404(Project, pk=pk)
    
    if not project.can_user_access(request.user):
        messages.error(request, 'У вас нет доступа к этому проекту.')
        return redirect('projects:dashboard')
    
    members = project.members.filter(is_active=True).select_related('user')
    access_keys = project.access_keys.filter(is_active=True).select_related('assigned_to')
    
    context = {
        'project': project,
        'members': members,
        'access_keys': access_keys,
        'can_manage': (
            request.user.can_edit_projects() or
            project.created_by == request.user or
            project.foreman == request.user
        )
    }
    
    return render(request, 'projects/project_members.html', context)


@login_required
def project_estimate(request, pk):
    """Смета проекта"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем доступ
    if not project.can_user_access(request.user):
        return HttpResponseForbidden("У вас нет доступа к этому проекту")
    
    # Получаем или создаем смету
    estimate, created = ProjectEstimate.objects.get_or_create(
        project=project,
        defaults={
            'total_amount': project.budget,
            'created_by': request.user
        }
    )
    
    # Обновляем потраченную сумму
    estimate.update_spent_amount()
    
    # Получаем расходы проекта
    from kanban.models import ExpenseItem
    expenses = ExpenseItem.objects.filter(
        project=project
    ).select_related('created_by', 'category').order_by('-created_at')
    
    # Статистика по типам расходов
    expense_stats = expenses.values('task_type').annotate(
        count=Count('id'),
        total_hours=Sum('estimated_hours')
    ).order_by('task_type')
    
    context = {
        'project': project,
        'estimate': estimate,
        'expenses': expenses,
        'expense_stats': expense_stats,
        'can_add_expenses': (
            request.user.is_admin_role() or
            project.created_by == request.user or
            project.foreman == request.user or
            request.user.role == 'contractor'
        )
    }
    
    return render(request, 'projects/project_estimate.html', context)


@login_required
@require_http_methods(["POST"])
def create_estimate(request, pk):
    """Создание или обновление сметы проекта"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем права
    if not (request.user.is_admin_role() or 
            project.created_by == request.user or 
            project.foreman == request.user):
        return JsonResponse({'error': 'Недостаточно прав'}, status=403)
    
    try:
        data = json.loads(request.body)
        total_amount = Decimal(data.get('total_amount', 0))
        
        if total_amount <= 0:
            return JsonResponse({'error': 'Сумма сметы должна быть больше 0'}, status=400)
        
        # Создаем или обновляем смету
        estimate, created = ProjectEstimate.objects.get_or_create(
            project=project,
            defaults={
                'total_amount': total_amount,
                'created_by': request.user
            }
        )
        
        if not created:
            estimate.total_amount = total_amount
            estimate.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Смета успешно создана/обновлена',
            'estimate': {
                'total_amount': str(estimate.total_amount),
                'spent_amount': str(estimate.spent_amount),
                'remaining_amount': str(estimate.remaining_amount),
                'utilization_percent': round(estimate.utilization_percent, 2)
            }
        })
        
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return JsonResponse({'error': 'Неверные данные'}, status=400)
    except Exception as e:
        logger.error(f"Error creating estimate: {e}")
        return JsonResponse({'error': 'Ошибка сервера'}, status=500)

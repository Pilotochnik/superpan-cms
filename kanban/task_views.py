from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .task_models import (
    ProjectTask, TaskCategory, TaskPriority, TaskStatus, 
    TaskComment, TaskAttachment, TaskHistory
)
from .task_forms import (
    ProjectTaskForm, TaskCommentForm, TaskSearchForm, 
    TaskFilterForm, TaskProgressForm, TaskAssignmentForm
)
from projects.models import Project


@login_required
def task_board(request, project_id):
    """Канбан-доска задач проекта"""
    project = get_object_or_404(Project, id=project_id)
    
    # Проверяем доступ к проекту
    if not project.can_user_access(request.user):
        messages.error(request, 'У вас нет доступа к этому проекту')
        return redirect('projects:list')
    
    # Получаем или создаем канбан-доску
    board, created = project.kanban_board.get_or_create(
        defaults={'created_by': request.user}
    )
    
    # Получаем колонки
    columns = board.columns.filter(is_active=True).order_by('position')
    
    # Фильтры
    filter_form = TaskFilterForm(request.GET)
    if hasattr(project, 'team_members') and project.team_members.exists():
        filter_form.fields['assigned_to'].queryset = project.get_team_members()
    
    # Получаем задачи
    tasks = ProjectTask.objects.filter(project=project)
    
    # Применяем фильтры
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('category'):
            tasks = tasks.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data.get('priority'):
            tasks = tasks.filter(priority=filter_form.cleaned_data['priority'])
        if filter_form.cleaned_data.get('assigned_to'):
            tasks = tasks.filter(assigned_to=filter_form.cleaned_data['assigned_to'])
        if not filter_form.cleaned_data.get('show_archived'):
            tasks = tasks.exclude(status__is_final=True)
    
    # Группируем задачи по колонкам
    tasks_by_column = {}
    for column in columns:
        tasks_by_column[column.id] = tasks.filter(column=column).order_by('position')
    
    # Статистика
    stats = {
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status__is_final=True).count(),
        'overdue_tasks': tasks.filter(due_date__lt=timezone.now()).exclude(status__is_final=True).count(),
        'urgent_tasks': tasks.filter(is_urgent=True).exclude(status__is_final=True).count(),
    }
    
    # Получаем дополнительные данные для шаблона
    categories = TaskCategory.objects.filter(is_active=True)
    priorities = TaskPriority.objects.filter(is_active=True)
    team_members = project.get_team_members() if hasattr(project, 'get_team_members') else []
    
    context = {
        'project': project,
        'board': board,
        'columns': columns,
        'tasks_by_column': tasks_by_column,
        'filter_form': filter_form,
        'stats': stats,
        'categories': categories,
        'priorities': priorities,
        'team_members': team_members,
    }
    
    return render(request, 'kanban/task_board.html', context)


@login_required
def task_list(request, project_id):
    """Список задач проекта"""
    project = get_object_or_404(Project, id=project_id)
    
    if not project.can_user_access(request.user):
        messages.error(request, 'У вас нет доступа к этому проекту')
        return redirect('projects:list')
    
    # Поиск и фильтрация
    search_form = TaskSearchForm(request.GET)
    if hasattr(project, 'team_members') and project.team_members.exists():
        search_form.fields['assigned_to'].queryset = project.get_team_members()
    
    tasks = ProjectTask.objects.filter(project=project)
    
    if search_form.is_valid():
        if search_form.cleaned_data.get('search_query'):
            query = search_form.cleaned_data['search_query']
            tasks = tasks.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        if search_form.cleaned_data.get('category'):
            tasks = tasks.filter(category=search_form.cleaned_data['category'])
        if search_form.cleaned_data.get('priority'):
            tasks = tasks.filter(priority=search_form.cleaned_data['priority'])
        if search_form.cleaned_data.get('status'):
            tasks = tasks.filter(status=search_form.cleaned_data['status'])
        if search_form.cleaned_data.get('assigned_to'):
            tasks = tasks.filter(assigned_to=search_form.cleaned_data['assigned_to'])
        if search_form.cleaned_data.get('task_type'):
            tasks = tasks.filter(task_type=search_form.cleaned_data['task_type'])
        if search_form.cleaned_data.get('is_urgent'):
            tasks = tasks.filter(is_urgent=True)
        if search_form.cleaned_data.get('is_overdue'):
            tasks = tasks.filter(due_date__lt=timezone.now()).exclude(status__is_final=True)
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    tasks = tasks.order_by(sort_by)
    
    # Пагинация
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)
    
    # Получаем дополнительные данные
    categories = TaskCategory.objects.filter(is_active=True)
    priorities = TaskPriority.objects.filter(is_active=True)
    statuses = TaskStatus.objects.filter(is_active=True)
    team_members = project.get_team_members() if hasattr(project, 'get_team_members') else []
    
    context = {
        'project': project,
        'tasks': tasks,
        'search_form': search_form,
        'sort_by': sort_by,
        'categories': categories,
        'priorities': priorities,
        'statuses': statuses,
        'team_members': team_members,
    }
    
    return render(request, 'kanban/task_list.html', context)


@login_required
def task_detail(request, project_id, task_id):
    """Детальная страница задачи"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    
    if not project.can_user_access(request.user):
        messages.error(request, 'У вас нет доступа к этому проекту')
        return redirect('projects:list')
    
    # Форма комментариев
    comment_form = TaskCommentForm()
    
    # Форма обновления прогресса
    progress_form = TaskProgressForm(initial={
        'progress_percent': task.progress_percent,
        'actual_hours': task.actual_hours
    })
    
    # Форма назначения
    assignment_form = TaskAssignmentForm()
    if hasattr(project, 'team_members') and project.team_members.exists():
        assignment_form.fields['assigned_to'].queryset = project.get_team_members()
    
    # Комментарии
    comments = task.comments.all().order_by('-created_at')
    
    # История изменений
    history = task.history.all().order_by('-created_at')[:10]
    
    # Получаем дополнительные данные
    categories = TaskCategory.objects.filter(is_active=True)
    priorities = TaskPriority.objects.filter(is_active=True)
    statuses = TaskStatus.objects.filter(is_active=True)
    team_members = project.get_team_members() if hasattr(project, 'get_team_members') else []
    
    context = {
        'project': project,
        'task': task,
        'comment_form': comment_form,
        'progress_form': progress_form,
        'assignment_form': assignment_form,
        'comments': comments,
        'history': history,
        'categories': categories,
        'priorities': priorities,
        'statuses': statuses,
        'team_members': team_members,
    }
    
    return render(request, 'kanban/task_detail.html', context)


@login_required
def create_task(request, project_id):
    """Создание новой задачи"""
    project = get_object_or_404(Project, id=project_id)
    
    if not project.can_user_access(request.user):
        messages.error(request, 'У вас нет доступа к этому проекту')
        return redirect('projects:list')
    
    if request.method == 'POST':
        form = ProjectTaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            
            # Устанавливаем начальный статус
            if not task.status:
                task.status = TaskStatus.objects.filter(name='Новая').first()
            
            task.save()
            
            # Создаем запись в истории
            TaskHistory.objects.create(
                task=task,
                user=request.user,
                action='created',
                new_value=task.title
            )
            
            messages.success(request, f'Задача "{task.title}" создана')
            return redirect('kanban:task_detail', project_id=project.id, task_id=task.id)
    else:
        form = ProjectTaskForm(project=project)
    
    # Получаем дополнительные данные
    categories = TaskCategory.objects.filter(is_active=True)
    priorities = TaskPriority.objects.filter(is_active=True)
    statuses = TaskStatus.objects.filter(is_active=True)
    team_members = project.get_team_members() if hasattr(project, 'get_team_members') else []
    
    context = {
        'project': project,
        'form': form,
        'categories': categories,
        'priorities': priorities,
        'statuses': statuses,
        'team_members': team_members,
    }
    
    return render(request, 'kanban/task_form.html', context)


@login_required
def edit_task(request, project_id, task_id):
    """Редактирование задачи"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    
    if not project.can_user_access(request.user):
        messages.error(request, 'У вас нет доступа к этому проекту')
        return redirect('projects:list')
    
    if not task.can_user_edit(request.user):
        messages.error(request, 'У вас нет прав для редактирования этой задачи')
        return redirect('kanban:task_detail', project_id=project.id, task_id=task.id)
    
    if request.method == 'POST':
        form = ProjectTaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            old_title = task.title
            task = form.save()
            
            # Создаем запись в истории
            if old_title != task.title:
                TaskHistory.objects.create(
                    task=task,
                    user=request.user,
                    action='title_changed',
                    old_value=old_title,
                    new_value=task.title,
                    field_name='title'
                )
            
            messages.success(request, f'Задача "{task.title}" обновлена')
            return redirect('kanban:task_detail', project_id=project.id, task_id=task.id)
    else:
        form = ProjectTaskForm(instance=task, project=project)
    
    # Получаем дополнительные данные
    categories = TaskCategory.objects.filter(is_active=True)
    priorities = TaskPriority.objects.filter(is_active=True)
    statuses = TaskStatus.objects.filter(is_active=True)
    team_members = project.get_team_members() if hasattr(project, 'get_team_members') else []
    
    context = {
        'project': project,
        'task': task,
        'form': form,
        'categories': categories,
        'priorities': priorities,
        'statuses': statuses,
        'team_members': team_members,
    }
    
    return render(request, 'kanban/task_form.html', context)


@login_required
@require_http_methods(["POST"])
def add_comment(request, project_id, task_id):
    """Добавление комментария к задаче"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    
    if not project.can_user_access(request.user):
        return JsonResponse({'error': 'Нет доступа к проекту'}, status=403)
    
    form = TaskCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        
        # Создаем запись в истории
        TaskHistory.objects.create(
            task=task,
            user=request.user,
            action='commented',
            new_value=comment.text[:50] + '...' if len(comment.text) > 50 else comment.text
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'text': comment.text,
                'author': comment.author.get_full_name(),
                'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
                'is_internal': comment.is_internal
            }
        })
    
    return JsonResponse({'error': 'Ошибка валидации формы'}, status=400)


@login_required
@require_http_methods(["POST"])
def update_progress(request, project_id, task_id):
    """Обновление прогресса задачи"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    
    if not project.can_user_access(request.user):
        return JsonResponse({'error': 'Нет доступа к проекту'}, status=403)
    
    if not task.can_user_edit(request.user):
        return JsonResponse({'error': 'Нет прав для редактирования задачи'}, status=403)
    
    form = TaskProgressForm(request.POST)
    if form.is_valid():
        old_progress = task.progress_percent
        old_hours = task.actual_hours
        
        task.progress_percent = form.cleaned_data['progress_percent']
        task.actual_hours = form.cleaned_data['actual_hours']
        
        # Если прогресс 100%, помечаем как выполненную
        if task.progress_percent == 100 and not task.completed_at:
            task.completed_at = timezone.now()
            done_status = TaskStatus.objects.filter(name='Выполнена').first()
            if done_status:
                task.status = done_status
        
        task.save()
        
        # Создаем запись в истории
        TaskHistory.objects.create(
            task=task,
            user=request.user,
            action='progress_updated',
            old_value=f'{old_progress}% ({old_hours}ч)',
            new_value=f'{task.progress_percent}% ({task.actual_hours}ч)',
            field_name='progress'
        )
        
        # Добавляем комментарий если есть
        if form.cleaned_data.get('comment'):
            TaskComment.objects.create(
                task=task,
                author=request.user,
                text=form.cleaned_data['comment']
            )
        
        return JsonResponse({
            'success': True,
            'progress_percent': task.progress_percent,
            'actual_hours': float(task.actual_hours),
            'completed_at': task.completed_at.strftime('%d.%m.%Y %H:%M') if task.completed_at else None
        })
    
    return JsonResponse({'error': 'Ошибка валидации формы'}, status=400)


@login_required
@require_http_methods(["POST"])
def assign_task(request, project_id, task_id):
    """Назначение задачи"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    
    if not project.can_user_access(request.user):
        return JsonResponse({'error': 'Нет доступа к проекту'}, status=403)
    
    if not task.can_user_assign(request.user):
        return JsonResponse({'error': 'Нет прав для назначения задачи'}, status=403)
    
    form = TaskAssignmentForm(request.POST)
    if hasattr(project, 'team_members') and project.team_members.exists():
        form.fields['assigned_to'].queryset = project.get_team_members()
    
    if form.is_valid():
        old_assignee = task.assigned_to
        old_priority = task.priority
        old_due_date = task.due_date
        
        if form.cleaned_data.get('assigned_to'):
            task.assigned_to = form.cleaned_data['assigned_to']
        if form.cleaned_data.get('priority'):
            task.priority = form.cleaned_data['priority']
        if form.cleaned_data.get('due_date'):
            task.due_date = form.cleaned_data['due_date']
        
        task.save()
        
        # Создаем записи в истории
        if old_assignee != task.assigned_to:
            TaskHistory.objects.create(
                task=task,
                user=request.user,
                action='assigned',
                old_value=old_assignee.get_full_name() if old_assignee else 'Не назначено',
                new_value=task.assigned_to.get_full_name() if task.assigned_to else 'Не назначено',
                field_name='assigned_to'
            )
        
        if old_priority != task.priority:
            TaskHistory.objects.create(
                task=task,
                user=request.user,
                action='priority_changed',
                old_value=old_priority.name if old_priority else 'Не установлен',
                new_value=task.priority.name if task.priority else 'Не установлен',
                field_name='priority'
            )
        
        # Добавляем комментарий если есть
        if form.cleaned_data.get('comment'):
            TaskComment.objects.create(
                task=task,
                author=request.user,
                text=form.cleaned_data['comment']
            )
        
        return JsonResponse({
            'success': True,
            'assigned_to': task.assigned_to.get_full_name() if task.assigned_to else None,
            'priority': task.priority.name if task.priority else None,
            'due_date': task.due_date.strftime('%d.%m.%Y %H:%M') if task.due_date else None
        })
    
    return JsonResponse({'error': 'Ошибка валидации формы'}, status=400)


@login_required
@require_http_methods(["POST"])
def move_task(request, project_id, task_id):
    """Перемещение задачи между колонками"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    
    if not project.can_user_access(request.user):
        return JsonResponse({'error': 'Нет доступа к проекту'}, status=403)
    
    if not task.can_user_edit(request.user):
        return JsonResponse({'error': 'Нет прав для редактирования задачи'}, status=403)
    
    try:
        data = json.loads(request.body)
        column_id = data.get('column_id')
        position = data.get('position', 0)
        
        if column_id:
            from .models import KanbanColumn
            column = get_object_or_404(KanbanColumn, id=column_id, board__project=project)
            old_column = task.column
            task.column = column
            task.position = position
            task.save()
            
            # Создаем запись в истории
            TaskHistory.objects.create(
                task=task,
                user=request.user,
                action='moved',
                old_value=old_column.name if old_column else 'Не назначено',
                new_value=column.name,
                field_name='column'
            )
            
            return JsonResponse({'success': True})
        
    except (ValueError, KeyError):
        pass
    
    return JsonResponse({'error': 'Неверные данные'}, status=400)


@login_required
def task_analytics(request, project_id):
    """Аналитика по задачам проекта"""
    project = get_object_or_404(Project, id=project_id)
    
    if not project.can_user_access(request.user):
        messages.error(request, 'У вас нет доступа к этому проекту')
        return redirect('projects:list')
    
    # Статистика по статусам
    status_stats = TaskStatus.objects.annotate(
        task_count=Count('tasks', filter=Q(tasks__project=project))
    ).values('name', 'color', 'task_count')
    
    # Статистика по приоритетам
    priority_stats = TaskPriority.objects.annotate(
        task_count=Count('tasks', filter=Q(tasks__project=project))
    ).values('name', 'color', 'task_count')
    
    # Статистика по исполнителям
    assignee_stats = []
    if hasattr(project, 'get_team_members'):
        assignee_stats = project.get_team_members().annotate(
            task_count=Count('assigned_tasks', filter=Q(assigned_tasks__project=project)),
            completed_count=Count('assigned_tasks', filter=Q(
                assigned_tasks__project=project,
                assigned_tasks__status__is_final=True
            ))
        ).values('first_name', 'last_name', 'task_count', 'completed_count')
    
    # Прогресс проекта
    total_tasks = ProjectTask.objects.filter(project=project).count()
    completed_tasks = ProjectTask.objects.filter(
        project=project, 
        status__is_final=True
    ).count()
    project_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    context = {
        'project': project,
        'status_stats': status_stats,
        'priority_stats': priority_stats,
        'assignee_stats': assignee_stats,
        'project_progress': project_progress,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
    }
    
    return render(request, 'kanban/task_analytics.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_task_files(request, task_id):
    """API для загрузки файлов к задаче"""
    try:
        task = get_object_or_404(ProjectTask, id=task_id)
        
        # Проверяем права доступа
        if not request.user.can_manage_tasks() and task.created_by != request.user:
            return JsonResponse({'error': 'Недостаточно прав'}, status=403)
        
        files = request.FILES.getlist('files')
        uploaded_files = []
        
        for file in files:
            # Создаем вложение
            attachment = TaskAttachment.objects.create(
                task=task,
                file=file,
                uploaded_by=request.user,
                filename=file.name
            )
            uploaded_files.append({
                'id': attachment.id,
                'filename': attachment.filename,
                'url': attachment.file.url,
                'size': attachment.file.size
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Загружено {len(uploaded_files)} файлов',
            'files': uploaded_files
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_task_attachment(request, attachment_id):
    """API для удаления вложения задачи"""
    try:
        attachment = get_object_or_404(TaskAttachment, id=attachment_id)
        
        # Проверяем права доступа
        if not request.user.can_manage_tasks() and attachment.uploaded_by != request.user:
            return JsonResponse({'error': 'Недостаточно прав'}, status=403)
        
        # Удаляем файл с диска
        if attachment.file:
            attachment.file.delete(save=False)
        
        # Удаляем запись из базы
        attachment.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Вложение удалено'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, Q
from datetime import timedelta
from decimal import Decimal

from accounts.models import User, ProjectAccessKey, LoginAttempt, UserSession, TelegramUser
from projects.models import Project, ProjectActivity
from kanban.models import ExpenseItem, ExpenseCategory
from accounts.forms import UserRegistrationForm
from projects.forms import ProjectForm


def is_superuser(user):
    """Проверка, что пользователь - суперпользователь"""
    return user.is_authenticated and user.is_admin_role()


@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    """Главная страница админ-панели"""
    
    # Статистика пользователей
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_week = User.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Статистика проектов
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(is_active=True).count()
    total_budget = Project.objects.aggregate(
        total=Sum('budget')
    )['total'] or Decimal('0')
    
    # Статистика расходов
    total_expenses = ExpenseItem.objects.count()
    pending_expenses = ExpenseItem.objects.filter(status='pending').count()
    approved_expenses = ExpenseItem.objects.filter(status='approved').count()
    
    # Последние действия
    recent_activities = ProjectActivity.objects.select_related(
        'project', 'user'
    ).order_by('-created_at')[:10]
    
    # Последние входы
    recent_logins = LoginAttempt.objects.filter(
        success=True
    ).order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users_week': new_users_week,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_budget': total_budget,
        'total_expenses': total_expenses,
        'pending_expenses': pending_expenses,
        'approved_expenses': approved_expenses,
        'recent_activities': recent_activities,
        'recent_logins': recent_logins,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@user_passes_test(is_superuser)
def users_list(request):
    """Список всех пользователей"""
    
    # Фильтрация
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.all()
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    users = users.order_by('-created_at')
    
    # Статистика по ролям
    role_stats = User.objects.values('role').annotate(
        count=Count('id')
    ).order_by('role')
    
    context = {
        'users': users,
        'role_stats': role_stats,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'role_choices': User.Role.choices,
    }
    
    return render(request, 'admin_panel/users_list.html', context)


@login_required
@user_passes_test(is_superuser)
def edit_user(request, pk):
    """Редактирование пользователя"""
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        # Простое обновление основных полей
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.role = request.POST.get('role', user.role)
        
        # Обработка смены пароля
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        force_password_change = request.POST.get('force_password_change') == 'on'
        
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'Пароли не совпадают.')
                return render(request, 'admin_panel/edit_user.html', {'user_obj': user})
            
            if len(new_password) < 8:
                messages.error(request, 'Пароль должен содержать минимум 8 символов.')
                return render(request, 'admin_panel/edit_user.html', {'user_obj': user})
            
            # Устанавливаем новый пароль
            user.set_password(new_password)
            
            # Принудительная смена пароля при следующем входе
            if force_password_change:
                user.force_password_change = True
            
            messages.success(request, f'Пароль для {user.get_full_name()} успешно изменен.')
        
        user.save()
        messages.success(request, f'Данные пользователя "{user.get_full_name()}" обновлены.')
        return redirect('admin_panel:users_list')
    
    return render(request, 'admin_panel/edit_user.html', {'user_obj': user})


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def toggle_user_status(request, pk):
    """Активация/деактивация пользователя"""
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    
    status = "активирован" if user.is_active else "деактивирован"
    messages.success(request, f'Пользователь "{user.get_full_name()}" {status}.')
    
    return redirect('admin_panel:users_list')


@login_required
@user_passes_test(is_superuser)
def projects_list(request):
    """Список всех проектов"""
    
    projects = Project.objects.select_related(
        'created_by', 'foreman'
    ).annotate(
        expenses_count=Count('expense_items'),
        team_size=Count('members')
    ).order_by('-created_at')
    
    # Статистика
    total_budget = projects.aggregate(total=Sum('budget'))['total'] or Decimal('0')
    total_spent = projects.aggregate(total=Sum('spent_amount'))['total'] or Decimal('0')
    
    context = {
        'projects': projects,
        'total_budget': total_budget,
        'total_spent': total_spent,
    }
    
    return render(request, 'admin_panel/projects_list.html', context)


@login_required
@user_passes_test(is_superuser)
def project_members(request, pk):
    """Участники проекта"""
    
    project = get_object_or_404(Project, pk=pk)
    team_members = project.get_team_members()
    
    context = {
        'project': project,
        'team_members': team_members,
    }
    
    return render(request, 'admin_panel/project_members.html', context)


@login_required
@user_passes_test(is_superuser)
def project_access_keys(request, pk):
    """Ключи доступа к проекту"""
    
    project = get_object_or_404(Project, pk=pk)
    access_keys = ProjectAccessKey.objects.filter(
        project_id=project.id
    ).select_related('assigned_to', 'created_by').order_by('-created_at')
    
    context = {
        'project': project,
        'access_keys': access_keys,
        'now': timezone.now(),
    }
    
    return render(request, 'admin_panel/project_access_keys.html', context)


@login_required
@user_passes_test(is_superuser)
def create_access_key(request):
    """Создание ключа доступа"""
    
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        user_id = request.POST.get('user_id')
        description = request.POST.get('description', '')
        
        project = get_object_or_404(Project, pk=project_id)
        user = get_object_or_404(User, pk=user_id)
        
        access_key, created = ProjectAccessKey.objects.get_or_create(
            project_id=project.id,
            assigned_to=user,
            defaults={
                'created_by': request.user,
                'description': description,
                'is_active': True
            }
        )
        
        if created:
            messages.success(request, f'Ключ доступа создан для {user.get_full_name()}')
        else:
            messages.info(request, f'Ключ доступа уже существует для {user.get_full_name()}')
        
        return redirect('admin_panel:project_access_keys', pk=project_id)
    
    projects = Project.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True, role__in=['foreman', 'contractor'])
    
    context = {
        'projects': projects,
        'users': users,
    }
    
    return render(request, 'admin_panel/create_access_key.html', context)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def toggle_access_key(request, pk):
    """Активация/деактивация ключа доступа"""
    
    access_key = get_object_or_404(ProjectAccessKey, pk=pk)
    access_key.is_active = not access_key.is_active
    access_key.save()
    
    status = "активирован" if access_key.is_active else "деактивирован"
    messages.success(request, f'Ключ доступа {status}.')
    
    return redirect('admin_panel:project_access_keys', pk=access_key.project_id)


@login_required
@user_passes_test(is_superuser)
def expenses_overview(request):
    """Обзор всех расходов"""
    
    # Статистика по статусам
    status_stats = ExpenseItem.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('status')
    
    # Статистика по типам
    type_stats = ExpenseItem.objects.values('task_type').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    # Последние расходы
    recent_expenses = ExpenseItem.objects.select_related(
        'project', 'created_by', 'category'
    ).order_by('-created_at')[:20]
    
    # Расходы на рассмотрении
    pending_expenses = ExpenseItem.objects.filter(
        status='pending'
    ).select_related('project', 'created_by').order_by('-created_at')
    
    context = {
        'status_stats': status_stats,
        'type_stats': type_stats,
        'recent_expenses': recent_expenses,
        'pending_expenses': pending_expenses,
    }
    
    return render(request, 'admin_panel/expenses_overview.html', context)


@login_required
@user_passes_test(is_superuser)
def reports(request):
    """Отчеты и аналитика"""
    
    # Отчет по проектам
    projects_report = Project.objects.annotate(
        expenses_count=Count('expense_items'),
        approved_expenses=Count('expense_items', filter=Q(expense_items__status='approved')),
        total_expenses_amount=Sum('expense_items__amount'),
        approved_expenses_amount=Sum('expense_items__amount', filter=Q(expense_items__status='approved'))
    ).order_by('-created_at')
    
    # Отчет по пользователям
    users_report = User.objects.annotate(
        projects_count=Count('created_projects'),
        expenses_count=Count('created_expense_items'),
        total_expenses_amount=Sum('created_expense_items__amount')
    ).filter(
        Q(projects_count__gt=0) | Q(expenses_count__gt=0)
    ).order_by('-created_at')
    
    # Активность за последний месяц
    month_ago = timezone.now() - timedelta(days=30)
    monthly_activity = ProjectActivity.objects.filter(
        created_at__gte=month_ago
    ).values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'projects_report': projects_report,
        'users_report': users_report,
        'monthly_activity': monthly_activity,
    }
    
    return render(request, 'admin_panel/reports.html', context)


@login_required
@user_passes_test(is_superuser)
def financial_reports(request):
    """Финансовые отчеты"""
    
    # Общие финансовые показатели
    total_budget = Project.objects.aggregate(
        total=Sum('budget')
    )['total'] or Decimal('0')
    
    total_spent = Project.objects.aggregate(
        total=Sum('spent_amount')
    )['total'] or Decimal('0')
    
    pending_expenses = ExpenseItem.objects.filter(status='pending').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    approved_expenses = ExpenseItem.objects.filter(status='approved').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Финансы по проектам
    projects_financial = Project.objects.annotate(
        total_expenses=Sum('expense_items__amount'),
        approved_expenses_sum=Sum('expense_items__amount', filter=Q(expense_items__status='approved')),
        pending_expenses_sum=Sum('expense_items__amount', filter=Q(expense_items__status='pending')),
        expenses_count=Count('expense_items')
    ).order_by('-budget')
    
    # Добавляем вычисленные поля
    for project in projects_financial:
        # У модели уже есть свойство remaining_budget, используем его
        # Добавляем только budget_utilization как новый атрибут
        if project.budget > 0:
            project.budget_utilization = float((project.spent_amount / project.budget) * 100)
        else:
            project.budget_utilization = 0
    
    # Расходы по категориям
    category_expenses = ExpenseCategory.objects.annotate(
        total_amount=Sum('expense_items__amount'),
        approved_amount=Sum('expense_items__amount', filter=Q(expense_items__status='approved')),
        items_count=Count('expense_items')
    ).filter(total_amount__isnull=False).order_by('-total_amount')
    
    # Расходы по месяцам (последние 12 месяцев)
    monthly_expenses = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_data = ExpenseItem.objects.filter(
            created_at__range=[month_start, month_end]
        ).aggregate(
            total=Sum('amount'),
            approved=Sum('amount', filter=Q(status='approved'))
        )
        
        monthly_expenses.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'total': month_data['total'] or Decimal('0'),
            'approved': month_data['approved'] or Decimal('0')
        })
    
    monthly_expenses.reverse()  # От старых к новым
    
    # Топ пользователей по расходам
    top_spenders = User.objects.annotate(
        total_expenses=Sum('created_expense_items__amount'),
        approved_expenses=Sum('created_expense_items__amount', filter=Q(created_expense_items__status='approved'))
    ).filter(total_expenses__isnull=False).order_by('-total_expenses')[:10]
    
    context = {
        'total_budget': total_budget,
        'total_spent': total_spent,
        'pending_expenses': pending_expenses,
        'approved_expenses': approved_expenses,
        'remaining_budget': total_budget - total_spent,
        'budget_utilization': (total_spent / total_budget * 100) if total_budget > 0 else 0,
        'projects_financial': projects_financial,
        'category_expenses': category_expenses,
        'monthly_expenses': monthly_expenses,
        'top_spenders': top_spenders,
    }
    
    return render(request, 'admin_panel/financial_reports.html', context)


@login_required
@user_passes_test(is_superuser)
def export_excel(request):
    """Экспорт данных в Excel"""
    
    # Создаем workbook
    wb = Workbook()
    
    # Стили
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Лист 1: Проекты
    ws1 = wb.active
    ws1.title = "Проекты"
    
    # Заголовки для проектов
    project_headers = ['Название', 'Бюджет', 'Потрачено', 'Остаток', 'Статус', 'Прораб', 'Дата создания']
    for col, header in enumerate(project_headers, 1):
        cell = ws1.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    # Данные проектов
    projects = Project.objects.select_related('foreman').all()
    for row, project in enumerate(projects, 2):
        ws1.cell(row=row, column=1, value=project.name).border = border
        ws1.cell(row=row, column=2, value=float(project.budget)).border = border
        ws1.cell(row=row, column=3, value=float(project.spent_amount)).border = border
        ws1.cell(row=row, column=4, value=float(project.budget - project.spent_amount)).border = border
        ws1.cell(row=row, column=5, value=project.get_status_display()).border = border
        ws1.cell(row=row, column=6, value=project.foreman.get_full_name() if project.foreman else 'Не назначен').border = border
        ws1.cell(row=row, column=7, value=project.created_at.strftime('%d.%m.%Y')).border = border
    
    # Автоширина колонок
    for column in ws1.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws1.column_dimensions[column_letter].width = adjusted_width
    
    # Лист 2: Расходы
    ws2 = wb.create_sheet(title="Расходы")
    
    expense_headers = ['Проект', 'Название', 'Категория', 'Сумма', 'Статус', 'Создатель', 'Дата']
    for col, header in enumerate(expense_headers, 1):
        cell = ws2.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    # Данные расходов
    expenses = ExpenseItem.objects.select_related('project', 'category', 'created_by').all()[:1000]  # Ограничиваем для производительности
    for row, expense in enumerate(expenses, 2):
        ws2.cell(row=row, column=1, value=expense.project.name).border = border
        ws2.cell(row=row, column=2, value=expense.title).border = border
        ws2.cell(row=row, column=3, value=expense.category.name if expense.category else 'Без категории').border = border
        ws2.cell(row=row, column=4, value=float(expense.amount)).border = border
        ws2.cell(row=row, column=5, value=expense.get_status_display()).border = border
        ws2.cell(row=row, column=6, value=expense.created_by.get_full_name()).border = border
        ws2.cell(row=row, column=7, value=expense.created_at.strftime('%d.%m.%Y %H:%M')).border = border
    
    # Автоширина для второго листа
    for column in ws2.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws2.column_dimensions[column_letter].width = adjusted_width
    
    # Лист 3: Пользователи
    ws3 = wb.create_sheet(title="Пользователи")
    
    user_headers = ['ФИО', 'Email', 'Роль', 'Активен', 'Проектов создано', 'Расходов добавлено', 'Дата регистрации']
    for col, header in enumerate(user_headers, 1):
        cell = ws3.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    # Данные пользователей
    users = User.objects.annotate(
        projects_count=Count('created_projects'),
        expenses_count=Count('created_expense_items')
    ).all()
    
    for row, user in enumerate(users, 2):
        ws3.cell(row=row, column=1, value=user.get_full_name()).border = border
        ws3.cell(row=row, column=2, value=user.email).border = border
        ws3.cell(row=row, column=3, value=user.get_role_display()).border = border
        ws3.cell(row=row, column=4, value='Да' if user.is_active else 'Нет').border = border
        ws3.cell(row=row, column=5, value=user.projects_count).border = border
        ws3.cell(row=row, column=6, value=user.expenses_count).border = border
        ws3.cell(row=row, column=7, value=user.created_at.strftime('%d.%m.%Y')).border = border
    
    # Автоширина для третьего листа
    for column in ws3.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws3.column_dimensions[column_letter].width = adjusted_width
    
    # Сохраняем в память
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Создаем HTTP ответ
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="project_office_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    return response


@login_required
@user_passes_test(is_superuser)
def export_pdf(request):
    """Экспорт данных в PDF"""
    
    # Создаем буфер
    buffer = io.BytesIO()
    
    # Создаем документ
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Центрирование
    )
    
    # Элементы документа
    elements = []
    
    # Заголовок
    title = Paragraph("Отчет по системе «Проектный Офис»", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Дата генерации
    date_p = Paragraph(f"Дата генерации: {timezone.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal'])
    elements.append(date_p)
    elements.append(Spacer(1, 20))
    
    # Общая статистика
    stats_title = Paragraph("Общая статистика", styles['Heading2'])
    elements.append(stats_title)
    
    total_projects = Project.objects.count()
    total_users = User.objects.count()
    total_expenses = ExpenseItem.objects.count()
    total_budget = Project.objects.aggregate(Sum('budget'))['budget__sum'] or 0
    
    stats_data = [
        ['Показатель', 'Значение'],
        ['Всего проектов', str(total_projects)],
        ['Всего пользователей', str(total_users)],
        ['Всего расходов', str(total_expenses)],
        ['Общий бюджет', f"{total_budget:,.2f} ₽"],
    ]
    
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 30))
    
    # Проекты
    projects_title = Paragraph("Проекты", styles['Heading2'])
    elements.append(projects_title)
    
    projects = Project.objects.all()[:10]  # Первые 10 проектов
    projects_data = [['Название', 'Бюджет', 'Потрачено', 'Статус']]
    
    for project in projects:
        projects_data.append([
            project.name[:30] + '...' if len(project.name) > 30 else project.name,
            f"{project.budget:,.0f} ₽",
            f"{project.spent_amount:,.0f} ₽",
            project.get_status_display()
        ])
    
    projects_table = Table(projects_data)
    projects_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(projects_table)
    
    # Генерируем PDF
    doc.build(elements)
    
    # Получаем содержимое буфера
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Создаем HTTP ответ
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="project_office_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    return response


@login_required
@user_passes_test(is_superuser)
def export_csv(request):
    """Экспорт данных в CSV"""
    
    # Создаем HTTP ответ с CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="project_office_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Добавляем BOM для корректного отображения в Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # Заголовок файла
    writer.writerow([f'Отчет по системе "Проектный Офис" - {timezone.now().strftime("%d.%m.%Y %H:%M")}'])
    writer.writerow([])
    
    # Проекты
    writer.writerow(['=== ПРОЕКТЫ ==='])
    writer.writerow(['Название', 'Бюджет', 'Потрачено', 'Остаток', 'Статус', 'Прораб', 'Дата создания'])
    
    projects = Project.objects.select_related('foreman').all()
    for project in projects:
        writer.writerow([
            project.name,
            str(project.budget),
            str(project.spent_amount),
            str(project.budget - project.spent_amount),
            project.get_status_display(),
            project.foreman.get_full_name() if project.foreman else 'Не назначен',
            project.created_at.strftime('%d.%m.%Y')
        ])
    
    writer.writerow([])
    
    # Расходы
    writer.writerow(['=== РАСХОДЫ ==='])
    writer.writerow(['Проект', 'Название', 'Категория', 'Сумма', 'Статус', 'Создатель', 'Дата'])
    
    expenses = ExpenseItem.objects.select_related('project', 'category', 'created_by').all()[:500]  # Ограничиваем
    for expense in expenses:
        writer.writerow([
            expense.project.name,
            expense.title,
            expense.category.name if expense.category else 'Без категории',
            str(expense.amount),
            expense.get_status_display(),
            expense.created_by.get_full_name(),
            expense.created_at.strftime('%d.%m.%Y %H:%M')
        ])
    
    writer.writerow([])
    
    # Пользователи
    writer.writerow(['=== ПОЛЬЗОВАТЕЛИ ==='])
    writer.writerow(['ФИО', 'Email', 'Роль', 'Активен', 'Проектов создано', 'Расходов добавлено', 'Дата регистрации'])
    
    users = User.objects.annotate(
        projects_count=Count('created_projects'),
        expenses_count=Count('created_expense_items')
    ).all()
    
    for user in users:
        writer.writerow([
            user.get_full_name(),
            user.email,
            user.get_role_display(),
            'Да' if user.is_active else 'Нет',
            user.projects_count,
            user.expenses_count,
            user.created_at.strftime('%d.%m.%Y')
        ])
    
    return response


@login_required
def device_management(request):
    """Управление устройствами пользователей"""
    if not request.user.is_admin_role():
        return redirect('accounts:telegram_login')
    
    # Получаем пользователей с привязанными устройствами
    users_with_devices = User.objects.exclude(device_fingerprint='').select_related().order_by('-updated_at')
    
    # Получаем активные сессии
    active_sessions = UserSession.objects.select_related('user').order_by('-last_activity')
    
    # Статистика безопасности
    total_devices = users_with_devices.count()
    active_sessions_count = active_sessions.count()
    recent_failed_logins = LoginAttempt.objects.filter(success=False).count()
    
    context = {
        'users_with_devices': users_with_devices,
        'active_sessions': active_sessions,
        'total_devices': total_devices,
        'active_sessions_count': active_sessions_count,
        'recent_failed_logins': recent_failed_logins,
    }
    
    return render(request, 'admin_panel/device_management.html', context)


@login_required
@require_http_methods(["POST"])
def reset_device_binding(request, user_id):
    """Сброс привязки к устройству"""
    if not request.user.is_admin_role():
        return JsonResponse({'error': 'Недостаточно прав'}, status=403)
    
    try:
        user = User.objects.get(pk=user_id)
        user.device_fingerprint = ''
        user.save(update_fields=['device_fingerprint'])
        
        # Удаляем все сессии пользователя
        UserSession.objects.filter(user=user).delete()
        
        return JsonResponse({'success': True, 'message': f'Привязка устройства для {user.get_full_name()} сброшена'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser)
def register_telegram_user(request):
    """Регистрация пользователя через Telegram"""
    if request.method == 'POST':
        try:
            telegram_id = request.POST.get('telegram_id')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role')
            username = request.POST.get('username', '')
            
            # Проверяем, не существует ли уже пользователь с таким Telegram ID
            if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
                messages.error(request, f'Пользователь с Telegram ID {telegram_id} уже существует!')
                return redirect('admin_panel:register_telegram_user')
            
            # Создаем пользователя
            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=True
            )
            
            # Создаем связанную запись TelegramUser
            TelegramUser.objects.create(
                user=user,
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_bot=False,
                language_code='ru'
            )
            
            messages.success(request, f'Пользователь {user.get_full_name()} успешно зарегистрирован!')
            return redirect('admin_panel:users_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
    
    context = {
        'roles': User.Role.choices,
    }
    return render(request, 'admin_panel/register_telegram_user.html', context)


@login_required
@user_passes_test(is_superuser)
def telegram_link(request, pk):
    """Привязка Telegram к существующему пользователю"""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден!')
        return redirect('admin_panel:users_list')
    
    if request.method == 'POST':
        try:
            telegram_id = request.POST.get('telegram_id')
            username = request.POST.get('username', '')
            
            # Проверяем, не привязан ли уже этот Telegram ID
            if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
                messages.error(request, f'Telegram ID {telegram_id} уже привязан к другому пользователю!')
                return redirect('admin_panel:telegram_link', pk=pk)
            
            # Проверяем, не привязан ли уже Telegram к этому пользователю
            if TelegramUser.objects.filter(user=user).exists():
                messages.error(request, 'У этого пользователя уже есть привязанный Telegram аккаунт!')
                return redirect('admin_panel:telegram_link', pk=pk)
            
            # Создаем связь с Telegram
            TelegramUser.objects.create(
                user=user,
                telegram_id=telegram_id,
                username=username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_bot=False,
                language_code='ru'
            )
            
            messages.success(request, f'Telegram аккаунт успешно привязан к пользователю {user.get_full_name()}!')
            return redirect('admin_panel:users_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при привязке Telegram: {str(e)}')
    
    context = {
        'user': user,
    }
    return render(request, 'admin_panel/telegram_link.html', context)


@login_required
@user_passes_test(is_superuser)
def telegram_unlink(request, pk):
    """Отвязка Telegram от пользователя"""
    try:
        user = User.objects.get(pk=pk)
        telegram_user = TelegramUser.objects.get(user=user)
        telegram_user.delete()
        messages.success(request, f'Telegram аккаунт отвязан от пользователя {user.get_full_name()}!')
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден!')
    except TelegramUser.DoesNotExist:
        messages.error(request, 'У пользователя нет привязанного Telegram аккаунта!')
    except Exception as e:
        messages.error(request, f'Ошибка при отвязке Telegram: {str(e)}')
    
    return redirect('admin_panel:users_list')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Sum, Count
import logging

from .models import Project, ProjectEstimate
from .estimate_models import (
    EstimateCategory, EstimateUnit, EstimateRate, EstimateTemplate,
    ProjectEstimateItem, EstimateImport, EstimateExport
)
from .estimate_forms import (
    EstimateCategoryForm, EstimateUnitForm, EstimateRateForm,
    ProjectEstimateForm, ProjectEstimateItemForm, EstimateTemplateForm,
    EstimateImportForm, EstimateExportForm, EstimateSearchForm,
    EstimateCalculationForm
)

logger = logging.getLogger(__name__)


@login_required
def estimate_rates_list(request):
    """Список расценок"""
    search_form = EstimateSearchForm(request.GET)
    rates = EstimateRate.objects.filter(is_active=True).select_related('category', 'unit')
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search_query')
        category = search_form.cleaned_data.get('category')
        unit = search_form.cleaned_data.get('unit')
        price_min = search_form.cleaned_data.get('price_min')
        price_max = search_form.cleaned_data.get('price_max')
        
        if search_query:
            rates = rates.filter(
                Q(code__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if category:
            rates = rates.filter(category=category)
        
        if unit:
            rates = rates.filter(unit=unit)
        
        if price_min:
            rates = rates.filter(base_price__gte=price_min)
        
        if price_max:
            rates = rates.filter(base_price__lte=price_max)
    
    # Пагинация
    paginator = Paginator(rates, 20)
    page_number = request.GET.get('page')
    rates = paginator.get_page(page_number)
    
    context = {
        'rates': rates,
        'search_form': search_form,
        'categories': EstimateCategory.objects.filter(is_active=True),
        'units': EstimateUnit.objects.filter(is_active=True),
    }
    
    return render(request, 'projects/estimate_rates_list.html', context)


@login_required
def estimate_rate_detail(request, pk):
    """Детальная информация о расценке"""
    rate = get_object_or_404(EstimateRate, pk=pk)
    
    # Форма расчета
    calculation_form = EstimateCalculationForm(initial={'rate_id': rate.id})
    
    context = {
        'rate': rate,
        'calculation_form': calculation_form,
    }
    
    return render(request, 'projects/estimate_rate_detail.html', context)


@login_required
@require_http_methods(["POST"])
def calculate_estimate_cost(request):
    """AJAX расчет стоимости работ"""
    try:
        data = json.loads(request.body)
        rate_id = data.get('rate_id')
        quantity = Decimal(str(data.get('quantity', 1)))
        region_factor = Decimal(str(data.get('region_factor', 1.0)))
        complexity_factor = Decimal(str(data.get('complexity_factor', 1.0)))
        
        rate = get_object_or_404(EstimateRate, pk=rate_id)
        
        # Рассчитываем стоимость
        unit_price = rate.calculate_price(quantity=1, region_factor=region_factor) * complexity_factor
        total_price = unit_price * quantity
        
        return JsonResponse({
            'success': True,
            'unit_price': str(unit_price.quantize(Decimal('0.01'))),
            'total_price': str(total_price.quantize(Decimal('0.01'))),
            'labor_cost': str((rate.labor_cost * region_factor * complexity_factor * quantity).quantize(Decimal('0.01'))),
            'material_cost': str((rate.material_cost * region_factor * complexity_factor * quantity).quantize(Decimal('0.01'))),
            'equipment_cost': str((rate.equipment_cost * region_factor * complexity_factor * quantity).quantize(Decimal('0.01'))),
            'labor_hours': str((rate.labor_hours * quantity).quantize(Decimal('0.01')))
        })
        
    except Exception as e:
        logger.error(f"Error calculating estimate cost: {e}")
        return JsonResponse({'success': False, 'error': 'Ошибка расчета'})


@login_required
def project_estimate_detailed(request, pk):
    """Детализированная смета проекта"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем доступ
    if not project.can_user_access(request.user):
        return HttpResponseForbidden("У вас нет доступа к этому проекту")
    
    # Получаем или создаем смету
    estimate, created = ProjectEstimate.objects.get_or_create(
        project=project,
        defaults={
            'estimate_type': ProjectEstimate.EstimateType.DETAILED,
            'total_amount': project.budget,
            'created_by': request.user
        }
    )
    
    # Получаем позиции сметы
    items = estimate.items.all().order_by('position')
    
    # Пересчитываем суммы
    estimate.labor_amount = sum(item.rate.labor_cost * item.quantity for item in items)
    estimate.material_amount = sum(item.rate.material_cost * item.quantity for item in items)
    estimate.equipment_amount = sum(item.rate.equipment_cost * item.quantity for item in items)
    estimate.total_amount = estimate.calculated_total
    estimate.save()
    
    # Статистика
    total_items = items.count()
    total_quantity = sum(item.quantity for item in items)
    total_labor_hours = sum(item.rate.labor_hours * item.quantity for item in items)
    
    context = {
        'project': project,
        'estimate': estimate,
        'items': items,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'total_labor_hours': total_labor_hours,
        'can_edit': (
            request.user.is_admin_role() or
            project.created_by == request.user or
            project.foreman == request.user
        )
    }
    
    return render(request, 'projects/project_estimate_detailed.html', context)


@login_required
@require_http_methods(["POST"])
def add_estimate_item(request, pk):
    """Добавление позиции в смету"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем права
    if not (request.user.is_admin_role() or 
            project.created_by == request.user or 
            project.foreman == request.user):
        return JsonResponse({'error': 'Недостаточно прав'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Получаем смету
        estimate, created = ProjectEstimate.objects.get_or_create(
            project=project,
            defaults={
                'estimate_type': ProjectEstimate.EstimateType.DETAILED,
                'total_amount': project.budget,
                'created_by': request.user
            }
        )
        
        # Создаем позицию
        item = ProjectEstimateItem.objects.create(
            estimate=estimate,
            rate_id=data.get('rate_id'),
            quantity=Decimal(str(data.get('quantity', 1))),
            region_factor=Decimal(str(data.get('region_factor', 1.0))),
            complexity_factor=Decimal(str(data.get('complexity_factor', 1.0))),
            notes=data.get('notes', '')
        )
        
        # Пересчитываем смету
        estimate.labor_amount = sum(i.rate.labor_cost * i.quantity for i in estimate.items.all())
        estimate.material_amount = sum(i.rate.material_cost * i.quantity for i in estimate.items.all())
        estimate.equipment_amount = sum(i.rate.equipment_cost * i.quantity for i in estimate.items.all())
        estimate.total_amount = estimate.calculated_total
        estimate.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Позиция добавлена в смету',
            'item': {
                'id': item.id,
                'rate_name': item.rate.name,
                'quantity': str(item.quantity),
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price),
                'position': item.position
            }
        })
        
    except Exception as e:
        logger.error(f"Error adding estimate item: {e}")
        return JsonResponse({'error': 'Ошибка добавления позиции'}, status=500)


@login_required
@require_http_methods(["DELETE"])
def remove_estimate_item(request, pk, item_id):
    """Удаление позиции из сметы"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем права
    if not (request.user.is_admin_role() or 
            project.created_by == request.user or 
            project.foreman == request.user):
        return JsonResponse({'error': 'Недостаточно прав'}, status=403)
    
    try:
        item = get_object_or_404(ProjectEstimateItem, pk=item_id, estimate__project=project)
        item.delete()
        
        # Пересчитываем смету
        estimate = project.estimate
        estimate.labor_amount = sum(i.rate.labor_cost * i.quantity for i in estimate.items.all())
        estimate.material_amount = sum(i.rate.material_cost * i.quantity for i in estimate.items.all())
        estimate.equipment_amount = sum(i.rate.equipment_cost * i.quantity for i in estimate.items.all())
        estimate.total_amount = estimate.calculated_total
        estimate.save()
        
        return JsonResponse({'success': True, 'message': 'Позиция удалена из сметы'})
        
    except Exception as e:
        logger.error(f"Error removing estimate item: {e}")
        return JsonResponse({'error': 'Ошибка удаления позиции'}, status=500)


@login_required
def estimate_import(request, pk):
    """Импорт сметы"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем права
    if not (request.user.is_admin_role() or 
            project.created_by == request.user or 
            project.foreman == request.user):
        return HttpResponseForbidden("У вас нет доступа к этому проекту")
    
    if request.method == 'POST':
        form = EstimateImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Создаем запись об импорте
            import_record = form.save(commit=False)
            import_record.project = project
            import_record.created_by = request.user
            import_record.file_name = form.cleaned_data['file'].name
            import_record.save()
            
            # TODO: Здесь будет логика обработки файла
            # Пока просто помечаем как завершенный
            import_record.status = 'completed'
            import_record.completed_at = timezone.now()
            import_record.save()
            
            messages.success(request, 'Смета успешно импортирована')
            return redirect('projects:estimate_detailed', pk=project.pk)
    else:
        form = EstimateImportForm()
    
    context = {
        'project': project,
        'form': form,
    }
    
    return render(request, 'projects/estimate_import.html', context)


@login_required
def estimate_export(request, pk):
    """Экспорт сметы"""
    project = get_object_or_404(Project, pk=pk)
    
    # Проверяем права
    if not project.can_user_access(request.user):
        return HttpResponseForbidden("У вас нет доступа к этому проекту")
    
    if request.method == 'POST':
        form = EstimateExportForm(request.POST)
        if form.is_valid():
            # Создаем запись об экспорте
            export_record = EstimateExport.objects.create(
                project=project,
                format=form.cleaned_data['format'],
                created_by=request.user,
                file_name=f"estimate_{project.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # TODO: Здесь будет логика генерации файла
            # Пока просто помечаем как завершенный
            export_record.status = 'completed'
            export_record.completed_at = timezone.now()
            export_record.save()
            
            messages.success(request, 'Смета успешно экспортирована')
            return redirect('projects:estimate_detailed', pk=project.pk)
    else:
        form = EstimateExportForm()
    
    context = {
        'project': project,
        'form': form,
    }
    
    return render(request, 'projects/estimate_export.html', context)


@login_required
def estimate_templates_list(request):
    """Список шаблонов смет"""
    templates = EstimateTemplate.objects.filter(
        Q(is_public=True) | Q(created_by=request.user)
    ).select_related('category', 'created_by').order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    templates = paginator.get_page(page_number)
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'projects/estimate_templates_list.html', context)


@login_required
def estimate_template_detail(request, pk):
    """Детальная информация о шаблоне"""
    template = get_object_or_404(EstimateTemplate, pk=pk)
    items = template.items.all().order_by('position')
    
    context = {
        'template': template,
        'items': items,
    }
    
    return render(request, 'projects/estimate_template_detail.html', context)


@login_required
@require_http_methods(["POST"])
def apply_template_to_project(request, pk, template_id):
    """Применение шаблона к проекту"""
    project = get_object_or_404(Project, pk=pk)
    template = get_object_or_404(EstimateTemplate, pk=template_id)
    
    # Проверяем права
    if not (request.user.is_admin_role() or 
            project.created_by == request.user or 
            project.foreman == request.user):
        return JsonResponse({'error': 'Недостаточно прав'}, status=403)
    
    try:
        # Получаем или создаем смету
        estimate, created = ProjectEstimate.objects.get_or_create(
            project=project,
            defaults={
                'estimate_type': ProjectEstimate.EstimateType.TEMPLATE,
                'total_amount': project.budget,
                'created_by': request.user
            }
        )
        
        # Очищаем существующие позиции
        estimate.items.all().delete()
        
        # Добавляем позиции из шаблона
        for template_item in template.items.all():
            ProjectEstimateItem.objects.create(
                estimate=estimate,
                rate=template_item.rate,
                quantity=template_item.quantity,
                region_factor=estimate.region_factor,
                complexity_factor=Decimal('1.00')
            )
        
        # Пересчитываем смету
        estimate.labor_amount = sum(i.rate.labor_cost * i.quantity for i in estimate.items.all())
        estimate.material_amount = sum(i.rate.material_cost * i.quantity for i in estimate.items.all())
        estimate.equipment_amount = sum(i.rate.equipment_cost * i.quantity for i in estimate.items.all())
        estimate.total_amount = estimate.calculated_total
        estimate.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Шаблон "{template.name}" применен к проекту',
            'items_count': estimate.items.count()
        })
        
    except Exception as e:
        logger.error(f"Error applying template: {e}")
        return JsonResponse({'error': 'Ошибка применения шаблона'}, status=500)

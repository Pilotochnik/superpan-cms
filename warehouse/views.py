from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import WarehouseCategory, WarehouseItem, WarehouseTransaction, ProjectEquipment
from .forms import (
    WarehouseCategoryForm, WarehouseItemForm, WarehouseTransactionForm, 
    ProjectEquipmentForm, WarehouseSearchForm
)
from projects.models import Project

@login_required
def warehouse_dashboard(request):
    """Главная страница склада"""
    # Статистика
    total_items = WarehouseItem.objects.filter(is_active=True).count()
    low_stock_items = WarehouseItem.objects.filter(is_active=True, current_quantity__lte=F('min_quantity')).count()
    total_materials = WarehouseItem.objects.filter(is_active=True, item_type='MATERIAL').count()
    total_equipment = WarehouseItem.objects.filter(is_active=True, item_type='EQUIPMENT').count()
    
    # Последние транзакции
    recent_transactions = WarehouseTransaction.objects.select_related('item', 'project', 'created_by').order_by('-created_at')[:10]
    
    # Товары с низким остатком
    low_stock_items_list = WarehouseItem.objects.filter(
        is_active=True, 
        current_quantity__lte=F('min_quantity')
    ).order_by('current_quantity')[:10]
    
    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'total_materials': total_materials,
        'total_equipment': total_equipment,
        'recent_transactions': recent_transactions,
        'low_stock_items_list': low_stock_items_list,
    }
    
    return render(request, 'warehouse/dashboard.html', context)

@login_required
def warehouse_items_list(request):
    """Список товаров склада"""
    form = WarehouseSearchForm(request.GET)
    items = WarehouseItem.objects.filter(is_active=True).select_related('category')
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        item_type = form.cleaned_data.get('item_type')
        category = form.cleaned_data.get('category')
        low_stock_only = form.cleaned_data.get('low_stock_only')
        
        if search_query:
            items = items.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        if item_type:
            items = items.filter(item_type=item_type)
        
        if category:
            items = items.filter(category=category)
        
        if low_stock_only:
            items = items.filter(current_quantity__lte=F('min_quantity'))
    
    # Пагинация
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'items': page_obj,
    }
    
    return render(request, 'warehouse/items_list.html', context)

@login_required
def warehouse_item_detail(request, item_id):
    """Детальная информация о товаре"""
    item = get_object_or_404(WarehouseItem, id=item_id)
    transactions = item.transactions.select_related('project', 'created_by').order_by('-created_at')[:20]
    
    context = {
        'item': item,
        'transactions': transactions,
    }
    
    return render(request, 'warehouse/item_detail.html', context)

@login_required
def warehouse_item_create(request):
    """Создание нового товара"""
    if request.method == 'POST':
        form = WarehouseItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()
            messages.success(request, _('Товар успешно создан.'))
            return redirect('warehouse:item_detail', item_id=item.id)
    else:
        form = WarehouseItemForm()
    
    context = {
        'form': form,
        'title': _('Создание товара'),
    }
    
    return render(request, 'warehouse/item_form.html', context)

@login_required
def warehouse_item_edit(request, item_id):
    """Редактирование товара"""
    item = get_object_or_404(WarehouseItem, id=item_id)
    
    if request.method == 'POST':
        form = WarehouseItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, _('Товар успешно обновлен.'))
            return redirect('warehouse:item_detail', item_id=item.id)
    else:
        form = WarehouseItemForm(instance=item)
    
    context = {
        'form': form,
        'title': _('Редактирование товара'),
        'item': item,
    }
    
    return render(request, 'warehouse/item_form.html', context)

@login_required
def warehouse_transaction_create(request):
    """Создание транзакции склада"""
    if request.method == 'POST':
        form = WarehouseTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, _('Транзакция успешно создана.'))
            return redirect('warehouse:transactions_list')
    else:
        form = WarehouseTransactionForm()
    
    context = {
        'form': form,
        'title': _('Создание транзакции'),
    }
    
    return render(request, 'warehouse/transaction_form.html', context)

@login_required
def warehouse_transactions_list(request):
    """Список транзакций склада"""
    transactions = WarehouseTransaction.objects.select_related(
        'item', 'project', 'created_by'
    ).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'transactions': page_obj,
    }
    
    return render(request, 'warehouse/transactions_list.html', context)

@login_required
def project_equipment_list(request, project_id):
    """Список оборудования проекта"""
    project = get_object_or_404(Project, id=project_id)
    equipment = project.equipment.select_related('item', 'created_by').order_by('-created_at')
    
    context = {
        'project': project,
        'equipment': equipment,
    }
    
    return render(request, 'warehouse/project_equipment_list.html', context)

@login_required
def project_equipment_add(request, project_id):
    """Добавление оборудования к проекту"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = ProjectEquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.project = project
            equipment.created_by = request.user
            equipment.save()
            messages.success(request, _('Оборудование успешно добавлено к проекту.'))
            return redirect('warehouse:project_equipment_list', project_id=project.id)
    else:
        form = ProjectEquipmentForm()
    
    context = {
        'form': form,
        'project': project,
        'title': _('Добавление оборудования к проекту'),
    }
    
    return render(request, 'warehouse/project_equipment_form.html', context)

@login_required
@require_http_methods(["POST"])
def update_equipment_photo(request, equipment_id):
    """Обновление фото оборудования"""
    equipment = get_object_or_404(ProjectEquipment, id=equipment_id)
    
    photo_type = request.POST.get('photo_type')
    if photo_type == 'before':
        equipment.equipment_photo_before = request.FILES.get('photo')
    elif photo_type == 'after':
        equipment.equipment_photo_after = request.FILES.get('photo')
    
    equipment.save()
    
    return JsonResponse({'success': True, 'message': _('Фото успешно обновлено.')})

@login_required
def warehouse_categories_list(request):
    """Список категорий склада"""
    categories = WarehouseCategory.objects.filter(is_active=True).order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'warehouse/categories_list.html', context)

@login_required
def warehouse_category_create(request):
    """Создание категории склада"""
    if request.method == 'POST':
        form = WarehouseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Категория успешно создана.'))
            return redirect('warehouse:categories_list')
    else:
        form = WarehouseCategoryForm()
    
    context = {
        'form': form,
        'title': _('Создание категории'),
    }
    
    return render(request, 'warehouse/category_form.html', context)

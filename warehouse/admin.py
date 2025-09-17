from django.contrib import admin
from django.utils.html import format_html
from .models import WarehouseCategory, WarehouseItem, WarehouseTransaction, ProjectEquipment

@admin.register(WarehouseCategory)
class WarehouseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(WarehouseItem)
class WarehouseItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'item_type', 'category', 'current_quantity', 
        'unit', 'purchase_price', 'selling_price', 'is_low_stock', 'is_active'
    ]
    list_filter = ['item_type', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    ordering = ['name']
    readonly_fields = ['current_quantity', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'item_type', 'category')
        }),
        ('Количество', {
            'fields': ('unit', 'current_quantity', 'min_quantity')
        }),
        ('Цены', {
            'fields': ('purchase_price', 'selling_price')
        }),
        ('Фото оборудования', {
            'fields': ('equipment_photo_before', 'equipment_photo_after'),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(WarehouseTransaction)
class WarehouseTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'item', 'transaction_type', 'quantity', 'price', 
        'total_amount', 'project', 'created_at', 'created_by'
    ]
    list_filter = ['transaction_type', 'created_at', 'project']
    search_fields = ['item__name', 'description', 'reference_number']
    ordering = ['-created_at']
    readonly_fields = ['total_amount', 'created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('item', 'transaction_type', 'quantity', 'price', 'total_amount')
        }),
        ('Связи', {
            'fields': ('project', 'created_by')
        }),
        ('Дополнительно', {
            'fields': ('description', 'reference_number')
        }),
        ('Системные поля', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProjectEquipment)
class ProjectEquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'item', 'quantity_used', 'start_date', 
        'end_date', 'created_at'
    ]
    list_filter = ['project', 'start_date', 'end_date', 'created_at']
    search_fields = ['project__name', 'item__name', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

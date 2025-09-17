from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Project, ProjectMember, ProjectActivity, ProjectDocument, ProjectEstimate
from .estimate_models import (
    EstimateCategory, EstimateUnit, EstimateRate, EstimateTemplate,
    ProjectEstimateItem, EstimateImport, EstimateExport
)


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'budget', 'spent_amount', 'foreman', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [ProjectMemberInline]
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'description', 'status')
        }),
        (_('Финансы'), {
            'fields': ('budget', 'spent_amount')
        }),
        (_('Управление'), {
            'fields': ('created_by', 'foreman', 'is_active')
        }),
        (_('Сроки'), {
            'fields': ('start_date', 'end_date')
        }),
    )


@admin.register(ProjectActivity)
class ProjectActivityAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'description', 'created_at')
    list_filter = ('created_at', 'project')
    search_fields = ('project__name', 'user__email', 'description')
    readonly_fields = ('created_at',)


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'document_type', 'uploaded_by', 'created_at')
    list_filter = ('document_type', 'created_at')
    search_fields = ('name', 'project__name')
    readonly_fields = ('created_at',)


@admin.register(ProjectEstimate)
class ProjectEstimateAdmin(admin.ModelAdmin):
    list_display = ('project', 'estimate_type', 'total_amount', 'spent_amount', 'is_approved', 'created_at')
    list_filter = ('estimate_type', 'is_approved', 'created_at')
    search_fields = ('project__name', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EstimateCategory)
class EstimateCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(EstimateUnit)
class EstimateUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'short_name')
    ordering = ('name',)


@admin.register(EstimateRate)
class EstimateRateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'unit', 'base_price', 'is_active')
    list_filter = ('category', 'unit', 'is_active', 'created_at')
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EstimateTemplate)
class EstimateTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_public', 'created_by', 'created_at')
    list_filter = ('is_public', 'category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


class ProjectEstimateItemInline(admin.TabularInline):
    model = ProjectEstimateItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(ProjectEstimateItem)
class ProjectEstimateItemAdmin(admin.ModelAdmin):
    list_display = ('estimate', 'rate', 'quantity', 'unit_price', 'total_price')
    list_filter = ('rate__category', 'created_at')
    search_fields = ('rate__name', 'rate__code')
    readonly_fields = ('total_price', 'created_at', 'updated_at')


@admin.register(EstimateImport)
class EstimateImportAdmin(admin.ModelAdmin):
    list_display = ('project', 'source', 'file_name', 'status', 'imported_items', 'created_by', 'created_at')
    list_filter = ('source', 'status', 'created_at')
    search_fields = ('project__name', 'file_name')
    readonly_fields = ('created_at', 'completed_at')


@admin.register(EstimateExport)
class EstimateExportAdmin(admin.ModelAdmin):
    list_display = ('project', 'format', 'file_name', 'status', 'created_by', 'created_at')
    list_filter = ('format', 'status', 'created_at')
    search_fields = ('project__name', 'file_name')
    readonly_fields = ('created_at', 'completed_at')
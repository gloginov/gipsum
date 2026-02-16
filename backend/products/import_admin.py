from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .import_models import ProductImport, ProductImportLog
from .import_service import ProductImportService


@admin.register(ProductImport)
class ProductImportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'status_colored', 'import_type', 
        'total_rows', 'created_count', 'updated_count', 
        'error_count', 'created_at', 'download_log_button'
    ]
    list_filter = ['status', 'import_type', 'created_at']
    search_fields = ['name', 'error_message']
    readonly_fields = [
        'status', 'total_rows', 'created_count', 'updated_count',
        'error_count', 'skipped_count', 'processed_at', 'log_file_link',
        'error_message_preview'
    ]
    date_hierarchy = 'created_at'
    actions = ['run_import_action']
    
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'file', 'import_type', 'created_by')
        }),
        ('Настройки импорта', {
            'fields': (
                'skip_existing', 'update_images', 'default_category'
            ),
        }),
        ('Результаты импорта', {
            'fields': (
                'status', 'total_rows', 'created_count', 'updated_count',
                'error_count', 'skipped_count', 'processed_at',
                'error_message_preview', 'log_file_link'
            ),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by', 'default_category')
    
    def status_colored(self, obj):
        colors = {
            'pending': '#ff9800',
            'processing': '#2196f3',
            'completed': '#4caf50',
            'partial': '#ff9800',
            'error': '#f44336',
        }
        color = colors.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Статус'
    
    def error_message_preview(self, obj):
        if obj.error_message:
            return format_html(
                '<div style="color: #f44336; max-width: 600px; white-space: pre-wrap;">{}</div>',
                obj.error_message[:1000]
            )
        return '-'
    error_message_preview.short_description = 'Сообщение об ошибке'
    
    def log_file_link(self, obj):
        if obj.log_file:
            return format_html(
                '<a href="{}" target="_blank" style="padding: 5px 10px; background: #4caf50; color: white; text-decoration: none; border-radius: 3px;">📥 Скачать лог</a>',
                obj.log_file.url
            )
        return 'Лог не создан'
    log_file_link.short_description = 'Файл лога'
    
    def download_log_button(self, obj):
        if obj.log_file:
            return format_html(
                '<a href="{}" target="_blank" class="button">Скачать</a>',
                obj.log_file.url
            )
        return '-'
    download_log_button.short_description = 'Лог'
    
    def run_import_action(self, request, queryset):
        """Запуск импорта для выбранных записей"""
        count = 0
        for import_task in queryset.filter(status='pending'):
            try:
                service = ProductImportService(import_task)
                service.process()
                count += 1
            except Exception as e:
                messages.error(request, f'Ошибка в импорте "{import_task.name}": {e}')
        
        if count:
            messages.success(request, f'Успешно обработано импортов: {count}')
    run_import_action.short_description = '🚀 Запустить импорт выбранных'
    
    def save_model(self, request, obj, form, change):
        """При сохранении автоматически запускаем импорт если статус pending"""
        if not change:  # Только при создании
            obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
        
        # Автозапуск импорта
        if obj.status == 'pending':
            try:
                service = ProductImportService(obj)
                service.process()
                
                # Обновляем объект из базы
                obj.refresh_from_db()
                
                if obj.status == 'completed':
                    messages.success(request, f'✅ Импорт "{obj.name}" успешно завершен! Создано: {obj.created_count}, Обновлено: {obj.updated_count}')
                elif obj.status == 'partial':
                    messages.warning(request, f'⚠️ Импорт "{obj.name}" частично завершен. Создано: {obj.created_count}, Ошибок: {obj.error_count}')
                else:
                    messages.error(request, f'❌ Импорт "{obj.name}" завершен с ошибками. Подробности в логе.')
                    
            except Exception as e:
                messages.error(request, f'❌ Критическая ошибка импорта: {str(e)[:200]}')


@admin.register(ProductImportLog)
class ProductImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'import_task_link', 'row_number', 'sku', 
        'product_name_short', 'status_colored', 'message_short'
    ]
    list_filter = ['status', 'import_task__name', 'import_task__created_at']
    search_fields = ['sku', 'product_name', 'message']
    readonly_fields = [
        'import_task', 'row_number', 'sku', 'product_name', 
        'status', 'message', 'raw_data_pretty'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def import_task_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:products_productimport_change', args=[obj.import_task_id])
        return format_html('<a href="{}">{}</a>', url, obj.import_task.name)
    import_task_link.short_description = 'Импорт'
    
    def product_name_short(self, obj):
        return obj.product_name[:50] + '...' if len(obj.product_name) > 50 else obj.product_name
    product_name_short.short_description = 'Товар'
    
    def status_colored(self, obj):
        colors = {
            'success': '#4caf50',
            'created': '#4caf50',
            'updated': '#2196f3',
            'error': '#f44336',
            'skipped': '#9e9e9e',
        }
        return format_html(
            '<span style="color: {};">● {}</span>',
            colors.get(obj.status, '#9e9e9e'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Статус'
    
    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Сообщение'
    
    def raw_data_pretty(self, obj):
        import json
        return format_html('<pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">{}</pre>', 
                          json.dumps(obj.raw_data, indent=2, ensure_ascii=False))
    raw_data_pretty.short_description = 'Исходные данные'
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import FeedbackMessage, FeedbackSettings


@admin.register(FeedbackMessage)
class FeedbackMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'email', 'message_type', 'status', 'status_colored',
        'has_attachment_icon', 'created_at', 'preview_short'
    ]
    list_filter = [
        'message_type', 'status', 'privacy_policy_accepted',
        'created_at', 'email_sent'
    ]
    search_fields = ['name', 'email', 'phone', 'subject', 'message']
    readonly_fields = [
        'created_at', 'updated_at', 'ip_address', 'user_agent',
        'referer', 'privacy_policy_url', 'email_sent', 'email_error',
        'attachment_preview', 'answered_at', 'answered_by'
    ]
    date_hierarchy = 'created_at'
    list_editable = ['status']
    actions = ['mark_as_answered', 'mark_as_closed', 'resend_email']
    
    fieldsets = (
        ('Контактная информация', {
            'fields': ('name', 'email', 'phone', 'message_type')
        }),
        ('Сообщение', {
            'fields': ('subject', 'message', 'attachment', 'attachment_preview')
        }),
        ('Политика конфиденциальности', {
            'fields': ('privacy_policy_accepted', 'privacy_policy_url'),
            'classes': ('collapse',),
        }),
        ('Мета-информация', {
            'fields': ('ip_address', 'user_agent', 'referer', 'created_at'),
            'classes': ('collapse',),
        }),
        ('Обработка', {
            'fields': (
                'status', 'admin_notes', 'answered_at', 'answered_by',
                'email_sent', 'email_error'
            ),
        }),
    )
    
    def status_colored(self, obj):
        colors = {
            'new': '#ff9800',
            'in_progress': '#2196f3',
            'answered': '#4caf50',
            'closed': '#9e9e9e',
            'spam': '#f44336',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 12px;">{}</span>',
            colors.get(obj.status, '#9e9e9e'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Статус'
    
    def has_attachment_icon(self, obj):
        if obj.has_attachment:
            return format_html(
                '<span style="color: #4caf50; font-size: 16px;">📎</span>'
            )
        return '-'
    has_attachment_icon.short_description = 'Файл'
    
    def preview_short(self, obj):
        text = obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
        return text
    preview_short.short_description = 'Превью сообщения'
    
    def attachment_preview(self, obj):
        if not obj.has_attachment:
            return 'Нет вложений'
        
        if obj.is_image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 500px; border-radius: 8px;" /><br>'
                '<a href="{}" target="_blank">Открыть оригинал</a>',
                obj.attachment.url,
                obj.attachment.url
            )
        elif obj.is_pdf:
            return format_html(
                '<span style="font-size: 48px;">📄</span><br>'
                '<strong>{}</strong><br>'
                '<a href="{}" target="_blank">Скачать PDF</a>',
                obj.attachment_filename,
                obj.attachment.url
            )
        else:
            return format_html(
                '<strong>{}</strong><br>'
                '<a href="{}" target="_blank">Скачать файл</a>',
                obj.attachment_filename,
                obj.attachment.url
            )
    attachment_preview.short_description = 'Просмотр вложения'
    
    def mark_as_answered(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status='answered',
            answered_at=timezone.now(),
            answered_by=request.user
        )
    mark_as_answered.short_description = 'Отметить как отвеченные'
    
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = 'Закрыть обращения'
    
    def resend_email(self, request, queryset):
        from .views import FeedbackViewSet
        viewset = FeedbackViewSet()
        for feedback in queryset:
            viewset._send_notifications(feedback)
    resend_email.short_description = 'Переотправить уведомления'


@admin.register(FeedbackSettings)
class FeedbackSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Email уведомления', {
            'fields': ('email_recipients',)
        }),
        ('Telegram уведомления', {
            'fields': ('notify_telegram', 'telegram_bot_token', 'telegram_chat_id'),
            'classes': ('collapse',),
        }),
        ('Настройки файлов', {
            'fields': ('max_file_size', 'allowed_extensions')
        }),
        ('Безопасность', {
            'fields': ('enable_captcha',)
        }),
    )
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return False
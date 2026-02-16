from django.contrib import admin
from django.utils.html import format_html
from .models import Gallery, GalleryImage


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 1
    fields = [
        'image', 'preview', 'title', 'alt_text', 
        'order', 'is_active', 'caption'
    ]
    readonly_fields = ['preview']
    
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px; border-radius: 4px;" />',
                obj.image.url
            )
        return "-"
    preview.short_description = 'Превью'


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'display_type', 'images_count', 
        'is_active', 'order', 'created_at'
    ]
    list_filter = ['display_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    inlines = [GalleryImageInline]
    
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'description', 'display_type', 'is_active', 'order')
        }),
        ('Настройки сетки', {
            'fields': ('columns', 'gap'),
            'classes': ('collapse',),
            'description': 'Настройки для типа "Сетка" и "Плитка"'
        }),
        ('Настройки слайдера/карусели', {
            'fields': (
                'autoplay', 'autoplay_speed', 'infinite_loop',
                'show_arrows', 'show_dots',
                'slides_to_show', 'slides_to_scroll'
            ),
            'classes': ('collapse',),
            'description': 'Настройки для типа "Слайдер" и "Карусель"'
        }),
        ('Настройки изображений', {
            'fields': ('image_height', 'object_fit', 'border_radius', 'shadow'),
            'classes': ('collapse',),
        }),
    )
    
    def images_count(self, obj):
        count = obj.images.filter(is_active=True).count()
        return format_html(
            '<span style="background: #79aec8; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
            count
        )
    images_count.short_description = 'Изображений'


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = [
        'preview', 'gallery', 'title', 'order', 
        'is_active', 'created_at'
    ]
    list_filter = ['gallery', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'gallery__name']
    list_editable = ['order', 'is_active']
    raw_id_fields = ['gallery']
    
    fieldsets = (
        ('Изображение', {
            'fields': ('gallery', 'image', 'preview_large', 'alt_text', 'order', 'is_active')
        }),
        ('Контент', {
            'fields': ('title', 'description', 'caption'),
            'classes': ('collapse',),
        }),
        ('Кнопка (для слайдера)', {
            'fields': ('button_text', 'button_link'),
            'classes': ('collapse',),
        }),
        ('Стили слайда', {
            'fields': (
                'overlay_color', 'overlay_opacity', 'text_position'
            ),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['preview_large']
    
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url
            )
        return "-"
    preview.short_description = 'Превью'
    
    def preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 400px; border-radius: 8px;" />',
                obj.image.url
            )
        return "-"
    preview_large.short_description = 'Превью'
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_main', 'alt_text', 'order', 'preview']
    readonly_fields = ['preview']
    
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url
            )
        return "-"
    preview.short_description = 'Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'product_count', 'is_active', 'order']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    raw_id_fields = ['parent']
    
    def product_count(self, obj):
        count = obj.products.filter(is_available=True).count()
        return format_html(
            '<a href="/admin/products/product/?categories__id={}">{} товаров</a>',
            obj.id, count
        )
    product_count.short_description = 'Товаров'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'price', 'old_price', 'stock', 
        'main_category', 'is_available', 'is_featured', 'created_at'
    ]
    list_filter = [
        'is_available', 'is_featured', 'is_new', 'is_bestseller',
        'categories', 'created_at'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['categories']  # Удобный виджет для ManyToMany
    raw_id_fields = ['main_category']
    inlines = [ProductImageInline]
    list_editable = ['price', 'stock', 'is_available', 'is_featured']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'sku', 'categories', 'main_category')
        }),
        ('Описание', {
            'fields': ('short_description', 'description')
        }),
        ('Цены', {
            'fields': (('price', 'old_price'), 'purchase_price'),
            'description': 'Основная цена и цена со скидкой'
        }),
        ('Наличие', {
            'fields': ('stock', 'stock_alert_threshold', 'is_available')
        }),
        ('Флаги', {
            'fields': (('is_featured', 'is_new', 'is_bestseller'),)
        }),
        ('Характеристики', {
            'fields': ('attributes',),
            'classes': ('collapse',)
        }),
        ('Размеры и вес', {
            'fields': (('weight', 'width', 'height', 'depth'),),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )
    # Импорт и регистрация моделей импорта (УДАЛИТЕ старый код и замените на этот)
try:
    from .import_admin import ProductImportAdmin, ProductImportLogAdmin
    from .import_models import ProductImport, ProductImportLog
    
    # Регистрируем только если ещё не зарегистрировано
    if ProductImport not in admin.site._registry:
        admin.site.register(ProductImport, ProductImportAdmin)
    if ProductImportLog not in admin.site._registry:
        admin.site.register(ProductImportLog, ProductImportLogAdmin)
        
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Import modules not loaded: {e}")
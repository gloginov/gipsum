from django.contrib import admin
from .models import Order, OrderItem, PaymentMethod, ShippingMethod


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'total']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'commission_percent', 'is_active', 'sort_order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'sort_order', 'commission_percent']
    search_fields = ['name', 'code']
    prepopulated_fields = {'code': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description')
        }),
        ('Настройки', {
            'fields': ('commission_percent', 'is_active', 'sort_order', 'icon')
        }),
    )


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'cost', 'free_from', 'estimated_days', 'is_active', 'sort_order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'sort_order', 'cost']
    search_fields = ['name', 'code']
    prepopulated_fields = {'code': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description')
        }),
        ('Стоимость', {
            'fields': ('cost', 'free_from')
        }),
        ('Настройки', {
            'fields': ('estimated_days', 'is_active', 'sort_order')
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'first_name', 'last_name', 
        'total', 'status', 'paid', 'payment_method', 'shipping_method', 'email_sent', 'created_at'
    ]
    list_filter = ['status', 'paid', 'email_sent', 'created_at', 'payment_method', 'shipping_method']
    search_fields = ['order_number', 'email', 'first_name', 'last_name']
    readonly_fields = [
        'order_number', 'subtotal', 'shipping_cost', 'tax', 'total',
        'email_sent', 'email_sent_at'
    ]
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'status', 'paid', 'paid_at', 'email_sent', 'email_sent_at')
        }),
        ('Customer', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping', {
            'fields': ('address', 'city', 'postal_code', 'country', 'shipping_method')
        }),
        ('Payment', {
            'fields': ('payment_method', 'subtotal', 'shipping_cost', 'tax', 'total')
        }),
        ('Notes', {
            'fields': ('customer_note', 'admin_note')
        }),
    )
    actions = ['resend_confirmation_email']

    def resend_confirmation_email(self, request, queryset):
        for order in queryset:
            order.email_sent = False
            order.save()
            order.send_confirmation_email()
        self.message_user(request, f"Emails resent for {queryset.count()} orders")
    resend_confirmation_email.short_description = "Resend confirmation emails"

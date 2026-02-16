from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'first_name', 'last_name', 
        'total', 'status', 'paid', 'email_sent', 'created_at'
    ]
    list_filter = ['status', 'paid', 'email_sent', 'created_at']
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
            'fields': ('address', 'city', 'postal_code', 'country')
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
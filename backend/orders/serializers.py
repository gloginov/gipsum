from rest_framework import serializers
from .models import Order, OrderItem, PaymentMethod, ShippingMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'code', 'description', 'commission_percent', 'icon']


class ShippingMethodSerializer(serializers.ModelSerializer):
    cost_display = serializers.CharField(source='get_cost_display', read_only=True)

    class Meta:
        model = ShippingMethod
        fields = ['id', 'name', 'code', 'description', 'cost', 'free_from', 'estimated_days', 'cost_display']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'product_price', 'quantity', 'total']


class OrderListSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(source='get_payment_method_display', read_only=True)
    shipping_method_name = serializers.CharField(source='get_shipping_method_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'total', 'paid', 
            'payment_method', 'payment_method_name',
            'shipping_method', 'shipping_method_name',
            'email_sent', 'created_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment_method_name = serializers.CharField(source='get_payment_method_display', read_only=True)
    shipping_method_name = serializers.CharField(source='get_shipping_method_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'first_name', 'last_name', 
            'email', 'phone', 'address', 'city', 'postal_code', 'country',
            'payment_method', 'payment_method_name',
            'shipping_method', 'shipping_method_name',
            'paid', 'paid_at', 'subtotal', 'shipping_cost',
            'tax', 'total', 'customer_note', 'admin_note', 'items',
            'email_sent', 'email_sent_at', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    payment_method_id = serializers.IntegerField(write_only=True, required=False)
    shipping_method_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'address', 'city', 'postal_code', 'country',
            'payment_method_id', 'shipping_method_id', 'customer_note'
        ]


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Добавлен недостающий сериализатор для обновления статуса"""
    class Meta:
        model = Order
        fields = ['status', 'admin_note']

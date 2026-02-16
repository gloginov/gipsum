from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'product_price', 'quantity', 'total']


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'total', 'paid', 'email_sent', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'first_name', 'last_name', 
            'email', 'phone', 'address', 'city', 'postal_code', 'country',
            'payment_method', 'paid', 'paid_at', 'subtotal', 'shipping_cost',
            'tax', 'total', 'customer_note', 'admin_note', 'items',
            'email_sent', 'email_sent_at', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'address', 'city', 'postal_code', 'country',
            'payment_method', 'customer_note'
        ]


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Добавлен недостающий сериализатор для обновления статуса"""
    class Meta:
        model = Order
        fields = ['status', 'admin_note']
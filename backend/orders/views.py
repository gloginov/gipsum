from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, OrderItem
from .serializers import (
    OrderListSerializer, 
    OrderDetailSerializer, 
    OrderCreateSerializer,
    OrderStatusUpdateSerializer
)
from cart.cart import CartService


class OrderViewSet(viewsets.ModelViewSet):
    """
    Заказы:
    - list, retrieve: только для авторизованных (свои заказы)
    - create: только для авторизованных
    - update, partial_update, destroy: только админ
    """
    queryset = Order.objects.all()
    lookup_field = 'order_number'
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'my_orders']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Пользователь видит только свои заказы, админ - все"""
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(email=self.request.user.email)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        """Создание заказа - только для авторизованных пользователей"""
        cart = CartService(request)
        
        if cart.get_count() == 0:
            return Response(
                {'error': 'Cart is empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Проверяем, что email совпадает с email пользователя
        # или используем email пользователя
        order_data = serializer.validated_data
        if not order_data.get('email'):
            order_data['email'] = request.user.email
        
        # Расчет стоимости
        subtotal = Decimal(cart.get_total())
        shipping_cost = Decimal('0') if subtotal > 100 else Decimal('10')
        tax = subtotal * Decimal('0.08')
        total = subtotal + shipping_cost + tax
        
        # Создание заказа
        order = Order.objects.create(
            **order_data,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total
        )
        
        # Создание элементов заказа
        for item in cart.get_items():
            product = get_object_or_404(Product, id=item['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=item['product_name'],
                product_price=Decimal(item['price']),
                quantity=item['quantity']
            )
            
            # Уменьшаем остаток на складе
            if product.stock >= item['quantity']:
                product.stock -= item['quantity']
                product.save()
        
        # Очистка корзины
        cart.clear()
        
        # Отправка email
        email_sent = order.send_confirmation_email()
        
        # Уведомление админу
        self._notify_admins(order)
        
        response_data = OrderDetailSerializer(order).data
        response_data['email_sent'] = email_sent
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    def _notify_admins(self, order):
        """Уведомление администраторов о новом заказе"""
        try:
            admin_message = f"""
Новый заказ #{order.order_number}

Клиент: {order.get_full_name()}
Email: {order.email}
Телефон: {order.phone}
Сумма: {order.total} ₽
Товаров: {order.items.count()}

Адрес: {order.address}, {order.city}, {order.postal_code}

https://api-gipsum.docker/admin/orders/order/{order.id}/change/
"""
            send_mail(
                subject=f'[ADMIN] Новый заказ #{order.order_number}',
                message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.ADMIN_EMAILS,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Admin notification error: {e}")

    @action(detail=True, methods=['patch'])
    def update_status(self, request, order_number=None):
        """Обновление статуса - только админ"""
        order = self.get_object()
        old_status = order.status
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        if old_status != order.status:
            self._send_status_update_email(order)
        
        return Response(OrderDetailSerializer(order).data)

    def _send_status_update_email(self, order):
        """Отправка уведомления об изменении статуса"""
        status_messages = {
            'processing': 'Ваш заказ обрабатывается',
            'shipped': 'Ваш заказ отправлен!',
            'delivered': 'Заказ доставлен!',
            'cancelled': 'Заказ отменен',
        }
        
        subject = status_messages.get(order.status, f'Обновление заказа #{order.order_number}')
        
        message = f"""
Здравствуйте, {order.get_full_name()}!

Статус вашего заказа #{order.order_number} изменен на: {order.get_status_display()}

{'Ваш заказ передан в доставку.' if order.status == 'shipped' else ''}
{'Спасибо за покупку!' if order.status == 'delivered' else ''}

С уважением,
Gipsum Shop
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Status email error: {e}")

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Заказы текущего пользователя"""
        orders = self.get_queryset().filter(email=request.user.email).order_by('-created_at')
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resend_email(self, request, order_number=None):
        """Повторная отправка письма - админ или владелец заказа"""
        order = self.get_object()
        
        # Проверяем права
        if not request.user.is_staff and order.email != request.user.email:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        success = order.send_confirmation_email()
        
        if success:
            return Response({'message': 'Email sent successfully'})
        return Response(
            {'error': 'Failed to send email or already sent'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
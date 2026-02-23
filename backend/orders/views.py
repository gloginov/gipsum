from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, OrderItem, PaymentMethod, ShippingMethod
from .serializers import (
    OrderListSerializer, 
    OrderDetailSerializer, 
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
    PaymentMethodSerializer,
    ShippingMethodSerializer
)
from cart.cart import CartService
from products.models import Product
from config.views import CsrfExemptAPIView




class PaymentMethodViewSet(CsrfExemptAPIView, viewsets.ReadOnlyModelViewSet):
    """API для способов оплаты (только активные)"""
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [AllowAny]


class ShippingMethodViewSet(CsrfExemptAPIView, viewsets.ReadOnlyModelViewSet):
    """API для способов доставки (только активные)"""
    queryset = ShippingMethod.objects.filter(is_active=True)
    serializer_class = ShippingMethodSerializer
    permission_classes = [AllowAny]


class OrderViewSet(CsrfExemptAPIView, viewsets.ModelViewSet):
    """
    Заказы:
    - list, retrieve: авторизованные (свои) + админ (все)
    - create: авторизованные
    - update, partial_update, destroy: только админ
    """
    queryset = Order.objects.all()
    lookup_field = 'order_number'

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'my_orders']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'update_status', 'resend_email']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Пользователь видит только свои заказы, админ - все"""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        # Для авторизованных — по email
        if user.is_authenticated:
            return Order.objects.filter(email=user.email)
        return Order.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        """Создание заказа из корзины"""
        cart = CartService(request)

        if cart.get_count() == 0:
            return Response(
                {'error': 'Cart is empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_data = serializer.validated_data

        # Используем email пользователя, если не передан
        if not order_data.get('email'):
            order_data['email'] = request.user.email

        # Получаем способы оплаты и доставки
        payment_method_id = request.data.get('payment_method_id')
        shipping_method_id = request.data.get('shipping_method_id')

        payment_method = None
        shipping_method = None

        if payment_method_id:
            try:
                payment_method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
            except PaymentMethod.DoesNotExist:
                return Response(
                    {'error': 'Invalid payment method'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if shipping_method_id:
            try:
                shipping_method = ShippingMethod.objects.get(id=shipping_method_id, is_active=True)
            except ShippingMethod.DoesNotExist:
                return Response(
                    {'error': 'Invalid shipping method'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Расчет стоимости
        subtotal = Decimal(str(cart.get_total()))

        # Расчет доставки
        shipping_cost = Decimal('0')
        if shipping_method:
            if shipping_method.free_from and subtotal >= shipping_method.free_from:
                shipping_cost = Decimal('0')
            else:
                shipping_cost = shipping_method.cost
        else:
            # Дефолтная логика если способ доставки не выбран
            shipping_cost = Decimal('0') if subtotal > Decimal('100') else Decimal('10')

        tax = subtotal * Decimal('0.08')
        total = subtotal + shipping_cost + tax

        # Создание заказа
        order = Order.objects.create(
            **order_data,
            payment_method=payment_method,
            shipping_method=shipping_method,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total
        )

        # Создание элементов заказа
        for item in cart.get_items():
            try:
                product = Product.objects.get(id=item['product_id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=item['product_name'],
                    product_price=Decimal(str(item['price'])),
                    quantity=item['quantity']
                )

                # Уменьшаем остаток на складе
                if product.stock >= item['quantity']:
                    product.stock -= item['quantity']
                    product.save()
            except Product.DoesNotExist:
                # Товар удален, но в корзине остался — пропускаем
                continue

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
            admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
            if not admin_emails:
                return

            payment_name = order.get_payment_method_display()
            shipping_name = order.get_shipping_method_display()

            admin_message = f"""
Новый заказ #{order.order_number}

Клиент: {order.get_full_name()}
Email: {order.email}
Телефон: {order.phone}
Сумма: {order.total} ₽
Товаров: {order.items.count()}
Способ оплаты: {payment_name}
Способ доставки: {shipping_name}

Адрес: {order.address}, {order.city}, {order.postal_code}

{settings.ADMIN_URL if hasattr(settings, 'ADMIN_URL') else ''}/admin/orders/order/{order.id}/change/
"""
            send_mail(
                subject=f'[ADMIN] Новый заказ #{order.order_number}',
                message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
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

        shipping_name = order.get_shipping_method_display()

        message = f"""
Здравствуйте, {order.get_full_name()}!

Статус вашего заказа #{order.order_number} изменен на: {order.get_status_display()}

Способ доставки: {shipping_name}

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
        orders = self.get_queryset().order_by('-created_at')
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
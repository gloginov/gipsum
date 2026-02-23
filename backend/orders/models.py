import uuid
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from products.models import Product


class PaymentMethod(models.Model):
    """Способы оплаты"""
    name = models.CharField(max_length=100, verbose_name='Название')
    code = models.SlugField(max_length=50, unique=True, verbose_name='Код')
    description = models.TextField(blank=True, verbose_name='Описание')
    commission_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Комиссия (%)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка (CSS класс)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'

    def __str__(self):
        return self.name


class ShippingMethod(models.Model):
    """Способы доставки"""
    name = models.CharField(max_length=100, verbose_name='Название')
    code = models.SlugField(max_length=50, unique=True, verbose_name='Код')
    description = models.TextField(blank=True, verbose_name='Описание')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Стоимость')
    free_from = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Бесплатно от суммы'
    )
    estimated_days = models.CharField(max_length=50, blank=True, verbose_name='Срок доставки')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Способ доставки'
        verbose_name_plural = 'Способы доставки'

    def __str__(self):
        return self.name

    def get_cost_display(self):
        if self.free_from and self.free_from > 0:
            return f'{self.cost} ₽ (бесплатно от {self.free_from} ₽)'
        return f'{self.cost} ₽' if self.cost > 0 else 'Бесплатно'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')

    # Обновленные поля - теперь ForeignKey
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='orders',
        verbose_name='Способ оплаты'
    )
    # Сохраняем старое поле для совместимости (можно удалить после миграции)
    payment_method_old = models.CharField(max_length=50, blank=True, editable=False)

    shipping_method = models.ForeignKey(
        ShippingMethod, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders',
        verbose_name='Способ доставки'
    )

    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    customer_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)

    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # CDEK поля
    cdek_tariff_code = models.IntegerField(null=True, blank=True)
    cdek_city_code = models.IntegerField(null=True, blank=True)
    cdek_pvz_code = models.CharField(max_length=50, null=True, blank=True)
    cdek_tracking_number = models.CharField(max_length=50, null=True, blank=True)
    delivery_type = models.CharField(max_length=20, default='warehouse')  # warehouse/door

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_payment_method_display(self):
        if self.payment_method:
            return self.payment_method.name
        return self.payment_method_old or 'Не указан'

    def get_shipping_method_display(self):
        if self.shipping_method:
            return self.shipping_method.name
        return 'Не указан'

    def send_confirmation_email(self):
        """Отправка email подтверждения заказа"""
        if self.email_sent:
            return False

        subject = f'Подтверждение заказа #{self.order_number}'

        # Формируем список товаров
        items_list = "\n".join([
            f"- {item.product_name} x {item.quantity} = {item.total} ₽"
            for item in self.items.all()
        ])

        payment_name = self.get_payment_method_display()
        shipping_name = self.get_shipping_method_display()

        message = f"""
Здравствуйте, {self.get_full_name()}!

Ваш заказ #{self.order_number} успешно оформлен.

📦 Детали заказа:
{items_list}

💰 Итого:
Товары: {self.subtotal} ₽
Доставка ({shipping_name}): {self.shipping_cost} ₽
Налог: {self.tax} ₽
━━━━━━━━━━━━━━
Всего: {self.total} ₽

💳 Способ оплаты: {payment_name}
🚚 Способ доставки: {shipping_name}

📍 Адрес доставки:
{self.address}
{self.city}, {self.postal_code}
{self.country}

📞 Контакты: {self.phone}

Статус заказа: {self.get_status_display()}

Мы свяжемся с вами для подтверждения доставки.

Спасибо за покупку!
"""

        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ background: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .items {{ background: white; padding: 15px; margin: 10px 0; }}
        .item {{ border-bottom: 1px solid #eee; padding: 10px 0; }}
        .total {{ font-size: 18px; font-weight: bold; color: #4CAF50; margin-top: 20px; }}
        .footer {{ text-align: center; color: #666; margin-top: 30px; }}
        .info-block {{ background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Заказ #{self.order_number}</h1>
            <p>Успешно оформлен!</p>
        </div>

        <div class="content">
            <p>Здравствуйте, <strong>{self.get_full_name()}</strong>!</p>

            <h3>📦 Товары:</h3>
            <div class="items">
                {''.join([f'<div class="item">{item.product_name} x {item.quantity} = <strong>{item.total} ₽</strong></div>' for item in self.items.all()])}
            </div>

            <div class="info-block">
                <strong>💳 Способ оплаты:</strong> {payment_name}<br>
                <strong>🚚 Способ доставки:</strong> {shipping_name}
            </div>

            <div class="total">
                Итого: {self.total} ₽
            </div>

            <h3>📍 Адрес доставки:</h3>
            <p>{self.address}<br>
            {self.city}, {self.postal_code}<br>
            {self.country}</p>

            <p>📞 Телефон: {self.phone}</p>
        </div>

        <div class="footer">
            <p>Спасибо за покупку!</p>
            <p><small>Если у вас есть вопросы, ответьте на это письмо</small></p>
        </div>
    </div>
</body>
</html>
"""

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                fail_silently=False,
                html_message=html_message,
            )

            from django.utils import timezone
            self.email_sent = True
            self.email_sent_at = timezone.now()
            self.save(update_fields=['email_sent', 'email_sent_at'])

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.product_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

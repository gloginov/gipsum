import uuid
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from products.models import Product


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
    
    payment_method = models.CharField(max_length=50, default='card')
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
        
        message = f"""
Здравствуйте, {self.get_full_name()}!

Ваш заказ #{self.order_number} успешно оформлен.

📦 Детали заказа:
{items_list}

💰 Итого:
Товары: {self.subtotal} ₽
Доставка: {self.shipping_cost} ₽
Налог: {self.tax} ₽
━━━━━━━━━━━━━━
Всего: {self.total} ₽

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
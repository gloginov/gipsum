from decimal import Decimal
from django.conf import settings
from products.models import Product
from .models import Cart, CartItem


class CartService:
    """Сервис для работы с корзиной (сессия + БД)"""
    
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self._cart_db = None
        
        # Получаем или создаем корзину в БД
        if request.user.is_authenticated:
            self._cart_db, _ = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = self.session.session_key
            if not session_key:
                self.session.create()
                session_key = self.session.session_key
            self._cart_db, _ = Cart.objects.get_or_create(
                session_key=session_key,
                user=None
            )

    def add(self, product, quantity=1, override_quantity=False):
        """Добавить товар в корзину"""
        product_id = product.id
        
        # Проверяем, есть ли уже этот товар в корзине
        cart_item, created = CartItem.objects.get_or_create(
            cart=self._cart_db,
            product=product,
            defaults={'price': product.price or 0, 'quantity': quantity}
        )
        
        if not created:
            if override_quantity:
                cart_item.quantity = quantity
            else:
                cart_item.quantity += quantity
            cart_item.save()
        
        # Также сохраняем в сессию для быстрого доступа
        self._update_session()
        
        return cart_item

    def remove(self, product):
        """Удалить товар из корзины"""
        CartItem.objects.filter(
            cart=self._cart_db,
            product=product
        ).delete()
        self._update_session()

    def update_quantity(self, product, quantity):
        """Обновить количество"""
        if quantity <= 0:
            self.remove(product)
            return
        
        CartItem.objects.filter(
            cart=self._cart_db,
            product=product
        ).update(quantity=quantity)
        self._update_session()

    def clear(self):
        """Очистить корзину"""
        self._cart_db.items.all().delete()
        self._update_session()

    def get_items(self):
        """Получить все элементы корзины"""
        items = self._cart_db.items.select_related('product').all()
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_slug': item.product.slug,
                'quantity': item.quantity,
                'price': str(item.price),
                'total': str(item.total),
                'main_image': item.product.main_image.image.url if item.product.main_image else None,
                'stock': item.product.stock,
                'in_stock': item.product.in_stock
            })
        return result

    def get_total(self):
        """Общая сумма корзины"""
        total = self._cart_db.total
        return str(total) if total is not None else '0.00'

    def get_count(self):
        """Количество товаров в корзине"""
        return self._cart_db.items_count

    def merge_with_user(self, user):
        """Объединить сессионную корзину с корзиной пользователя (при логине)"""
        try:
            user_cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            # Просто привязываем текущую корзину к пользователю
            self._cart_db.user = user
            self._cart_db.session_key = None
            self._cart_db.save()
            return
        
        # Переносим товары из сессионной корзины в пользовательскую
        for item in self._cart_db.items.all():
            existing = user_cart.items.filter(product=item.product).first()
            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                CartItem.objects.create(
                    cart=user_cart,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.price or 0
                )
        
        # Удаляем старую сессионную корзину
        self._cart_db.delete()
        self._cart_db = user_cart

    def _update_session(self):
        """Обновляем сессию для быстрого доступа"""
        self.session[settings.CART_SESSION_ID] = {
            'count': self.get_count(),
            'total': self.get_total()
        }
        self.session.modified = True

    # Для обратной совместимости с session-based cart
    def __iter__(self):
        items = self.get_items()
        for item in items:
            item['price'] = Decimal(item['price'])
            item['total_price'] = Decimal(item['total'])
            yield item

    def __len__(self):
        return self.get_count()
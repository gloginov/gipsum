from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    image = models.ImageField(
        upload_to='categories/%Y/%m/', 
        blank=True, 
        null=True
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Полный путь категории (например: Электроника > Телефоны > Смартфоны)"""
        path = []
        current = self
        while current:
            path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path))

    def get_all_children(self, include_self=True):
        """Получить все подкатегории рекурсивно"""
        categories = [self] if include_self else []
        for child in self.children.filter(is_active=True):
            categories.extend(child.get_all_children(include_self=True))
        return categories


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    sku = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True,
        help_text="Артикул товара (автогенерация если пусто)"
    )
    description = models.TextField()
    short_description = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Краткое описание для списка товаров"
    )
    
    # Цены
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    old_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Старая цена (для отображения скидки)"
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Закупочная цена (для админки)"
    )
    
    # Наличие
    stock = models.PositiveIntegerField(default=0)
    stock_alert_threshold = models.PositiveIntegerField(
        default=5,
        help_text="Минимальный остаток для уведомления"
    )
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True, help_text="Новинка")
    is_bestseller = models.BooleanField(default=False, help_text="Хит продаж")
    
    # Категории (многие-ко-многим)
    categories = models.ManyToManyField(
        Category,
        related_name='products',
        blank=True,
        help_text="Выберите одну или несколько категорий"
    )
    main_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='main_products',
        help_text="Основная категория (для хлебных крошек)"
    )
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    
    # Характеристики (JSON для гибкости)
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"color": "Черный", "weight": "200г", "material": "Алюминий"}'
    )
    
    # Вес и размеры (для доставки)
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Вес в кг"
    )
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    depth = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-is_featured', 'name']
        verbose_name_plural = 'Товары'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_available', 'is_featured']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Автогенерация SKU
        if not self.sku:
            prefix = 'PRD'
            last_product = Product.objects.order_by('-id').first()
            last_id = last_product.id if last_product else 0
            self.sku = f"{prefix}-{last_id + 1:06d}"
        super().save(*args, **kwargs)

    @property
    def main_image(self):
        """Главное изображение товара"""
        main = self.images.filter(is_main=True).first()
        return main if main else self.images.first()

    @property
    def discount_percent(self):
        """Процент скидки"""
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0

    @property
    def in_stock(self):
        """Есть ли в наличии"""
        return self.stock > 0 and self.is_available

    @property
    def is_low_stock(self):
        """Заканчивается ли товар"""
        return self.stock <= self.stock_alert_threshold

    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})

    def get_categories_list(self):
        """Получить список всех категорий товара"""
        return list(self.categories.filter(is_active=True))


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='products/%Y/%m/%d/')
    is_main = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=models.Q(is_main=True),
                name='unique_main_image_per_product'
            )
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class ProductAttribute(models.Model):
    """Модель для предопределенных характеристик (опционально)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """Значения характеристик для товаров"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attribute_values'
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE
    )
    value = models.CharField(max_length=255)
    
    class Meta:
        unique_together = ['product', 'attribute']
    
    def __str__(self):
        return f"{self.product.name}: {self.attribute.name} = {self.value}"
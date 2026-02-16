from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Gallery(models.Model):
    """Галерея изображений"""
    
    DISPLAY_TYPES = [
        ('grid', 'Сетка'),
        ('masonry', 'Плитка (Masonry)'),
        ('slider', 'Слайдер'),
        ('carousel', 'Карусель'),
        ('lightbox', 'Лайтбокс галерея'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='URL-идентификатор')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Тип отображения
    display_type = models.CharField(
        max_length=20,
        choices=DISPLAY_TYPES,
        default='grid',
        verbose_name='Тип отображения'
    )
    
    # Настройки отображения
    columns = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        verbose_name='Колонки (для сетки)',
        help_text='Количество колонок при отображении сеткой'
    )
    
    gap = models.PositiveSmallIntegerField(
        default=20,
        verbose_name='Отступ между изображениями (px)'
    )
    
    # Настройки слайдера/карусели
    autoplay = models.BooleanField(
        default=True,
        verbose_name='Автопрокрутка',
        help_text='Для слайдера и карусели'
    )
    autoplay_speed = models.PositiveSmallIntegerField(
        default=3000,
        verbose_name='Скорость автопрокрутки (мс)',
        help_text='3000 = 3 секунды'
    )
    infinite_loop = models.BooleanField(
        default=True,
        verbose_name='Бесконечная прокрутка'
    )
    show_arrows = models.BooleanField(
        default=True,
        verbose_name='Показывать стрелки навигации'
    )
    show_dots = models.BooleanField(
        default=True,
        verbose_name='Показывать точки навигации'
    )
    slides_to_show = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Слайдов одновременно',
        help_text='Для карусели - сколько слайдов показывать'
    )
    slides_to_scroll = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Слайдов за раз'
    )
    
    # Настройки изображений
    image_height = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Фиксированная высота (px)',
        help_text='Оставьте пустым для оригинальных пропорций'
    )
    object_fit = models.CharField(
        max_length=20,
        choices=[
            ('cover', 'Cover - заполнить'),
            ('contain', 'Contain - вписать'),
            ('fill', 'Fill - растянуть'),
        ],
        default='cover',
        verbose_name='Обрезка изображений'
    )
    
    # Стили
    border_radius = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Скругление углов (px)'
    )
    shadow = models.BooleanField(
        default=False,
        verbose_name='Тень'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Галерея'
        verbose_name_plural = 'Галереи'
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_display_type_display()})"

    @property
    def images_count(self):
        return self.images.filter(is_active=True).count()


class GalleryImage(models.Model):
    """Изображение в галерее"""
    
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Галерея'
    )
    
    image = models.ImageField(
        upload_to='galleries/%Y/%m/',
        verbose_name='Изображение'
    )
    
    # Мета-информация
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Заголовок'
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Alt текст (SEO)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание / Подпись'
    )
    
    # Для слайдера - дополнительный контент
    caption = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Подпись на слайде'
    )
    button_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Текст кнопки'
    )
    button_link = models.URLField(
        blank=True,
        verbose_name='Ссылка кнопки'
    )
    overlay_color = models.CharField(
        max_length=7,
        default='#000000',
        verbose_name='Цвет оверлея',
        help_text='HEX цвет, например #000000'
    )
    overlay_opacity = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name='Прозрачность оверлея'
    )
    
    # Позиционирование контента на слайде
    text_position = models.CharField(
        max_length=20,
        choices=[
            ('center', 'По центру'),
            ('left', 'Слева'),
            ('right', 'Справа'),
            ('bottom-left', 'Снизу слева'),
            ('bottom-center', 'Снизу по центру'),
            ('bottom-right', 'Снизу справа'),
        ],
        default='center',
        verbose_name='Позиция текста'
    )
    
    # Порядок
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Изображение галереи'
        verbose_name_plural = 'Изображения галереи'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.gallery.name} - {self.title or f'Image {self.order}'}"

    @property
    def thumbnail_url(self):
        """URL миниатюры (можно подключить sorl-thumbnail)"""
        return self.image.url
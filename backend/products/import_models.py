import os
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


def import_file_path(instance, filename):
    """Генерация пути для файла импорта"""
    ext = filename.split('.')[-1]
    filename = f"import_{uuid.uuid4().hex[:8]}.{ext}"
    # Если объект уже сохранён — используем created_at, иначе текущую дату
    if instance.created_at:
        date = instance.created_at
    else:
        date = datetime.now()
    
    return f'imports/{date.strftime("%Y/%m")}/{filename}'


class ProductImport(models.Model):
    """Загрузка и обработка файла импорта товаров"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Завершено'),
        ('partial', 'Частично завершено'),
        ('error', 'Ошибка'),
    ]
    
    IMPORT_TYPE_CHOICES = [
        ('create', 'Только создание'),
        ('update', 'Только обновление'),
        ('create_update', 'Создание и обновление'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название импорта')
    file = models.FileField(
        upload_to=import_file_path,
        verbose_name='Файл Excel',
        help_text='Поддерживаемые форматы: .xlsx, .xls, .csv'
    )
    
    import_type = models.CharField(
        max_length=20,
        choices=IMPORT_TYPE_CHOICES,
        default='create_update',
        verbose_name='Тип импорта'
    )
    
    # Статус и результаты
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    total_rows = models.PositiveIntegerField(default=0, verbose_name='Всего строк')
    created_count = models.PositiveIntegerField(default=0, verbose_name='Создано')
    updated_count = models.PositiveIntegerField(default=0, verbose_name='Обновлено')
    error_count = models.PositiveIntegerField(default=0, verbose_name='Ошибок')
    skipped_count = models.PositiveIntegerField(default=0, verbose_name='Пропущено')
    
    # Логи и ошибки
    log_file = models.FileField(
        upload_to='imports/logs/',
        blank=True,
        null=True,
        verbose_name='Лог импорта'
    )
    error_message = models.TextField(blank=True, verbose_name='Сообщение об ошибке')
    
    # Настройки
    skip_existing = models.BooleanField(
        default=False,
        verbose_name='Пропускать существующие (по SKU)'
    )
    update_images = models.BooleanField(
        default=False,
        verbose_name='Обновлять изображения'
    )
    default_category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория по умолчанию'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Кто создал'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Импорт товаров'
        verbose_name_plural = 'Импорты товаров'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class ProductImportLog(models.Model):
    """Детальный лог каждой строки импорта"""
    
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('created', 'Создан'),
        ('updated', 'Обновлен'),
        ('error', 'Ошибка'),
        ('skipped', 'Пропущен'),
    ]
    
    import_task = models.ForeignKey(
        ProductImport,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Импорт'
    )
    row_number = models.PositiveIntegerField(verbose_name='Номер строки')
    sku = models.CharField(max_length=50, blank=True, verbose_name='SKU')
    product_name = models.CharField(max_length=200, blank=True, verbose_name='Название товара')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Статус')
    message = models.TextField(blank=True, verbose_name='Сообщение')
    raw_data = models.JSONField(default=dict, verbose_name='Исходные данные')

    class Meta:
        verbose_name = 'Лог импорта'
        verbose_name_plural = 'Логи импорта'
        ordering = ['row_number']
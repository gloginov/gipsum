import os
import uuid
from django.db import models
from django.core.validators import RegexValidator


def feedback_file_path(instance, filename):
    """Генерация пути для файла обратной связи"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex[:8]}.{ext}"
    return f'feedback/{instance.created_at.strftime("%Y/%m")}/{filename}'


class FeedbackMessage(models.Model):
    """Сообщение обратной связи"""
    
    MESSAGE_TYPES = [
        ('general', 'Общий вопрос'),
        ('support', 'Техподдержка'),
        ('sales', 'Отдел продаж'),
        ('partnership', 'Партнерство'),
        ('complaint', 'Жалоба'),
        ('other', 'Другое'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('in_progress', 'В работе'),
        ('answered', 'Отвечено'),
        ('closed', 'Закрыто'),
        ('spam', 'Спам'),
    ]
    
    # Основные поля
    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Номер телефона должен быть в формате: +79991234567 или 89991234567'
        )],
        verbose_name='Телефон'
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='general',
        verbose_name='Тип обращения'
    )
    
    subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Тема'
    )
    message = models.TextField(verbose_name='Сообщение')
    
    # Файл
    attachment = models.FileField(
        upload_to=feedback_file_path,
        blank=True,
        null=True,
        verbose_name='Прикрепленный файл',
        help_text='Допустимые форматы: JPG, PNG, GIF, PDF. Максимальный размер: 10MB'
    )
    
    # Валидация
    privacy_policy_accepted = models.BooleanField(
        default=False,
        verbose_name='Согласие с политикой конфиденциальности'
    )
    privacy_policy_url = models.URLField(
        blank=True,
        verbose_name='URL политики конфиденциальности (на момент отправки)'
    )
    
    # Мета-информация
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP адрес'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    referer = models.URLField(
        blank=True,
        verbose_name='Страница отправки'
    )
    
    # Статус и обработка
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    admin_notes = models.TextField(
        blank=True,
        verbose_name='Заметки администратора'
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата ответа'
    )
    answered_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_feedbacks',
        verbose_name='Ответил'
    )
    
    # Email уведомления
    email_sent = models.BooleanField(
        default=False,
        verbose_name='Email отправлен'
    )
    email_error = models.TextField(
        blank=True,
        verbose_name='Ошибка отправки email'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Сообщение обратной связи'
        verbose_name_plural = 'Сообщения обратной связи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_message_type_display()} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"

    @property
    def has_attachment(self):
        return bool(self.attachment)

    @property
    def attachment_filename(self):
        if self.attachment:
            return os.path.basename(self.attachment.name)
        return None

    @property
    def attachment_extension(self):
        if self.attachment:
            return os.path.splitext(self.attachment.name)[1].lower()
        return None

    @property
    def is_image(self):
        return self.attachment_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    @property
    def is_pdf(self):
        return self.attachment_extension == '.pdf'


class FeedbackSettings(models.Model):
    """Настройки формы обратной связи (singleton)"""
    
    email_recipients = models.TextField(
        default='admin@example.com',
        verbose_name='Email получателей',
        help_text='Укажите email через запятую'
    )
    notify_telegram = models.BooleanField(
        default=False,
        verbose_name='Уведомлять в Telegram'
    )
    telegram_bot_token = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Токен бота Telegram'
    )
    telegram_chat_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Chat ID Telegram'
    )
    max_file_size = models.PositiveIntegerField(
        default=10,
        verbose_name='Максимальный размер файла (MB)'
    )
    allowed_extensions = models.CharField(
        default='jpg,jpeg,png,gif,pdf',
        max_length=200,
        verbose_name='Разрешенные расширения'
    )
    enable_captcha = models.BooleanField(
        default=False,
        verbose_name='Включить капчу'
    )
    
    class Meta:
        verbose_name = 'Настройки обратной связи'
        verbose_name_plural = 'Настройки обратной связи'

    def __str__(self):
        return 'Настройки формы обратной связи'

    def get_email_list(self):
        return [email.strip() for email in self.email_recipients.split(',') if email.strip()]
from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import FeedbackMessage


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания обращения"""
    
    # Поле для загрузки файла
    attachment = serializers.FileField(
        required=False,
        allow_empty_file=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf']
            )
        ],
        help_text='Допустимые форматы: JPG, PNG, GIF, PDF. Макс. размер: 10MB'
    )
    
    # Согласие с политикой (обязательное)
    privacy_policy_accepted = serializers.BooleanField(
        required=True,
        help_text='Необходимо принять политику конфиденциальности'
    )
    
    # Дополнительные поля (не сохраняются в модель)
    privacy_policy_url = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='URL политики конфиденциальности из настроек'
    )

    class Meta:
        model = FeedbackMessage
        fields = [
            'name',
            'email',
            'phone',
            'message_type',
            'subject',
            'message',
            'attachment',
            'privacy_policy_accepted',
            'privacy_policy_url',
        ]

    def validate_privacy_policy_accepted(self, value):
        """Валидация согласия с политикой"""
        if not value:
            raise serializers.ValidationError(
                'Необходимо принять политику конфиденциальности'
            )
        return value

    def validate_attachment(self, value):
        """Валидация файла"""
        if value is None:
            return value
            
        # Проверка размера (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'Размер файла не должен превышать 10MB. '
                f'Текущий размер: {value.size / 1024 / 1024:.2f}MB'
            )
        
        # Проверка типа файла по content_type
        allowed_types = [
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/pdf'
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f'Недопустимый тип файла: {value.content_type}. '
                f'Разрешены: JPG, PNG, GIF, PDF'
            )
        
        return value

    def validate_phone(self, value):
        """Валидация телефона"""
        if value and not value.replace('+', '').replace(' ', '').isdigit():
            raise serializers.ValidationError(
                'Номер телефона должен содержать только цифры и +'
            )
        return value

    def create(self, validated_data):
        # Убираем поля, которых нет в модели
        validated_data.pop('privacy_policy_url', None)
        
        # Добавляем мета-информацию из request
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self._get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
            validated_data['referer'] = request.META.get('HTTP_REFERER', '')[:500]
        
        return super().create(validated_data)

    def _get_client_ip(self, request):
        """Получение IP клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FeedbackResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа (после создания)"""
    
    class Meta:
        model = FeedbackMessage
        fields = [
            'id',
            'name',
            'email',
            'message_type',
            'subject',
            'status',
            'created_at',
        ]
        read_only_fields = fields


class FeedbackListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка (только для админов)"""
    
    has_attachment = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = FeedbackMessage
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'message_type',
            'subject',
            'status',
            'has_attachment',
            'created_at',
        ]
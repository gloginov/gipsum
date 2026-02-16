from rest_framework import serializers
from .models import SiteSetting


class SiteSettingSerializer(serializers.ModelSerializer):
    """Базовый сериализатор с value"""
    value = serializers.SerializerMethodField()

    class Meta:
        model = SiteSetting
        fields = ['key', 'name', 'value', 'type']

    def get_value(self, obj):
        return obj.get_value()


class SiteSettingDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор со всеми полями из админки"""
    value = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SiteSetting
        fields = [
            'id',
            'key',
            'name',
            'description',
            'type',
            'value',
            'image',
            'image_url',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def get_value(self, obj):
        return obj.get_value()
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class SiteSettingBulkRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса нескольких настроек по ключам"""
    keys = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=False,
    )
    key = serializers.CharField(
        max_length=100,
        required=False,
    )

    def validate(self, data):
        if not data.get('keys') and not data.get('key'):
            raise serializers.ValidationError("Укажите 'key' или 'keys'")
        return data

    def get_keys_list(self):
        """Возвращает список ключей из запроса"""
        if self.validated_data.get('keys'):
            return self.validated_data['keys']
        if self.validated_data.get('key'):
            return [self.validated_data['key']]
        return []
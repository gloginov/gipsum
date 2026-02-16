from rest_framework import serializers
from .models import Gallery, GalleryImage


class GalleryImageSerializer(serializers.ModelSerializer):
    """Сериализатор изображения галереи"""
    image_url = serializers.SerializerMethodField()
    image_url_relative = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryImage
        fields = [
            'id',
            'image',
            'image_url',
            'image_url_relative',
            'thumbnail_url',
            'title',
            'alt_text',
            'description',
            'caption',
            'button_text',
            'button_link',
            'overlay_color',
            'overlay_opacity',
            'text_position',
            'order',
        ]
    
    def get_image_url(self, obj):
        """Полный URL с доменом"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_image_url_relative(self, obj):
        """Относительный URL без домена (/media/galleries/...)"""
        if obj.image:
            return obj.image.url
        return None
    
    def get_thumbnail_url(self, obj):
        """URL миниатюры (можно подключить sorl-thumbnail)"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class GalleryListSerializer(serializers.ModelSerializer):
    """Список галерей (кратко)"""
    images_count = serializers.IntegerField(read_only=True)
    preview_image = serializers.SerializerMethodField()
    preview_image_relative = serializers.SerializerMethodField()
    
    class Meta:
        model = Gallery
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'display_type',
            'images_count',
            'preview_image',
            'preview_image_relative',
        ]
    
    def get_preview_image(self, obj):
        first_image = obj.images.filter(is_active=True).first()
        if first_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None
    
    def get_preview_image_relative(self, obj):
        first_image = obj.images.filter(is_active=True).first()
        if first_image:
            return first_image.image.url
        return None


class GalleryConfigSerializer(serializers.ModelSerializer):
    """Конфигурация галереи для фронтенда"""
    
    class Meta:
        model = Gallery
        fields = [
            'id',
            'name',
            'slug',
            'display_type',
            'columns',
            'gap',
            'autoplay',
            'autoplay_speed',
            'infinite_loop',
            'show_arrows',
            'show_dots',
            'slides_to_show',
            'slides_to_scroll',
            'image_height',
            'object_fit',
            'border_radius',
            'shadow',
        ]


class GalleryDetailSerializer(serializers.ModelSerializer):
    """Полная информация о галерее с изображениями"""
    config = serializers.SerializerMethodField()
    images = GalleryImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Gallery
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'config',
            'images',
        ]
    
    def get_config(self, obj):
        """Возвращаем конфиг как отдельный объект"""
        return GalleryConfigSerializer(obj, context=self.context).data


class GalleryRenderSerializer(serializers.ModelSerializer):
    """Сериализатор для рендеринга галереи на фронте"""
    images = GalleryImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Gallery
        fields = [
            'name',
            'display_type',
            'columns',
            'gap',
            'autoplay',
            'autoplay_speed',
            'infinite_loop',
            'show_arrows',
            'show_dots',
            'slides_to_show',
            'slides_to_scroll',
            'image_height',
            'object_fit',
            'border_radius',
            'shadow',
            'images',
        ]
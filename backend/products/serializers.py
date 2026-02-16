from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductAttribute, ProductAttributeValue


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main', 'alt_text', 'order']


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Сериализатор для дерева категорий"""
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'children', 'product_count', 'is_active']

    def get_children(self, obj):
        if obj.children.filter(is_active=True).exists():
            return CategoryTreeSerializer(
                obj.children.filter(is_active=True), 
                many=True
            ).data
        return []

    def get_product_count(self, obj):
        # Подсчет товаров в категории и подкатегориях
        all_categories = obj.get_all_children(include_self=True)
        return Product.objects.filter(
            categories__in=all_categories,
            is_available=True
        ).distinct().count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent', 'parent_name']


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор категории"""
    parent = CategoryListSerializer(read_only=True)
    children = CategoryListSerializer(many=True, read_only=True)
    breadcrumbs = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image',
            'parent', 'children', 'breadcrumbs',
            'meta_title', 'meta_description'
        ]
    
    def get_breadcrumbs(self, obj):
        """Хлебные крошки для категории"""
        crumbs = []
        current = obj
        while current:
            crumbs.append({
                'id': current.id,
                'name': current.name,
                'slug': current.slug
            })
            current = current.parent
        return list(reversed(crumbs))


class ProductCategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории для товара"""
    breadcrumbs = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'breadcrumbs']
    
    def get_breadcrumbs(self, obj):
        return [{'id': c.id, 'name': c.name, 'slug': c.slug} 
                for c in obj.get_all_children(include_self=False)]


class ProductListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка товаров"""
    main_image = serializers.SerializerMethodField()
    categories = ProductCategorySerializer(many=True, read_only=True)
    main_category = ProductCategorySerializer(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'short_description',
            'price', 'old_price', 'discount_percent',
            'main_image', 'categories', 'main_category',
            'is_available', 'in_stock', 'is_low_stock',
            'is_featured', 'is_new', 'is_bestseller',
            'created_at'
        ]

    def get_main_image(self, obj):
        if obj.main_image:
            return {
                'url': obj.main_image.image.url,
                'alt': obj.main_image.alt_text or obj.name
            }
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор товара"""
    images = ProductImageSerializer(many=True, read_only=True)
    categories = ProductCategorySerializer(many=True, read_only=True)
    main_category = ProductCategorySerializer(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    attributes = serializers.JSONField()
    related_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku',
            'description', 'short_description',
            'price', 'old_price', 'discount_percent',
            'purchase_price',  # Только для админов в реальном проекте
            'stock', 'stock_alert_threshold',
            'is_available', 'in_stock', 'is_low_stock',
            'is_featured', 'is_new', 'is_bestseller',
            'categories', 'main_category',
            'images', 'attributes',
            'weight', 'width', 'height', 'depth',
            'meta_title', 'meta_description', 'meta_keywords',
            'related_products',
            'created_at', 'updated_at'
        ]

    def get_related_products(self, obj):
        """Похожие товары из тех же категорий"""
        related = Product.objects.filter(
            categories__in=obj.categories.all(),
            is_available=True
        ).exclude(id=obj.id).distinct()[:4]
        return ProductListSerializer(related, many=True).data


class ProductFilterSerializer(serializers.Serializer):
    """Сериализатор для фильтрации товаров"""
    category = serializers.CharField(required=False, help_text="Slug категории")
    category_id = serializers.IntegerField(required=False, help_text="ID категории")
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    in_stock = serializers.BooleanField(required=False)
    is_featured = serializers.BooleanField(required=False)
    is_new = serializers.BooleanField(required=False)
    is_bestseller = serializers.BooleanField(required=False)
    search = serializers.CharField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            'price', '-price',
            'created_at', '-created_at',
            'name', '-name',
            'popularity'
        ],
        required=False
    )

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления товара (только для админов)"""
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.filter(is_active=True)
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description', 'short_description',
            'price', 'old_price', 'purchase_price', 'stock', 'stock_alert_threshold',
            'categories', 'main_category', 'is_available', 'is_featured', 
            'is_new', 'is_bestseller', 'attributes',
            'weight', 'width', 'height', 'depth',
            'meta_title', 'meta_description', 'meta_keywords'
        ]
        read_only_fields = ['sku']  # Автогенерация
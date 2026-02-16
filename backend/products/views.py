from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from .models import Category, Product
from .serializers import (
    CategoryTreeSerializer,
    CategoryListSerializer,
    CategoryDetailSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,  # Для админов
    ProductFilterSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Категории - только чтение для всех.
    Создание/редактирование/удаление только через Django Admin.
    """
    queryset = Category.objects.filter(is_active=True)
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryTreeSerializer
        elif self.action == 'tree':
            return CategoryTreeSerializer
        return CategoryDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            return queryset.filter(parent=None)
        return queryset

    @action(detail=False, methods=['get'])
    def tree(self, request):
        root_categories = self.get_queryset().filter(parent=None)
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def flat(self, request):
        categories = Category.objects.filter(is_active=True)
        serializer = CategoryListSerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        category = self.get_object()
        all_categories = category.get_all_children(include_self=True)
        
        queryset = Product.objects.filter(
            categories__in=all_categories,
            is_available=True
        ).distinct()
        
        # Применяем фильтры из query params
        params = request.query_params
        
        if params.get('in_stock') == 'true':
            queryset = queryset.filter(stock__gt=0)
        
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        if params.get('is_featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        ordering = params.get('ordering', '-created_at')
        if ordering in ['price', '-price', 'created_at', '-created_at', 'name', '-name']:
            queryset = queryset.order_by(ordering)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(queryset, many=True)
        
        return Response({
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'breadcrumbs': self._get_breadcrumbs(category)
            },
            'products': serializer.data,
            'total_count': queryset.count()
        })

    def _get_breadcrumbs(self, category):
        crumbs = []
        current = category
        while current:
            crumbs.append({
                'id': current.id,
                'name': current.name,
                'slug': current.slug
            })
            current = current.parent
        return list(reversed(crumbs))


class ProductViewSet(viewsets.ModelViewSet):
    """
    Товары:
    - list, retrieve: доступно всем (AllowAny)
    - create, update, partial_update, destroy: только админ (IsAdminUser)
    """
    queryset = Product.objects.filter(is_available=True)
    lookup_field = 'slug'
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve', 'featured', 'new_arrivals', 
                          'bestsellers', 'by_category', 'related', 'search']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def get_queryset(self):
        # Для админов показываем все товары, для остальных только доступные
        if self.request.user.is_staff:
            queryset = Product.objects.all()
        else:
            queryset = Product.objects.filter(is_available=True)
        
        params = self.request.query_params
        
        category_slug = params.get('category')
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)
        
        category_id = params.get('category_id')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        
        if params.get('in_stock') == 'true':
            queryset = queryset.filter(stock__gt=0)
        
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        if params.get('is_featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        if params.get('is_new') == 'true':
            queryset = queryset.filter(is_new=True)
        if params.get('is_bestseller') == 'true':
            queryset = queryset.filter(is_bestseller=True)
        
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search) |
                Q(sku__icontains=search)
            )
        
        ordering = params.get('ordering', '-created_at')
        if ordering in ['price', '-price', 'created_at', '-created_at', 'name', '-name']:
            queryset = queryset.order_by(ordering)
        
        return queryset.distinct()

    def retrieve(self, request, *args, **kwargs):
        lookup_value = kwargs.get(self.lookup_field)
        
        try:
            product_id = int(lookup_value)
            if request.user.is_staff:
                product = get_object_or_404(Product, pk=product_id)
            else:
                product = get_object_or_404(Product, pk=product_id, is_available=True)
        except (ValueError, TypeError):
            if request.user.is_staff:
                product = get_object_or_404(Product, slug=lookup_value)
            else:
                product = get_object_or_404(Product, slug=lookup_value, is_available=True)
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = self.get_queryset().filter(is_featured=True)[:10]
        serializer = ProductListSerializer(featured, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        new_products = self.get_queryset().filter(is_new=True)[:10]
        serializer = ProductListSerializer(new_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        bestsellers = self.get_queryset().filter(is_bestseller=True)[:10]
        serializer = ProductListSerializer(bestsellers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        categories = Category.objects.filter(is_active=True, parent=None)
        
        result = []
        for category in categories:
            products = Product.objects.filter(
                categories__in=category.get_all_children(include_self=True),
                is_available=True
            ).distinct()[:5]
            
            result.append({
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug
                },
                'products': ProductListSerializer(products, many=True).data
            })
        
        return Response(result)

    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        product = self.get_object()
        related = Product.objects.filter(
            categories__in=product.categories.all(),
            is_available=True
        ).exclude(id=product.id).distinct()[:8]
        
        serializer = ProductListSerializer(related, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Расширенный поиск товаров"""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        products = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(categories__name__icontains=query)
        ).distinct()[:20]
        
        serializer = ProductListSerializer(products, many=True)
        return Response({
            'query': query,
            'count': len(serializer.data),
            'results': serializer.data
        })
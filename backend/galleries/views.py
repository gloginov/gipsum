from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import Gallery, GalleryImage
from .serializers import (
    GalleryListSerializer,
    GalleryDetailSerializer,
    GalleryRenderSerializer,
    GalleryImageSerializer
)


class GalleryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для галерей.
    Доступно всем без авторизации (только чтение).
    """
    queryset = Gallery.objects.filter(is_active=True)
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return GalleryListSerializer
        elif self.action == 'render':
            return GalleryRenderSerializer
        return GalleryDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Фильтр по типу отображения
        display_type = self.request.query_params.get('type')
        if display_type:
            queryset = queryset.filter(display_type=display_type)
        return queryset

    @action(detail=True, methods=['get'])
    def render(self, request, slug=None):
        """
        GET /api/galleries/{slug}/render/
        Возвращает галерею готовую для рендеринга на фронте
        """
        gallery = self.get_object()
        serializer = self.get_serializer(gallery)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        GET /api/galleries/by_type/?type=slider
        Получить галереи по типу отображения
        """
        display_type = request.query_params.get('type')
        if not display_type:
            return Response(
                {'error': 'Parameter "type" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        galleries = self.get_queryset().filter(display_type=display_type)
        serializer = GalleryListSerializer(
            galleries, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sliders(self, request):
        """
        GET /api/galleries/sliders/
        Все слайдеры и карусели
        """
        galleries = self.get_queryset().filter(
            display_type__in=['slider', 'carousel']
        )
        serializer = GalleryListSerializer(
            galleries,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def grids(self, request):
        """
        GET /api/galleries/grids/
        Все сетки и плитки
        """
        galleries = self.get_queryset().filter(
            display_type__in=['grid', 'masonry']
        )
        serializer = GalleryListSerializer(
            galleries,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class GalleryImageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для изображений галерей.
    """
    queryset = GalleryImage.objects.filter(is_active=True)
    serializer_class = GalleryImageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Фильтр по галерее
        gallery_slug = self.request.query_params.get('gallery')
        if gallery_slug:
            queryset = queryset.filter(gallery__slug=gallery_slug)
        return queryset
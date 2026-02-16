from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import SiteSetting
from .serializers import (
    SiteSettingSerializer, 
    SiteSettingDetailSerializer,
    SiteSettingBulkRequestSerializer
)


class SiteSettingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с настройками сайта.
    """
    queryset = SiteSetting.objects.filter(is_active=True)
    serializer_class = SiteSettingSerializer
    lookup_field = 'key'

    def get_serializer_class(self):
        """Для retrieve возвращаем полные данные"""
        if self.action == 'retrieve':
            return SiteSettingDetailSerializer
        return SiteSettingSerializer

    def get_queryset(self):
        """Фильтрация по query параметрам keys или key"""
        queryset = super().get_queryset()
        
        keys_param = self.request.query_params.get('keys')
        if keys_param:
            keys = [k.strip() for k in keys_param.split(',')]
            queryset = queryset.filter(key__in=keys)
        
        single_key = self.request.query_params.get('key')
        if single_key:
            queryset = queryset.filter(key=single_key)
            
        return queryset

    def list(self, request, *args, **kwargs):
        """
        GET /api/settings/ - все настройки с полными полями
        GET /api/settings/?keys=site_name,home_hero_title - фильтр по ключам
        GET /api/settings/?key=site_name - одна настройка
        """
        queryset = self.get_queryset()
        
        # Если запрошены конкретные ключи - возвращаем только key-value для совместимости
        if request.query_params.get('keys') or request.query_params.get('key'):
            data = {}
            for setting in queryset:
                data[setting.key] = {
                    'value': setting.get_value(),
                    'name': setting.name,
                    'type': setting.type,
                    'description': setting.description,
                }
            return Response(data)
        
        # По умолчанию возвращаем полные данные всех настроек
        serializer = SiteSettingDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """
        POST /api/settings/bulk/
        Body: {"keys": ["site_name", "home_hero_title", "footer_text"]}
        """
        serializer = SiteSettingBulkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        keys = serializer.get_keys_list()
        settings = SiteSetting.objects.filter(key__in=keys, is_active=True)
        
        # Проверяем какие ключи не найдены
        found_keys = {s.key for s in settings}
        not_found = set(keys) - found_keys
        
        result = {
            'data': {setting.key: SiteSettingDetailSerializer(setting).data for setting in settings},
            'found': list(found_keys),
            'not_found': list(not_found) if not_found else None
        }
        
        return Response(result)

    @action(detail=False, methods=['get', 'post'])
    def by_key(self, request):
        """
        GET /api/settings/by-key/?key=site_name
        или
        POST /api/settings/by-key/ {"key": "site_name"}
        """
        if request.method == 'GET':
            key = request.query_params.get('key')
        else:
            key = request.data.get('key')
        
        if not key:
            return Response(
                {'error': 'Parameter "key" is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        setting = get_object_or_404(SiteSetting, key=key, is_active=True)
        
        # Возвращаем полные данные
        return Response(SiteSettingDetailSerializer(setting).data)

    @action(detail=False, methods=['get'])
    def group(self, request):
        """
        GET /api/settings/group/?prefix=home_
        """
        prefix = request.query_params.get('prefix')
        if not prefix:
            return Response(
                {'error': 'Parameter "prefix" is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settings = SiteSetting.objects.filter(key__startswith=prefix, is_active=True)
        
        return Response({
            'prefix': prefix,
            'count': settings.count(),
            'settings': {s.key: SiteSettingDetailSerializer(s).data for s in settings}
        })


class HomePageSettingsView(views.APIView):
    """Конечная точка для получения настроек главной страницы"""
    
    def get(self, request):
        # Получаем настройки с префиксом 'home_'
        home_settings = SiteSetting.objects.filter(key__startswith='home_', is_active=True)
        
        # Дополнительные ключи
        extra_keys_param = request.query_params.get('extra')
        extra_settings = None
        if extra_keys_param:
            extra_keys = [k.strip() for k in extra_keys_param.split(',')]
            extra_settings_qs = SiteSetting.objects.filter(key__in=extra_keys, is_active=True)
            extra_settings = {s.key: SiteSettingDetailSerializer(s).data for s in extra_settings_qs}
        
        return Response({
            'home_settings': {s.key: SiteSettingDetailSerializer(s).data for s in home_settings},
            'extra_settings': extra_settings
        })
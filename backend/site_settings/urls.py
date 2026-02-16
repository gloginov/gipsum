from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteSettingViewSet, HomePageSettingsView

router = DefaultRouter()
router.register(r'', SiteSettingViewSet, basename='setting')

urlpatterns = [
    path('', include(router.urls)),
    path('homepage/', HomePageSettingsView.as_view(), name='homepage-settings'),
]
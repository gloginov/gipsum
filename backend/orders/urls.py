from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, PaymentMethodViewSet, ShippingMethodViewSet

router = DefaultRouter()

# ВАЖНО: сначала регистрируем специфические пути (payment-methods, shipping-methods)
# Потом общий путь с пустым префиксом ''

router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'shipping-methods', ShippingMethodViewSet, basename='shipping-method')
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]
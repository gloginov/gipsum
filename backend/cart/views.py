from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from products.models import Product
from .cart import CartService
from .serializers import CartAddSerializer, CartUpdateSerializer, CartRemoveSerializer


class CsrfExemptAPIView(APIView):
    """Базовый класс для APIView без CSRF защиты"""
    def dispatch(self, request, *args, **kwargs):
        # Отключаем CSRF проверку для этого view
        request._dont_enforce_csrf_checks = True
        return super().dispatch(request, *args, **kwargs)

class CartDetailView(CsrfExemptAPIView):
    """Просмотр корзины - доступно всем"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        cart = CartService(request)
        return Response({
            'items': cart.get_items(),
            'total': cart.get_total(),
            'count': cart.get_count(),
            'is_authenticated': request.user.is_authenticated
        })


class CartAddView(CsrfExemptAPIView):
    """Добавление в корзину - доступно всем"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        if serializer.is_valid():
            cart = CartService(request)
            product = get_object_or_404(
                Product, 
                id=serializer.validated_data['product_id'],
                is_available=True
            )
            
            # Проверка наличия на складе
            requested_qty = serializer.validated_data['quantity']
            if product.stock < requested_qty:
                return Response(
                    {
                        'error': 'Insufficient stock',
                        'available': product.stock,
                        'requested': requested_qty
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart.add(
                product=product,
                quantity=requested_qty,
                override_quantity=serializer.validated_data.get('override', False)
            )
            
            return Response({
                'message': 'Product added to cart',
                'cart': {
                    'total': cart.get_total(),
                    'count': cart.get_count(),
                    'items': cart.get_items()
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartUpdateView(CsrfExemptAPIView):
    """Обновление количества - доступно всем"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = CartUpdateSerializer(data=request.data)
        if serializer.is_valid():
            cart = CartService(request)
            product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
            
            quantity = serializer.validated_data['quantity']
            
            # Проверка наличия
            if quantity > 0 and product.stock < quantity:
                return Response(
                    {'error': f'Only {product.stock} items available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart.update_quantity(product, quantity)
            
            return Response({
                'message': 'Cart updated',
                'cart': {
                    'total': cart.get_total(),
                    'count': cart.get_count(),
                    'items': cart.get_items()
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartRemoveView(CsrfExemptAPIView):
    """Удаление из корзины - доступно всем"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = CartRemoveSerializer(data=request.data)
        if serializer.is_valid():
            cart = CartService(request)
            product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
            cart.remove(product)
            
            return Response({
                'message': 'Product removed',
                'cart': {
                    'total': cart.get_total(),
                    'count': cart.get_count(),
                    'items': cart.get_items()
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartClearView(CsrfExemptAPIView):
    """Очистка корзины - доступно всем"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        cart = CartService(request)
        cart.clear()
        return Response({
            'message': 'Cart cleared',
            'cart': {
                'total': '0.00',
                'count': 0,
                'items': []
            }
        })


class CartMergeView(APIView):
    """Объединение корзин при логине - требует авторизации"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Объединить сессионную корзину с корзиной пользователя"""
        cart = CartService(request)
        cart.merge_with_user(request.user)
        
        return Response({
            'message': 'Cart merged successfully',
            'cart': {
                'total': cart.get_total(),
                'count': cart.get_count(),
                'items': cart.get_items()
            }
        })
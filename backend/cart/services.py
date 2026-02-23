# cart/services.py


def to_dict(self):
    """Сериализует корзину в словарь"""
    cart = self.cart
    
    items = []
    for item in cart.items.select_related('product').prefetch_related('product__images'):
        product = item.product
        
        # Получаем URL изображения
        image_url = None
        main_image = product.main_image  # это ProductImage или None
        if main_image and main_image.image:
            image_url = main_image.image.url
        
        items.append({
            'id': item.id,
            'product_id': product.id,
            'name': product.name,
            'slug': product.slug,
            'quantity': item.quantity,
            'price': str(item.price) if item.price else '0.00',
            'total': str(item.total),
            'stock': product.stock,
            'image': image_url,
        })
    
    return {
        'id': cart.id,
        'items': items,
        'total': str(cart.total),
        'count': cart.count,
        'is_authenticated': self.request.user.is_authenticated,
    }
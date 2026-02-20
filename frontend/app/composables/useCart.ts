export function useCart() {
  const cart = useCartStore()
  const toast = useToast()
  
  // Добавление с уведомлением
  async function addToCartWithToast(productId: number, quantity: number = 1) {
    const result = await cart.addToCart({ 
      product_id: productId, 
      quantity,
      override: false 
    })
    
    if (result.success) {
      toast.add({
        title: 'Добавлено в корзину',
        description: 'Товар успешно добавлен',
        color: 'success',
        icon: 'i-lucide-shopping-cart',
      })
    } else {
      toast.add({
        title: 'Ошибка',
        description: result.message || 'Не удалось добавить товар',
        color: 'error',
        icon: 'i-lucide-alert-circle',
      })
    }
    
    return result
  }
  
  // Удаление с подтверждением
  async function removeWithConfirm(productId: number, productName: string) {
    const confirmed = confirm(`Удалить "${productName}" из корзины?`)
    if (!confirmed) return false
    
    const result = await cart.removeFromCart(productId)
    
    if (result.success) {
      toast.add({
        title: 'Удалено',
        description: 'Товар удален из корзины',
        color: 'success',
      })
    }
    
    return result.success
  }
  
  return {
    cart,
    addToCartWithToast,
    removeWithConfirm,
  }
}
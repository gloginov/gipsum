export function useCartPersistence() {
  const cart = useCartStore()
  
  // Cookie для хранения ID сессии корзины
  const cartSession = useCookie('cart-session', {
    maxAge: 60 * 60 * 24 * 30, // 30 дней
  })
  
  // Загрузка при старте
  async function init() {
    await cart.fetchCart()
  }
  
  return {
    init,
    cartSession,
  }
}
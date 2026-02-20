import { get } from '@nuxt/ui/runtime/utils/index.js'
import { defineStore } from 'pinia'
import type { Cart, CartItem, CartAddPayload, CartUpdatePayload, CartRemovePayload } from '~/types/cart'
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

interface CartState {
  items: CartItem[]
  total: string
  count: number
  isLoading: boolean
  isUpdating: boolean
  error: string | null
}

export const useCartStore = defineStore('cart', {
  state: (): CartState => ({
    items: [],
    total: '0.00',
    count: 0,
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    // Проверка пустой корзины
    isEmpty: (state) => state.count === 0,
    
    // Общая сумма как число
    totalNumeric: (state) => parseFloat(state.total) || 0,
    
    // Количество уникальных товаров
    uniqueItemsCount: (state) => state.items.length,
    
    // Проверка наличия товара в корзине
    hasItem: (state) => (productId: number) => {
      return state.items.some(item => item.product_id === productId)
    },
    
    // Получение количества конкретного товара
    getItemQuantity: (state) => (productId: number) => {
      const item = state.items.find(i => i.product_id === productId)
      return item?.quantity || 0
    },
    
    // Проверка возможности увеличить количество
    canIncreaseQuantity: (state) => (productId: number) => {
      const item = state.items.find(i => i.product_id === productId)
      return item ? item.quantity < item.stock : false
    },
  },

  actions: {
    // Сброс ошибки
    clearError() {
      this.error = null
    },

    // Загрузка корзины с сервера
    async fetchCart() {
      this.isLoading = true
      this.error = null
      
      try {
        const { data, error } = await useFetch<Cart>('/api/cart/', {
          credentials: 'include',
          baseURL: getCurrentApiUrl()
        })
        
        if (error.value) {
          throw new Error(error.value.data?.error || 'Failed to load cart')
        }
        
        if (data.value) {
          this.items = data.value.items
          this.total = data.value.total
          this.count = data.value.count
        }
      } catch (err: any) {
        this.error = err.message
        console.error('Fetch cart error:', err)
      } finally {
        this.isLoading = false
      }
    },

    // Добавление товара в корзину
    async addToCart(payload: CartAddPayload) {
      this.isUpdating = true
      this.error = null
      
      try {
        const { data, error } = await useFetch<{
          message: string
          cart: Cart
        }>('/api/cart/add/', {
          method: 'POST',
          body: payload,
          credentials: 'include',
          baseURL: getCurrentApiUrl()
        })
        
        if (error.value) {
          throw new Error(error.value.data?.error || 'Failed to add to cart')
        }
        
        if (data.value?.cart) {
          this.items = data.value.cart.items
          this.total = data.value.cart.total
          this.count = data.value.cart.count
        }
        
        return { success: true, message: data.value?.message }
      } catch (err: any) {
        this.error = err.message
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Обновление количества
    async updateQuantity(payload: CartUpdatePayload) {
      this.isUpdating = true
      this.error = null
      
      try {
        const { data, error } = await useFetch<{
          message: string
          cart: Cart
        }>('/api/cart/update/', {
          method: 'POST',
          body: payload,
          credentials: 'include',
          baseURL: getCurrentApiUrl()
        })
        
        if (error.value) {
          throw new Error(error.value.data?.error || 'Failed to update cart')
        }
        
        if (data.value?.cart) {
          this.items = data.value.cart.items
          this.total = data.value.cart.total
          this.count = data.value.cart.count
        }
        
        return { success: true }
      } catch (err: any) {
        this.error = err.message
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Удаление товара
    async removeFromCart(productId: number) {
      this.isUpdating = true
      this.error = null
      
      try {
        const { data, error } = await useFetch<{
          message: string
          cart: Cart
        }>('/api/cart/remove/', {
          method: 'POST',
          body: { product_id: productId },
          credentials: 'include',
          baseURL: getCurrentApiUrl()
        })
        
        if (error.value) {
          throw new Error(error.value.data?.error || 'Failed to remove from cart')
        }
        
        if (data.value?.cart) {
          this.items = data.value.cart.items
          this.total = data.value.cart.total
          this.count = data.value.cart.count
        }
        
        return { success: true }
      } catch (err: any) {
        this.error = err.message
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Очистка корзины
    async clearCart() {
      this.isUpdating = true
      this.error = null
      
      try {
        const { data, error } = await useFetch<{
          message: string
          cart: Cart
        }>('/api/cart/clear/', {
          method: 'POST',
          credentials: 'include',
          baseURL: getCurrentApiUrl()
        })
        
        if (error.value) {
          throw new Error(error.value.data?.error || 'Failed to clear cart')
        }
        
        this.items = []
        this.total = '0.00'
        this.count = 0
        
        return { success: true }
      } catch (err: any) {
        this.error = err.message
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Быстрое добавление (без await для UI)
    quickAdd(productId: number, quantity: number = 1) {
      // Оптимистичное обновление UI
      const existingItem = this.items.find(i => i.product_id === productId)
      
      if (existingItem) {
        existingItem.quantity += quantity
        existingItem.total = String(parseFloat(existingItem.price) * existingItem.quantity)
      }
      
      // Фоновый запрос
      this.addToCart({ product_id: productId, quantity, override: false })
    },

    // Инициализация (вызвать в layout/app)
    async init() {
      await this.fetchCart()
    },
  },

  // Сохранение в localStorage (опционально)
  // persist: {
  //   storage: piniaPluginPersistedstate.localStorage(),
  //   paths: ['items', 'total', 'count'], // Что сохранять
  // },
})
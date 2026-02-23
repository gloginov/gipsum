import { defineStore } from 'pinia'
import type { Cart, CartItem, CartAddPayload, CartUpdatePayload } from '~/types/cart'

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
    isEmpty: (state) => state.count === 0,
    totalNumeric: (state) => parseFloat(state.total) || 0,
    uniqueItemsCount: (state) => state.items.length,
    hasItem: (state) => (productId: number) => {
      return state.items.some(item => item.product_id === productId)
    },
    getItemQuantity: (state) => (productId: number) => {
      const item = state.items.find(i => i.product_id === productId)
      return item?.quantity || 0
    },
    canIncreaseQuantity: (state) => (productId: number) => {
      const item = state.items.find(i => i.product_id === productId)
      return item ? item.quantity < item.stock : false
    },
  },

  actions: {
    clearError() {
      this.error = null
    },

    // Получение baseURL для API
    getApiUrl(): string {
      const config = useRuntimeConfig()
      // На сервере используем прямой URL к Django, на клиенте — публичный
      if (process.server) {
        return config.apiBaseUrl || 'http://server-gipsum:5000'
      }
      return config.public.apiBase || 'https://api.gipsum.docker'
    },

    // Получение headers с cookies для SSR
    getHeaders(): Record<string, string> {
      if (process.server) {
        // На сервере пробрасываем cookies от клиента
        const headers = useRequestHeaders(['cookie'])
        return {
          ...headers,
          'Accept': 'application/json',
        }
      }
      // На клиенте cookies отправляются автоматически
      return {
        'Accept': 'application/json',
      }
    },

    // Загрузка корзины — работает и на сервере, и на клиенте
    async fetchCart() {
      this.isLoading = true
      this.error = null
      
      try {
        const data = await $fetch<Cart>('/api/cart/', {
          baseURL: this.getApiUrl(),
          headers: this.getHeaders(),
          credentials: 'include',
        })

        if (data) {
          this.items = data.items
          this.total = data.total
          this.count = data.count
        }

        return { success: true, data }
      } catch (err: any) {
        this.error = err.message || 'Failed to load cart'
        console.error('Fetch cart error:', err)
        return { success: false, error: err.message }
      } finally {
        this.isLoading = false
      }
    },

    // Добавление товара (только клиент)
    async addToCart(payload: CartAddPayload) {
      this.isUpdating = true
      this.error = null
      
      try {
        const data = await $fetch<{
          message: string
          cart: Cart
        }>('/api/cart/add/', {
          method: 'POST',
          body: payload,
          baseURL: this.getApiUrl(),
          headers: this.getHeaders(),
          credentials: 'include',
        })
        
        if (data?.cart) {
          this.items = data.cart.items
          this.total = data.cart.total
          this.count = data.cart.count
        }
        
        return { success: true, message: data?.message }
      } catch (err: any) {
        this.error = err.message || 'Failed to add to cart'
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Обновление количества (только клиент)
    async updateQuantity(payload: CartUpdatePayload) {
      this.isUpdating = true
      this.error = null
      
      try {
        const data = await $fetch<{
          message: string
          cart: Cart
        }>('/api/cart/update/', {
          method: 'POST',
          body: payload,
          baseURL: this.getApiUrl(),
          headers: this.getHeaders(),
          credentials: 'include',
        })
        
        if (data?.cart) {
          this.items = data.cart.items
          this.total = data.cart.total
          this.count = data.cart.count
        }
        
        return { success: true, message: data?.message }
      } catch (err: any) {
        this.error = err.message || 'Failed to update cart'
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Удаление товара (только клиент)
    async removeFromCart(productId: number) {
      this.isUpdating = true
      this.error = null
      
      try {
        const data = await $fetch<{
          message: string
          cart: Cart
        }>('/api/cart/remove/', {
          method: 'POST',
          body: { product_id: productId },
          baseURL: this.getApiUrl(),
          headers: this.getHeaders(),
          credentials: 'include',
        })
        
        if (data?.cart) {
          this.items = data.cart.items
          this.total = data.cart.total
          this.count = data.cart.count
        }
        
        return { success: true, message: data?.message }
      } catch (err: any) {
        this.error = err.message || 'Failed to remove from cart'
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Очистка корзины (только клиент)
    async clearCart() {
      this.isUpdating = true
      this.error = null
      
      try {
        await $fetch('/api/cart/clear/', {
          method: 'POST',
          baseURL: this.getApiUrl(),
          headers: this.getHeaders(),
          credentials: 'include',
        })
        
        this.items = []
        this.total = '0.00'
        this.count = 0
        
        return { success: true }
      } catch (err: any) {
        this.error = err.message || 'Failed to clear cart'
        return { success: false, message: err.message }
      } finally {
        this.isUpdating = false
      }
    },

    // Быстрое добавление (оптимистичное)
    quickAdd(productId: number, quantity: number = 1) {
      const existingItem = this.items.find(i => i.product_id === productId)
      
      if (existingItem) {
        existingItem.quantity += quantity
        existingItem.total = String(parseFloat(existingItem.price) * existingItem.quantity)
      }
      
      // Фоновый запрос
      this.addToCart({ product_id: productId, quantity, override: false })
    },

    // Инициализация — вызывать в компоненте через useAsyncData
    async init() {
      return await this.fetchCart()
    },
  },
})
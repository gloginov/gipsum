<template>
  <NuxtLink to="/cart" class="relative">
    <UButton
      color="neutral"
      variant="ghost"
      icon="i-lucide-shopping-cart"
      :loading="cart.isLoading"
    />
    
    <!-- Бейдж с количеством -->
    <UBadge
      v-if="cart.count > 0"
      color="primary"
      size="xs"
      class="absolute -top-1 -right-1 min-w-[20px] text-center"
    >
      {{ cart.count > 99 ? '99+' : cart.count }}
    </UBadge>
  </NuxtLink>
</template>

<script setup lang="ts">
const cart = useCartStore()

// Загружаем корзину при монтировании
onMounted(() => {
  cart.fetchCart()
})
</script>
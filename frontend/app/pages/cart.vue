<template>
  <UPage>
    <UPageHeader
      title="Корзина"
      :description="`Товаров: ${cart.count}`"
    />

    <UPageBody>
      <!-- Загрузка -->
      <div
        v-if="cart.isLoading"
        class="flex justify-center py-12"
      >
        <ULoading size="lg" />
      </div>

      <!-- Пустая корзина -->
      <UAlert
        v-else-if="cart.isEmpty"
        icon="i-lucide-shopping-cart"
        title="Корзина пуста"
        description="Добавьте товары из каталога"
      >
        <template #actions>
          <UButton
            to="/catalog"
            color="primary"
          >
            В каталог
          </UButton>
        </template>
      </UAlert>

      <!-- Список товаров -->
      <template v-else>
        <UCard
          v-for="item in cart.items"
          :key="item.id"
          class="mb-4"
        >
          <div class="flex gap-4">
            <!-- Изображение -->
            <img
              :src="item.main_image || '/placeholder.png'"
              class="w-24 h-24 object-cover rounded"
              :alt="item.product_name"
            >

            <!-- Информация -->
            <div class="flex-1">
              <NuxtLink
                :to="`/product/${item.product_slug}`"
                class="font-semibold hover:text-primary"
              >
                {{ item.product_name }}
              </NuxtLink>

              <p class="text-gray-500 text-sm">
                {{ item.price }} ₽ / шт.
              </p>

              <!-- Управление количеством -->
              <div class="flex items-center gap-2 mt-2">
                <UButton
                  color="neutral"
                  variant="soft"
                  size="xs"
                  icon="i-lucide-minus"
                  :disabled="item.quantity <= 1 || cart.isUpdating"
                  @click="updateQuantity(item.product_id, item.quantity - 1)"
                />

                <span class="w-8 text-center">{{ item.quantity }}</span>

                <UButton
                  color="neutral"
                  variant="soft"
                  size="xs"
                  icon="i-lucide-plus"
                  :disabled="!cart.canIncreaseQuantity(item.product_id) || cart.isUpdating"
                  @click="updateQuantity(item.product_id, item.quantity + 1)"
                />
              </div>
            </div>

            <!-- Цена и удаление -->
            <div class="text-right">
              <p class="font-bold">
                {{ item.total }} ₽
              </p>
              <UButton
                color="red"
                variant="ghost"
                size="xs"
                icon="i-lucide-trash-2"
                :loading="cart.isUpdating"
                @click="removeItem(item.product_id, item.product_name)"
              />
            </div>
          </div>
        </UCard>

        <!-- Итого -->
        <UCard class="mt-6">
          <div class="flex justify-between items-center">
            <div>
              <p class="text-gray-500">
                Всего товаров: {{ cart.count }}
              </p>
              <p class="text-2xl font-bold">
                {{ cart.total }} ₽
              </p>
            </div>

            <div class="flex gap-2">
              <UButton
                color="neutral"
                variant="soft"
                :loading="cart.isUpdating"
                @click="cart.clearCart()"
              >
                Очистить
              </UButton>
              <UButton
                color="primary"
                to="/checkout"
              >
                Оформить заказ
              </UButton>
            </div>
          </div>
        </UCard>
      </template>
    </UPageBody>
  </UPage>
</template>

<script setup lang="ts">
const cart = useCartStore()
const { removeWithConfirm } = useCart()

// Загружаем корзину
onMounted(() => {
  cart.fetchCart()
})

async function updateQuantity(productId: number, quantity: number) {
  if (quantity < 1) return

  const result = await cart.updateQuantity({ product_id: productId, quantity })

  if (!result.success) {
    useToast().add({
      title: 'Ошибка',
      description: result.message,
      color: 'error'
    })
  }
}

async function removeItem(productId: number, productName: string) {
  await removeWithConfirm(productId, productName)
}
</script>

<template>
  <UPage>
    <UPageHeader
      title="Мои заказы"
      description="История и статус ваших заказов"
    />

    <UPageBody>
      <!-- Загрузка -->
      <div
        v-if="pending"
        class="flex justify-center py-12"
      >
        <ULoading size="lg" />
      </div>

      <!-- Ошибка -->
      <UAlert
        v-else-if="error"
        icon="i-lucide-alert-triangle"
        title="Ошибка загрузки"
        description="Не удалось загрузить список заказов"
        color="error"
      />

      <!-- Пусто -->
      <UAlert
        v-else-if="!orders?.length"
        icon="i-lucide-package"
        title="Нет заказов"
        description="Вы ещё не сделали ни одного заказа"
        color="neutral"
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

      <!-- Список заказов -->
      <div
        v-else
        class="space-y-4"
      >
        <UCard
          v-for="order in orders"
          :key="order.id"
          class="hover:shadow-md transition-shadow"
        >
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <!-- Информация о заказе -->
            <div class="flex-1">
              <div class="flex items-center gap-3 flex-wrap">
                <NuxtLink
                  :to="`/orders/${order.order_number}`"
                  class="text-lg font-mono font-medium hover:text-primary-600 transition-colors"
                >
                  {{ order.order_number }}
                </NuxtLink>
                <OrderStatusBadge
                  :status="order.status"
                  size="sm"
                />
              </div>

              <div class="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span class="flex items-center gap-1">
                  <UIcon
                    name="i-lucide-calendar"
                    class="w-4 h-4"
                  />
                  {{ formatDate(order.created_at) }}
                </span>
                <span class="flex items-center gap-1">
                  <UIcon
                    name="i-lucide-wallet"
                    class="w-4 h-4"
                  />
                  {{ formatPrice(order.total) }} ₽
                </span>
              </div>
            </div>

            <!-- Действия -->
            <div class="flex items-center gap-2">
              <UBadge
                v-if="order.paid"
                color="success"
                variant="soft"
                size="sm"
              >
                Оплачен
              </UBadge>
              <UButton
                :to="`/orders/${order.order_number}`"
                color="primary"
                variant="soft"
                size="sm"
                trailing-icon="i-lucide-arrow-right"
              >
                Подробнее
              </UButton>
            </div>
          </div>
        </UCard>
      </div>
    </UPageBody>
  </UPage>
</template>

<script setup lang="ts">
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

definePageMeta({
  middleware: ['auth']
})

// Загрузка заказов
const { data: orders, pending, error } = await useAsyncData(
  'my-orders',
  () => $fetch('/api/orders/my_orders/', {
    baseURL: getCurrentApiUrl(),
    headers: useRequestHeaders(['cookie']),
    credentials: 'include'
  })
)

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

function formatPrice(price: string | number): string {
  const num = typeof price === 'string' ? parseFloat(price) : price
  return num.toFixed(2)
}

// SEO
useHead({
  title: 'Мои заказы | Gipsum'
})
</script>

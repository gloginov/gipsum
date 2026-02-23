<template>
  <UPage>
    <UPageHeader
      :title="`Заказ ${order?.order_number || ''}`"
      :description="order ? `Создан ${formatDate(order.created_at)}` : ''"
    >
      <template #right>
        <UButton
          to="/orders"
          color="neutral"
          variant="ghost"
          icon="i-lucide-arrow-left"
        >
          К заказам
        </UButton>
      </template>
    </UPageHeader>

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
        :description="error.message || 'Не удалось загрузить заказ'"
        color="error"
      >
        <template #actions>
          <UButton @click="refresh()">
            Повторить
          </UButton>
        </template>
      </UAlert>

      <!-- Не найден -->
      <UAlert
        v-else-if="!order"
        icon="i-lucide-search"
        title="Заказ не найден"
        description="Возможно, он был удалён или у вас нет доступа"
        color="neutral"
      >
        <template #actions>
          <UButton
            to="/orders"
            color="primary"
          >
            Мои заказы
          </UButton>
        </template>
      </UAlert>

      <!-- Контент заказа -->
      <div
        v-else
        class="grid grid-cols-1 lg:grid-cols-3 gap-8"
      >
        <!-- Левая колонка: таймлайн и товары -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Статус -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold">
                  Статус заказа
                </h3>
                <OrderStatusBadge :status="order.status" />
              </div>
            </template>

            <OrderTimeline
              :status="order.status"
              :created-at="order.created_at"
              :updated-at="order.updated_at"
            />
          </UCard>

          <!-- Товары -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">
                Товары заказа
              </h3>
            </template>

            <OrderItemsList
              :items="order.items"
              :subtotal="order.subtotal"
              :shipping-cost="order.shipping_cost"
              :tax="order.tax"
              :total="order.total"
            />
          </UCard>
        </div>

        <!-- Правая колонка: информация -->
        <div>
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">
                Информация о заказе
              </h3>
            </template>

            <OrderInfoCard :order="order" />
          </UCard>

          <!-- Действия -->
          <div class="mt-4 space-y-2">
            <UButton
              v-if="canResendEmail"
              block
              color="neutral"
              variant="soft"
              icon="i-lucide-mail"
              :loading="resendingEmail"
              @click="resendEmail"
            >
              Отправить письмо повторно
            </UButton>

            <UButton
              to="/catalog"
              block
              color="primary"
              icon="i-lucide-shopping-bag"
            >
              Продолжить покупки
            </UButton>
          </div>
        </div>
      </div>
    </UPageBody>
  </UPage>
</template>

<script setup lang="ts">
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

definePageMeta({
  middleware: ['auth'] // или ваш middleware для проверки авторизации
})

const route = useRoute()
const toast = useToast()
const orderNumber = route.params.orderNumber as string

// Загрузка заказа
const { data: order, pending, error, refresh } = await useAsyncData(
  `order-${orderNumber}`,
  () => $fetch(`/api/orders/${orderNumber}/`, {
    baseURL: getCurrentApiUrl(),
    headers: useRequestHeaders(['cookie']),
    credentials: 'include'
  })
)

// Проверка прав на повторную отправку письма
const canResendEmail = computed(() => {
  return order.value && !order.value.email_sent
})

const resendingEmail = ref(false)

async function resendEmail() {
  if (!order.value) return

  resendingEmail.value = true
  try {
    await $fetch(`/api/orders/${order.value.order_number}/resend_email/`, {
      method: 'POST',
      baseURL: getCurrentApiUrl(),
      headers: useRequestHeaders(['cookie']),
      credentials: 'include'
    })

    toast.add({
      title: 'Успешно',
      description: 'Письмо отправлено повторно',
      color: 'success'
    })
  } catch (err: any) {
    toast.add({
      title: 'Ошибка',
      description: err.data?.error || 'Не удалось отправить письмо',
      color: 'error'
    })
  } finally {
    resendingEmail.value = false
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

// SEO
useHead(() => ({
  title: order.value
    ? `Заказ ${order.value.order_number} | Gipsum`
    : 'Заказ | Gipsum'
}))
</script>

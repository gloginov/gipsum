<template>
  <div class="space-y-6">
    <!-- Номер заказа и дата -->
    <div>
      <p class="text-sm text-gray-500">
        Номер заказа
      </p>
      <p class="text-lg font-mono font-medium">
        {{ order.order_number }}
      </p>
    </div>

    <UDivider />

    <!-- Даты -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <p class="text-sm text-gray-500">
          Создан
        </p>
        <p class="font-medium">
          {{ formatDate(order.created_at) }}
        </p>
      </div>
      <div v-if="order.paid_at">
        <p class="text-sm text-gray-500">
          Оплачен
        </p>
        <p class="font-medium">
          {{ formatDate(order.paid_at) }}
        </p>
      </div>
    </div>

    <UDivider />

    <!-- Клиент -->
    <div>
      <p class="text-sm text-gray-500 mb-2">
        Получатель
      </p>
      <div class="space-y-1">
        <p class="font-medium">
          {{ order.first_name }} {{ order.last_name }}
        </p>
        <div class="flex items-center gap-2 text-sm text-gray-600">
          <UIcon
            name="i-lucide-mail"
            class="w-4 h-4"
          />
          {{ order.email }}
        </div>
        <div class="flex items-center gap-2 text-sm text-gray-600">
          <UIcon
            name="i-lucide-phone"
            class="w-4 h-4"
          />
          {{ order.phone }}
        </div>
      </div>
    </div>

    <UDivider />

    <!-- Адрес -->
    <div>
      <p class="text-sm text-gray-500 mb-2">
        Адрес доставки
      </p>
      <div class="space-y-1 text-sm">
        <p>{{ order.address }}</p>
        <p>{{ order.city }}, {{ order.postal_code }}</p>
        <p>{{ countryName }}</p>
      </div>
    </div>

    <UDivider v-if="order.customer_note" />

    <!-- Примечание -->
    <div v-if="order.customer_note">
      <p class="text-sm text-gray-500 mb-1">
        Примечание к заказу
      </p>
      <p class="text-sm bg-gray-50 p-3 rounded-lg">
        {{ order.customer_note }}
      </p>
    </div>

    <!-- Статус оплаты -->
    <UAlert
      v-if="order.paid"
      icon="i-lucide-check-circle"
      title="Оплачен"
      color="success"
      variant="soft"
    />
    <UAlert
      v-else
      icon="i-lucide-clock"
      title="Ожидает оплаты"
      color="warning"
      variant="soft"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  order: {
    order_number: string
    first_name: string
    last_name: string
    email: string
    phone: string
    address: string
    city: string
    postal_code: string
    country: string
    customer_note?: string
    created_at: string
    paid: boolean
    paid_at?: string
  }
}

const props = defineProps<Props>()

const countryNames: Record<string, string> = {
  RU: 'Россия',
  KZ: 'Казахстан',
  BY: 'Беларусь',
  USA: 'США'
}

const countryName = computed(() =>
  countryNames[props.order.country] || props.order.country
)

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}
</script>

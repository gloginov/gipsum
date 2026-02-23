<template>
  <div class="space-y-4">
    <div
      v-for="(step, index) in timelineSteps"
      :key="step.status"
      class="flex gap-4 relative"
    >
      <!-- Линия соединения -->
      <div
        v-if="index < timelineSteps.length - 1"
        class="absolute left-5 top-10 bottom-0 w-0.5 bg-gray-200"
        :class="{ 'bg-primary-500': step.isCompleted }"
      />

      <!-- Иконка статуса -->
      <div
        class="relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0"
        :class="stepClasses(step)"
      >
        <UIcon
          :name="step.icon"
          class="w-5 h-5"
        />
      </div>

      <!-- Контент -->
      <div class="flex-1 pb-8">
        <p
          class="font-medium"
          :class="step.isActive || step.isCompleted ? 'text-gray-900' : 'text-gray-400'"
        >
          {{ step.title }}
        </p>
        <p
          v-if="step.description"
          class="text-sm mt-1"
          :class="step.isActive || step.isCompleted ? 'text-gray-600' : 'text-gray-400'"
        >
          {{ step.description }}
        </p>
        <p
          v-if="step.date"
          class="text-xs text-gray-400 mt-1"
        >
          {{ formatDate(step.date) }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type OrderStatus = 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled'

interface Props {
  status: OrderStatus | string
  createdAt: string
  updatedAt?: string
}

const props = defineProps<Props>()

const statusOrder = ['pending', 'processing', 'shipped', 'delivered']

const timelineSteps = computed(() => {
  const currentStatus = props.status
  const isCancelled = currentStatus === 'cancelled'

  const steps = [
    {
      status: 'pending',
      title: 'Заказ создан',
      description: 'Ожидает подтверждения',
      icon: 'i-lucide-file-text',
      isCompleted: !isCancelled && statusOrder.indexOf(currentStatus) > 0,
      isActive: currentStatus === 'pending',
      date: props.createdAt
    },
    {
      status: 'processing',
      title: 'В обработке',
      description: 'Собираем ваш заказ',
      icon: 'i-lucide-package',
      isCompleted: !isCancelled && statusOrder.indexOf(currentStatus) > 1,
      isActive: currentStatus === 'processing',
      date: currentStatus !== 'pending' ? props.updatedAt : undefined
    },
    {
      status: 'shipped',
      title: 'Отправлен',
      description: 'Заказ в пути',
      icon: 'i-lucide-truck',
      isCompleted: !isCancelled && statusOrder.indexOf(currentStatus) > 2,
      isActive: currentStatus === 'shipped',
      date: ['shipped', 'delivered'].includes(currentStatus) ? props.updatedAt : undefined
    },
    {
      status: 'delivered',
      title: 'Доставлен',
      description: 'Заказ получен',
      icon: 'i-lucide-check-circle',
      isCompleted: currentStatus === 'delivered',
      isActive: currentStatus === 'delivered',
      date: currentStatus === 'delivered' ? props.updatedAt : undefined
    }
  ]

  // Если заказ отменён, показываем только отмену
  if (isCancelled) {
    return [
      {
        status: 'pending',
        title: 'Заказ создан',
        icon: 'i-lucide-file-text',
        isCompleted: true,
        isActive: false,
        date: props.createdAt
      },
      {
        status: 'cancelled',
        title: 'Заказ отменён',
        description: 'Свяжитесь с поддержкой для уточнения',
        icon: 'i-lucide-x-circle',
        isCompleted: false,
        isActive: true,
        date: props.updatedAt
      }
    ]
  }

  return steps
})

function stepClasses(step: any) {
  if (step.isActive) return 'bg-primary-500 text-white ring-4 ring-primary-100'
  if (step.isCompleted) return 'bg-primary-500 text-white'
  return 'bg-gray-100 text-gray-400'
}

function formatDate(dateString: string | undefined) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

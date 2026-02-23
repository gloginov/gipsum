<template>
  <UBadge
    :color="statusColor"
    :variant="variant"
    size="md"
    class="font-medium"
  >
    <template #leading>
      <UIcon :name="statusIcon" />
    </template>
    {{ statusText }}
  </UBadge>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type OrderStatus = 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled'

interface Props {
  status: OrderStatus | string
  variant?: 'solid' | 'soft' | 'outline' | 'subtle'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'soft'
})

const statusConfig: Record<string, { color: any, icon: string, text: string }> = {
  pending: {
    color: 'warning',
    icon: 'i-lucide-clock',
    text: 'Ожидает обработки'
  },
  processing: {
    color: 'info',
    icon: 'i-lucide-loader-2',
    text: 'Обрабатывается'
  },
  shipped: {
    color: 'primary',
    icon: 'i-lucide-truck',
    text: 'Отправлен'
  },
  delivered: {
    color: 'success',
    icon: 'i-lucide-check-circle',
    text: 'Доставлен'
  },
  cancelled: {
    color: 'error',
    icon: 'i-lucide-x-circle',
    text: 'Отменён'
  }
}

const statusColor = computed(() => statusConfig[props.status]?.color || 'neutral')
const statusIcon = computed(() => statusConfig[props.status]?.icon || 'i-lucide-help-circle')
const statusText = computed(() => statusConfig[props.status]?.text || props.status)
</script>

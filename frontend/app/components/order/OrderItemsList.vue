<template>
  <div class="space-y-4">
    <div
      v-for="item in items"
      :key="item.product_name"
      class="flex gap-4 py-4 border-b border-gray-100 last:border-0"
    >
      <!-- Изображение -->
      <div class="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden shrink-0">
        <img
          v-if="item.product?.main_image"
          :src="item.product.main_image"
          class="w-full h-full object-cover"
          :alt="item.product_name"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
          <UIcon name="i-lucide-image" class="w-8 h-8" />
        </div>
      </div>

      <!-- Информация -->
      <div class="flex-1 min-w-0">
        <p class="font-medium text-gray-900 truncate">
          {{ item.product_name }}
        </p>
        <p class="text-sm text-gray-500 mt-1">
          {{ formatPrice(item.product_price) }} ₽ × {{ item.quantity }}
        </p>
      </div>

      <!-- Сумма -->
      <div class="text-right shrink-0">
        <p class="font-semibold text-gray-900">{{ formatPrice(item.total) }} ₽</p>
      </div>
    </div>

    <!-- Итого -->
    <div class="space-y-2 pt-4 border-t border-gray-200">
      <div class="flex justify-between text-sm">
        <span class="text-gray-500">Товары</span>
        <span>{{ formatPrice(subtotal) }} ₽</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-500">Доставка</span>
        <span :class="shippingCost === 0 ? 'text-green-600' : ''">
          {{ shippingCost === 0 ? "Бесплатно" : formatPrice(shippingCost) + " ₽" }}
        </span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-500">Налог</span>
        <span>{{ formatPrice(tax) }} ₽</span>
      </div>
      <UDivider />
      <div class="flex justify-between items-center">
        <span class="text-lg font-semibold">Итого</span>
        <span class="text-2xl font-bold text-primary-600"
          >{{ formatPrice(total) }} ₽</span
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface OrderItem {
  product_name: string;
  product_price: string | number;
  quantity: number;
  total: string | number;
  product?: {
    main_image?: string;
    slug?: string;
  };
}

interface Props {
  items: OrderItem[];
  subtotal: string | number;
  shippingCost: string | number;
  tax: string | number;
  total: string | number;
}

defineProps<Props>();

function formatPrice(price: string | number): string {
  const num = typeof price === "string" ? parseFloat(price) : price;
  return num.toFixed(2);
}
</script>

<template>
  <UPageGrid
    v-if="props?.items && props.items.length > 0"
    class="w-full max-w-(--ui-container) mx-auto px-4 sm:px-6 lg:px-8 relative z-10 pt-20 pb-0"

    :cols="3"
    :gap="6"
    :item-key="'id'"
  >
    <ProductItem
      v-for="product in items"
      :key="product.id"
      :product="product"
      :view-mode="viewMode"
    />
  </UPageGrid>
  <!-- <div :class="gridClass">
    <ProductCard
      v-for="product in items"
      :key="product.id"
      :product="product"
      :view-mode="viewMode"
    />
  </div> -->
</template>

<script setup lang="ts">
import type { Product } from '~/types/product'

interface Props {
  items: Product[]
  viewMode?: 'grid' | 'list'
}

const props = withDefaults(defineProps<Props>(), {
  viewMode: 'grid'
})
</script>

<script setup lang="ts">
import type { Product } from '~/types/product'
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

const props = defineProps<{
  product: Product
  viewMode?: 'grid' | 'list' | 'undefined'
}>()
</script>

<template>
  <UBlogPost
    :title="props?.product?.name"
    :description="props?.product?.short_description"
    :badge="props?.product?.is_new ? {
      label: 'Новинка',
      color: 'primary',
      variant: 'solid'
    } : undefined"
    :image="{
      src: getCurrentApiUrl() + props?.product?.main_image?.url,
      alt: props?.product?.main_image?.alt || props?.product?.name
    }"
    :to="'/products/'+ props?.product?.id"
    :ui="{
      header: 'relative overflow-hidden aspect-[9/9] w-full pointer-events-none',
      image: 'object-cover object-center w-full h-full transform transition-transform duration-200 group-hover/blog-post:scale-110'
    }"
  >
    <template #footer>
      <div class="p-4 sm:p-6 -mt-4 flex justify-between items-center">
        <div class="space-y-2">
          <h4 class="text-lg font-semibold">
            {{ props?.product?.price }} ₽
          </h4>
        </div>

        <UButton
          variant="outline"
          color="primary"
          size="xl"
          :to="'/products/'+ props?.product?.id"
        >
          Купить
        </UButton>
      </div>
    </template>
  </UBlogPost>
</template>

<script setup lang="ts">
import type { ButtonProps } from '@nuxt/ui'
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'
import type { Product } from '~/types/product'
import Masonry from '~/components/gallery/Masonry.vue'
import Feedback from '~/components/form/Feedback.vue'

const { data } = await useFetch(
  'api/settings/?keys=site_name,site_description,site_header_image,about_products,about_products_lead,about_products_title,,about_products_description', {
    baseURL: getCurrentApiUrl()
  })

const links = ref<ButtonProps[]>([
  {
    label: 'Перейти в каталог',
    to: '/products',
    target: '_self'
  }
])

const { data: dataProductBestseller } = await useFetch('api/products/bestsellers/', {
  baseURL: getCurrentApiUrl()
})
const { data: dataMasonryImages } = await useFetch('api/galleries/galereya-na-glavnoj/', {
  baseURL: getCurrentApiUrl()
})
</script>

<template>
  <UPage>
    <div class="relative z-10 py-20">
      <div class="absolute inset-0 z-0">
        <img
          :src="
            getCurrentApiUrl() + data?.site_header_image?.value
              || '/assets/images/P1230407.JPG'
          "
          alt="Фон"
          class="w-full h-full object-cover"
        >
        <!-- Или видео -->
        <!-- <video autoplay muted loop class="w-full h-full object-cover">
        <source src="/hero-video.mp4" type="video/mp4">
      </video> -->
      </div>

      <!-- Затемнение фона (опционально) -->
      <div class="absolute inset-0 bg-black/20 z-1" />

      <UPageSection
        class="relative z-10 py-20"
        :title="data?.site_name?.value"
        :description="data?.site_description?.value"
      />
    </div>

    <UPageHero
      v-if="data?.about_products?.value"
      :title="data?.about_products_title?.value"
      :description="data?.about_products_description?.value"
      :headline="data?.about_products_lead?.value"
    />

    <Masonry
      v-if="!!dataMasonryImages?.images"
      :images="dataMasonryImages?.images"
    />

    <!-- <template #left ></template>

    <template #right >dasda</template> -->
    <UContainer
      id="popular-products"
      class="relative z-10 pt-10"
    >
      <UPageHeader
        title="Популярные товары"
        :links="links"
      />
      <ProductList
        v-if="dataProductBestseller"
        :items="dataProductBestseller as Product[]"
      />
    </UContainer>

    <UContainer
      id="feedback"
      class="relative z-10 py-10"
    >
      <UPageHeader
        title="Обратная связь"
        :ui="{
          root: 'relative py-8 flex justify-center border-none',
          wrapper: 'text-center',
          title: 'text-3xl sm:text-4xl font-bold text-highlighted no-underline border-none'
        }"
      />
      <Feedback />
    </UContainer>
  </UPage>
</template>

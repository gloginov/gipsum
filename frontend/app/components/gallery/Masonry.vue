<script setup lang="ts">
import type { Image } from '~/types/images'
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

const props = defineProps<{
  images: Image[]
}>()

// console.log(getCurrentApiUrl())
</script>

<template>
  <UContainer>
    <div class="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4 space-y-4">
      <div
        v-for="image in props.images"
        :key="image.id"
        class="break-inside-avoid"
      >
        <UCard :ui="{ body: 'p-0 sm:p-0', root: 'overflow-hidden' }">
          <NuxtImg
            :src="getCurrentApiUrl() + image.image_url_relative"
            :alt="image.alt_text"
            class="w-full h-auto"
            format="webp"
          />
        </UCard>
      </div>
    </div>
  </UContainer>
</template>

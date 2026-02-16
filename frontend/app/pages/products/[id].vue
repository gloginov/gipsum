<template>
  <UPage class="pt-20">
    <UContainer class="relative z-10 py-20">
      <div class="grid grid-cols-2 gap-12">
        <!-- Левая колонка: Слайдер изображений -->
        <div class="space-y-4">
          <Slider
            v-if="product?.main_image"
            :images="productImages"
          />
          <div
            v-else
            class="aspect-square bg-gray-100 rounded-lg flex items-center justify-center"
          >
            <UIcon
              name="i-heroicons-photo"
              class="w-20 h-20 text-gray-300"
            />
          </div>
        </div>

        <!-- Правая колонка: Информация о товаре -->
        <div class="space-y-6">
          <!-- Хлебные крошки -->
          <UBreadcrumb
            :links="breadcrumbLinks"
            class="mb-4"
          />

          <!-- Заголовок и метки -->
          <div class="space-y-2">
            <div class="flex items-center gap-2 flex-wrap">
              <UBadge
                v-if="product?.is_new"
                color="green"
                variant="soft"
              >
                Новинка
              </UBadge>
              <UBadge
                v-if="product?.is_bestseller"
                color="amber"
                variant="soft"
              >
                Хит продаж
              </UBadge>
              <UBadge
                v-if="product?.is_featured"
                color="purple"
                variant="soft"
              >
                Рекомендуем
              </UBadge>
              <UBadge
                v-if="!product?.is_available"
                color="red"
                variant="soft"
              >
                Нет в наличии
              </UBadge>
            </div>
            <h1 class="text-3xl font-bold text-gray-900">
              {{ product?.name }}
            </h1>
          </div>

          <!-- Категории -->
          <div
            v-if="product?.categories?.length"
            class="flex items-center gap-2 text-sm text-gray-600"
          >
            <span>Категории:</span>
            <NuxtLink
              v-for="cat in product.categories"
              :key="cat.id"
              :to="`/catalog/${cat.slug}`"
              class="text-primary-600 hover:text-primary-700 underline"
            >
              {{ cat.name }}
            </NuxtLink>
          </div>

          <!-- Цены -->
          <div class="flex items-baseline gap-4">
            <span class="text-4xl font-bold text-gray-900">
              {{ formatPrice(product?.price) }}
            </span>
            <span
              v-if="product?.old_price"
              class="text-xl text-gray-400 line-through"
            >
              {{ formatPrice(product.old_price) }}
            </span>
            <span
              v-if="product?.old_price"
              class="text-sm font-medium text-red-600 bg-red-50 px-2 py-1 rounded"
            >
              Экономия {{ calculateDiscount(product.price, product.old_price) }}%
            </span>
          </div>

          <!-- Краткое описание -->
          <p class="text-lg text-gray-600 leading-relaxed">
            {{ product?.short_description }}
          </p>

          <!-- Блок покупки -->
          <div class="bg-gray-50 rounded-xl p-6 space-y-4">
            <!-- Статус наличия -->
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">Наличие:</span>
              <span
                :class="product?.stock > 0 ? 'text-green-600' : 'text-red-600'"
                class="font-medium flex items-center gap-1"
              >
                <UIcon
                  :name="product?.stock > 0 ? 'i-heroicons-check-circle' : 'i-heroicons-x-circle'"
                  class="w-5 h-5"
                />
                {{ product?.stock > 0 ? `В наличии (${product.stock} шт.)` : 'Нет в наличии' }}
              </span>
            </div>

            <!-- Количество и кнопка -->
            <div class="flex items-center gap-4">
              <!-- Счетчик количества -->
              <div class="flex items-center border border-gray-300 rounded-lg bg-white">
                <UButton
                  variant="ghost"
                  color="gray"
                  icon="i-heroicons-minus"
                  :disabled="quantity <= 1"
                  @click="quantity--"
                />
                <span class="w-12 text-center font-medium">{{ quantity }}</span>
                <UButton
                  variant="ghost"
                  color="gray"
                  icon="i-heroicons-plus"
                  :disabled="quantity >= (product?.stock || 1)"
                  @click="quantity++"
                />
              </div>

              <!-- Кнопка добавления в корзину -->
              <UButton
                size="xl"
                color="primary"
                :loading="cartStore.isUpdating"
                :disabled="!product?.is_available || product?.stock === 0"
                class="flex-1 justify-center"
                @click="handleAddToCart"
              >
                <template #leading>
                  <UIcon name="i-heroicons-shopping-cart" />
                </template>
                {{ cartStore.hasItem(product?.id) ? 'Добавить ещё' : 'В корзину' }}
              </UButton>

              <!-- Кнопка быстрого заказа (опционально) -->
              <UButton
                v-if="product?.is_available"
                size="xl"
                variant="outline"
                color="gray"
                @click="openQuickOrder"
              >
                Купить в 1 клик
              </UButton>
            </div>

            <!-- Уведомление о добавлении -->
            <UAlert
              v-if="showSuccessMessage"
              color="green"
              variant="soft"
              icon="i-heroicons-check-circle"
              :title="`Товар добавлен в корзину (${cartStore.getItemQuantity(product?.id)} шт.)`"
              class="animate-fade-in"
            />
          </div>

          <!-- Полное описание -->
          <div
            v-if="product?.description"
            class="prose prose-gray max-w-none"
          >
            <h3 class="text-lg font-semibold mb-2">
              Описание
            </h3>
            <div v-html="product.description" />
          </div>

          <!-- SKU/Артикул -->
          <div class="text-sm text-gray-500 border-t pt-4">
            Артикул: <span class="font-mono">{{ product?.slug }}-{{ product?.id }}</span>
          </div>
        </div>
      </div>
    </UContainer>
  </UPage>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Slider from '~/components/Slider/Slider.vue'
import { useCartStore } from '~/stores/cart'
import type { Product } from '~/types/product'

const route = useRoute()
const cartStore = useCartStore()

// Состояние
const quantity = ref(1)
const showSuccessMessage = ref(false)

// Загрузка данных товара
const { data: product, pending, error } = await useFetch<Product>(`/api/products/${route.params.id}/`)

// SEO метаданные
useHead(() => ({
  title: product.value?.name
    ? `${product.value.name} — Купить по выгодной цене`
    : 'Товар не найден',
  meta: [
    {
      name: 'description',
      content: product.value?.short_description || 'Описание товара'
    },
    {
      property: 'og:title',
      content: product.value?.name
    },
    {
      property: 'og:description',
      content: product.value?.short_description
    },
    {
      property: 'og:image',
      content: product.value?.main_image?.url
    },
    {
      property: 'og:type',
      content: 'product'
    },
    {
      name: 'twitter:card',
      content: 'summary_large_image'
    }
  ],
  link: [
    {
      rel: 'canonical',
      href: `https://your-site.com/products/${route.params.id}`
    }
  ]
}))

// JSON-LD разметка для SEO
useJsonLd(() => {
  if (!product.value) return null

  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    'name': product.value.name,
    'image': product.value.main_image?.url,
    'description': product.value.short_description,
    'sku': `${product.value.slug}-${product.value.id}`,
    'offers': {
      '@type': 'Offer',
      'url': `https://your-site.com/products/${route.params.id}`,
      'priceCurrency': 'RUB',
      'price': product.value.price,
      'availability': product.value.is_available
        ? 'https://schema.org/InStock'
        : 'https://schema.org/OutOfStock',
      'itemCondition': 'https://schema.org/NewCondition'
    }
  }
})

// Вычисляемые свойства
const productImages = computed(() => {
  if (!product.value?.main_image) return []
  return [
    {
      url: product.value.main_image.url,
      alt: product.value.main_image.alt || product.value.name
    }
  ]
})

const breadcrumbLinks = computed(() => [
  { label: 'Главная', to: '/' },
  { label: 'Каталог', to: '/catalog' },
  ...(product.value?.categories?.[0]
    ? [{
        label: product.value.categories[0].name,
        to: `/catalog/${product.value.categories[0].slug}`
      }]
    : []),
  { label: product.value?.name || 'Товар', to: route.path }
])

// Методы
const formatPrice = (price?: number) => {
  if (!price) return '0 ₽'
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0
  }).format(price)
}

const calculateDiscount = (price: number, oldPrice: number) => {
  return Math.round(((oldPrice - price) / oldPrice) * 100)
}

const handleAddToCart = async () => {
  if (!product.value) return

  const result = await cartStore.addToCart({
    product_id: product.value.id,
    quantity: quantity.value,
    override: false
  })

  if (result.success) {
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)

    // Сбросить количество после добавления
    quantity.value = 1
  } else {
    // Показать ошибку
    useToast().add({
      title: 'Ошибка',
      description: result.message || 'Не удалось добавить товар в корзину',
      color: 'red'
    })
  }
}

const openQuickOrder = () => {
  // Открыть модалку быстрого заказа
  // или перенаправить на страницу оформления с pre-filled данными
  navigateTo({
    path: '/checkout/quick',
    query: { product_id: product.value?.id, quantity: quantity.value }
  })
}

// Инициализация корзины при монтировании
onMounted(() => {
  cartStore.init()
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

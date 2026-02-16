<template>
  <UPage>
    <div class="relative z-10 py-20">
      <div class="absolute inset-0 z-0">
        <img
          :src="
            getCurrentApiUrl() + data?.products_header_image?.value
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
    </div>

    <!-- Хлебные крошки -->
    <UBreadcrumb
      :links="breadcrumbLinks"
      class="mb-4"
    />

    <div class="flex gap-6">
      <!-- Боковая панель фильтров -->
      <aside class="w-64 flex-shrink-0 hidden lg:block">
        <div class="sticky top-4 space-y-6">
          <!-- Фильтр по категории -->
          <UCard v-if="categories.length">
            <template #header>
              <h3 class="font-semibold">
                Категории
              </h3>
            </template>
            <UAccordion :items="categoryAccordionItems" />
          </UCard>

          <!-- Фильтр по цене -->
          <UCard>
            <template #header>
              <h3 class="font-semibold">
                Цена
              </h3>
            </template>
            <div class="space-y-4">
              <div class="flex gap-2">
                <UInput
                  v-model="filters.min_price"
                  type="number"
                  placeholder="От"
                  size="sm"
                />
                <UInput
                  v-model="filters.max_price"
                  type="number"
                  placeholder="До"
                  size="sm"
                />
              </div>
              <URange
                v-model="priceRange"
                :min="0"
                :max="maxPrice"
                :step="100"
                @change="onPriceRangeChange"
              />
              <div class="flex justify-between text-sm text-gray-500">
                <span>{{ priceRange[0] }} ₽</span>
                <span>{{ priceRange[1] }} ₽</span>
              </div>
            </div>
          </UCard>

          <!-- Фильтры по наличию и статусу -->
          <UCard>
            <template #header>
              <h3 class="font-semibold">
                Наличие
              </h3>
            </template>
            <div class="space-y-2">
              <UCheckbox
                v-model="filters.in_stock"
                label="Только в наличии"
              />
              <UCheckbox
                v-model="filters.is_new"
                label="Новинки"
              />
              <UCheckbox
                v-model="filters.is_featured"
                label="Рекомендуемые"
              />
              <UCheckbox
                v-model="filters.is_bestseller"
                label="Хиты продаж"
              />
            </div>
          </UCard>

          <!-- Кнопка сброса -->
          <UButton
            block
            variant="soft"
            icon="i-heroicons-x-mark"
            @click="resetFilters"
          >
            Сбросить фильтры
          </UButton>
        </div>
      </aside>

      <!-- Основной контент -->
      <main class="flex-1">
        <!-- Мобильные фильтры -->
        <div class="lg:hidden mb-4">
          <UButton
            block
            icon="i-heroicons-funnel"
            @click.prevent="isMobileFilterOpen = true"
          >
            Фильтры
          </UButton>
        </div>

        <!-- Шапка каталога -->
        <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
          <h1 class="text-2xl font-bold">
            {{ currentCategory?.name || 'Каталог' }}
            <span class="text-gray-500 text-lg font-normal">
              ({{ pagination.count }} товаров)
            </span>
          </h1>

          <div class="flex items-center gap-4">
            <!-- Сортировка -->
            <USelectMenu
              v-model="sortOption"
              :items="sortOptions"
              option-attribute="label"
              value-attribute="value"
              class="w-48"
              @change="onSortChange"
            />

            <!-- Вид отображения -->
            <UButtonGroup>
              <UButton
                variant="soft"
                icon="i-heroicons-squares-2x2"
                @click="viewMode = 'grid'"
              />
              <UButton
                variant="soft"
                icon="i-heroicons-list-bullet"
                @click="viewMode = 'list'"
              />
            </UButtonGroup>
          </div>
        </div>

        <!-- Активные фильтры -->
        <div
          v-if="activeFilters.length"
          class="flex flex-wrap gap-2 mb-4"
        >
          <UBadge
            v-for="filter in activeFilters"
            :key="filter.key"
            color="primary"
            variant="soft"
            class="cursor-pointer"
            @click="removeFilter(filter.key)"
          >
            {{ filter.label }}
            <UIcon
              name="i-heroicons-x-mark"
              class="ml-1"
            />
          </UBadge>
        </div>

        <!-- Список товаров -->
        <div
          v-if="pending"
          class="flex justify-center py-12"
        >
          <ULoading size="lg" />
        </div>

        <div
          v-else-if="error"
          class="text-center py-12"
        >
          <UIcon
            name="i-heroicons-exclamation-triangle"
            class="text-4xl text-red-500 mb-2"
          />
          <p>Ошибка загрузки товаров</p>
          <UButton
            color="primary"
            @click="refresh"
          >
            Повторить
          </UButton>
        </div>

        <div
          v-else-if="!products.length"
          class="text-center py-12"
        >
          <UIcon
            name="i-heroicons-inbox"
            class="text-4xl text-gray-400 mb-2"
          />
          <p class="text-gray-500">
            Товары не найдены
          </p>
          <UButton
            color="primary"
            variant="soft"
            @click="resetFilters"
          >
            Сбросить фильтры
          </UButton>
        </div>

        <template v-else>
          <!-- Плитка товаров -->
          <ProductList
            :items="products"
            :view-mode="viewMode"
          />

          <!-- Пагинация -->
          <div
            v-if="pagination.pages > 1"
            class="mt-8 flex justify-center"
          >
            <UPagination
              v-model="page"
              :total="pagination.count"
              :page-count="pageSize"
              :max="5"
              @update:model-value="onPageChange"
            />
          </div>
        </template>
      </main>
    </div>

    <!-- Мобильный drawer с фильтрами -->
    <USlideover
      v-model:open="isMobileFilterOpen"
      side="left"
    >
      <template #body>
        <div class="p-4 space-y-6 h-full overflow-y-auto">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">
              Фильтры
            </h2>
            <UButton
              variant="ghost"
              icon="i-heroicons-x-mark"
              @click="isMobileFilterOpen = false"
            />
          </div>

          <!-- Мобильные фильтры (такие же как в aside) -->
          <UCard v-if="categories.length">
            <template #header>
              <h3 class="font-semibold">
                Категории
              </h3>
            </template>
            <UAccordion :items="categoryAccordionItems" />
          </UCard>

          <UCard>
            <template #header>
              <h3 class="font-semibold">
                Цена
              </h3>
            </template>
            <div class="space-y-4">
              <div class="flex gap-2">
                <UInput
                  v-model="filters.min_price"
                  type="number"
                  placeholder="От"
                />
                <UInput
                  v-model="filters.max_price"
                  type="number"
                  placeholder="До"
                />
              </div>
              <URange
                v-model="priceRange"
                :min="0"
                :max="maxPrice"
                :step="100"
                @change="onPriceRangeChange"
              />
            </div>
          </UCard>

          <UCard>
            <template #header>
              <h3 class="font-semibold">
                Наличие
              </h3>
            </template>
            <div class="space-y-2">
              <UCheckbox
                v-model="filters.in_stock"
                label="Только в наличии"
              />
              <UCheckbox
                v-model="filters.is_new"
                label="Новинки"
              />
              <UCheckbox
                v-model="filters.is_featured"
                label="Рекомендуемые"
              />
              <UCheckbox
                v-model="filters.is_bestseller"
                label="Хиты продаж"
              />
            </div>
          </UCard>

          <UButton
            block
            color="primary"
            @click="applyFilters"
          >
            Применить
          </UButton>
          <UButton
            block
            color="gray"
            variant="soft"
            @click="resetFilters"
          >
            Сбросить
          </UButton>
        </div>
      </template>
    </USlideover>
  </UPage>
</template>

<script setup lang="ts">
import type { Product } from '~/types/product'
import type { Category } from '~/types/category'
import type { Filters } from '~/types/filters'
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

const { data } = await useFetch(
  'api/settings/?keys=products_header_image', {
    baseURL: getCurrentApiUrl()
  })

// Состояние
const route = useRoute()
const router = useRouter()

const page = ref(1)
const pageSize = ref(20)
const viewMode = ref<'grid' | 'list'>('grid')
const isMobileFilterOpen = ref(false)
const maxPrice = ref(100000)

const filters = reactive<Filters>({
  category: undefined,
  min_price: null,
  max_price: null,
  in_stock: false,
  is_new: false,
  is_featured: false,
  is_bestseller: false,
  search: ''
})

const priceRange = ref([0, 100000])

const sortOptions = [
  { label: 'По умолчанию', value: '-created_at' },
  { label: 'Цена: по возрастанию', value: 'price' },
  { label: 'Цена: по убыванию', value: '-price' },
  { label: 'Название А-Я', value: 'name' },
  { label: 'Название Я-А', value: '-name' },
  { label: 'Популярные', value: '-popularity' }
]
const sortOption = ref({ label: sortOptions[0]?.label, value: sortOptions[0]?.value })

// Загрузка категорий
const { data: categoriesData } = await useFetch<Category[]>('/api/products/categories/', {
  baseURL: getCurrentApiUrl()
})
const categories = computed(() => categoriesData.value || [])

// Загрузка товаров
const { data: productsData, pending, error, refresh } = await useFetch<{
  results: Product[]
  count: number
}>('/api/products/', {
  baseURL: getCurrentApiUrl(),
  query: computed(() => ({
    page: page.value,
    page_size: pageSize.value,
    category: filters.category,
    min_price: filters.min_price || undefined,
    max_price: filters.max_price || undefined,
    in_stock: filters.in_stock || undefined,
    is_new: filters.is_new || undefined,
    is_featured: filters.is_featured || undefined,
    is_bestseller: filters.is_bestseller || undefined,
    search: filters.search || undefined,
    ordering: sortOption.value
  })),
  watch: [filters, sortOption, page]
})

const products = computed(() => productsData.value?.results || [])
const pagination = computed(() => ({
  count: productsData.value?.count || 0,
  pages: Math.ceil((productsData.value?.count || 0) / pageSize.value)
}))

// Текущая категория
const currentCategory = computed(() => {
  if (!filters.category) return null
  return findCategory(categories.value, filters.category)
})

// Хлебные крошки
const breadcrumbLinks = computed(() => {
  const links = [{ label: 'Главная', to: '/' }, { label: 'Каталог', to: '/catalog' }]
  if (currentCategory.value) {
    links.push({ label: currentCategory.value.name, to: `/catalog?category=${currentCategory.value.slug}` })
  }
  return links
})

// Аккордеон категорий
const categoryAccordionItems = computed(() => {
  return categories.value.map(cat => ({
    label: cat.name,
    defaultOpen: filters.category === cat.slug || hasActiveChild(cat),
    slot: 'category',
    children: cat.children?.map(child => ({
      label: child.name,
      click: () => selectCategory(child.slug)
    })) || []
  }))
})

// Активные фильтры для отображения
const activeFilters = computed(() => {
  const list: { key: string, label: string }[] = []

  if (filters.category && currentCategory.value) {
    list.push({ key: 'category', label: `Категория: ${currentCategory.value.name}` })
  }
  if (filters.min_price || filters.max_price) {
    const min = filters.min_price || 0
    const max = filters.max_price || '∞'
    list.push({ key: 'price', label: `Цена: ${min} - ${max} ₽` })
  }
  if (filters.in_stock) list.push({ key: 'in_stock', label: 'В наличии' })
  if (filters.is_new) list.push({ key: 'is_new', label: 'Новинки' })
  if (filters.is_featured) list.push({ key: 'is_featured', label: 'Рекомендуемые' })
  if (filters.is_bestseller) list.push({ key: 'is_bestseller', label: 'Хиты продаж' })

  return list
})

// Методы
function findCategory(cats: Category[], slug: string): Category | null {
  for (const cat of cats) {
    if (cat.slug === slug) return cat
    if (cat.children) {
      const found = findCategory(cat.children, slug)
      if (found) return found
    }
  }
  return null
}

function hasActiveChild(cat: Category): boolean {
  if (!cat.children) return false
  return cat.children.some(c => c.slug === filters.category)
}

function selectCategory(slug: string) {
  filters.category = filters.category === slug ? undefined : slug
  page.value = 1
  updateQuery()
}

function onPriceRangeChange(value: number[]) {
  filters.min_price = value[0] || null
  filters.max_price = value[1] || null
  page.value = 1
  updateQuery()
}

function onSortChange() {
  page.value = 1
  updateQuery()
}

function onPageChange() {
  updateQuery()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function removeFilter(key: string) {
  switch (key) {
    case 'category':
      filters.category = undefined
      break
    case 'price':
      filters.min_price = null
      filters.max_price = null
      priceRange.value = [0, maxPrice.value]
      break
    case 'in_stock':
      filters.in_stock = false
      break
    case 'is_new':
      filters.is_new = false
      break
    case 'is_featured':
      filters.is_featured = false
      break
    case 'is_bestseller':
      filters.is_bestseller = false
      break
  }
  page.value = 1
  updateQuery()
}

function resetFilters() {
  filters.category = undefined
  filters.min_price = null
  filters.max_price = null
  filters.in_stock = false
  filters.is_new = false
  filters.is_featured = false
  filters.is_bestseller = false
  filters.search = ''
  priceRange.value = [0, maxPrice.value]
  sortOption.value = { label: sortOptions[0]?.label, value: sortOptions[0]?.value }
  page.value = 1
  updateQuery()
}

function applyFilters() {
  isMobileFilterOpen.value = false
  page.value = 1
  updateQuery()
}

function updateQuery() {
  const query: Record<string, string> = {}

  if (page.value > 1) query.page = String(page.value)
  if (filters.category) query.category = filters.category
  if (filters.min_price) query.min_price = String(filters.min_price)
  if (filters.max_price) query.max_price = String(filters.max_price)
  if (filters.in_stock) query.in_stock = 'true'
  if (filters.is_new) query.is_new = 'true'
  if (filters.is_featured) query.is_featured = 'true'
  if (filters.is_bestseller) query.is_bestseller = 'true'
  if (filters.search) query.search = filters.search
  if (sortOption.value !== '-created_at') query.sort = sortOption.value

  router.replace({ query })
}

// Инициализация из URL
onMounted(() => {
  const query = route.query

  if (query.page) page.value = Number(query.page)
  if (query.category) filters.category = String(query.category)
  if (query.min_price) {
    filters.min_price = Number(query.min_price)
    priceRange.value[0] = Number(query.min_price)
  }
  if (query.max_price) {
    filters.max_price = Number(query.max_price)
    priceRange.value[1] = Number(query.max_price)
  }
  if (query.in_stock === 'true') filters.in_stock = true
  if (query.is_new === 'true') filters.is_new = true
  if (query.is_featured === 'true') filters.is_featured = true
  if (query.is_bestseller === 'true') filters.is_bestseller = true
  if (query.search) filters.search = String(query.search)
  if (query.sort) sortOption.value = String(query.sort)
})

// SEO
useHead({
  title: computed(() => currentCategory.value
    ? `${currentCategory.value.name} - Каталог`
    : 'Каталог товаров'
  )
})
</script>

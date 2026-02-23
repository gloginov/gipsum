<template>
  <UPage>
    <UPageHeader
      title="Оформление заказа"
      :description="cart.isEmpty ? 'Ваша корзина пуста' : `Товаров: ${cart.count} на сумму ${cart.total} ₽`"
    />

    <UPageBody>
      <!-- Загрузка -->
      <UAlert
        v-if="loading"
        icon="i-lucide-loader-2"
        title="Загрузка..."
        :description="loadingText"
        color="neutral"
      />

      <!-- Пустая корзина -->
      <UAlert
        v-else-if="cart.isEmpty && !orderSuccess"
        icon="i-lucide-shopping-cart"
        title="Корзина пуста"
        description="Добавьте товары из каталога для оформления заказа"
        color="warning"
      >
        <template #actions>
          <UButton
            to="/catalog"
            color="primary"
          >
            В каталог
          </UButton>
        </template>
      </UAlert>

      <!-- Успешное оформление -->
      <UAlert
        v-else-if="orderSuccess"
        icon="i-lucide-check-circle"
        title="Заказ оформлен!"
        :description="`Номер заказа: ${createdOrder?.order_number}. Подтверждение отправлено на ${createdOrder?.email}`"
        color="success"
      >
        <template #actions>
          <UButton
            to="/catalog"
            color="primary"
          >
            Продолжить покупки
          </UButton>
          <UButton
            v-if="createdOrder"
            :to="`/orders/${createdOrder.order_number}`"
            color="neutral"
            variant="soft"
          >
            Мои заказы
          </UButton>
        </template>
      </UAlert>

      <!-- Форма заказа -->
      <div
        v-else
        class="grid grid-cols-1 lg:grid-cols-2 gap-8"
      >
        <!-- Левая колонка -->
        <div class="space-y-6">
          <!-- Контактные данные -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">
                Контактные данные
              </h3>
            </template>
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <UFormField
                  label="Имя"
                  required
                >
                  <UInput
                    v-model="formState.first_name"
                    placeholder="Иван"
                    icon="i-lucide-user"
                  />
                </UFormField>
                <UFormField
                  label="Фамилия"
                  required
                >
                  <UInput
                    v-model="formState.last_name"
                    placeholder="Иванов"
                  />
                </UFormField>
              </div>
              <UFormField
                label="Email"
                required
              >
                <UInput
                  v-model="formState.email"
                  type="email"
                  placeholder="ivan@example.com"
                  icon="i-lucide-mail"
                />
              </UFormField>
              <UFormField
                label="Телефон"
                required
              >
                <UInput
                  v-model="formState.phone"
                  type="tel"
                  placeholder="+7 (999) 123-45-67"
                  icon="i-lucide-phone"
                />
              </UFormField>
            </div>
          </UCard>

          <!-- Адрес доставки с Картой + CDEK -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">
                Адрес доставки
              </h3>
            </template>
            <div class="space-y-4">
              <!-- Поиск города через Яндекс Геокодер -->
              <UFormField
                label="Город"
                required
              >
                <div class="flex gap-2">
                  <UInput
                    v-model="citySearchInput"
                    placeholder="Введите название города..."
                    icon="i-lucide-map-pin"
                    class="flex-1"
                    @keyup.enter="searchCity"
                  />
                  <UButton
                    color="primary"
                    :loading="loadingCity"
                    @click="searchCity"
                  >
                    Найти
                  </UButton>
                </div>
              </UFormField>

              <!-- Карта с выбором локации -->
              <div
                v-if="mapVisible"
                class="space-y-2"
              >
                <div class="text-sm text-gray-600">
                  Уточните местоположение на карте или выберите ПВЗ:
                </div>
                <div class="rounded-lg overflow-hidden border border-gray-200 h-80 relative">
                  <ClientOnly>
                    <yandex-map
                      :settings="ymapSettings"
                      :coordinates="mapCenter"
                      :zoom="zoom"
                      :controls="['zoomControl']"
                      @click="onMapClick"
                    >
                      <!-- Маркер выбранной точки -->
                      <yandex-marker
                        v-if="selectedCoords"
                        :coordinates="selectedCoords"
                        :marker-id="1"
                        :options="{ preset: 'islands#redDotIcon' }"
                      />

                      <!-- Маркеры ПВЗ -->
                      <yandex-marker
                        v-for="pvz in pvzList"
                        :key="pvz.code"
                        :coordinates="[pvz.location.latitude, pvz.location.longitude]"
                        :marker-id="pvz.code"
                        :options="{
                          preset: selectedPVZ?.code === pvz.code ? 'islands#greenIcon' : 'islands#blueIcon'
                        }"
                        :properties="{
                          hintContent: pvz.name,
                          balloonContent: pvzBalloonContent(pvz)
                        }"
                        @click="selectPVZ(pvz)"
                      />
                    </yandex-map>
                  </ClientOnly>
                </div>

                <!-- Кнопки управления картой -->
                <div class="flex gap-2">
                  <UButton
                    size="sm"
                    variant="soft"
                    @click="resetMap"
                  >
                    Сбросить
                  </UButton>
                  <UButton
                    v-if="deliveryType === 'pvz' && pvzList.length > 0"
                    size="sm"
                    variant="soft"
                    color="primary"
                    @click="fitMapToPVZ"
                  >
                    Показать все ПВЗ
                  </UButton>
                </div>
              </div>

              <!-- Информация о выбранном городе -->
              <div
                v-if="selectedCity"
                class="bg-green-50 p-3 rounded-lg"
              >
                <p class="text-sm font-medium text-green-800">
                  {{ selectedCity.name }}
                </p>
                <p class="text-xs text-green-600">
                  {{ selectedCity.description }}
                  <span v-if="selectedCity.postalCode">• Почтовый индекс: {{ selectedCity.postalCode }}</span>
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  Координаты: {{ selectedCity.lat.toFixed(4) }}, {{ selectedCity.lon.toFixed(4) }}
                </p>
              </div>

              <!-- Выбор типа доставки -->
              <UFormField label="Тип доставки">
                <URadioGroup
                  v-model="deliveryType"
                  :items="[
                    { value: 'pvz', label: 'До пункта выдачи (ПВЗ)' },
                    { value: 'door', label: 'Курьером до двери' }
                  ]"
                />
              </UFormField>

              <!-- Список ПВЗ (если выбран пункт выдачи) -->
              <template v-if="deliveryType === 'pvz' && selectedCity && pvzList.length > 0">
                <UFormField
                  label="Пункт выдачи СДЭК"
                  required
                >
                  <USelectMenu
                    v-model="selectedPVZ"
                    :items="pvzList"
                    placeholder="Выберите ПВЗ на карте или из списка"
                    :loading="loadingPVZ"
                    icon="i-lucide-package"
                    option-attribute="name"
                    value-attribute="code"
                  >
                    <template #item="{ item }">
                      <div class="flex flex-col py-1">
                        <span class="font-medium">{{ item.name }}</span>
                        <span class="text-xs text-gray-500">{{ item.address }}</span>
                        <span
                          v-if="item.work_time"
                          class="text-xs text-green-600"
                        >{{ item.work_time }}</span>
                      </div>
                    </template>
                  </USelectMenu>
                </UFormField>

                <!-- Карточка выбранного ПВЗ -->
                <div
                  v-if="selectedPVZ"
                  class="bg-gray-50 p-4 rounded-lg border border-gray-200"
                >
                  <div class="flex items-start gap-3">
                    <UIcon
                      name="i-lucide-map-pin"
                      class="w-5 h-5 text-primary mt-0.5"
                    />
                    <div>
                      <p class="font-medium">
                        {{ selectedPVZ.name }}
                      </p>
                      <p class="text-sm text-gray-600 mt-1">
                        {{ selectedPVZ.address }}
                      </p>
                      <div
                        v-if="selectedPVZ.work_time"
                        class="flex items-center gap-1 mt-2 text-sm text-green-700"
                      >
                        <UIcon
                          name="i-lucide-clock"
                          class="w-4 h-4"
                        />
                        {{ selectedPVZ.work_time }}
                      </div>
                      <div
                        v-if="selectedPVZ.phone"
                        class="flex items-center gap-1 mt-1 text-sm text-gray-500"
                      >
                        <UIcon
                          name="i-lucide-phone"
                          class="w-4 h-4"
                        />
                        {{ selectedPVZ.phone }}
                      </div>
                      <div
                        v-if="selectedPVZ.location"
                        class="text-xs text-gray-400 mt-1"
                      >
                        Расстояние: {{ calculateDistance(selectedPVZ.location) }} км
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- Предупреждение если нет ПВЗ -->
              <UAlert
                v-if="deliveryType === 'pvz' && selectedCity && !loadingPVZ && pvzList.length === 0"
                icon="i-lucide-alert-circle"
                title="Нет пунктов выдачи"
                description="В выбранном городе нет ПВЗ СДЭК. Выберите доставку курьером."
                color="warning"
              />

              <!-- Адрес для курьерской доставки -->
              <template v-if="deliveryType === 'door'">
                <UFormField
                  label="Улица, дом, квартира"
                  required
                >
                  <UInput
                    v-model="formState.address"
                    placeholder="ул. Ленина, д. 1, кв. 10"
                    icon="i-lucide-home"
                  />
                </UFormField>
              </template>
            </div>
          </UCard>

          <!-- Расчет доставки CDEK -->
          <UCard v-if="selectedCity && cdekTariffs.length > 0">
            <template #header>
              <h3 class="text-lg font-semibold">
                Выбор тарифа СДЭК
              </h3>
            </template>
            <div class="space-y-3">
              <div
                v-for="tariff in cdekTariffs"
                :key="tariff.tariff_code"
                class="flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-colors"
                :class="selectedTariff?.tariff_code === tariff.tariff_code ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'"
                @click="selectTariff(tariff)"
              >
                <URadio
                  :value="tariff.tariff_code"
                  :model-value="selectedTariff?.tariff_code"
                />
                <div class="flex-1">
                  <div class="flex justify-between items-start">
                    <div>
                      <p class="font-medium">
                        {{ tariff.tariff_name }}
                      </p>
                      <p class="text-sm text-gray-500 mt-1">
                        <UIcon
                          name="i-lucide-calendar"
                          class="w-4 h-4 inline"
                        />
                        {{ tariff.period_min }}-{{ tariff.period_max }} дней
                      </p>
                    </div>
                    <p class="text-xl font-bold text-primary">
                      {{ tariff.delivery_sum }} ₽
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Способ оплаты -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">
                Способ оплаты
              </h3>
            </template>
            <div class="space-y-3">
              <div
                v-for="method in paymentMethods"
                :key="method.id"
                class="flex items-start gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors"
                :class="selectedPaymentMethod === method.id ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'"
                @click="selectedPaymentMethod = method.id"
              >
                <URadio
                  :value="method.id"
                  :model-value="selectedPaymentMethod"
                />
                <div class="flex-1">
                  <div class="flex justify-between items-center">
                    <span class="font-medium">{{ method.name }}</span>
                    <UIcon
                      :name="method.icon || 'i-lucide-credit-card'"
                      class="w-5 h-5 text-gray-400"
                    />
                  </div>
                  <p
                    v-if="method.commission_percent > 0"
                    class="text-xs text-orange-500 mt-1"
                  >
                    Комиссия {{ method.commission_percent }}%
                  </p>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Комментарий -->
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">
                Комментарий к заказу
              </h3>
            </template>
            <UTextarea
              v-model="formState.customer_note"
              placeholder="Удобное время доставки, дополнительная информация..."
              :rows="3"
            />
          </UCard>
        </div>

        <!-- Правая колонка: итог -->
        <div class="space-y-6">
          <UCard>
            <template #header>
              <h3 class="text-lg font-semibold">
                Ваш заказ
              </h3>
            </template>

            <!-- Товары -->
            <div class="space-y-4 max-h-96 overflow-y-auto">
              <div
                v-for="item in cart.items"
                :key="item.id"
                class="flex gap-4 py-2 border-b border-gray-100 last:border-0"
              >
                <img
                  :src="item.main_image || '/placeholder.png'"
                  class="w-16 h-16 object-cover rounded"
                  :alt="item.product_name"
                >
                <div class="flex-1">
                  <p class="font-medium text-sm">
                    {{ item.product_name }}
                  </p>
                  <p class="text-gray-500 text-xs">
                    {{ item.price }} ₽ × {{ item.quantity }}
                  </p>
                </div>
                <p class="font-semibold text-sm">
                  {{ item.total }} ₽
                </p>
              </div>
            </div>

            <template #footer>
              <div class="space-y-2">
                <div class="flex justify-between text-sm">
                  <span class="text-gray-500">Товары ({{ cart.count }})</span>
                  <span>{{ cart.total }} ₽</span>
                </div>

                <div class="flex justify-between text-sm">
                  <span class="text-gray-500">Доставка (СДЭК)</span>
                  <span :class="shippingCost === 0 ? 'text-green-600 font-semibold' : ''">
                    {{ shippingCost === 0 ? 'Бесплатно' : shippingCost + ' ₽' }}
                  </span>
                </div>

                <div
                  v-if="commissionAmount > 0"
                  class="flex justify-between text-sm text-orange-600"
                >
                  <span>Комиссия ({{ selectedPaymentMethodData?.commission_percent }}%)</span>
                  <span>+{{ commissionAmount.toFixed(2) }} ₽</span>
                </div>

                <div class="flex justify-between text-sm">
                  <span class="text-gray-500">Налог (8%)</span>
                  <span>{{ taxAmount }} ₽</span>
                </div>

                <UDivider />

                <div class="flex justify-between items-center">
                  <span class="text-lg font-semibold">Итого</span>
                  <span class="text-2xl font-bold text-primary">{{ totalAmount }} ₽</span>
                </div>

                <!-- Информация о доставке -->
                <div class="text-xs text-gray-500 space-y-1 bg-gray-50 p-3 rounded">
                  <div class="flex items-center gap-2">
                    <UIcon
                      name="i-lucide-truck"
                      class="w-4 h-4"
                    />
                    <span>СДЭК: {{ selectedTariff?.tariff_name || 'Не выбрано' }}</span>
                  </div>
                  <div
                    v-if="selectedCity"
                    class="flex items-center gap-2"
                  >
                    <UIcon
                      name="i-lucide-map-pin"
                      class="w-4 h-4"
                    />
                    <span>{{ selectedCity.name }}</span>
                  </div>
                  <div
                    v-if="deliveryType === 'pvz' && selectedPVZ"
                    class="flex items-center gap-2"
                  >
                    <UIcon
                      name="i-lucide-package"
                      class="w-4 h-4"
                    />
                    <span>ПВЗ: {{ selectedPVZ.name }}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <UIcon
                      name="i-lucide-credit-card"
                      class="w-4 h-4"
                    />
                    <span>Оплата: {{ selectedPaymentMethodData?.name || 'Не выбрана' }}</span>
                  </div>
                </div>

                <UButton
                  block
                  size="lg"
                  color="primary"
                  :loading="isSubmitting"
                  :disabled="!isFormValid"
                  @click="submitOrder"
                >
                  {{ isSubmitting ? 'Оформление...' : 'Подтвердить заказ' }}
                </UButton>

                <p
                  v-if="!isFormValid"
                  class="text-xs text-center text-gray-500"
                >
                  Заполните все обязательные поля и выберите способ доставки
                </p>
              </div>
            </template>
          </UCard>
        </div>
      </div>
    </UPageBody>
  </UPage>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { createYmapsOptions } from 'vue-yandex-maps'
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

// Типы CDEK
interface CDEKTariff {
  tariff_code: number
  tariff_name: string
  delivery_sum: number
  period_min: number
  period_max: number
}

interface CDEKPVZ {
  code: string
  name: string
  address: string
  work_time?: string
  phone?: string
  location: {
    latitude: number
    longitude: number
  }
}

// Типы приложения
interface PaymentMethod {
  id: number
  name: string
  code: string
  commission_percent: string | number
  icon?: string
}

interface CityData {
  name: string
  description: string
  lat: number
  lon: number
  postalCode?: string
  cdekCityCode?: number
}

// Состояние
const cart = useCartStore()
const { user } = useAuth()
const toast = useToast()

// Загрузка корзины
await useAsyncData('cart-checkout', () => cart.fetchCart())

// Состояние загрузки
const loading = ref(true)
const loadingText = ref('Загрузка...')
const loadingCity = ref(false)
const loadingPVZ = ref(false)

// Яндекс Карты - НАСТРОЙКИ (только валидные ключи)
const yandexMapsApiKey = useRuntimeConfig().public.yandexMapsApiKey || ''

// Создаем настройки для Яндекс Карт с API ключом (только допустимые параметры)
const ymapSettings = createYmapsOptions({
  apikey: yandexMapsApiKey,
  lang: 'ru_RU',
  version: '2.1'
})

const mapCenter = ref<[number, number]>([55.76, 37.64]) // Москва по умолчанию
const zoom = ref(10)
const citySearchInput = ref('')
const selectedCoords = ref<[number, number] | null>(null)
const mapVisible = ref(false)

// Данные города
const selectedCity = ref<CityData | null>(null)

// CDEK
const deliveryType = ref<'pvz' | 'door'>('pvz')
const pvzList = ref<CDEKPVZ[]>([])
const selectedPVZ = ref<CDEKPVZ | null>(null)
const cdekTariffs = ref<CDEKTariff[]>([])
const selectedTariff = ref<CDEKTariff | null>(null)

// Оплата
const paymentMethods = ref<PaymentMethod[]>([])
const selectedPaymentMethod = ref<number | null>(null)

// Форма
const formState = reactive({
  first_name: user.value?.first_name || '',
  last_name: user.value?.last_name || '',
  email: user.value?.email || '',
  phone: '',
  address: '',
  customer_note: ''
})

const isSubmitting = ref(false)
const orderSuccess = ref(false)
const createdOrder = ref<any>(null)

// ==================== ЯНДЕКС КАРТЫ ====================

// Поиск города через Яндекс Геокодер
async function searchCity() {
  if (!citySearchInput.value || citySearchInput.value.length < 2) {
    toast.add({
      title: 'Введите город',
      description: 'Минимум 2 символа',
      color: 'warning'
    })
    return
  }

  if (!yandexMapsApiKey) {
    toast.add({
      title: 'Ошибка конфигурации',
      description: 'API ключ Яндекс Карт не настроен',
      color: 'error'
    })
    return
  }

  loadingCity.value = true

  try {
    const response = await $fetch<any>(
      `https://geocode-maps.yandex.ru/1.x/?apikey=${yandexMapsApiKey}&geocode=${encodeURIComponent(citySearchInput.value)}&format=json&kind=locality&results=1&lang=ru_RU`
    )

    const feature = response.response.GeoObjectCollection.featureMember[0]

    if (!feature) {
      toast.add({
        title: 'Город не найден',
        description: 'Попробуйте уточнить название',
        color: 'warning'
      })
      return
    }

    const geo = feature.GeoObject
    const pos = geo.Point.pos.split(' ')
    const lon = parseFloat(pos[0])
    const lat = parseFloat(pos[1])

    // Извлекаем почтовый индекс если есть
    const postalCode = geo.metaDataProperty?.GeocoderMetaData?.Address?.postal_code

    selectedCity.value = {
      name: geo.name,
      description: geo.description || '',
      lat,
      lon,
      postalCode
    }

    selectedCoords.value = [lat, lon]
    mapCenter.value = [lat, lon]
    zoom.value = 11
    mapVisible.value = true

    // Сбрасываем предыдущие данные CDEK
    selectedPVZ.value = null
    pvzList.value = []
    cdekTariffs.value = []
    selectedTariff.value = null

    // Загружаем данные CDEK через прокси
    await findCDEKCityAndLoadData(lat, lon)
  } catch (error) {
    console.error('Geocoding error:', error)
    toast.add({
      title: 'Ошибка поиска',
      description: 'Не удалось найти город на карте',
      color: 'error'
    })
  } finally {
    loadingCity.value = false
  }
}

// Клик по карте
function onMapClick(e: any) {
  const coords = e.get('coords') as [number, number]
  selectedCoords.value = coords

  // Обратный геокодинг для получения адреса
  reverseGeocode(coords)
}

// Обратный геокодинг
async function reverseGeocode(coords: [number, number]) {
  if (!yandexMapsApiKey) return

  try {
    const response = await $fetch<any>(
      `https://geocode-maps.yandex.ru/1.x/?apikey=${yandexMapsApiKey}&geocode=${coords[1]},${coords[0]}&format=json&kind=locality&lang=ru_RU`
    )

    const feature = response.response.GeoObjectCollection.featureMember[0]
    if (feature) {
      const geo = feature.GeoObject
      selectedCity.value = {
        name: geo.name,
        description: geo.description || '',
        lat: coords[0],
        lon: coords[1],
        postalCode: geo.metaDataProperty?.GeocoderMetaData?.Address?.postal_code
      }

      // Перезагружаем данные CDEK для новых координат
      await findCDEKCityAndLoadData(coords[0], coords[1])
    }
  } catch (error) {
    console.error('Reverse geocoding error:', error)
  }
}

// Сброс карты
function resetMap() {
  selectedCity.value = null
  selectedCoords.value = null
  pvzList.value = []
  selectedPVZ.value = null
  cdekTariffs.value = []
  selectedTariff.value = null
  mapVisible.value = false
  citySearchInput.value = ''
  mapCenter.value = [55.76, 37.64]
  zoom.value = 10
}

// Подстроить карту под все ПВЗ
function fitMapToPVZ() {
  if (pvzList.value.length === 0) return

  // Вычисляем bounds для всех ПВЗ
  const lats = pvzList.value.map(p => p.location.latitude)
  const lons = pvzList.value.map(p => p.location.longitude)

  if (selectedCoords.value) {
    lats.push(selectedCoords.value[0])
    lons.push(selectedCoords.value[1])
  }

  const minLat = Math.min(...lats)
  const maxLat = Math.max(...lats)
  const minLon = Math.min(...lons)
  const maxLon = Math.max(...lons)

  // Центрируем карту
  mapCenter.value = [(minLat + maxLat) / 2, (minLon + maxLon) / 2]

  // Вычисляем zoom примерно
  const latDiff = maxLat - minLat
  const lonDiff = maxLon - minLon
  const maxDiff = Math.max(latDiff, lonDiff)

  if (maxDiff < 0.01) zoom.value = 15
  else if (maxDiff < 0.05) zoom.value = 13
  else if (maxDiff < 0.1) zoom.value = 12
  else if (maxDiff < 0.5) zoom.value = 10
  else zoom.value = 9
}

// Контент балуна для ПВЗ
function pvzBalloonContent(pvz: CDEKPVZ): string {
  return `
    <div style="padding: 8px; max-width: 200px;">
      <strong style="font-size: 14px;">${pvz.name}</strong><br>
      <span style="font-size: 12px; color: #666;">${pvz.address}</span><br>
      ${pvz.work_time ? `<span style="font-size: 12px; color: #059669;">${pvz.work_time}</span><br>` : ''}
      ${pvz.phone ? `<span style="font-size: 12px;">Тел: ${pvz.phone}</span>` : ''}
    </div>
  `
}

// Расчет расстояния от выбранной точки до ПВЗ
function calculateDistance(location: { latitude: number, longitude: number }): string {
  if (!selectedCoords.value) return '0'

  const R = 6371 // Радиус Земли в км
  const dLat = (location.latitude - selectedCoords.value[0]) * Math.PI / 180
  const dLon = (location.longitude - selectedCoords.value[1]) * Math.PI / 180
  const a
    = Math.sin(dLat / 2) * Math.sin(dLat / 2)
      + Math.cos(selectedCoords.value[0] * Math.PI / 180) * Math.cos(location.latitude * Math.PI / 180)
      * Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  const distance = R * c

  return distance.toFixed(1)
}

// ==================== CDEK (через прокси) ====================

// Находим город CDEК по координатам и загружаем данные
async function findCDEKCityAndLoadData(lat: number, lon: number) {
  try {
    loadingPVZ.value = true
    loadingText.value = 'Поиск города в CDEК...'

    // Ищем ближайший город CDEК через прокси
    const citiesResponse = await $fetch<{ cities: any[] }>('/api/cdek/cities', {
      params: { lat, lon, size: 1 }
    })

    if (!citiesResponse.cities?.length) {
      toast.add({
        title: 'Город не обслуживается',
        description: 'CDEK не работает в этом населенном пункте',
        color: 'warning'
      })
      cdekTariffs.value = []
      return
    }

    const cdekCity = citiesResponse
    console.log(citiesResponse)
    // Сохраняем код города CDEК
    if (selectedCity.value) {
      selectedCity.value.cdekCityCode = cdekCity.code
    }

    loadingText.value = 'Загрузка пунктов выдачи...'

    // Загружаем ПВЗ через прокси
    if (deliveryType.value === 'pvz') {
      await loadPVZByCityCode(cdekCity.code)
    }

    // Расчет стоимости через прокси
    await calculateDeliveryByCityCode(cdekCity.code)
  } catch (error: any) {
    console.error('CDEK city search error:', error)
    toast.add({
      title: 'Ошибка CDEК',
      description: error.statusMessage || 'Не удалось получить данные о доставке',
      color: 'error'
    })
  } finally {
    loadingPVZ.value = false
    loadingText.value = 'Загрузка...'
  }
}

// Загрузка ПВЗ по коду города (через прокси)
async function loadPVZByCityCode(cityCode: number) {
  try {
    const pvzResponse = await $fetch<{ points: CDEKPVZ[] }>('/api/cdek/pvz', {
      params: { city_code: cityCode }
    })

    pvzList.value = pvzResponse.points || []

    if (pvzList.value.length === 0 && deliveryType.value === 'pvz') {
      toast.add({
        title: 'Нет ПВЗ',
        description: 'В этом городе нет пунктов выдачи. Выберите доставку курьером.',
        color: 'warning'
      })
    }
  } catch (error) {
    console.error('CDEK PVZ error:', error)
    throw error
  }
}

// Расчет стоимости доставки (через прокси)
async function calculateDeliveryByCityCode(cityCode: number) {
  try {
    loadingText.value = 'Расчет стоимости доставки...'

    // Расчет веса и габаритов
    const totalWeight = cart.items.reduce((sum, item) => {
      const weight = item.weight || 500
      return sum + weight * item.quantity
    }, 0)

    const maxDimension = Math.max(
      ...cart.items.map(item => Math.max(item.length || 20, item.width || 15, item.height || 10))
    )

    const calcResponse = await $fetch<{ tariffs: CDEKTariff[] }>('/api/cdek/calculate', {
      method: 'POST',
      body: {
        type: 1,
        currency: 1,
        lang: 'rus',
        from_location: { code: 44 }, // Москва
        to_location: { code: cityCode },
        packages: [{
          weight: totalWeight,
          length: maxDimension,
          width: maxDimension,
          height: maxDimension
        }]
      }
    })

    cdekTariffs.value = calcResponse.tariffs || []

    if (cdekTariffs.value.length > 0) {
      selectedTariff.value = cdekTariffs.value[0]
    } else {
      toast.add({
        title: 'Нет доступных тарифов',
        description: 'Не удалось рассчитать стоимость доставки в этот город',
        color: 'warning'
      })
    }
  } catch (error) {
    console.error('CDEK calculation error:', error)
    throw error
  } finally {
    loadingText.value = 'Загрузка...'
  }
}

// Выбор ПВЗ
function selectPVZ(pvz: CDEKPVZ) {
  selectedPVZ.value = pvz
  // Центрируем карту на выбранном ПВЗ
  mapCenter.value = [pvz.location.latitude, pvz.location.longitude]
  zoom.value = 16
}

// ==================== ОСТАЛЬНОЕ ====================

// Загрузка методов оплаты
async function loadPaymentMethods() {
  try {
    const apiUrl = getCurrentApiUrl()
    const response = await $fetch<{ results: PaymentMethod[] }>(
      `${apiUrl}/api/orders/payment-methods/`,
      { credentials: 'include' }
    )
    paymentMethods.value = response.results || []
    if (paymentMethods.value.length > 0) {
      selectedPaymentMethod.value = paymentMethods.value[0].id
    }
  } catch (error) {
    console.error('Payment methods error:', error)
  }
}

// Инициализация
async function init() {
  try {
    loading.value = true
    await loadPaymentMethods()
  } finally {
    loading.value = false
  }
}

// Watchers
watch(deliveryType, async (newType) => {
  if (selectedCity.value?.cdekCityCode) {
    selectedPVZ.value = null

    if (newType === 'pvz') {
      try {
        loadingPVZ.value = true
        await loadPVZByCityCode(selectedCity.value.cdekCityCode)
      } catch (error) {
        console.error('Error loading PVZ:', error)
      } finally {
        loadingPVZ.value = false
      }
    }

    // Пересчитываем доставку (тарифы могут отличаться для ПВЗ и двери)
    try {
      await calculateDeliveryByCityCode(selectedCity.value.cdekCityCode)
    } catch (error) {
      console.error('Error recalculating delivery:', error)
    }
  }
})

// Выбор тарифа
function selectTariff(tariff: CDEKTariff) {
  selectedTariff.value = tariff
}

// Расчеты стоимости
const subtotal = computed(() => parseFloat(cart.total) || 0)
const shippingCost = computed(() => selectedTariff.value?.delivery_sum || 0)
const commissionAmount = computed(() => {
  const method = paymentMethods.value.find(m => m.id === selectedPaymentMethod.value)
  if (!method) return 0
  const percent = parseFloat(String(method.commission_percent)) || 0
  return (subtotal.value + shippingCost.value) * (percent / 100)
})
const taxAmount = computed(() => ((subtotal.value + shippingCost.value + commissionAmount.value) * 0.08).toFixed(2))
const totalAmount = computed(() => {
  const base = subtotal.value + shippingCost.value + commissionAmount.value
  return (base * 1.08).toFixed(2)
})

const selectedPaymentMethodData = computed(() =>
  paymentMethods.value.find(m => m.id === selectedPaymentMethod.value)
)

// Валидация
const isFormValid = computed(() => {
  const baseValid = formState.first_name.trim()
    && formState.last_name.trim()
    && formState.email.trim()
    && formState.phone.trim()

  const deliveryValid = selectedCity.value
    && selectedTariff.value
    && (deliveryType.value === 'door' || selectedPVZ.value)

  const paymentValid = selectedPaymentMethod.value !== null

  return baseValid && deliveryValid && paymentValid && !cart.isEmpty
})

// Отправка заказа
async function submitOrder() {
  if (!isFormValid.value) return

  isSubmitting.value = true

  try {
    const apiUrl = getCurrentApiUrl()

    const orderData = {
      first_name: formState.first_name,
      last_name: formState.last_name,
      email: formState.email,
      phone: formState.phone,
      country: 'RU',
      city: selectedCity.value?.name || '',
      address: deliveryType.value === 'door'
        ? formState.address
        : `ПВЗ: ${selectedPVZ.value?.name}, ${selectedPVZ.value?.address}`,
      postal_code: selectedCity.value?.postalCode || '',
      payment_method_id: selectedPaymentMethod.value,
      shipping_method_id: 1,
      cdek_tariff_code: selectedTariff.value?.tariff_code,
      cdek_city_code: selectedCity.value?.cdekCityCode,
      cdek_pvz_code: selectedPVZ.value?.code,
      delivery_type: deliveryType.value,
      shipping_cost: shippingCost.value,
      customer_note: formState.customer_note,
      // Дополнительные данные для логистики
      geo_lat: selectedCoords.value?.[0],
      geo_lon: selectedCoords.value?.[1]
    }

    const { data, error } = await useFetch('/api/orders/', {
      method: 'POST',
      baseURL: apiUrl,
      credentials: 'include',
      body: orderData
    })

    if (error.value) {
      throw new Error(error.value.data?.error || 'Ошибка при создании заказа')
    }

    createdOrder.value = data.value
    orderSuccess.value = true
    cart.clear()

    toast.add({
      title: 'Заказ оформлен!',
      description: `Номер: ${data.value?.order_number}`,
      color: 'success'
    })
  } catch (err: any) {
    toast.add({
      title: 'Ошибка',
      description: err.message,
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

// Инициализация при монтировании
init()

useHead({ title: 'Оформление заказа' })
</script>

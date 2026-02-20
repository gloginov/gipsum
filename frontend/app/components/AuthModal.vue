<!-- components/AuthModal.vue -->
<template>
  <UModal
    v-model:open="isOpen"
    :ui="{ width: 'sm:max-w-md' }"
    :title="isLogin ? 'Вход в аккаунт' : 'Регистрация'"
  >
    <template #body>
      <!-- <UCard :ui="{ ring: '', divide: 'divide-y divide-gray-100' }"> -->
      <!-- <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">
              {{ isLogin ? 'Вход в аккаунт' : 'Регистрация' }}
            </h3>
            <UButton
              color="gray"
              variant="ghost"
              icon="i-heroicons-x-mark"
              size="sm"
              @click="close"
            />
          </div>
        </template> -->
      <UForm @submit="submit">
        <div class="space-y-4 py-4">
          <!-- Ошибка CSRF -->
          <UAlert
            v-if="csrfError"
            color="amber"
            variant="soft"
            icon="i-heroicons-shield-exclamation"
            title="Ошибка безопасности"
            description="Обновите страницу и попробуйте снова"
            class="mb-4"
          />

          <!-- Ошибка сервера -->
          <UAlert
            v-if="error"
            color="red"
            variant="soft"
            icon="i-heroicons-exclamation-triangle"
            :title="error"
            class="mb-4"
          />

          <!-- Email -->
          <UFormGroup
            label="Email"
            required
            :error="errors.email"
          >
            <UInput
              v-model="form.email"
              type="email"
              placeholder="your@email.com"
              icon="i-heroicons-envelope"
              :disabled="isLoading"
              @keyup.enter="submit"
            />
          </UFormGroup>

          <!-- Пароль -->
          <UFormGroup
            label="Пароль"
            required
            :error="errors.password"
          >
            <UInput
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              icon="i-heroicons-lock-closed"
              :disabled="isLoading"
              :ui="{ icon: { trailing: { pointer: '' } } }"
              @keyup.enter="submit"
            >
              <template #trailing>
                <UButton
                  color="gray"
                  variant="link"
                  :icon="showPassword ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
                  :padded="false"
                  @click="showPassword = !showPassword"
                />
              </template>
            </UInput>
          </UFormGroup>

          <!-- Подтверждение пароля -->
          <UFormGroup
            v-if="!isLogin"
            label="Подтвердите пароль"
            required
            :error="errors.password2"
          >
            <UInput
              v-model="form.password2"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              icon="i-heroicons-lock-closed"
              :disabled="isLoading"
              @keyup.enter="submit"
            />
          </UFormGroup>

          <!-- Имя -->
          <UFormGroup
            v-if="!isLogin"
            label="Имя"
            :error="errors.first_name"
          >
            <UInput
              v-model="form.first_name"
              placeholder="Иван"
              icon="i-heroicons-user"
              :disabled="isLoading"
            />
          </UFormGroup>

          <div
            v-if="isLogin"
            class="flex items-center justify-between"
          >
            <UCheckbox
              v-model="form.remember"
              label="Запомнить меня"
            />
            <UButton
              variant="link"
              color="primary"
              size="sm"
              @click="forgotPassword"
            >
              Забыли пароль?
            </UButton>
          </div>
        </div>

        <!-- <template #footer> -->
        <div class="space-y-3">
          <UButton
            block
            color="primary"
            size="lg"
            :loading="isLoading"
            :disabled="!isValid || !hasCSRF"
            type="submit"
          >
            {{ isLogin ? 'Войти' : 'Зарегистрироваться' }}
          </UButton>

          <UDivider label="или" />

          <UButton
            block
            variant="soft"
            color="gray"
            :disabled="isLoading"
            @click="toggleMode"
          >
            {{ isLogin ? 'Создать аккаунт' : 'Уже есть аккаунт? Войти' }}
          </UButton>
        </div>
      </UForm>
      <!-- </template> -->
      <!-- </UCard> -->
    </template>
  </UModal>
</template>

<script setup lang="ts">
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [user: any]
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

const isLogin = ref(true)
const isLoading = ref(false)
const error = ref('')
const csrfError = ref(false)
const showPassword = ref(false)
const csrfToken = ref('')

const form = reactive({
  email: '',
  password: '',
  password2: '',
  first_name: '',
  remember: false
})

const errors = reactive({
  email: '',
  password: '',
  password2: '',
  first_name: ''
})

// Проверка наличия CSRF токена
const hasCSRF = computed(() => csrfToken.value.length > 0)

const isValid = computed(() => {
  if (!form.email || !form.password) return false
  if (!isLogin.value && form.password !== form.password2) return false
  return true
})

// Получение CSRF из cookie с проверкой
const getCSRFToken = (): string => {
  // Пробуем разные варианты имени cookie
  const cookieNames = ['csrftoken', 'CSRFToken', 'csrfmiddlewaretoken']

  for (const name of cookieNames) {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) {
      const token = parts.pop()?.split(';').shift()
      if (token && token.length > 10) { // Проверка минимальной длины
        return token
      }
    }
  }

  // Fallback: ищем любой токен по шаблону
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

// Загрузка CSRF при открытии модалки
watch(isOpen, async (open) => {
  if (open) {
    await ensureCSRF()
  }
})

// Гарантированное получение CSRF токена
const ensureCSRF = async () => {
  csrfError.value = false

  // Сначала проверяем существующий
  let token = getCSRFToken()

  if (!token) {
    // Запрашиваем с сервера
    try {
      await $fetch('/auth/csrf/', {
        credentials: 'include',
        headers: {
          Accept: 'application/json'
        },
        baseURL: getCurrentApiUrl()
      })

      // Повторная проверка cookie после запроса
      await new Promise(resolve => setTimeout(resolve, 100)) // Небольшая задержка
      token = getCSRFToken()
    } catch (e) {
      console.error('Failed to get CSRF:', e)
    }
  }

  if (!token) {
    csrfError.value = true
  }

  csrfToken.value = token || ''
}

const close = () => {
  isOpen.value = false
  resetForm()
}

const resetForm = () => {
  form.email = ''
  form.password = ''
  form.password2 = ''
  form.first_name = ''
  form.remember = false
  error.value = ''
  csrfError.value = false
  clearErrors()
}

const clearErrors = () => {
  errors.email = ''
  errors.password = ''
  errors.password2 = ''
  errors.first_name = ''
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  clearErrors()
  error.value = ''
}

const validate = (): boolean => {
  clearErrors()
  let valid = true

  if (!form.email) {
    errors.email = 'Введите email'
    valid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Некорректный email'
    valid = false
  }

  if (!form.password) {
    errors.password = 'Введите пароль'
    valid = false
  } else if (form.password.length < 8) {
    errors.password = 'Минимум 8 символов'
    valid = false
  }

  if (!isLogin.value) {
    if (!form.password2) {
      errors.password2 = 'Подтвердите пароль'
      valid = false
    } else if (form.password !== form.password2) {
      errors.password2 = 'Пароли не совпадают'
      valid = false
    }
  }

  return valid
}

const submit = async () => {
  if (!validate()) return

  // Дополнительная проверка CSRF
  if (!csrfToken.value) {
    await ensureCSRF()
    if (!csrfToken.value) {
      csrfError.value = true
      return
    }
  }

  isLoading.value = true
  error.value = ''

  try {
    const endpoint = isLogin.value ? 'auth/login/' : 'auth/register/'

    const payload = isLogin.value
      ? {
          username: form.email,
          password: form.password,
          remember: form.remember
        }
      : {
          email: form.email,
          password: form.password,
          password2: form.password2,
          first_name: form.first_name
        }

    const response = await $fetch(endpoint, {
      baseURL: getCurrentApiUrl(),
      method: 'POST',
      body: payload,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken.value,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      }
    })

    emit('success', response)
    close()

    useToast().add({
      title: isLogin.value ? 'Добро пожаловать!' : 'Регистрация успешна',
      description: isLogin.value
        ? `Вы вошли как ${response.first_name || response.email}`
        : 'Проверьте email для подтверждения аккаунта',
      color: 'green'
    })

    await refreshNuxtData('user')
  } catch (err: any) {
    console.error('Auth error:', err)

    if (err.response?.status === 403 && err.response?._data?.detail?.includes('CSRF')) {
      csrfError.value = true
      error.value = 'Ошибка CSRF. Обновите страницу.'
    } else if (err.response?._data) {
      const data = err.response._data

      if (data.email) errors.email = Array.isArray(data.email) ? data.email[0] : data.email
      if (data.username) errors.email = Array.isArray(data.username) ? data.username[0] : data.username
      if (data.password) errors.password = Array.isArray(data.password) ? data.password[0] : data.password
      if (data.password2) errors.password2 = Array.isArray(data.password2) ? data.password2[0] : data.password2
      if (data.first_name) errors.first_name = Array.isArray(data.first_name) ? data.first_name[0] : data.first_name

      if (data.detail) {
        error.value = data.detail
      } else if (data.non_field_errors) {
        error.value = Array.isArray(data.non_field_errors)
          ? data.non_field_errors.join(', ')
          : data.non_field_errors
      } else if (err.response.status === 401) {
        error.value = 'Неверный email или пароль'
      } else {
        error.value = 'Произошла ошибка. Попробуйте позже'
      }
    } else {
      error.value = 'Ошибка соединения с сервером'
    }
  } finally {
    isLoading.value = false
  }
}

const forgotPassword = () => {
  navigateTo('/auth/forgot-password')
  close()
}
</script>

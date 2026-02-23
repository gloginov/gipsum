<template>
  <UPage>
    <UPageBody class="max-w-md mx-auto">
      <UCard>
        <template #header>
          <h1 class="text-2xl font-bold text-center">
            Вход
          </h1>
        </template>

        <UForm
          :state="form"
          class="space-y-4"
          @submit="handleLogin"
        >
          <UFormField
            label="Email"
            name="username"
            required
          >
            <UInput
              v-model="form.username"
              type="email"
              placeholder="email@example.com"
              icon="i-lucide-mail"
              :disabled="loading"
            />
          </UFormField>

          <UFormField
            label="Пароль"
            name="password"
            required
          >
            <UInput
              v-model="form.password"
              type="password"
              placeholder="••••••••"
              icon="i-lucide-lock"
              :disabled="loading"
            />
          </UFormField>

          <UCheckbox
            v-model="form.remember"
            label="Запомнить меня"
          />

          <UButton
            type="submit"
            block
            color="primary"
            :loading="loading"
          >
            Войти
          </UButton>
        </UForm>

        <template #footer>
          <p class="text-center text-sm text-gray-500">
            Нет аккаунта?
            <NuxtLink
              to="/register"
              class="text-primary-600 hover:underline"
            >
              Зарегистрироваться
            </NuxtLink>
          </p>
        </template>
      </UCard>
    </UPageBody>
  </UPage>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['guest']
})

const { login, fetchUser } = useAuth()
const toast = useToast()
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
  remember: false
})

async function handleLogin() {
  loading.value = true

  try {
    await login({
      username: form.username,
      password: form.password,
      remember: form.remember
    })

    // Загружаем пользователя в состояние
    await fetchUser()

    toast.add({
      title: 'Успешный вход',
      color: 'success'
    })

    // Редирект на сохранённый URL или в профиль
    const redirect = route.query.redirect as string
    await navigateTo(redirect || '/profile', { replace: true })
  } catch (error: any) {
    toast.add({
      title: 'Ошибка входа',
      description: error.data?.error || 'Неверные учётные данные',
      color: 'error'
    })
  } finally {
    loading.value = false
  }
}
</script>

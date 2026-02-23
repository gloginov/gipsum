<script setup lang="ts">
const { user, isAuthenticated, fetchUser, logout } = useAuth()

const config = useRuntimeConfig()
const showAuthModal = ref(false)
const { data } = await useFetch('api/settings/?keys=footer_copyright', {
  // key: 'unique-key-' + Date.now(), // уникальный ключ каждый раз
  baseURL: import.meta.server
    ? config.apiUrl// имя контейнера или внутренний адрес
    : config.public.apiBase
  // getCachedData: false // не использовать кешированные данные
})

// Загрузить пользователя при старте
onMounted(() => {
  fetchUser()
})

const onAuthSuccess = (userData: any) => {
  user.value = userData
}

const userMenuItems = [
  {
    label: 'Профиль',
    icon: 'i-lucide-user',
    to: '/profile'
  },
  {
    label: 'Заказы',
    icon: 'i-lucide-credit-card',
    to: '/orders'
  },
  {
    label: 'Корзина',
    icon: 'i-lucide-shopping-cart',
    to: '/cart'
  }
]
</script>

<template>
  <UApp>
    <UHeader
      variant="clear"
      class="bg-transparent fixed w-full border-none text-white"
    >
      <template #left>
        <NuxtLink to="/">
          <AppLogoHoriz class="w-auto h-12 shrink-0" />
        </NuxtLink>

        <!-- <TemplateMenu /> -->
      </template>

      <template #right>
        <NavigationMenu />

        <UColorModeButton />

        <UButton
          v-if="!isAuthenticated"
          color="gray"
          variant="ghost"
          icon="i-heroicons-user"
          @click="showAuthModal = true"
        >
          Войти
        </UButton>
        <UDropdownMenu
          v-else
          :items="userMenuItems"
        >
          <UButton
            color="gray"
            variant="ghost"
          >
            {{ user?.first_name || user?.email }}
          </UButton>
        </UDropdownMenu>

        <!-- <UButton
          to="https://github.com/nuxt-ui-templates/starter"
          target="_blank"
          icon="i-simple-icons-github"
          aria-label="GitHub"
          color="neutral"
          variant="ghost"
        /> -->
      </template>
    </UHeader>
    <UMain>
      <NuxtPage />
    </UMain>
    <USeparator class="w-full" />

    <UFooter>
      <template #left>
        <p class="text-sm text-muted">
          {{ data?.footer_copyright?.value }} • © {{ new Date().getFullYear() }}
        </p>
      </template>

      <template #right>
        <!-- <UButton
          to="https://github.com/nuxt-ui-templates/starter"
          target="_blank"
          icon="i-simple-icons-github"
          aria-label="GitHub"
          color="neutral"
          variant="ghost"
        /> -->
      </template>
    </UFooter>

    <AuthModal
      v-model="showAuthModal"
      @success="onAuthSuccess"
    />
  </UApp>
</template>

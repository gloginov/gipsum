<script setup>
const config = useRuntimeConfig()
const { data } = await useFetch('api/settings/?keys=footer_copyright', {
  // key: 'unique-key-' + Date.now(), // уникальный ключ каждый раз
  baseURL: import.meta.server
    ? config.apiUrl// имя контейнера или внутренний адрес
    : config.public.apiBase
  // getCachedData: false // не использовать кешированные данные
})
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
  </UApp>
</template>

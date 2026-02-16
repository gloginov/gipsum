<template>
  <UNavigationMenu
    :items="navigationItems"
    class="text-white"
    :ui="{
      link: 'text-black text-lg dark:text-white'
    }"
    @select="handleSelect"
  />
</template>

<script setup>
const route = useRoute()
const router = useRouter()

const navigationItems = computed(() => [
  {
    label: 'Главная',
    to: '/'
  },
  {
    label: 'Каталог',
    to: '/products'
  },
  {
    label: 'Популярные товары',
    to: route.path === '/' ? '#popular-products' : '/#popular-products'
  },
  {
    label: 'Задать вопрос',
    to: route.path === '/' ? '#feedback' : '/#feedback'
  }
])

const handleSelect = (item) => {
  if (item.to.includes('#')) {
    const [path, hash] = item.to.split('#')

    if (path === '' || path === '/') {
      // Мы на главной или переходим на главную
      if (route.path === '/') {
        // Уже на главной - просто скроллим
        scrollToSection(hash)
      } else {
        // На другой странице - переходим на главную с якорем
        router.push(`/#${hash}`)
      }
    }
  }
}

const scrollToSection = (id) => {
  nextTick(() => {
    setTimeout(() => {
      const element = document.getElementById(id)
      if (element) {
        const yOffset = -64
        const y = element.getBoundingClientRect().top + window.scrollY + yOffset
        window.scrollTo({ top: y, behavior: 'smooth' })
      }
    }, 500)
  })
}

// Автоскролл при переходе на главную с якорем
watch(() => route.hash, (hash) => {
  if (hash && route.path === '/') {
    const id = hash.slice(1)
    nextTick(() => scrollToSection(id))
  }
}, { immediate: true })
</script>

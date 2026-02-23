import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

export default defineNuxtRouteMiddleware(async (to, from) => {
  // Пропускаем, если уже на странице логина (чтобы избежать цикла)
  if (to.path === '/login' || to.path === '/register') {
    return
  }

  const user = useState<any>('user')
  const isAuthenticated = computed(() => !!user.value)

  // Если пользователь уже загружен в состоянии
  if (isAuthenticated.value) {
    return
  }

  // Пробуем загрузить пользователя (работает и на сервере, и на клиенте)
  try {
    const data = await $fetch('auth/me/', {
      credentials: 'include',
      headers: {
        ...useRequestHeaders(['cookie']), // Пробрасываем cookies на сервере
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      },
      baseURL: getCurrentApiUrl()
    })

    // Если успешно — сохраняем пользователя
    if (data) {
      user.value = data
      return
    }
  } catch (error: any) {
    // 401 или другая ошибка — пользователь не авторизован
    console.log('Auth check failed:', error.statusCode || error.message)
  }

  // Пользователь не авторизован
  if (process.server) {
    // На сервере делаем редирект
    return navigateTo('/login?redirect=' + encodeURIComponent(to.fullPath))
  } else {
    // На клиенте тоже редирект
    return navigateTo('/login?redirect=' + encodeURIComponent(to.fullPath))
  }
})
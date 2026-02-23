import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

export default defineNuxtRouteMiddleware(async (to, from) => {
  const user = useState<any>('user')

  // Если пользователь уже в состоянии — редиректим в профиль
  if (user.value) {
    return navigateTo('/profile')
  }

  // Пробуем загрузить пользователя
  try {
    const data = await $fetch('auth/me/', {
      credentials: 'include',
      headers: {
        ...useRequestHeaders(['cookie']),
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      },
      baseURL: getCurrentApiUrl()
    })

    if (data) {
      user.value = data
      // Если авторизован — не пускаем на страницы логина/регистрации
      return navigateTo('/profile')
    }
  } catch {
    // Не авторизован — разрешаем доступ к странице
  }
})
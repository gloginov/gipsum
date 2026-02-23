import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

export default defineNuxtPlugin(async () => {
  const user = useState<any>('user')
  
  // На клиенте проверяем авторизацию при старте приложения
  if (!user.value) {
    try {
      const data = await $fetch('auth/me/', {
        credentials: 'include',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        baseURL: getCurrentApiUrl()
      })
      user.value = data
    } catch {
      user.value = null
    }
  }
})
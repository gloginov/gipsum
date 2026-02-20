// // composables/useAuth.ts
// import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

// export const useAuth = () => {
//   const user = useState<any>('user', () => null)
//   const isAuthenticated = computed(() => !!user.value)

//   // Получить текущего пользователя
//   const fetchUser = async () => {
//     try {
//       const data = await $fetch('auth/me/', {
//         credentials: 'include',
//         baseURL: getCurrentApiUrl()
//       })
//       user.value = data
//       return data
//     } catch (e) {
//       user.value = null
//       return null
//     }
//   }

//   // Выход
//   const logout = async () => {
//     try {
//       await $fetch('auth/logout/', {
//         method: 'POST',
//         credentials: 'include',
//         baseURL: getCurrentApiUrl()
//       })
//       user.value = null
//       useToast().add({
//         title: 'Выход выполнен',
//         color: 'green'
//       })
//       await navigateTo('/')
//     } catch (e) {
//       useToast().add({
//         title: 'Ошибка при выходе',
//         color: 'red'
//       })
//     }
//   }

//   return {
//     user,
//     isAuthenticated,
//     fetchUser,
//     logout
//   }
// }

// composables/useAuth.ts
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

export const useAuth = () => {
  const user = useState<any>('user', () => null)
  const isAuthenticated = computed(() => !!user.value)
  const isLoading = ref(false)
  const csrfToken = useState<string>('csrf-token', () => '')

  // Получение CSRF из cookie (работает только если cookie не HttpOnly)
  const getCSRFToken = (): string => {
    const match = document.cookie.match(/csrftoken=([^;]+)/)
    return match ? match[1] : ''
  }

  // Главное исправление: получаем CSRF с сервера и сохраняем в состоянии
  const ensureCSRF = async (): Promise<string> => {
    // Если уже есть в состоянии - используем его
    if (csrfToken.value) {
      return csrfToken.value
    }

    // Пробуем получить из cookie (если не HttpOnly)
    let token = getCSRFToken()
    
    // Если нет в cookie - запрашиваем с сервера
    if (!token) {
      try {
        const response = await $fetch<{ csrfToken: string }>('auth/csrf/', {
          method: 'GET',
          credentials: 'include',
          headers: { 
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          baseURL: getCurrentApiUrl()
        })
        
        // Сервер возвращает токен в теле ответа
        if (response.csrfToken) {
          token = response.csrfToken
        }
        
        // Даем время на установку cookie
        await new Promise(r => setTimeout(r, 100))
        
        // Повторная проверка cookie
        if (!token) {
          token = getCSRFToken()
        }
      } catch (e) {
        console.error('CSRF fetch failed:', e)
      }
    }
    
    // Сохраняем в состояние приложения
    if (token) {
      csrfToken.value = token
    }
    
    return token
  }

  const fetchUser = async (): Promise<any | null> => {
    isLoading.value = true
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
      return data
    } catch (e) {
      user.value = null
      return null
    } finally {
      isLoading.value = false
    }
  }

  const initCSRF = async (): Promise<void> => {
    await ensureCSRF()
  }

  const logout = async (): Promise<void> => {
    const token = await ensureCSRF()
    
    if (!token) {
      useToast().add({
        title: 'Ошибка CSRF',
        description: 'Не удалось получить токен безопасности',
        color: 'red'
      })
      return
    }
    
    try {
      await $fetch('auth/logout/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': token,
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        baseURL: getCurrentApiUrl()
      })
      user.value = null
      csrfToken.value = ''
      useToast().add({
        title: 'Выход выполнен',
        color: 'green'
      })
      await navigateTo('/')
    } catch (e) {
      useToast().add({
        title: 'Ошибка при выходе',
        color: 'red'
      })
    }
  }

  // Новый метод для логина/регистрации с CSRF
  const login = async (credentials: { username: string; password: string; remember?: boolean }) => {
    const token = await ensureCSRF()
    
    if (!token) {
      throw new Error('CSRF token not available')
    }

    const response = await $fetch('auth/login/', {
      method: 'POST',
      body: credentials,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': token,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      },
      baseURL: getCurrentApiUrl()
    })

    return response
  }

  const register = async (data: { email: string; password: string; password2: string; first_name?: string }) => {
    const token = await ensureCSRF()
    
    if (!token) {
      throw new Error('CSRF token not available')
    }

    const response = await $fetch('auth/register/', {
      method: 'POST',
      body: data,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': token,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      },
      baseURL: getCurrentApiUrl()
    })

    return response
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    csrfToken,
    fetchUser,
    ensureCSRF,
    initCSRF,
    logout,
    login,
    register
  }
}
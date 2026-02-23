// ~/helpers/refreshCSRFToken.ts
import getCurrentApiUrl from './getCurrentApiUrl'

export async function refreshCSRFToken(): Promise<string> {
  const { data } = await useFetch<{ csrfToken: string }>('auth/csrf/', {
    credentials: 'include',
    baseURL: getCurrentApiUrl(),
  })
  
  // Обновляем куку вручную если нужно
  if (data.value?.csrfToken) {
    document.cookie = `csrftoken=${data.value.csrfToken}; path=/; domain=.gipsum.docker; Secure; SameSite=None`
  }
  
  return data.value?.csrfToken || ''
}
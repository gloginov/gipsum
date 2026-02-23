export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const token = await getCDEKToken()
  
  try {
    const response = await $fetch('https://api.edu.cdek.ru/v2/calculator/tarifflist', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body,
    })
    
    return response
  } catch (error: any) {
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || 'Failed to calculate delivery',
    })
  }
})

async function getCDEKToken(): Promise<string> {
  const config = useRuntimeConfig()
  
  const response = await $fetch<{ access_token: string }>('https://api.edu.cdek.ru/v2/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: config.cdekClientId,
      client_secret: config.cdekClientSecret,
    }),
  })
  
  return response.access_token
}
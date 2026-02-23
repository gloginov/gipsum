export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const { lat, lon, city, size = 1 } = query
  
  const token = await getCDEKToken()
  
  let url = 'https://api.edu.cdek.ru/v2/location/coordinates?'
  
  if (city) {
    url += `city=${encodeURIComponent(String(city))}&`
  } else if (lat && lon) {
    url += `latitude=${lat}&longitude=${lon}&`
  }
  
  url += `size=${size}`
  
  try {
    const response = await $fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    
    return response
  } catch (error: any) {
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || 'Failed to fetch cities',
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
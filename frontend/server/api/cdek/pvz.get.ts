export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const { city_code, lat, lon, radius = 50 } = query
  
  const token = await getCDEKToken()
  
  let url = 'https://api.edu.cdek.ru/v2/deliverypoints?take_only=true'
  
  if (city_code) {
    url += `&city_code=${city_code}`
  } else if (lat && lon) {
    url += `&latitude=${lat}&longitude=${lon}&radius=${radius}`
  }
  
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
      statusMessage: error.message || 'Failed to fetch PVZ',
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
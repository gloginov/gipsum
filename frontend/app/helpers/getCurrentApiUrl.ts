export default function getCurrentApiUrl() {
  const config = useRuntimeConfig()
  return import.meta.server
    ? config.apiUrl // имя контейнера или внутренний адрес
    : config.public.apiBase
}

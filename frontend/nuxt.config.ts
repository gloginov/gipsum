// https://nuxt.com/docs/api/configuration/nuxt-config
// import { loadEnv } from "vite";
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@nuxt/fonts',
    '@nuxt/image',
    // '@nuxt/google-fonts',
    '@pinia/nuxt',
    'nuxt-jsonld',
    'vue-yandex-maps/nuxt',
  ],

  yandexMaps: {
    apikey: process.env.NUXT_PUBLIC_YANDEX_MAPS_API_KEY,
  },

  pinia: {
    storesDirs: ['./stores/**'],
  },

  ui: {
    primary: 'FFC847', // меняет var(--ui-primary)
  },
  // devServer: {
  //   host: '127.0.0.1',
  //   port: 3000
  // },

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  // eslint: {
  // options here
  // },
  runtimeConfig: {
    apiUrl: 'http://server-gipsum:5000/',
    // Server-only (not exposed to browser)
    cdekClientId: process.env.NUXT_PUBLIC_CDEK_CLIENT_ID,
    cdekClientSecret: process.env.NUXT_PUBLIC_CDEK_CLIENT_SECRET,

    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE,
      yandexMapsApiKey: process.env.NUXT_PUBLIC_YANDEX_MAPS_API_KEY,
    }
  },

  // routeRules: {
  //   '/': { prerender: true }
  // },

  compatibilityDate: '2025-01-15',

  vite: {
    server: {
      allowedHosts: true
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },
  // vite: {
  //   // Загрузить env из кастомной директории
  //   envDir: "../",
  // },

  fonts: {}
})
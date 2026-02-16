// https://nuxt.com/docs/api/configuration/nuxt-config
// import { loadEnv } from "vite";
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@nuxt/fonts',
    '@nuxt/image'
    // '@nuxt/google-fonts',
  ],

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
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE
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
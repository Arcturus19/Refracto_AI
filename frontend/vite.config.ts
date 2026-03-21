import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      react(),
      VitePWA({
        registerType: 'autoUpdate',
        manifest: {
          name: 'Refracto Medical',
          short_name: 'Refracto',
          description: 'Refracto medical PWA',
          theme_color: '#0ea5e9',
          background_color: '#ffffff',
          display: 'standalone',
          start_url: '/',
          icons: [
            { src: '/pwa-192x192.svg', sizes: '192x192', type: 'image/svg+xml' },
            { src: '/pwa-512x512.svg', sizes: '512x512', type: 'image/svg+xml' }
          ]
        }
      })
    ],
    server: {
      proxy: {
        '/api/auth': {
          target: env.VITE_AUTH_PROXY_TARGET || 'http://localhost:8001',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/auth/, ''),
        },
        '/api/patients': {
          target: env.VITE_PATIENT_PROXY_TARGET || 'http://localhost:8002',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/patients/, ''),
        },
        '/api/imaging': {
          target: env.VITE_IMAGING_PROXY_TARGET || 'http://localhost:8003',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/imaging/, ''),
        },
        '/api/ml': {
          target: env.VITE_ML_PROXY_TARGET || 'http://localhost:8004',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/ml/, ''),
        },
      },
    },
  }
})

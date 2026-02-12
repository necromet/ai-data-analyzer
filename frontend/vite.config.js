import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/runs': {
        target: 'http://127.0.0.1:2024',
        changeOrigin: true,
        secure: false,
      },
      '/threads': {
        target: 'http://127.0.0.1:2024',
        changeOrigin: true,
        secure: false,
      },
      '/assistants': {
        target: 'http://127.0.0.1:2024',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})

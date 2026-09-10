import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/tasks': 'http://127.0.0.1:8000',
      '/sections': 'http://127.0.0.1:8000',
      '/schedule': 'http://127.0.0.1:8000',
      '/metrics': 'http://127.0.0.1:8000',
      '/audit': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000',
    },
  },
})


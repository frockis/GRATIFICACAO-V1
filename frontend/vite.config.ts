import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Encaminha /api para o backend Django (backend/). Sem backend rodando, o front usa o mockData.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})

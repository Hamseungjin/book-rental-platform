import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // VITE_API_BASE_URL=/api 를 사용할 때만 이 프록시가 사용됩니다.
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
    },
  },
})

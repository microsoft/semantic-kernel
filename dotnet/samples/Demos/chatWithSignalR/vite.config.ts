import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    cors: false,
    proxy: {
      '/chatHub': {
        target: "http://localhost:58848",
        changeOrigin: true,
        secure: false
      }
    }
  }
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/webhook': 'http://localhost:8080',
      '/ledger': 'http://localhost:8080',
      '/batch': 'http://localhost:8080',
      '/metrics': 'http://localhost:8080',
      '/tts': 'http://localhost:8080'
    }
  }
})

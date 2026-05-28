import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // indispensable pour que le mapping de port Docker fonctionne
    port: 5173,
    watch: {
      usePolling: true // assure la détection des changements de fichiers sous Docker (macOS/Linux)
    }
  }
})

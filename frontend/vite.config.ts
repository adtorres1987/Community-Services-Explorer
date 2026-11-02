import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // 5173 is used by another local project; the API allows this origin via CORS_ORIGINS
  server: { port: 5174, strictPort: true },
})

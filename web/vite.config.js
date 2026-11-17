import { defineConfig } from 'vite'
import { existsSync } from 'node:fs'
export default defineConfig({
  define: {
    __VAULT_PREVIEW_AVAILABLE__: JSON.stringify(existsSync(new URL('./public/images/vault-preview.webp', import.meta.url))),
  },
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { outDir: 'dist' }
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify('https://lcbaterias.automatexia.com.br'),
    'import.meta.env.VITE_SUPABASE_URL': JSON.stringify('https://iexwyilovmxllfgggbvp.supabase.co'),
    'import.meta.env.VITE_SUPABASE_ANON_KEY': JSON.stringify('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlleHd5aWxvdm14bGxmZ2dnYnZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA3MjI5NTksImV4cCI6MjA2NjI5ODk1OX0.hrodZAa2W-2BlHEin8HdCg--2gOvQCpklSnBkqrf9no'),
  },
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        // Ignorar warnings de variáveis não usadas
        if (warning.code === 'UNUSED_EXTERNAL_IMPORT') return;
        warn(warning);
      }
    }
  }
})

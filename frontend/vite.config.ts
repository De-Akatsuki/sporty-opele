import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, path.resolve(__dirname, '..'), '');
  const localEnv = loadEnv(mode, __dirname, '');

  return {
    plugins: [react()],
    envDir: __dirname,
    define: {
      'import.meta.env.VITE_SUPABASE_URL': JSON.stringify(
        localEnv.VITE_SUPABASE_URL || rootEnv.SUPABASE_URL || ''
      ),
      'import.meta.env.VITE_SUPABASE_ANON_KEY': JSON.stringify(
        localEnv.VITE_SUPABASE_ANON_KEY || rootEnv.SUPABASE_KEY || ''
      ),
    },
    optimizeDeps: {
      exclude: ['lucide-react'],
    },
  };
});

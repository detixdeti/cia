import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In development, API calls are forwarded to the locally running backend.
// In Docker, nginx does the same (see nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});

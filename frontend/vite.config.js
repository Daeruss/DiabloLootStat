import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// В dev-режиме проксируем API/админку на Django (localhost:8000),
// чтобы браузер работал с одним origin и не было проблем с CORS/CSRF.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/admin": "http://localhost:8000",
      "/static": "http://localhost:8000",
    },
  },
});

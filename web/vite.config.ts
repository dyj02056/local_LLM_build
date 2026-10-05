import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // 개발 중에는 FastAPI(8000)로 API 요청을 넘긴다
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server runs on 5173 and proxies nothing — the app talks to the backend
// directly via VITE_API_BASE_URL (default http://localhost:8000).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
});

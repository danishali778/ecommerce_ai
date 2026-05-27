import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: path.resolve(__dirname, "src/test/setup.ts")
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@frontend/ui": path.resolve(__dirname, "../../packages/frontend/ui/index.tsx"),
      "@frontend/types": path.resolve(__dirname, "../../packages/frontend/types/index.ts"),
      "@frontend/config": path.resolve(__dirname, "../../packages/frontend/config/index.ts"),
      "@frontend/api-client": path.resolve(__dirname, "../../packages/frontend/api-client/index.ts")
    }
  },
  server: {
    port: 5173
  }
});

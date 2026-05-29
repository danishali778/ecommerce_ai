import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          if (id.includes("recharts")) return "charts";
          if (id.includes("react-router")) return "router";
          if (id.includes("@tanstack/react-query")) return "query";
          if (id.includes("react") || id.includes("scheduler")) return "react-vendor";
        }
      }
    }
  },
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

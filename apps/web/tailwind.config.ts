import type { Config } from "tailwindcss";

export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
    "../../packages/frontend/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        accent: {
          50: "#eef5ff",
          100: "#dce9ff",
          500: "#1558d6",
          600: "#0f49b3",
          700: "#123b87"
        }
      },
      boxShadow: {
        soft: "0 12px 36px rgba(15, 73, 179, 0.10)"
      }
    }
  },
  plugins: []
} satisfies Config;

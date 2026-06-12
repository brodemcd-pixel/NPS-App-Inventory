import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0f1c",
          900: "#0e1526",
          850: "#121a2e",
          800: "#172238",
          700: "#1f2d49",
          600: "#2b3d5f",
        },
      },
    },
  },
  plugins: [],
};

export default config;

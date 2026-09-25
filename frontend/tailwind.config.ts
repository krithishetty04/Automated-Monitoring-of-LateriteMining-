import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark "field survey" palette — quarry/topographic feel
        base: {
          950: "#12140f",
          900: "#191c15",
          800: "#22261c",
          700: "#2e3325",
          600: "#3f4732",
        },
        clay: {
          400: "#e0a05b",
          500: "#cf8a3f",
          600: "#b5722c",
        },
        permit: "#5fa777",   // GREEN — official boundary
        excavate: "#c8503d", // RED — detected excavation
        alertY: "#d9b84a",   // YELLOW — unauthorized new excavation
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        sans: ["ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;

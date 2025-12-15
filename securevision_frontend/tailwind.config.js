
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0f172a", // Slate 900
        surface: "#1e293b", // Slate 800
        primary: "#3b82f6", // Blue 500
        secondary: "#8b5cf6", // Violet 500
        accent: "#f43f5e", // Rose 500
      },
    },
  },
  plugins: [],
}

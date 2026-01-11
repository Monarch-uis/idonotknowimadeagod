/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brutal-black': '#0a0a0a',
        'brutal-white': '#f5f5f5',
        'brutal-gray': '#262626',
        'brutal-blue': '#0033ff',
        'brutal-red': '#ff0033',
      },
      fontFamily: {
        'display': ['"Space Grotesk"', 'sans-serif'],
        'mono': ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'brutal': '4px 4px 0px 0px #000000',
        'brutal-lg': '8px 8px 0px 0px #000000',
        'brutal-hover': '2px 2px 0px 0px #000000',
      }
    },
  },
  plugins: [],
}
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        navy: {
          DEFAULT: '#0a2540',
          mid: '#1a3a5c',
        },
        accent: {
          DEFAULT: '#0570de',
          light: '#eff6ff',
        },
      },
    },
  },
  plugins: [],
}

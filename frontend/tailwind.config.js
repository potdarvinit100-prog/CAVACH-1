/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { 900: '#0a1220', 800: '#0f1b2d', 700: '#16263f' },
        ink: '#e8eef6',
        muted: '#93a4b8',
        accent: '#22c3c3',
        danger: '#f26d6d',
        warn: '#f5b544',
        ok: '#4ade80',
      },
    },
  },
  plugins: [],
}

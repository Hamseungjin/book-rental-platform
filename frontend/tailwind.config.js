/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { brand: { 50: '#eef7ff', 500: '#2785d8', 600: '#176bb4', 700: '#14558d' } } } },
  plugins: [],
}

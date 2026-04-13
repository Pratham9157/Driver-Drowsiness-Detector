/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        drowsy: {
          50: '#fef3f2',
          100: '#fce7e4',
          200: '#f9d4ce',
          300: '#f4a89a',
          400: '#ed7964',
          500: '#e54e35',
          600: '#d23b27',
          700: '#b02e19',
          800: '#932a17',
          900: '#7a2817',
        }
      }
    },
  },
  plugins: [],
}

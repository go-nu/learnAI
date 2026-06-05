/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        daum: {
          blue: '#0068C3',
          'blue-dark': '#0052A3',
          'blue-light': '#E8F2FC',
          orange: '#FF5E00',
          bg: '#F2F4F8',
          border: '#D9DCE3',
          text: '#1A1A1A',
          subtle: '#767676',
          card: '#FFFFFF',
        },
      },
      fontFamily: {
        sans: ['"Noto Sans KR"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

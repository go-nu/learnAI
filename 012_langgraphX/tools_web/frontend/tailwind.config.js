/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        dark: {
          bg:      '#0d1117',
          surface: '#161b22',
          card:    '#1c2a1c',
          input:   '#0f1f10',
          border:  '#2a4a2a',
          hover:   '#243824',
        },
        green: {
          soft:    '#86efac',
          bright:  '#4ade80',
          active:  '#22c55e',
          dim:     '#3d7a4a',
          glow:    'rgba(134,239,172,0.12)',
          glowMd:  'rgba(134,239,172,0.25)',
        },
        txt: {
          primary:   '#e8fde8',
          secondary: '#a3c9a8',
          muted:     '#5a7a5a',
        },
      },
      fontFamily: {
        sans: ['"Noto Sans KR"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
      boxShadow: {
        green: '0 0 0 3px rgba(134,239,172,0.2)',
        card:  '0 4px 24px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
}

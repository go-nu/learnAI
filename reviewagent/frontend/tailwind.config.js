/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary:        'var(--primary)',
        'primary-dark': 'var(--primary-dark)',
        ink:            'var(--ink)',
        ink2:           'var(--ink2)',
        danger:         'var(--danger)',
        success:        'var(--success)',
        surface:        'var(--surface)',
        'page-bg':      'var(--page-bg)',
        'hover-bg':     'var(--hover-bg)',
        divider:        'var(--divider)',
      },
      boxShadow: {
        card: '0 2px 12px rgba(0,0,0,0.06)',
        nav:  '0 1px 8px rgba(0,0,0,0.06)',
      },
      borderRadius: {
        '2xl': '16px',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}


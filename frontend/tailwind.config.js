/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Playfair Display"', 'Georgia', 'serif'],
      },
      colors: {
        primary:   { DEFAULT: '#C8102E', light: '#E8344A', dark: '#9B0D22' },
        secondary: '#F5A623',
        surface:   { DEFAULT: '#1A1D27', 2: '#22263A' },
        border:    'rgba(255,255,255,0.08)',
      },
      boxShadow: {
        card:  '0 4px 16px rgba(0,0,0,0.4)',
        hover: '0 8px 32px rgba(0,0,0,0.5)',
        glow:  '0 0 24px rgba(200,16,46,0.2)',
      },
      animation: {
        'fade-in':   'fadeIn 0.3s ease forwards',
        'slide-up':  'slideUp 0.4s ease forwards',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:   { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp:  { from: { opacity: 0, transform: 'translateY(16px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        pulseDot: { '0%,80%,100%': { transform: 'scale(0)' }, '40%': { transform: 'scale(1)' } },
      },
    },
  },
  plugins: [],
}

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
        accent:  { DEFAULT: '#C9A84C', light: '#DFC06E', dark: '#A8872E' },
        ink:     '#F0EBE0',
        muted:   '#8A8070',
        bg:      '#0C0B08',
        surface: { DEFAULT: '#161410', 2: '#1E1C18' },
      },
      borderColor: {
        subtle: 'rgba(240,235,224,0.07)',
      },
      boxShadow: {
        card:  '0 2px 20px rgba(0,0,0,0.5)',
        glow:  '0 0 32px rgba(201,168,76,0.15)',
      },
      animation: {
        'fade-in':   'fadeIn 0.4s ease forwards',
        'slide-up':  'slideUp 0.35s ease forwards',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
        'spin-pasta':'spinPasta 1.8s linear infinite',
      },
      keyframes: {
        fadeIn:    { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp:   { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        pulseDot:  { '0%,80%,100%': { transform: 'scale(0)' }, '40%': { transform: 'scale(1)' } },
        spinPasta: {
          '0%':   { transform: 'rotate(0deg)   scale(1)    translateY(0px)' },
          '25%':  { transform: 'rotate(90deg)  scale(1.15) translateY(-6px)' },
          '50%':  { transform: 'rotate(180deg) scale(1)    translateY(0px)' },
          '75%':  { transform: 'rotate(270deg) scale(1.15) translateY(-6px)' },
          '100%': { transform: 'rotate(360deg) scale(1)    translateY(0px)' },
        },
      },
    },
  },
  plugins: [],
}

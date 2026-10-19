/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: { '2xl': '1400px' },
    },
    extend: {
      colors: {
        background: '#0B0B0B',
        surface: {
          DEFAULT: '#121212',
          elevated: '#171717',
        },
        border: 'rgba(255, 255, 255, 0.08)',
        brand: {
          DEFAULT: '#FF6B1A',
          soft: '#FFB27A',
        },
        text: {
          primary: '#F5F5F5',
          secondary: '#A3A3A3',
        },
        success: '#22C55E',
        error: '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #FF6B1A 0%, #FFB27A 100%)',
        'brand-radial': 'radial-gradient(circle at 30% 20%, rgba(255,107,26,0.18), transparent 60%)',
      },
      boxShadow: {
        glow: '0 0 40px -10px rgba(255,107,26,0.5)',
        card: '0 10px 30px -10px rgba(0,0,0,0.6)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-slow': {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.5s ease-out',
        'pulse-slow': 'pulse-slow 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.4s ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
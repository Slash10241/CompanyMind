/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        rm: {
          white:  '#FFFFFF',
          cream:  '#F8F8F6',
          gold:   '#F7B731',
          'gold-dark': '#D9A020',
          navy:   '#00529F',
          'navy-dark': '#003D7A',
          'navy-light': '#E8F0FA',
          gray:   '#6B7280',
          'gray-light': '#E5E7EB',
          'gray-ultra': '#F3F4F6',
          text:   '#1A2744',
        },
      },
    },
  },
  plugins: [],
}

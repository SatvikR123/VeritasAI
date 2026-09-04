/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0B0F17',
          darker: '#070a10',
          card: '#111827',
          glass: 'rgba(17, 24, 39, 0.7)',
          hover: '#141922',
          border: 'rgba(255, 255, 255, 0.06)',
          borderHover: 'rgba(255, 255, 255, 0.12)',
        },
        accent: {
          blue: "#4F7EFF",
          purple: "#7C5CFF",
        },
        success: "#3DDC97",
        warning: "#F6B73C",
        danger: "#FF5C7A",
        text: {
          primary: "#F8FAFC",
          secondary: "#94A3B8",
          muted: "#64748B",
        }
      },
      fontFamily: {
        sans: ["Inter", "Geist", "SF Pro Display", "sans-serif"],
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}

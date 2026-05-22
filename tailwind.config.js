/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './base/templates/**/*.html',
    './game/templates/**/*.html',
    './script/templates/**/*.html',
    './users/templates/**/*.html',
    './templates/**/*.html',
    './base/static/js/**/*.js',
    './game/static/js/**/*.js',
    './script/templatetags/**/*.py',
  ],
  safelist: [
    // Damage type pill colors — generated dynamically via template tag
    'bg-stone-500',   'text-white',
    'bg-yellow-400',  'text-black',
    'bg-orange-500',
    'bg-cyan-400',
    'bg-lime-600',
    'bg-blue-500',
    'bg-purple-500',
    'bg-gray-700',    'text-gray-200',
    'bg-yellow-200',  'text-yellow-900',
    'bg-indigo-900',  'text-indigo-200',
  ],
  theme: {
    extend: {
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'attack': 'attack 0.3s ease-in-out',
        'damage': 'damage 0.5s ease-in-out',
      },
      keyframes: {
        attack: {
          '0%, 100%': { transform: 'translateX(0)' },
          '50%': { transform: 'translateX(10px)' },
        },
        damage: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        }
      }
    },
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        efilwol: {
          "primary": "#8b5cf6",
          "secondary": "#ec4899",
          "accent": "#14b8a6",
          "neutral": "#1f2937",
          "base-100": "#0f172a",
          "base-200": "#1e293b",
          "base-300": "#334155",
          "info": "#3b82f6",
          "success": "#10b981",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
      },
      "dark",
      "forest",
      "dracula",
    ],
    darkTheme: "efilwol",
    base: true,
    styled: true,
    utils: true,
  },
}

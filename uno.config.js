import { defineConfig, presetUno } from 'unocss';

// UnoCSS configuration for the static (no-build-runtime) GitHub Pages app.
//
// IMPORTANT: styles are PRECOMPILED into assets/css/uno.css.
// If you add or change utility classes in index.html, 404.html or
// assets/js/app.js, regenerate the stylesheet with:
//
//   npx --yes @unocss/cli index.html 404.html assets/js/app.js -o assets/css/uno.css
//
// Dark mode is CLASS-BASED: `dark:` variants key off the `.dark` class on
// <body>, which is toggled by assets/js/app.js (applyTheme).

export default defineConfig({
  presets: [
    presetUno({ dark: 'class' }),
  ],

  // Component classes previously done with Tailwind CDN `@apply`.
  shortcuts: {
    card: 'rounded-[2rem] shadow-xl border bg-white border-gray-200 shadow-gray-200 dark:bg-gray-800 dark:border-gray-700 dark:shadow-gray-900',

    field: 'w-full p-4 rounded-2xl border bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition dark:bg-gray-900 dark:border-gray-700 dark:text-white dark:placeholder-gray-600',

    'select-field': 'w-full p-4 rounded-2xl border appearance-none bg-gray-50 border-gray-200 text-gray-900 font-bold cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 transition dark:bg-gray-900 dark:border-gray-700 dark:text-white',

    'muted-label': 'block text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-3',

    'tab-btn': 'flex-1 pb-4 text-xs font-black uppercase tracking-widest border-b-2 border-transparent transition text-gray-400 hover:text-gray-500',

    'ghost-btn': 'border py-4 rounded-2xl font-bold text-[10px] uppercase tracking-widest transition flex items-center justify-center gap-2 bg-white text-gray-600 border-gray-100 hover:text-gray-900 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-300 dark:hover:text-white',
  },

  content: {
    pipeline: {
      include: [
        /\.(html|js)$/,
      ],
    },
  },
});

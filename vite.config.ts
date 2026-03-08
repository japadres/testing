/**
 * Vite build config — mirrors the nicegui/examples/vue_vite pattern.
 *
 * Each .vue file is compiled to a standalone ES module in js/.
 * Vue is marked external so the output uses `import { ref } from 'vue'`,
 * which NiceGUI's frontend resolves against its own bundled Vue instance
 * via the import map it injects into the page.
 *
 * Build:  npm run build
 * Watch:  npm run watch   (rebuilds on .vue file changes)
 *
 * Output:
 *   js/GridContainer.js
 *   js/GridItem.js
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// import.meta.url is always the URL of THIS file (vite.config.ts),
// so new URL('./src/...', import.meta.url) gives an absolute path
// regardless of which directory `npm run build` is invoked from.
const entry = (rel: string) => fileURLToPath(new URL(rel, import.meta.url))

export default defineConfig({
  plugins: [vue()],

  build: {
    outDir:      'js',
    emptyOutDir: true,

    lib: {
      entry: {
        GridContainer: entry('./src/GridContainer.vue'),
        GridItem:      entry('./src/GridItem.vue'),
      },
      formats: ['es'],
      fileName: (_format, name) => `${name}.js`,
    },

    rollupOptions: {
      // Vue is provided by NiceGUI's frontend bundle — don't ship it twice.
      external: ['vue'],
    },
  },
})
import { createPinia, setActivePinia } from 'pinia';

// Create a SINGLETON pinia instance and activate it immediately.
// This runs when the module is first imported (by any .vue file via Vite transform).
const pinia = createPinia();
setActivePinia(pinia);

// Also export for explicit use
export { pinia };

// Astro appEntrypoint — registers pinia on each Vue app instance.
// In Astro 6 with client:only, each island creates its own Vue app.
// This ensures app.provide() and app.config.globalProperties are set.
export default (app: any) => {
  if (!app._piniaInstalled) {
    app.use(pinia);
    app._piniaInstalled = true;
  }
};

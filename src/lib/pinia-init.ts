/**
 * Pinia auto-initialization.
 * Import this BEFORE using any Pinia store to ensure pinia is active.
 * This is needed because Astro 6 client:only islands create separate Vue apps,
 * and the appEntrypoint may not fire before store usage.
 */
import { createPinia, setActivePinia, getActivePinia } from 'pinia';

let pinia: ReturnType<typeof createPinia> | null = null;

export function getPinia() {
  if (pinia) return pinia;
  try {
    pinia = getActivePinia();
    if (pinia) return pinia;
  } catch {
    // No active pinia — create one
  }
  pinia = createPinia();
  setActivePinia(pinia);
  return pinia;
}

// Auto-initialize on module load
getPinia();

export default getPinia;
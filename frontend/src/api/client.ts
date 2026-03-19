import axios from 'axios'

declare global {
  interface Window {
    __TAURI__?: unknown
    __TAURI_INTERNALS__?: unknown
  }
}

// Detect Tauri environment (v1 uses __TAURI__, v2 uses __TAURI_INTERNALS__)
export const isTauri = !!(window.__TAURI__ || window.__TAURI_INTERNALS__)

// In Tauri desktop: backend runs on localhost:8000
// In browser dev (vite proxy): /api proxies to localhost:8000
// In production SaaS: VITE_API_URL env var
const BASE_URL =
  (import.meta as any).env?.VITE_API_URL ??
  (isTauri ? 'http://localhost:8000/api' : '/api')

console.log(`[SemioVis] API base URL: ${BASE_URL} (tauri=${isTauri})`)

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
})

/**
 * Check if the backend is reachable right now.
 */
export async function checkBackend(): Promise<boolean> {
  try {
    await axios.get(`${BASE_URL.replace('/api', '')}/docs`, { timeout: 3000 })
    return true
  } catch {
    return false
  }
}

/**
 * Wait for the backend to become available.
 * The PyInstaller-bundled backend can take 60-120s on first launch.
 */
export async function waitForBackend(maxWaitMs = 120000): Promise<boolean> {
  const interval = 2000
  const start = Date.now()
  while (Date.now() - start < maxWaitMs) {
    if (await checkBackend()) return true
    await new Promise((r) => setTimeout(r, interval))
  }
  return false
}

import axios from 'axios'

declare global {
  interface Window {
    __TAURI__?: unknown
    __TAURI_INTERNALS__?: unknown
  }
}

// Detect Tauri environment (v1 uses __TAURI__, v2 uses __TAURI_INTERNALS__)
export const isTauri = !!(window.__TAURI__ || window.__TAURI_INTERNALS__)

// Resolved backend base URL — updated dynamically in Tauri mode
let resolvedBaseUrl: string =
  (import.meta as any).env?.VITE_API_URL ??
  (isTauri ? 'http://localhost:8000/api' : '/api')

/**
 * In Tauri mode, ask the Rust side which port the backend is actually on.
 * Uses the Tauri v2 internals IPC directly (no npm package needed).
 * Falls back to 8000 if the invoke fails (e.g. dev mode).
 */
async function resolveBackendPort(): Promise<void> {
  if (!isTauri) return
  try {
    const internals = window.__TAURI_INTERNALS__ as any
    if (internals?.invoke) {
      const port: number = await internals.invoke('get_backend_port')
      resolvedBaseUrl = `http://localhost:${port}/api`
      apiClient.defaults.baseURL = resolvedBaseUrl
      console.log(`[SemioVis] Backend port resolved: ${port}`)
    }
  } catch {
    console.log('[SemioVis] Could not resolve backend port, using default 8000')
  }
}

// Kick off port resolution immediately (non-blocking)
const portReady = resolveBackendPort()

console.log(`[SemioVis] API base URL: ${resolvedBaseUrl} (tauri=${isTauri})`)

export const apiClient = axios.create({
  baseURL: resolvedBaseUrl,
  timeout: 120000,
})

/**
 * Check if the backend is reachable via the lightweight /health endpoint.
 */
export async function checkBackend(): Promise<boolean> {
  await portReady // ensure we have the correct port
  try {
    const base = resolvedBaseUrl.replace('/api', '')
    await axios.get(`${base}/health`, { timeout: 2000 })
    return true
  } catch {
    return false
  }
}

/**
 * Wait for the backend to become available with adaptive polling:
 * - 500ms interval for the first 15s (fast detection)
 * - 1000ms interval after that
 */
export async function waitForBackend(maxWaitMs = 120000): Promise<boolean> {
  const start = Date.now()
  while (Date.now() - start < maxWaitMs) {
    if (await checkBackend()) return true
    const elapsed = Date.now() - start
    const interval = elapsed < 15000 ? 500 : 1000
    await new Promise((r) => setTimeout(r, interval))
  }
  return false
}

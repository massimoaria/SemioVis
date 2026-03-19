import axios from 'axios'

declare global {
  interface Window {
    __TAURI__?: unknown
    __TAURI_INTERNALS__?: unknown
  }
}

// Detect Tauri environment (v1 uses __TAURI__, v2 uses __TAURI_INTERNALS__)
const isTauri = !!(window.__TAURI__ || window.__TAURI_INTERNALS__)

// In Tauri desktop: backend runs on localhost:8000
// In browser dev (vite proxy): /api proxies to localhost:8000
// In production SaaS: VITE_API_URL env var
const BASE_URL =
  (import.meta as any).env?.VITE_API_URL ??
  (isTauri ? 'http://localhost:8000/api' : '/api')

console.log(`[SemioVis] API base URL: ${BASE_URL} (tauri=${isTauri})`)

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

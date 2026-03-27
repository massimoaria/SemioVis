import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { apiClient } from './api/client'
import './styles/globals.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

// Restore saved settings and send API keys to backend (retries silently)
async function sendSavedKeys() {
  try {
    const saved = localStorage.getItem('semiovis_settings')
    if (!saved) return
    const settings = JSON.parse(saved)
    const keys = settings.apiKeys
    if (keys && (keys.gemini || keys.openai || keys.mistral)) {
      // Retry a few times — backend may not be up yet on first attempt
      for (let i = 0; i < 5; i++) {
        try {
          await apiClient.post('/settings/keys', {
            gemini: keys.gemini || '',
            openai: keys.openai || '',
            mistral: keys.mistral || '',
          })
          return
        } catch {
          await new Promise((r) => setTimeout(r, 3000))
        }
      }
    }
  } catch {}
}
sendSavedKeys()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)

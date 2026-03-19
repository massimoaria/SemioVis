import { useState, useEffect } from 'react'
import { AlertTriangle, X, Loader2 } from 'lucide-react'
import { Layout } from './components/layout/Layout'
import { HomePage } from './components/layout/HomePage'
import { MethodologyGuide } from './components/layout/MethodologyGuide'
import { ImageUploader } from './components/upload/ImageUploader'
import { ImagePreview } from './components/upload/ImagePreview'
import { RepresentationalPanel } from './components/representational/RepresentationalPanel'
import { InteractivePanel } from './components/interactive/InteractivePanel'
import { CompositionalPanel } from './components/compositional/CompositionalPanel'
import { DashboardPanel } from './components/dashboard/DashboardPanel'
import { ReportPanel } from './components/report/ReportPanel'
import { useAnalysisStore } from './store/analysisStore'
import { isTauri, checkBackend } from './api/client'

function ApiKeyBanner() {
  const settings = useAnalysisStore((s) => s.settings)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    const stored = sessionStorage.getItem('semiovis_api_banner_dismissed')
    if (stored === 'true') setDismissed(true)
  }, [])

  const hasKey = settings.apiKeys.gemini || settings.apiKeys.openai || settings.apiKeys.mistral
  if (hasKey || dismissed) return null

  const dismiss = () => {
    setDismissed(true)
    sessionStorage.setItem('semiovis_api_banner_dismissed', 'true')
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex items-center gap-3">
      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
      <p className="text-sm text-amber-800 flex-1">
        <span className="font-medium">No LLM API key configured.</span>{' '}
        Analysis reports will use basic rule-based interpretations. For richer, contextual
        semiotic analysis, add a free{' '}
        <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer" className="underline font-medium">
          Google Gemini API key
        </a>{' '}
        in Settings.
      </p>
      <button onClick={dismiss} className="p-1 hover:bg-amber-100 rounded flex-shrink-0" title="Dismiss">
        <X className="w-4 h-4 text-amber-600" />
      </button>
    </div>
  )
}

function BackendLoadingScreen({ elapsed }: { elapsed: number }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <Loader2 className="w-10 h-10 text-primary-600 animate-spin mb-4" />
      <h2 className="text-xl font-semibold text-gray-800 mb-2">Starting SemioVis</h2>
      <p className="text-sm text-gray-500 text-center max-w-sm">
        {elapsed < 30
          ? 'Loading the analysis engine...'
          : elapsed < 60
            ? 'Still loading. This may take up to a minute on first launch...'
            : 'Almost ready. The first launch takes longer while the engine initializes...'}
      </p>
    </div>
  )
}

function App() {
  const activeTab = useAnalysisStore((s) => s.activeTab)
  const imageId = useAnalysisStore((s) => s.imageId)
  const [showMethodology, setShowMethodology] = useState(false)
  const [backendReady, setBackendReady] = useState(!isTauri)
  const [elapsed, setElapsed] = useState(0)

  // In desktop mode, wait for backend to start
  useEffect(() => {
    if (!isTauri) return
    let cancelled = false
    const startTime = Date.now()

    // Update elapsed timer every second
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    // Poll until backend is ready (no hard timeout — keep trying)
    const poll = async () => {
      while (!cancelled) {
        if (await checkBackend()) {
          setBackendReady(true)
          break
        }
        await new Promise((r) => setTimeout(r, 2000))
      }
    }
    poll()

    return () => { cancelled = true; clearInterval(timer) }
  }, [])

  // Listen for help modal opening methodology
  useEffect(() => {
    const handler = () => setShowMethodology(true)
    window.addEventListener('open-methodology', handler)
    return () => window.removeEventListener('open-methodology', handler)
  }, [])

  if (!backendReady) {
    return <BackendLoadingScreen elapsed={elapsed} />
  }

  if (showMethodology) {
    return (
      <Layout>
        <ApiKeyBanner />
        <MethodologyGuide onBack={() => setShowMethodology(false)} />
      </Layout>
    )
  }

  return (
    <Layout>
      <ApiKeyBanner />
      <div className="flex h-full">
        {/* Sidebar: image preview */}
        <aside className="w-64 border-r border-gray-200 bg-white p-4 flex flex-col gap-4 overflow-y-auto">
          {imageId ? <ImagePreview /> : <ImageUploader />}
        </aside>

        {/* Main content */}
        <main className="flex-1 p-6 overflow-auto">
          {activeTab === 'upload' && !imageId && <HomePage />}
          {activeTab === 'upload' && imageId && (
            <div className="flex items-center justify-center h-full text-gray-400">
              Select an analysis tab to begin
            </div>
          )}
          {activeTab === 'representational' && <RepresentationalPanel />}
          {activeTab === 'interactive' && <InteractivePanel />}
          {activeTab === 'compositional' && <CompositionalPanel />}
          {activeTab === 'dashboard' && <DashboardPanel />}
          {activeTab === 'report' && <ReportPanel />}
        </main>
      </div>
    </Layout>
  )
}

export default App

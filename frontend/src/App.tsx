import { useState, useEffect } from 'react'
import { AlertTriangle, X } from 'lucide-react'
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

function App() {
  const activeTab = useAnalysisStore((s) => s.activeTab)
  const imageId = useAnalysisStore((s) => s.imageId)
  const [showMethodology, setShowMethodology] = useState(false)

  // Listen for help modal opening methodology
  useEffect(() => {
    const handler = () => setShowMethodology(true)
    window.addEventListener('open-methodology', handler)
    return () => window.removeEventListener('open-methodology', handler)
  }, [])

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

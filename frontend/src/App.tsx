import { useState, useEffect } from 'react'
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
        <MethodologyGuide onBack={() => setShowMethodology(false)} />
      </Layout>
    )
  }

  return (
    <Layout>
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

import { useAnalysisStore } from '../../store/analysisStore'
import type { TabName } from '../../types/analysis'

const tabs: { id: TabName; label: string }[] = [
  { id: 'upload', label: 'Upload' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'representational', label: 'Representational' },
  { id: 'interactive', label: 'Interactive' },
  { id: 'compositional', label: 'Compositional' },
  { id: 'report', label: 'Report' },
]

export function Sidebar() {
  const activeTab = useAnalysisStore((s) => s.activeTab)
  const setActiveTab = useAnalysisStore((s) => s.setActiveTab)
  const imageId = useAnalysisStore((s) => s.imageId)

  return (
    <nav className="flex border-b border-gray-200 bg-white px-4">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          disabled={tab.id !== 'upload' && !imageId}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === tab.id
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          } ${tab.id !== 'upload' && !imageId ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}

import { Play, Loader2, CheckCircle } from 'lucide-react'
import { useAnalysisStore } from '../../store/analysisStore'
import {
  useRepresentationalAnalysis,
  useInteractiveAnalysis,
  useCompositionalAnalysis,
} from '../../hooks/useImageAnalysis'

export function DashboardPanel() {
  const imageId = useAnalysisStore((s) => s.imageId)
  const rep = useAnalysisStore((s) => s.representational)
  const inter = useAnalysisStore((s) => s.interactive)
  const comp = useAnalysisStore((s) => s.compositional)
  const isLoading = useAnalysisStore((s) => s.isLoading)

  const { mutate: runRep } = useRepresentationalAnalysis()
  const { mutate: runInt } = useInteractiveAnalysis()
  const { mutate: runComp } = useCompositionalAnalysis()

  if (!imageId) {
    return <div className="text-gray-400 p-8">Upload an image first</div>
  }

  const anyLoading = isLoading['representational'] || isLoading['interactive'] || isLoading['compositional']

  const runAll = () => {
    if (!rep) runRep()
    if (!inter) runInt()
    if (!comp) runComp()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Full Analysis Dashboard</h2>
          <p className="text-sm text-gray-500">Run all three analyses at once</p>
        </div>
        <button
          onClick={runAll}
          disabled={anyLoading}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
        >
          {anyLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {anyLoading ? 'Running...' : 'Run All Analyses'}
        </button>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard
          title="Representational"
          done={!!rep}
          loading={!!isLoading['representational']}
          summary={rep ? `${rep.structure_type} / ${rep.narrative_subtype || rep.conceptual_subtype || 'N/A'}` : undefined}
        />
        <StatusCard
          title="Interactive"
          done={!!inter}
          loading={!!isLoading['interactive']}
          summary={inter ? `${inter.faces.length} faces | modality ${inter.modality_score.toFixed(2)}` : undefined}
        />
        <StatusCard
          title="Compositional"
          done={!!comp}
          loading={!!isLoading['compositional']}
          summary={comp ? `${comp.composition_type} / ${comp.dominant_structure}` : undefined}
        />
      </div>

      {/* Summary when all done */}
      {rep && inter && comp && (
        <div className="bg-green-50 rounded-lg border border-green-200 p-6 space-y-4">
          <h3 className="font-semibold text-green-800">All analyses complete</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Representational</h4>
              <p className="text-gray-600">{rep.interpretation.slice(0, 200)}...</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Interactive</h4>
              <p className="text-gray-600">{inter.interpretation.slice(0, 200)}...</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-1">Compositional</h4>
              <p className="text-gray-600">{comp.interpretation.slice(0, 200)}...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusCard({ title, done, loading, summary }: {
  title: string
  done: boolean
  loading: boolean
  summary?: string
}) {
  return (
    <div className={`rounded-lg border p-4 ${done ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'}`}>
      <div className="flex items-center gap-2 mb-1">
        {done ? (
          <CheckCircle className="w-4 h-4 text-green-600" />
        ) : loading ? (
          <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
        ) : (
          <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
        )}
        <span className="font-medium text-sm">{title}</span>
      </div>
      {summary && <p className="text-xs text-gray-600 ml-6">{summary}</p>}
      {!done && !loading && <p className="text-xs text-gray-400 ml-6">Not run yet</p>}
    </div>
  )
}

import { Play, Loader2 } from 'lucide-react'
import { useAnalysisStore } from '../../store/analysisStore'
import { useRepresentationalAnalysis } from '../../hooks/useImageAnalysis'
import { VectorOverlay } from './VectorOverlay'
import { ParticipantsTable } from './ParticipantsTable'

export function RepresentationalPanel() {
  const result = useAnalysisStore((s) => s.representational)
  const isLoading = useAnalysisStore((s) => s.isLoading['representational'])
  const imageId = useAnalysisStore((s) => s.imageId)
  const imageMeta = useAnalysisStore((s) => s.imageMeta)
  const { mutate: analyse } = useRepresentationalAnalysis()

  if (!imageId) {
    return <div className="text-gray-400 p-8">Upload an image first</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Representational Analysis</h2>
          <p className="text-sm text-gray-500">
            Narrative/conceptual structure, vectors, and participants (Ch. 2-3)
          </p>
        </div>
        <button
          onClick={() => analyse()}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {isLoading ? 'Analysing...' : 'Run Analysis'}
        </button>
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Image with vector overlay */}
          <div className="space-y-3">
            <h3 className="font-medium text-sm text-gray-700">Vector Overlay</h3>
            {imageMeta && (
              <VectorOverlay
                imageBase64={imageMeta.thumbnail_base64}
                vectors={result.vectors}
                participants={result.participants}
                imgWidth={imageMeta.width}
                imgHeight={imageMeta.height}
              />
            )}
          </div>

          {/* Results */}
          <div className="space-y-4">
            {/* Structure classification */}
            <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
              <h3 className="font-medium text-sm text-gray-700">Structure Classification</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-500">Type</div>
                <div className="font-medium capitalize">{result.structure_type}</div>
                <div className="text-gray-500">Subtype</div>
                <div className="font-medium capitalize">
                  {(result.narrative_subtype || result.conceptual_subtype || 'N/A').replace(/_/g, ' ')}
                </div>
                <div className="text-gray-500">Vectors</div>
                <div className="font-medium">{result.vector_count}</div>
                <div className="text-gray-500">Dominant Direction</div>
                <div className="font-medium capitalize">{result.dominant_direction}</div>
              </div>
            </div>

            {/* Participants */}
            {result.participants.length > 0 && (
              <ParticipantsTable participants={result.participants} />
            )}

            {/* Interpretation */}
            <div className="bg-blue-50 rounded-lg border border-blue-100 p-4">
              <h3 className="font-medium text-sm text-blue-800 mb-2">Semiotic Interpretation</h3>
              <p className="text-sm text-blue-900 leading-relaxed">{result.interpretation}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

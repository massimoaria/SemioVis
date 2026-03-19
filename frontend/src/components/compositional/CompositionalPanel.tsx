import { Play, Loader2 } from 'lucide-react'
import { useAnalysisStore } from '../../store/analysisStore'
import { useCompositionalAnalysis } from '../../hooks/useImageAnalysis'
import { SaliencyHeatmap } from './SaliencyHeatmap'
import { SemioticGrid } from './SemioticGrid'
import { ColorPalette } from './ColorPalette'

export function CompositionalPanel() {
  const result = useAnalysisStore((s) => s.compositional)
  const isLoading = useAnalysisStore((s) => s.isLoading['compositional'])
  const imageId = useAnalysisStore((s) => s.imageId)
  const { mutate: analyse } = useCompositionalAnalysis()

  if (!imageId) {
    return <div className="text-gray-400 p-8">Upload an image first</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Compositional Analysis</h2>
          <p className="text-sm text-gray-500">
            Information value, salience, framing, and reading path (Ch. 6)
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
        <div className="space-y-6">
          {/* Top row: saliency + grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h3 className="font-medium text-sm text-gray-700">Saliency Heatmap</h3>
              <SaliencyHeatmap saliencyMap={result.saliency_map} />
            </div>

            <div className="space-y-3">
              <h3 className="font-medium text-sm text-gray-700">Semiotic Grid</h3>
              <SemioticGrid zones={result.zones} compositionType={result.composition_type} />
            </div>
          </div>

          {/* Classification + framing */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
              <h3 className="font-medium text-sm text-gray-700">Composition</h3>
              <div className="grid grid-cols-2 gap-1 text-sm">
                <div className="text-gray-500">Type</div>
                <div className="font-medium capitalize">{result.composition_type}</div>
                <div className="text-gray-500">Subtype</div>
                <div className="font-medium capitalize">
                  {result.centred_subtype?.replace(/_/g, ' ') ||
                   result.polarization_axes?.join(', ').replace(/_/g, ' ') || 'N/A'}
                </div>
                <div className="text-gray-500">Dominant</div>
                <div className="font-medium capitalize">{result.dominant_structure.replace(/_/g, ' ')}</div>
                <div className="text-gray-500">Triptych</div>
                <div className="font-medium">{result.has_triptych ? 'Yes' : 'No'}</div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
              <h3 className="font-medium text-sm text-gray-700">Framing</h3>
              <div className="grid grid-cols-2 gap-1 text-sm">
                <div className="text-gray-500">Disconnection</div>
                <div className="font-medium">{result.framing.disconnection_score.toFixed(2)}</div>
                <div className="text-gray-500">Connection</div>
                <div className="font-medium">{result.framing.connection_score.toFixed(2)}</div>
                <div className="text-gray-500">Frame lines</div>
                <div className="font-medium">{result.framing.frame_lines.length}</div>
                <div className="text-gray-500">Empty regions</div>
                <div className="font-medium">{result.framing.empty_space_regions}</div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
              <h3 className="font-medium text-sm text-gray-700">Reading Path</h3>
              <div className="grid grid-cols-2 gap-1 text-sm">
                <div className="text-gray-500">Shape</div>
                <div className="font-medium capitalize">{result.reading_path.path_shape.replace(/_/g, ' ')}</div>
                <div className="text-gray-500">Waypoints</div>
                <div className="font-medium">{result.reading_path.waypoints.length}</div>
                <div className="text-gray-500">Linear</div>
                <div className="font-medium">{result.reading_path.is_linear ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>

          {/* Colour palette */}
          <ColorPalette palette={result.color_palette} />

          {/* Interpretation */}
          <div className="bg-blue-50 rounded-lg border border-blue-100 p-4">
            <h3 className="font-medium text-sm text-blue-800 mb-2">Semiotic Interpretation</h3>
            <p className="text-sm text-blue-900 leading-relaxed">{result.interpretation}</p>
          </div>
        </div>
      )}
    </div>
  )
}

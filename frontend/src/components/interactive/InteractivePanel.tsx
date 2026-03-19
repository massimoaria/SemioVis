import { Play, Loader2 } from 'lucide-react'
import { useAnalysisStore } from '../../store/analysisStore'
import { useInteractiveAnalysis } from '../../hooks/useImageAnalysis'
import { GazeOverlay } from './GazeOverlay'
import { ModalityRadar } from './ModalityRadar'

export function InteractivePanel() {
  const result = useAnalysisStore((s) => s.interactive)
  const isLoading = useAnalysisStore((s) => s.isLoading['interactive'])
  const imageId = useAnalysisStore((s) => s.imageId)
  const imageMeta = useAnalysisStore((s) => s.imageMeta)
  const { mutate: analyse } = useInteractiveAnalysis()

  if (!imageId) {
    return <div className="text-gray-400 p-8">Upload an image first</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Interactive Analysis</h2>
          <p className="text-sm text-gray-500">
            Gaze, social distance, modality, and perspective (Ch. 4-5)
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
          {/* Left: image + gaze overlay */}
          <div className="space-y-4">
            {imageMeta && (
              <GazeOverlay
                imageBase64={imageMeta.thumbnail_base64}
                faces={result.faces}
                imgWidth={imageMeta.width}
                imgHeight={imageMeta.height}
                vanishingPoint={result.vanishing_point}
              />
            )}

            {/* Faces table */}
            {result.faces.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="font-medium text-sm text-gray-700 mb-2">
                  Faces ({result.faces.length})
                </h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="pb-1">ID</th>
                      <th className="pb-1">Gaze</th>
                      <th className="pb-1">Distance</th>
                      <th className="pb-1">Shot</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.faces.map((f) => (
                      <tr key={f.face_id} className="border-b border-gray-50">
                        <td className="py-1">#{f.face_id}</td>
                        <td className="py-1">
                          <span className={f.gaze_type === 'demand' ? 'text-red-600 font-medium' : 'text-gray-600'}>
                            {f.gaze_type}
                          </span>
                        </td>
                        <td className="py-1 capitalize">{f.social_distance.replace(/_/g, ' ')}</td>
                        <td className="py-1 capitalize">{f.shot_type.replace(/_/g, ' ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Right: modality + perspective */}
          <div className="space-y-4">
            {/* Perspective & power */}
            <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
              <h3 className="font-medium text-sm text-gray-700">Perspective & Power</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-500">Vertical Angle</div>
                <div className="font-medium capitalize">{result.vertical_angle.replace(/_/g, ' ')}</div>
                <div className="text-gray-500">Horizontal Angle</div>
                <div className="font-medium capitalize">{result.horizontal_angle}</div>
                <div className="text-gray-500">Power Relation</div>
                <div className="font-medium capitalize">{result.power_relation.replace(/_/g, ' ')}</div>
                <div className="text-gray-500">Involvement</div>
                <div className="font-medium capitalize">{result.involvement}</div>
                <div className="text-gray-500">Vanishing Point</div>
                <div className="font-medium">
                  {result.vanishing_point
                    ? `(${result.vanishing_point[0].toFixed(2)}, ${result.vanishing_point[1].toFixed(2)})`
                    : 'Not detected'}
                </div>
              </div>
            </div>

            {/* Modality radar */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-sm text-gray-700">Modality Profile (8 scales)</h3>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                  {result.coding_orientation} | score: {result.modality_score.toFixed(3)}
                </span>
              </div>
              <ModalityRadar profile={result.modality_profile} />
            </div>

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

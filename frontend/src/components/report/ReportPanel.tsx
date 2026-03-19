import { useState } from 'react'
import { FileText, Loader2, Download } from 'lucide-react'
import { useAnalysisStore } from '../../store/analysisStore'
import { apiClient } from '../../api/client'

type ReportFormat = 'pdf' | 'docx' | 'html'

const MIME_TYPES: Record<ReportFormat, string> = {
  pdf: 'application/pdf',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  html: 'text/html',
}

export function ReportPanel() {
  const imageId = useAnalysisStore((s) => s.imageId)
  const rep = useAnalysisStore((s) => s.representational)
  const inter = useAnalysisStore((s) => s.interactive)
  const comp = useAnalysisStore((s) => s.compositional)
  const imageMeta = useAnalysisStore((s) => s.imageMeta)

  const [format, setFormat] = useState<ReportFormat>('pdf')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const hasResults = !!(rep || inter || comp)

  const generateReport = async () => {
    if (!imageId) return
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const response = await apiClient.post(
        '/report',
        {
          image_id: imageId,
          analysis_results: {
            representational: rep,
            interactive: inter,
            compositional: comp,
            thumbnail_base64: imageMeta?.thumbnail_base64,
            image_meta: imageMeta
              ? { width: imageMeta.width, height: imageMeta.height, format: imageMeta.format }
              : undefined,
          },
          format,
        },
        { responseType: 'blob' },
      )

      // Create a download link from the blob
      const blob = new Blob([response.data], { type: MIME_TYPES[format] })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `semiovis_report.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      setSuccess(true)
    } catch (err: unknown) {
      console.error('[SemioVis] Report generation failed:', err)
      setError(err instanceof Error ? err.message : 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  if (!imageId) {
    return <div className="text-gray-400 p-8">Upload an image first</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Report Generation</h2>
        <p className="text-sm text-gray-500">Export analysis as PDF, DOCX, or HTML</p>
      </div>

      {!hasResults && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
          Run at least one analysis before generating a report.
        </div>
      )}

      {hasResults && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
            <div className="flex gap-2">
              {(['pdf', 'docx', 'html'] as ReportFormat[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`px-4 py-2 text-sm rounded-md border ${
                    format === f
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Included analyses
            </label>
            <div className="text-sm text-gray-600 space-y-0.5">
              {rep && <div>- Representational</div>}
              {inter && <div>- Interactive</div>}
              {comp && <div>- Compositional</div>}
            </div>
          </div>

          <button
            onClick={generateReport}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
            {loading ? 'Generating...' : 'Generate & Download'}
          </button>

          {success && (
            <div className="flex items-center gap-2 text-sm text-green-700">
              <Download className="w-4 h-4" />
              Report downloaded!
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      )}
    </div>
  )
}

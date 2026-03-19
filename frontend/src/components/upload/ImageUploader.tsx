import { useCallback, useState } from 'react'
import { Upload, Loader2, AlertCircle } from 'lucide-react'
import { apiClient } from '../../api/client'
import { useAnalysisStore } from '../../store/analysisStore'

export function ImageUploader() {
  const setImage = useAnalysisStore((s) => s.setImage)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [description, setDescription] = useState('')

  const handleUpload = useCallback(
    async (file: File) => {
      setLoading(true)
      setError(null)
      try {
        const formData = new FormData()
        formData.append('file', file)
        const { data } = await apiClient.post('/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        // Store description in the image meta for use in analysis
        data.description = description
        setImage(data.image_id, data)
      } catch (err: unknown) {
        console.error('[SemioVis] Upload failed:', err)
        if (err && typeof err === 'object' && 'message' in err) {
          const msg = (err as Error).message
          if (msg.includes('Network Error') || msg.includes('ECONNREFUSED')) {
            setError('Cannot connect to backend. Is the server running on port 8000?')
          } else {
            setError(`Upload failed: ${msg}`)
          }
        } else {
          setError('Upload failed: unknown error')
        }
      } finally {
        setLoading(false)
      }
    },
    [setImage, description],
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      const file = e.dataTransfer.files[0]
      if (file) handleUpload(file)
    },
    [handleUpload],
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) handleUpload(file)
    },
    [handleUpload],
  )

  return (
    <div className="space-y-3">
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="flex flex-col items-center justify-center gap-3 p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-400 transition-colors cursor-pointer"
      >
        {loading ? (
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        ) : (
          <Upload className="w-8 h-8 text-gray-400" />
        )}
        <p className="text-sm text-gray-500 text-center">
          {loading ? 'Uploading...' : 'Drop an image here or click to upload'}
        </p>
        {!loading && (
          <label className="px-4 py-2 bg-primary-600 text-white text-sm rounded-md hover:bg-primary-700 cursor-pointer">
            Choose File
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileSelect}
            />
          </label>
        )}
      </div>

      {/* Image description for context */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Image Description (optional)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="E.g.: Coca-Cola print advertisement from 1960s Italy, targeting families..."
          rows={3}
          className="w-full px-3 py-2 text-xs border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 resize-none"
        />
        <p className="text-[10px] text-gray-400 mt-1">
          Add context about the image source, brand, era, or purpose to improve AI interpretation.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { RefreshCw, Edit3, Check } from 'lucide-react'
import { useAnalysisStore } from '../../store/analysisStore'

export function ImagePreview() {
  const imageMeta = useAnalysisStore((s) => s.imageMeta)
  const setImage = useAnalysisStore((s) => s.setImage)
  const resetAll = useAnalysisStore((s) => s.resetAll)
  const [editing, setEditing] = useState(false)
  const [desc, setDesc] = useState(imageMeta?.description || '')

  if (!imageMeta) return null

  const saveDescription = () => {
    setImage(imageMeta.image_id, { ...imageMeta, description: desc })
    setEditing(false)
  }

  return (
    <div className="flex flex-col gap-3">
      <img
        src={`data:image/jpeg;base64,${imageMeta.thumbnail_base64}`}
        alt={imageMeta.filename}
        className="w-full rounded-md border border-gray-200"
      />
      <div className="text-xs text-gray-500 space-y-1">
        <p className="font-medium text-gray-700 truncate">{imageMeta.filename}</p>
        <p>{imageMeta.width} x {imageMeta.height} px</p>
        <p>{imageMeta.format.toUpperCase()}</p>
      </div>

      {/* Description */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-medium text-gray-600 uppercase tracking-wide">
            Description
          </span>
          {!editing && (
            <button onClick={() => setEditing(true)} className="p-0.5 hover:bg-gray-100 rounded">
              <Edit3 className="w-3 h-3 text-gray-400" />
            </button>
          )}
        </div>
        {editing ? (
          <div className="space-y-1">
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={3}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded-md resize-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Brand, source, era, context..."
              autoFocus
            />
            <button
              onClick={saveDescription}
              className="flex items-center gap-1 text-xs text-primary-600 hover:underline"
            >
              <Check className="w-3 h-3" /> Save
            </button>
          </div>
        ) : (
          <p className="text-[11px] text-gray-500 italic">
            {imageMeta.description || 'No description added'}
          </p>
        )}
      </div>

      <button
        onClick={resetAll}
        className="flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
      >
        <RefreshCw className="w-4 h-4" />
        New Image
      </button>
    </div>
  )
}

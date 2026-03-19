import { X, BookOpen, Globe } from 'lucide-react'

interface Props {
  open: boolean
  onClose: () => void
}

export function HelpModal({ open, onClose }: Props) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Help</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <button
            onClick={() => {
              onClose()
              // Open methodology docs in a new panel
              const el = document.getElementById('methodology-docs')
              if (el) el.scrollIntoView()
              else window.dispatchEvent(new CustomEvent('open-methodology'))
            }}
            className="w-full flex items-start gap-4 p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors text-left"
          >
            <BookOpen className="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-gray-900">Methodology Guide</h3>
              <p className="text-sm text-gray-500 mt-1">
                A comprehensive guide explaining the semiotic analysis methodologies
                implemented in SemioVis, including representational structures,
                interactive meanings, compositional grammar, and all analysis metrics.
              </p>
            </div>
          </button>

          <a
            href="https://www.massimoaria.com"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-start gap-4 p-4 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors text-left block"
          >
            <Globe className="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-gray-900">Author Website</h3>
              <p className="text-sm text-gray-500 mt-1">
                Visit Massimo Aria's website for more information, publications,
                and other research tools.
              </p>
              <p className="text-xs text-primary-600 mt-1">www.massimoaria.com</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  )
}

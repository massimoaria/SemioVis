import { X, BookOpen, Globe, Key } from 'lucide-react'

interface Props {
  open: boolean
  onClose: () => void
  onOpenSettings?: () => void
}

export function HelpModal({ open, onClose, onOpenSettings }: Props) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Help</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* API Key Setup */}
          <div className="p-4 rounded-lg border border-amber-200 bg-amber-50">
            <div className="flex items-start gap-3">
              <Key className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-gray-900">API Key Setup</h3>
                <p className="text-sm text-gray-600 mt-1">
                  SemioVis works fully offline, but adding an LLM API key significantly
                  improves the quality of semiotic interpretations in your analysis reports.
                  Without a key, the app generates structured rule-based text. With a key,
                  you get rich, contextual academic prose that interprets the visual features
                  in depth.
                </p>
                <p className="text-sm text-gray-600 mt-2 font-medium">
                  How to get a free API key:
                </p>
                <ol className="text-sm text-gray-600 mt-1 list-decimal list-inside space-y-1">
                  <li>
                    Visit{' '}
                    <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                      Google AI Studio
                    </a>{' '}
                    and sign in with your Google account
                  </li>
                  <li>Click "Create API key" and copy the generated key</li>
                  <li>
                    Open{' '}
                    <button
                      onClick={() => { onClose(); onOpenSettings?.() }}
                      className="text-primary-600 hover:underline font-medium"
                    >
                      Settings
                    </button>{' '}
                    and paste it into the Google Gemini field
                  </li>
                </ol>
                <p className="text-xs text-gray-500 mt-2">
                  The Gemini free tier includes 15 requests/minute and 1 million tokens/day,
                  more than enough for regular use. Alternatively, you can use{' '}
                  <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                    OpenAI GPT-4o
                  </a>{' '}
                  (paid, best quality) or{' '}
                  <a href="https://console.mistral.ai/api-keys" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                    Mistral Pixtral
                  </a>{' '}
                  (free tier available).
                </p>
              </div>
            </div>
          </div>

          {/* Methodology Guide */}
          <button
            onClick={() => {
              onClose()
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

          {/* Author Website */}
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

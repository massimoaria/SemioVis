import { useState } from 'react'
import { X } from 'lucide-react'
import { useAnalysisStore } from '../../store/analysisStore'
import { apiClient } from '../../api/client'
import type { AppSettings } from '../../types/analysis'

interface Props {
  open: boolean
  onClose: () => void
}

export function SettingsModal({ open, onClose }: Props) {
  const settings = useAnalysisStore((s) => s.settings)
  const updateSettings = useAnalysisStore((s) => s.updateSettings)
  const [local, setLocal] = useState<AppSettings>(settings)

  if (!open) return null

  const save = async () => {
    updateSettings(local)
    localStorage.setItem('semiovis_settings', JSON.stringify(local))
    // Send API keys to backend
    try {
      await apiClient.post('/settings/keys', {
        gemini: local.apiKeys.gemini,
        openai: local.apiKeys.openai,
        mistral: local.apiKeys.mistral,
      })
    } catch (e) {
      console.warn('Failed to send API keys to backend:', e)
    }
    onClose()
  }

  const updateKey = (key: keyof AppSettings['apiKeys'], value: string) => {
    setLocal({ ...local, apiKeys: { ...local.apiKeys, [key]: value } })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-6">
          {/* API Keys */}
          <section>
            <h3 className="font-medium text-sm text-gray-800 mb-3">LLM Interpretation API Keys</h3>
            <p className="text-xs text-gray-500 mb-3">
              Optional. Without keys, the app uses rule-based interpretation. Gemini offers a free tier.
            </p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Google Gemini (free tier: 15 RPM)
                </label>
                <input
                  type="password"
                  value={local.apiKeys.gemini}
                  onChange={(e) => updateKey('gemini', e.target.value)}
                  placeholder="AIza..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  OpenAI GPT-4o (paid)
                </label>
                <input
                  type="password"
                  value={local.apiKeys.openai}
                  onChange={(e) => updateKey('openai', e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Mistral / Pixtral (free tier available)
                </label>
                <input
                  type="password"
                  value={local.apiKeys.mistral}
                  onChange={(e) => updateKey('mistral', e.target.value)}
                  placeholder="..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </section>

          {/* Analysis Settings */}
          <section>
            <h3 className="font-medium text-sm text-gray-800 mb-3">Analysis Settings</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Saliency Method</label>
                <select
                  value={local.saliencyMethod}
                  onChange={(e) => setLocal({ ...local, saliencyMethod: e.target.value as 'spectral' | 'itti' })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
                >
                  <option value="spectral">Spectral Residual</option>
                  <option value="itti">Itti-Koch</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Grid Size</label>
                <select
                  value={local.gridSize}
                  onChange={(e) => setLocal({ ...local, gridSize: e.target.value as '2x2' | '3x3' })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
                >
                  <option value="3x3">3 x 3</option>
                  <option value="2x2">2 x 2</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Coding Orientation</label>
                <select
                  value={local.codingOrientation}
                  onChange={(e) => setLocal({ ...local, codingOrientation: e.target.value as AppSettings['codingOrientation'] })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
                >
                  <option value="naturalistic">Naturalistic</option>
                  <option value="sensory">Sensory</option>
                  <option value="technological">Technological</option>
                  <option value="abstract">Abstract</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Reading Direction</label>
                <select
                  value={local.readingDirection}
                  onChange={(e) => setLocal({ ...local, readingDirection: e.target.value as 'ltr' | 'rtl' })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
                >
                  <option value="ltr">Left to Right (Western)</option>
                  <option value="rtl">Right to Left (Arabic/Hebrew)</option>
                </select>
              </div>
            </div>
          </section>

          {/* Working Directory */}
          <section>
            <h3 className="font-medium text-sm text-gray-800 mb-3">Working Directory</h3>
            <p className="text-xs text-gray-500 mb-2">
              Reports and exported files will be saved here.
            </p>
            <input
              type="text"
              value={(local as any).workingDirectory || ''}
              onChange={(e) => setLocal({ ...local, workingDirectory: e.target.value } as AppSettings)}
              placeholder="~/Documents/SemioVis"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
          </section>
        </div>

        <div className="flex justify-end gap-2 p-4 border-t">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md">
            Cancel
          </button>
          <button onClick={save} className="px-4 py-2 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700">
            Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}

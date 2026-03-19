import { useAnalysisStore } from '../store/analysisStore'
import type { AppSettings } from '../types/analysis'

export function useSettings() {
  const settings = useAnalysisStore((s) => s.settings)
  const updateSettings = useAnalysisStore((s) => s.updateSettings)

  const save = (updates: Partial<AppSettings>) => {
    updateSettings(updates)
    localStorage.setItem(
      'semiovis_settings',
      JSON.stringify({ ...settings, ...updates }),
    )
  }

  return { settings, save }
}

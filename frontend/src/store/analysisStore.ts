import { create } from 'zustand'
import type {
  ImageMeta,
  RepresentationalResult,
  InteractiveResult,
  CompositionalResult,
  AppSettings,
  TabName,
} from '../types/analysis'

interface AnalysisStore {
  imageId: string | null
  imageMeta: ImageMeta | null
  representational: RepresentationalResult | null
  interactive: InteractiveResult | null
  compositional: CompositionalResult | null
  isLoading: Record<string, boolean>
  activeTab: TabName
  settings: AppSettings
  setImage: (id: string, meta: ImageMeta) => void
  setResult: (type: string, result: unknown) => void
  setLoading: (type: string, val: boolean) => void
  setActiveTab: (tab: TabName) => void
  updateSettings: (s: Partial<AppSettings>) => void
  resetAll: () => void
}

const defaultSettings: AppSettings = {
  detectionBackend: 'local',
  interpretationLLM: 'auto',
  saliencyMethod: 'spectral',
  gridSize: '3x3',
  language: 'en',
  vectorMinLength: 50,
  vectorThreshold: 100,
  overlayOpacity: 0.5,
  codingOrientation: 'naturalistic',
  readingDirection: 'ltr',
  workingDirectory: '',
  apiKeys: {
    gemini: '',
    openai: '',
    mistral: '',
    google_vision: '',
    aws_id: '',
    aws_key: '',
  },
}

function loadPersistedSettings(): AppSettings {
  try {
    const raw = localStorage.getItem('semiovis_settings')
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        ...defaultSettings,
        ...parsed,
        apiKeys: { ...defaultSettings.apiKeys, ...parsed.apiKeys },
      }
    }
  } catch {
    // ignore corrupted data
  }
  return defaultSettings
}

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  imageId: null,
  imageMeta: null,
  representational: null,
  interactive: null,
  compositional: null,
  isLoading: {},
  activeTab: 'upload',
  settings: loadPersistedSettings(),

  setImage: (id, meta) =>
    set({
      imageId: id,
      imageMeta: meta,
      representational: null,
      interactive: null,
      compositional: null,
    }),

  setResult: (type, result) =>
    set((state) => ({ ...state, [type]: result })),

  setLoading: (type, val) =>
    set((state) => ({
      isLoading: { ...state.isLoading, [type]: val },
    })),

  setActiveTab: (tab) => set({ activeTab: tab }),

  updateSettings: (s) =>
    set((state) => {
      const updated = {
        ...state.settings,
        ...s,
        apiKeys: s.apiKeys
          ? { ...state.settings.apiKeys, ...s.apiKeys }
          : state.settings.apiKeys,
      }
      localStorage.setItem('semiovis_settings', JSON.stringify(updated))
      return { settings: updated }
    }),

  resetAll: () =>
    set({
      imageId: null,
      imageMeta: null,
      representational: null,
      interactive: null,
      compositional: null,
      isLoading: {},
      activeTab: 'upload',
    }),
}))

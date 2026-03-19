import { useMutation } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { useAnalysisStore } from '../store/analysisStore'

export function useRepresentationalAnalysis() {
  const imageId = useAnalysisStore((s) => s.imageId)
  const imageMeta = useAnalysisStore((s) => s.imageMeta)
  const setResult = useAnalysisStore((s) => s.setResult)
  const setLoading = useAnalysisStore((s) => s.setLoading)
  const settings = useAnalysisStore((s) => s.settings)

  return useMutation({
    mutationFn: async () => {
      setLoading('representational', true)
      const { data } = await apiClient.post('/analyse/representational', {
        image_id: imageId,
        api_backend: settings.detectionBackend,
        image_description: imageMeta?.description || '',
      })
      return data
    },
    onSuccess: (data) => {
      setResult('representational', data)
      setLoading('representational', false)
    },
    onError: () => setLoading('representational', false),
  })
}

export function useInteractiveAnalysis() {
  const imageId = useAnalysisStore((s) => s.imageId)
  const imageMeta = useAnalysisStore((s) => s.imageMeta)
  const setResult = useAnalysisStore((s) => s.setResult)
  const setLoading = useAnalysisStore((s) => s.setLoading)
  const settings = useAnalysisStore((s) => s.settings)

  return useMutation({
    mutationFn: async () => {
      setLoading('interactive', true)
      const { data } = await apiClient.post('/analyse/interactive', {
        image_id: imageId,
        api_backend: settings.detectionBackend,
        coding_orientation: settings.codingOrientation,
        image_description: imageMeta?.description || '',
      })
      return data
    },
    onSuccess: (data) => {
      setResult('interactive', data)
      setLoading('interactive', false)
    },
    onError: () => setLoading('interactive', false),
  })
}

export function useCompositionalAnalysis() {
  const imageId = useAnalysisStore((s) => s.imageId)
  const imageMeta = useAnalysisStore((s) => s.imageMeta)
  const setResult = useAnalysisStore((s) => s.setResult)
  const setLoading = useAnalysisStore((s) => s.setLoading)
  const settings = useAnalysisStore((s) => s.settings)

  return useMutation({
    mutationFn: async () => {
      setLoading('compositional', true)
      const { data } = await apiClient.post('/analyse/compositional', {
        image_id: imageId,
        saliency_method: settings.saliencyMethod,
        grid_size: settings.gridSize,
        reading_direction: settings.readingDirection,
        image_description: imageMeta?.description || '',
      })
      return data
    },
    onSuccess: (data) => {
      setResult('compositional', data)
      setLoading('compositional', false)
    },
    onError: () => setLoading('compositional', false),
  })
}

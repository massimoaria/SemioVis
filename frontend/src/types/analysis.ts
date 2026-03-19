// TypeScript types matching backend Pydantic models

export type TabName =
  | 'upload'
  | 'representational'
  | 'interactive'
  | 'compositional'
  | 'dashboard'
  | 'report'

export interface ImageMeta {
  image_id: string
  filename: string
  width: number
  height: number
  format: string
  file_path: string
  thumbnail_base64: string
  description?: string
}

// --- Representational ---

export interface Vector {
  x1: number; y1: number; x2: number; y2: number
  angle: number; strength: number
  direction: 'horizontal' | 'vertical' | 'diagonal'
}

export interface Participant {
  label: string
  confidence: number
  bbox: [number, number, number, number]
  is_human: boolean
  is_animal: boolean
}

export interface RepresentationalResult {
  structure_type: 'narrative' | 'conceptual'
  narrative_subtype?: string | null
  conceptual_subtype?: string | null
  vectors: Vector[]
  participants: Participant[]
  vector_count: number
  dominant_direction: string
  interpretation: string
}

// --- Interactive ---

export interface FaceAnalysis {
  face_id: number
  face_bbox: [number, number, number, number]
  person_bbox?: [number, number, number, number] | null
  gaze_type: 'demand' | 'offer'
  pan_angle: number; tilt_angle: number; roll_angle: number
  social_distance: 'intimate' | 'personal' | 'social' | 'public' | 'very_public'
  shot_type: string
  emotions: Record<string, number>
}

export interface ModalityProfile {
  colour_saturation: number
  colour_differentiation: number
  colour_modulation: number
  contextualization: number
  representation: number
  depth: number
  illumination: number
  brightness: number
}

export interface InteractiveResult {
  faces: FaceAnalysis[]
  vertical_angle: 'high' | 'eye_level' | 'low'
  horizontal_angle: 'frontal' | 'oblique'
  power_relation: 'viewer_power' | 'equality' | 'subject_power'
  involvement: 'high' | 'low'
  modality_profile: ModalityProfile
  coding_orientation: string
  modality_score: number
  vanishing_point?: [number, number] | null
  interpretation: string
}

// --- Compositional ---

export interface SpatialZone {
  zone_id: string
  position_label: string
  semiotic_label: string
  mean_saliency: number
  visual_weight: number
  color_temperature: 'warm' | 'neutral' | 'cool'
  edge_density: number
  object_count: number
  tonal_contrast: number
  colour_contrast: number
  has_human_figure: boolean
  foreground_ratio: number
  sharpness: number
  information_value_score: number
}

export interface ColorSwatch {
  hex: string
  rgb: [number, number, number]
  proportion: number
  zone_association: string
}

export interface FramingAnalysis {
  disconnection_score: number
  connection_score: number
  frame_lines: Record<string, unknown>[]
  empty_space_regions: number
  colour_discontinuities: number
  colour_continuities: number
  visual_vectors: number
  shape_rhymes: number
}

export interface ReadingPath {
  waypoints: Record<string, unknown>[]
  path_shape: string
  is_linear: boolean
}

export interface CompositionalResult {
  composition_type: 'centred' | 'polarized'
  centred_subtype?: string | null
  polarization_axes?: string[] | null
  has_triptych: boolean
  triptych_orientation?: string | null
  zones: SpatialZone[]
  saliency_map: number[][]
  color_palette: ColorSwatch[]
  framing: FramingAnalysis
  reading_path: ReadingPath
  dominant_structure: string
  interpretation: string
}

// --- Settings ---

export interface AppSettings {
  detectionBackend: 'local' | 'google' | 'aws'
  interpretationLLM: 'auto' | 'openai' | 'gemini' | 'mistral' | 'local'
  saliencyMethod: 'spectral' | 'itti'
  gridSize: '2x2' | '3x3'
  language: 'en'
  vectorMinLength: number
  vectorThreshold: number
  overlayOpacity: number
  codingOrientation: 'naturalistic' | 'sensory' | 'technological' | 'abstract'
  readingDirection: 'ltr' | 'rtl'
  workingDirectory: string
  apiKeys: {
    gemini: string
    openai: string
    mistral: string
    google_vision: string
    aws_id: string
    aws_key: string
  }
}

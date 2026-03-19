import Plot from 'react-plotly.js'
import type { ModalityProfile } from '../../types/analysis'

interface Props {
  profile: ModalityProfile
}

const LABELS = [
  'Colour Saturation',
  'Colour Differentiation',
  'Colour Modulation',
  'Contextualization',
  'Representation',
  'Depth',
  'Illumination',
  'Brightness',
]

export function ModalityRadar({ profile }: Props) {
  const values = [
    profile.colour_saturation,
    profile.colour_differentiation,
    profile.colour_modulation,
    profile.contextualization,
    profile.representation,
    profile.depth,
    profile.illumination,
    profile.brightness,
  ]

  // Close the polygon
  const closedValues = [...values, values[0]]
  const closedLabels = [...LABELS, LABELS[0]]

  return (
    <Plot
      data={[
        {
          type: 'scatterpolar',
          r: closedValues,
          theta: closedLabels,
          fill: 'toself',
          fillcolor: 'rgba(59, 130, 246, 0.15)',
          line: { color: '#3b82f6', width: 2 },
          marker: { size: 5, color: '#3b82f6' },
          name: 'Image profile',
        },
      ]}
      layout={{
        polar: {
          radialaxis: {
            visible: true,
            range: [0, 1],
            tickvals: [0.25, 0.5, 0.75, 1.0],
            ticktext: ['0.25', '0.50', '0.75', '1.00'],
          },
        },
        showlegend: false,
        margin: { t: 20, b: 20, l: 60, r: 60 },
        height: 320,
        font: { size: 10 },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
    />
  )
}

import Plot from 'react-plotly.js'

interface Props {
  saliencyMap: number[][]
}

export function SaliencyHeatmap({ saliencyMap }: Props) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <Plot
        data={[
          {
            z: saliencyMap,
            type: 'heatmap',
            colorscale: [
              [0, '#1e3a5f'],
              [0.25, '#2563eb'],
              [0.5, '#fbbf24'],
              [0.75, '#f97316'],
              [1, '#ef4444'],
            ],
            showscale: true,
            colorbar: {
              title: { text: 'Salience', side: 'right' } as any,
              thickness: 12,
              len: 0.8,
            },
          },
        ]}
        layout={{
          margin: { t: 10, b: 10, l: 10, r: 50 },
          height: 300,
          yaxis: { autorange: 'reversed', showticklabels: false },
          xaxis: { showticklabels: false },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
    </div>
  )
}

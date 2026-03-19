import type { SpatialZone } from '../../types/analysis'

interface Props {
  zones: SpatialZone[]
  compositionType: 'centred' | 'polarized'
}

function getZoneColor(zone: SpatialZone): string {
  const w = zone.visual_weight
  if (w > 0.15) return 'bg-red-100 border-red-300'
  if (w > 0.08) return 'bg-orange-100 border-orange-300'
  if (w > 0.04) return 'bg-yellow-100 border-yellow-300'
  return 'bg-gray-50 border-gray-200'
}

export function SemioticGrid({ zones, compositionType }: Props) {
  // Determine grid dimensions
  const maxRow = Math.max(...zones.map((z) => parseInt(z.zone_id.split('_')[0])))
  const maxCol = Math.max(...zones.map((z) => parseInt(z.zone_id.split('_')[1])))
  const nRows = maxRow + 1
  const nCols = maxCol + 1

  const getZone = (r: number, c: number) =>
    zones.find((z) => z.zone_id === `${r}_${c}`)

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div
        className="grid gap-px bg-gray-300"
        style={{ gridTemplateColumns: `repeat(${nCols}, 1fr)` }}
        data-testid="semiotic-grid"
      >
        {Array.from({ length: nRows }, (_, r) =>
          Array.from({ length: nCols }, (_, c) => {
            const zone = getZone(r, c)
            if (!zone) return <div key={`${r}_${c}`} />

            return (
              <div
                key={zone.zone_id}
                data-testid="grid-zone"
                className={`p-3 min-h-[80px] flex flex-col justify-between ${getZoneColor(zone)}`}
                title={`${zone.position_label}\nSaliency: ${zone.mean_saliency.toFixed(4)}\nWeight: ${zone.visual_weight.toFixed(4)}\nTemp: ${zone.color_temperature}`}
              >
                <div>
                  <div className="text-xs font-semibold text-gray-800">
                    {zone.semiotic_label}
                  </div>
                  <div className="text-[10px] text-gray-500">{zone.position_label}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-gray-600">
                    w: {zone.visual_weight.toFixed(3)}
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
      <div className="p-2 bg-white text-xs text-gray-500 text-center">
        {compositionType === 'centred' ? 'Centre-Margin structure' : 'Polarized structure (Given-New / Ideal-Real)'}
      </div>
    </div>
  )
}

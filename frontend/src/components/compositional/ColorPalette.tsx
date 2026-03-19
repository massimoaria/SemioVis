import type { ColorSwatch } from '../../types/analysis'

interface Props {
  palette: ColorSwatch[]
}

export function ColorPalette({ palette }: Props) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="font-medium text-sm text-gray-700 mb-3">Colour Palette</h3>
      <div className="flex gap-2 flex-wrap">
        {palette.map((swatch, i) => (
          <div key={i} className="flex flex-col items-center gap-1">
            <div
              className="w-14 h-14 rounded-md border border-gray-300 shadow-sm"
              style={{ backgroundColor: swatch.hex }}
              title={`${swatch.hex} (${(swatch.proportion * 100).toFixed(1)}%)`}
            />
            <span className="text-[10px] text-gray-600 font-mono">{swatch.hex}</span>
            <span className="text-[10px] text-gray-400">
              {(swatch.proportion * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

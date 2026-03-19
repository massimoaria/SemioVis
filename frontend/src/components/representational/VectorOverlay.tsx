import { Stage, Layer, Arrow, Rect, Text, Image as KImage } from 'react-konva'
import { useEffect, useState } from 'react'
import type { Vector, Participant } from '../../types/analysis'

interface Props {
  imageBase64: string
  vectors: Vector[]
  participants: Participant[]
  imgWidth: number
  imgHeight: number
}

const DISPLAY_WIDTH = 500
const DIRECTION_COLORS: Record<string, string> = {
  horizontal: '#3b82f6',
  vertical: '#ef4444',
  diagonal: '#f97316',
}

export function VectorOverlay({ imageBase64, vectors, participants, imgWidth, imgHeight }: Props) {
  const [image, setImage] = useState<HTMLImageElement | null>(null)
  const scale = DISPLAY_WIDTH / imgWidth
  const displayHeight = imgHeight * scale

  useEffect(() => {
    const img = new window.Image()
    img.src = `data:image/jpeg;base64,${imageBase64}`
    img.onload = () => setImage(img)
  }, [imageBase64])

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-100">
      <Stage width={DISPLAY_WIDTH} height={displayHeight}>
        <Layer>
          {image && <KImage image={image} width={DISPLAY_WIDTH} height={displayHeight} />}

          {/* Participant bounding boxes */}
          {participants.map((p, i) => {
            const x = p.bbox[0] * DISPLAY_WIDTH
            const y = p.bbox[1] * displayHeight
            const w = (p.bbox[2] - p.bbox[0]) * DISPLAY_WIDTH
            const h = (p.bbox[3] - p.bbox[1]) * displayHeight
            return (
              <Rect
                key={`p-${i}`}
                x={x} y={y} width={w} height={h}
                stroke={p.is_human ? '#22c55e' : '#a855f7'}
                strokeWidth={2}
                dash={[4, 2]}
              />
            )
          })}

          {/* Participant labels */}
          {participants.map((p, i) => (
            <Text
              key={`pl-${i}`}
              x={p.bbox[0] * DISPLAY_WIDTH}
              y={p.bbox[1] * displayHeight - 14}
              text={`${p.label} (${(p.confidence * 100).toFixed(0)}%)`}
              fontSize={11}
              fill={p.is_human ? '#22c55e' : '#a855f7'}
              fontStyle="bold"
            />
          ))}

          {/* Vectors as arrows */}
          {vectors.map((v, i) => (
            <Arrow
              key={`v-${i}`}
              points={[
                v.x1 * DISPLAY_WIDTH,
                v.y1 * displayHeight,
                v.x2 * DISPLAY_WIDTH,
                v.y2 * displayHeight,
              ]}
              stroke={DIRECTION_COLORS[v.direction] || '#888'}
              strokeWidth={2}
              pointerLength={6}
              pointerWidth={5}
              opacity={0.7}
            />
          ))}
        </Layer>
      </Stage>

      {/* Legend */}
      <div className="flex gap-4 p-2 bg-white text-xs">
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-blue-500 inline-block" /> Horizontal
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-red-500 inline-block" /> Vertical
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-orange-500 inline-block" /> Diagonal
        </span>
      </div>
    </div>
  )
}

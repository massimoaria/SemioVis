import { Stage, Layer, Rect, Circle, Text, Image as KImage } from 'react-konva'
import { useEffect, useState } from 'react'
import type { FaceAnalysis } from '../../types/analysis'

interface Props {
  imageBase64: string
  faces: FaceAnalysis[]
  imgWidth: number
  imgHeight: number
  vanishingPoint?: [number, number] | null
}

const DISPLAY_WIDTH = 500

export function GazeOverlay({ imageBase64, faces, imgWidth, imgHeight, vanishingPoint }: Props) {
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

          {/* Face bounding boxes */}
          {faces.map((f) => {
            const x = f.face_bbox[0] * DISPLAY_WIDTH
            const y = f.face_bbox[1] * displayHeight
            const w = (f.face_bbox[2] - f.face_bbox[0]) * DISPLAY_WIDTH
            const h = (f.face_bbox[3] - f.face_bbox[1]) * displayHeight
            const isDemand = f.gaze_type === 'demand'

            return (
              <Rect
                key={`fb-${f.face_id}`}
                x={x} y={y} width={w} height={h}
                stroke={isDemand ? '#ef4444' : '#9ca3af'}
                strokeWidth={isDemand ? 3 : 2}
              />
            )
          })}

          {/* Gaze labels */}
          {faces.map((f) => (
            <Text
              key={`fl-${f.face_id}`}
              x={f.face_bbox[0] * DISPLAY_WIDTH}
              y={f.face_bbox[1] * displayHeight - 16}
              text={`${f.gaze_type.toUpperCase()} | ${f.social_distance}`}
              fontSize={11}
              fill={f.gaze_type === 'demand' ? '#ef4444' : '#6b7280'}
              fontStyle="bold"
            />
          ))}

          {/* Person body boxes */}
          {faces.filter(f => f.person_bbox).map((f) => {
            const pb = f.person_bbox!
            return (
              <Rect
                key={`pb-${f.face_id}`}
                x={pb[0] * DISPLAY_WIDTH}
                y={pb[1] * displayHeight}
                width={(pb[2] - pb[0]) * DISPLAY_WIDTH}
                height={(pb[3] - pb[1]) * displayHeight}
                stroke="#22c55e"
                strokeWidth={1}
                dash={[6, 3]}
              />
            )
          })}

          {/* Vanishing point */}
          {vanishingPoint && (
            <>
              <Circle
                x={vanishingPoint[0] * DISPLAY_WIDTH}
                y={vanishingPoint[1] * displayHeight}
                radius={8}
                stroke="#f59e0b"
                strokeWidth={2}
                fill="rgba(245,158,11,0.2)"
              />
              <Text
                x={vanishingPoint[0] * DISPLAY_WIDTH + 12}
                y={vanishingPoint[1] * displayHeight - 6}
                text="VP"
                fontSize={11}
                fill="#f59e0b"
                fontStyle="bold"
              />
            </>
          )}
        </Layer>
      </Stage>

      <div className="flex gap-4 p-2 bg-white text-xs">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 border-2 border-red-500 inline-block" /> Demand
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 border-2 border-gray-400 inline-block" /> Offer
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 border border-green-500 border-dashed inline-block" /> Body
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> VP
        </span>
      </div>
    </div>
  )
}

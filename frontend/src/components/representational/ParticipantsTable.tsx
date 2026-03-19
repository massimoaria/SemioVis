import type { Participant } from '../../types/analysis'

interface Props {
  participants: Participant[]
}

export function ParticipantsTable({ participants }: Props) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="font-medium text-sm text-gray-700 mb-2">
        Participants ({participants.length})
      </h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b">
            <th className="pb-1">Label</th>
            <th className="pb-1">Confidence</th>
            <th className="pb-1">Type</th>
          </tr>
        </thead>
        <tbody>
          {participants.map((p, i) => (
            <tr key={i} className="border-b border-gray-50">
              <td className="py-1 font-medium">{p.label}</td>
              <td className="py-1">{(p.confidence * 100).toFixed(0)}%</td>
              <td className="py-1">
                {p.is_human ? (
                  <span className="text-green-600">Human</span>
                ) : p.is_animal ? (
                  <span className="text-purple-600">Animal</span>
                ) : (
                  <span className="text-gray-500">Object</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

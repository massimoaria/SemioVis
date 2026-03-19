export function HomePage() {
  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-xl mx-auto text-center px-6 py-8">
        <h1 className="text-4xl font-bold text-gray-900 tracking-tight mb-1">
          SemioVis
        </h1>
        <p className="text-lg text-primary-600 font-medium mb-4">
          Visual Semiotic Analysis
        </p>
        <p className="text-sm text-gray-600 leading-relaxed mb-5">
          Implements the visual grammar framework by Kress and van Leeuwen (2006)
          to perform <strong>Representational</strong>, <strong>Interactive</strong>,
          and <strong>Compositional</strong> analysis of images.
        </p>

        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-5 text-left text-sm">
          <ul className="space-y-2 text-gray-600">
            <li><strong className="text-primary-700">Representational</strong> — Narrative/conceptual
            structures: actors, goals, vectors, visual processes.</li>
            <li><strong className="text-primary-700">Interactive</strong> — Viewer relationship:
            gaze (demand/offer), social distance, power, 8-scale modality.</li>
            <li><strong className="text-primary-700">Compositional</strong> — Information value
            (Given/New, Ideal/Real), salience, framing, reading paths.</li>
          </ul>
        </div>

        <p className="text-xs text-gray-400 mb-4">
          Upload an image, then use <strong>Dashboard</strong> to run all analyses.
        </p>

        <div className="pt-4 border-t border-gray-200 text-xs text-gray-500">
          <p className="font-medium text-gray-700">Developed by Massimo Aria</p>
          <p className="mt-1">All rights reserved.</p>
          <p className="mt-1 italic">
            Based on: Kress, G., &amp; van Leeuwen, T. (2006). Reading Images:
            The Grammar of Visual Design (2nd ed.). Routledge.
          </p>
        </div>
      </div>
    </div>
  )
}

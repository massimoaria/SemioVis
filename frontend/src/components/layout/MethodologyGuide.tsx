import { ArrowLeft } from 'lucide-react'

interface Props {
  onBack: () => void
}

export function MethodologyGuide({ onBack }: Props) {
  return (
    <div className="h-full overflow-y-auto bg-white">
      <div className="max-w-3xl mx-auto px-8 py-6">
        <button
          onClick={onBack}
          className="flex items-center gap-1 text-sm text-primary-600 hover:underline mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> Back to analysis
        </button>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Methodology Guide</h1>
        <p className="text-gray-500 mb-8">
          This guide explains the semiotic analysis framework implemented in SemioVis,
          based on the visual grammar theory by Kress and van Leeuwen (2006).
        </p>

        {/* REPRESENTATIONAL */}
        <section className="mb-10">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4 pb-2 border-b border-primary-200">
            1. Representational Analysis
          </h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            Representational analysis examines <strong>what</strong> is being depicted
            in an image — the participants, the processes connecting them, and the
            circumstances in which they occur. Images represent the world either
            through <em>narrative</em> or <em>conceptual</em> structures.
          </p>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Narrative Structures</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            Narrative images depict unfolding actions or events, characterised by the
            presence of <strong>vectors</strong> — visual lines of action that connect
            participants. The types of narrative process include:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 text-sm mb-4">
            <li><strong>Transactional</strong>: A vector connects an Actor to a Goal, establishing
            a clear "doing-to" relationship (e.g., a person pointing at an object).</li>
            <li><strong>Non-transactional</strong>: An Actor performs an action (vector present)
            but no clear Goal is identifiable — the action is open-ended.</li>
            <li><strong>Bidirectional</strong>: Two participants act upon each other reciprocally.</li>
            <li><strong>Reactional</strong>: The vector is formed by an eyeline (gaze),
            connecting a Reacter to a Phenomenon.</li>
            <li><strong>Mental / Verbal</strong>: Thought bubbles or speech bubbles represent
            mental or verbal processes.</li>
          </ul>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Conceptual Structures</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            Conceptual images represent participants in terms of their stable,
            generalised essence — their class, structure, or meaning:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 text-sm mb-4">
            <li><strong>Classificational</strong>: Taxonomic relationships (superordinate/subordinate).</li>
            <li><strong>Analytical</strong>: Part-whole relationships (Carrier and Possessive Attributes).</li>
            <li><strong>Symbolic</strong>: What a participant means or is (Carrier and Symbolic Attribute).</li>
          </ul>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Key Metrics</h3>
          <div className="bg-gray-50 rounded-lg p-4 text-sm space-y-1">
            <p><strong>Vector count</strong>: Number of detected action lines in the image.</p>
            <p><strong>Dominant direction</strong>: Whether vectors are primarily horizontal, vertical, or diagonal.</p>
            <p><strong>Participants</strong>: Detected objects/persons with classification and confidence scores.</p>
          </div>
        </section>

        {/* INTERACTIVE */}
        <section className="mb-10">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4 pb-2 border-b border-primary-200">
            2. Interactive Analysis
          </h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            Interactive analysis examines the relationship between the represented
            participants and the viewer. It covers four key dimensions:
            <strong> contact</strong>, <strong>social distance</strong>,
            <strong> attitude</strong>, and <strong>modality</strong>.
          </p>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Contact (Demand / Offer)</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            When a represented participant looks directly at the viewer (<strong>demand</strong>),
            an imaginary social relationship is established — the image "demands" something
            from the viewer. When the participant's gaze is directed elsewhere
            (<strong>offer</strong>), they are presented as objects of contemplation.
          </p>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Social Distance</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            Based on the framing of the human body (not face size), social distance
            maps Hall's proxemics to shot types: close-up (intimate), medium (social),
            long shot (public).
          </p>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Attitude (Angles)</h3>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 text-sm mb-4">
            <li><strong>Vertical angle</strong>: High angle = viewer power; eye level = equality;
            low angle = subject power.</li>
            <li><strong>Horizontal angle</strong>: Frontal = involvement and identification;
            oblique = detachment and otherness.</li>
          </ul>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Modality (8-Scale Profile)</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            Modality measures the visual "credibility" or "reality value" of an image
            across 8 independent scales. The interpretation depends on the
            <strong> coding orientation</strong>:
          </p>
          <div className="bg-gray-50 rounded-lg p-4 text-sm space-y-1 mb-3">
            <p><strong>Colour saturation</strong>: From black-and-white (0) to full colour (1).</p>
            <p><strong>Colour differentiation</strong>: From monochrome (0) to maximally diversified palette (1).</p>
            <p><strong>Colour modulation</strong>: From flat colour (0) to fully modulated shading (1).</p>
            <p><strong>Contextualization</strong>: From no background (0) to detailed environment (1).</p>
            <p><strong>Representation</strong>: From maximum abstraction (0) to maximum pictorial detail (1).</p>
            <p><strong>Depth</strong>: From flat/no perspective (0) to deep perspective (1).</p>
            <p><strong>Illumination</strong>: From no light/shade (0) to full light modelling (1).</p>
            <p><strong>Brightness</strong>: From two values only (0) to many brightness degrees (1).</p>
          </div>
          <p className="text-gray-700 text-sm">
            <strong>Coding orientations</strong>: Naturalistic (photographic norm, moderate = high modality),
            Sensory (high values = high modality), Technological (low values = high modality),
            Abstract (reduction = high modality).
          </p>
        </section>

        {/* COMPOSITIONAL */}
        <section className="mb-10">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4 pb-2 border-b border-primary-200">
            3. Compositional Analysis
          </h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            Compositional analysis examines how the elements of an image are arranged
            to create meaning through three interrelated systems: <strong>information value</strong>,
            <strong> salience</strong>, and <strong>framing</strong>.
          </p>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Information Value</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            The spatial position of elements carries meaning:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 text-sm mb-4">
            <li><strong>Given / New</strong> (left-right axis): Left = familiar, established information;
            Right = the message, the issue, the "new" (reversed in RTL cultures).</li>
            <li><strong>Ideal / Real</strong> (top-bottom axis): Top = generalised, aspirational essence;
            Bottom = practical, specific, evidential detail.</li>
            <li><strong>Centre / Margin</strong>: Centre = nucleus of information; margins = subordinate elements.</li>
            <li><strong>Triptych</strong>: Three-panel structure with a Mediator between two poles.</li>
          </ul>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Salience</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            Salience determines the relative visual weight of elements. It is influenced by
            size, sharpness, tonal contrast, colour contrast, placement in the foreground,
            and the presence of human figures.
          </p>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Framing</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            Framing determines the degree of connection or disconnection between elements:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-700 text-sm mb-4">
            <li><strong>Disconnection</strong>: Frame lines, empty space, colour discontinuities
            separate elements into distinct units of information.</li>
            <li><strong>Connection</strong>: Colour continuity, visual vectors, and shape rhymes
            (repeated forms) link elements together.</li>
          </ul>

          <h3 className="text-lg font-medium text-gray-800 mt-6 mb-2">Reading Path</h3>
          <p className="text-gray-700 leading-relaxed mb-3">
            The predicted visual reading path traces the order in which the viewer's eye
            moves through the image, based on salience peaks. Common patterns include
            linear (left-right, top-bottom), Z-pattern, circular, and irregular paths.
          </p>
        </section>

        {/* Reference */}
        <section className="mb-6 pt-6 border-t border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Reference</h2>
          <p className="text-sm text-gray-600 italic">
            Kress, G., &amp; van Leeuwen, T. (2006). <em>Reading Images: The Grammar of
            Visual Design</em> (2nd ed.). Routledge.
          </p>
        </section>
      </div>
    </div>
  )
}

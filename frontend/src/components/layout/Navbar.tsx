import { Settings, HelpCircle } from 'lucide-react'
import { useState } from 'react'
import { SettingsModal } from './SettingsModal'
import { HelpModal } from './HelpModal'

export function Navbar() {
  const [showSettings, setShowSettings] = useState(false)
  const [showHelp, setShowHelp] = useState(false)

  return (
    <>
      <header className="h-14 border-b border-gray-200 bg-white px-6 flex items-center justify-between">
        <h1 className="text-lg font-semibold tracking-tight">
          SemioVis
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 rounded-md hover:bg-gray-100"
            title="Settings"
          >
            <Settings className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={() => setShowHelp(true)}
            className="p-2 rounded-md hover:bg-gray-100"
            title="Help"
          >
            <HelpCircle className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </header>

      <SettingsModal open={showSettings} onClose={() => setShowSettings(false)} />
      <HelpModal open={showHelp} onClose={() => setShowHelp(false)} onOpenSettings={() => setShowSettings(true)} />
    </>
  )
}

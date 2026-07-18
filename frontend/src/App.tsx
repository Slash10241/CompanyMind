import { useState, useEffect } from 'react'
import { Brain, FileUp, FileText, Activity } from 'lucide-react'
import { ChatInterface } from './components/ChatInterface'
import { DocumentUpload } from './components/DocumentUpload'
import { DocumentList } from './components/DocumentList'
import { getHealth, type HealthData } from './lib/api'

type Tab = 'chat' | 'documents'

export default function App() {
  const [tab, setTab] = useState<Tab>('chat')
  const [health, setHealth] = useState<HealthData | null>(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => {
    const load = async () => {
      try { setHealth(await getHealth()) } catch { setHealth(null) }
    }
    load()
    const interval = setInterval(load, 15000)
    return () => clearInterval(interval)
  }, [refreshTrigger])

  const onIngestionComplete = () => setRefreshTrigger(t => t + 1)

  const tabs: { id: Tab; icon: typeof Brain; label: string }[] = [
    { id: 'chat',      icon: Brain,    label: 'Copilot' },
    { id: 'documents', icon: FileText, label: 'Documents' },
  ]

  return (
    <div className="flex flex-col h-screen bg-rm-cream max-w-screen-2xl mx-auto">

      {/* Header */}
      <header className="bg-rm-navy border-b-4 border-rm-gold px-4 py-3 flex items-center gap-4 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-rm-gold flex items-center justify-center">
            <Activity size={16} className="text-rm-navy" />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-bold text-white tracking-wide">CompanyMind</p>
            <p className="text-xs text-blue-200">Knowledge Intelligence Platform</p>
          </div>
        </div>

        {health && (
          <div className="flex items-center gap-3 ml-auto text-xs text-blue-200">
            <span className="hidden md:block">{health.total_chunks} chunks</span>
            <span className={`flex items-center gap-1 font-medium ${health.status === 'ok' ? 'text-rm-gold' : 'text-red-400'}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current" />
              {health.status === 'ok' ? 'Online' : 'Offline'}
            </span>
          </div>
        )}
      </header>

      {/* Main layout */}
      <div className="flex flex-1 min-h-0">

        {/* Desktop sidebar */}
        <aside className="hidden md:flex flex-col w-64 bg-white border-r border-rm-gray-light shrink-0 shadow-sm">
          <nav className="p-3 space-y-1 border-b border-rm-gray-light">
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  tab === t.id
                    ? 'bg-rm-navy text-white shadow-sm'
                    : 'text-rm-gray hover:text-rm-text hover:bg-rm-gray-ultra'
                }`}
              >
                <t.icon size={16} className={tab === t.id ? 'text-rm-gold' : ''} />
                {t.label}
              </button>
            ))}
          </nav>

          <div className="p-4 border-b border-rm-gray-light">
            <p className="text-xs text-rm-gray font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <FileUp size={11} /> Ingest Documents
            </p>
            <DocumentUpload onComplete={onIngestionComplete} />
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
            <DocumentList refreshTrigger={refreshTrigger} />
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 flex flex-col bg-rm-cream">
          <div className={tab === 'chat' ? 'flex flex-col flex-1 min-h-0' : 'hidden'}>
            <ChatInterface />
          </div>

          <div className={tab === 'documents' ? 'flex-1 overflow-y-auto scrollbar-thin p-4 md:p-6 max-w-2xl mx-auto w-full' : 'hidden'}>
            <h2 className="text-lg font-bold text-rm-text mb-4">Document Management</h2>
            <div className="mb-6">
              <p className="text-xs text-rm-gray font-semibold uppercase tracking-wider mb-3">Upload</p>
              <DocumentUpload onComplete={onIngestionComplete} />
            </div>
            <DocumentList refreshTrigger={refreshTrigger} />
          </div>
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="md:hidden bg-rm-navy border-t-2 border-rm-gold flex shrink-0">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex flex-col items-center gap-1 py-3 text-xs font-medium transition-colors ${
              tab === t.id ? 'text-rm-gold' : 'text-blue-300'
            }`}
          >
            <t.icon size={20} />
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

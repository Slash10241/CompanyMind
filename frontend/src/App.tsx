import { useState, useEffect } from 'react'
import { Brain, FileUp, Network, FileText, Activity } from 'lucide-react'
import { ChatInterface } from './components/ChatInterface'
import { DocumentUpload } from './components/DocumentUpload'
import { DocumentList } from './components/DocumentList'
import { KnowledgeGraph } from './components/KnowledgeGraph'
import { getHealth, type HealthData } from './lib/api'

type Tab = 'chat' | 'documents' | 'graph'

export default function App() {
  const [tab, setTab] = useState<Tab>('chat')
  const [health, setHealth] = useState<HealthData | null>(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => {
    const load = async () => {
      try {
        setHealth(await getHealth())
      } catch {
        setHealth(null)
      }
    }
    load()
    const interval = setInterval(load, 15000)
    return () => clearInterval(interval)
  }, [refreshTrigger])

  const onIngestionComplete = () => {
    setRefreshTrigger(t => t + 1)
  }

  const tabs: { id: Tab; icon: typeof Brain; label: string }[] = [
    { id: 'chat', icon: Brain, label: 'Copilot' },
    { id: 'documents', icon: FileText, label: 'Documents' },
    { id: 'graph', icon: Network, label: 'Knowledge Graph' },
  ]

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 max-w-screen-2xl mx-auto">
      {/* Header */}
      <header className="border-b border-slate-800 px-4 py-3 flex items-center gap-4 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-industrial-900 border border-industrial-700/50 flex items-center justify-center">
            <Activity size={16} className="text-industrial-400" />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold text-slate-100">Sunrise Refinery</p>
            <p className="text-xs text-slate-500">Knowledge Intelligence Platform</p>
          </div>
        </div>

        {/* Stats */}
        {health && (
          <div className="flex items-center gap-3 ml-auto text-xs text-slate-500">
            <span className="hidden md:block">{health.graph_nodes} nodes</span>
            <span className="hidden md:block">{health.graph_edges} edges</span>
            <span className="hidden md:block">{health.total_chunks} chunks</span>
            <span className={`flex items-center gap-1 ${health.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current" />
              {health.status === 'ok' ? 'Online' : 'Offline'}
            </span>
          </div>
        )}
      </header>

      {/* Main layout */}
      <div className="flex flex-1 min-h-0">
        {/* Desktop sidebar */}
        <aside className="hidden md:flex flex-col w-64 border-r border-slate-800 shrink-0">
          <nav className="p-3 space-y-1 border-b border-slate-800">
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  tab === t.id
                    ? 'bg-industrial-900/60 text-industrial-300 border border-industrial-800/50'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <t.icon size={16} />
                {t.label}
              </button>
            ))}
          </nav>

          {/* Document upload sidebar panel */}
          <div className="p-4 border-b border-slate-800">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <FileUp size={11} /> Ingest Documents
            </p>
            <DocumentUpload onComplete={onIngestionComplete} />
          </div>

          {/* Document list sidebar */}
          <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
            <DocumentList refreshTrigger={refreshTrigger} />
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 flex flex-col">
          {tab === 'chat' && <ChatInterface />}

          {tab === 'documents' && (
            <div className="flex-1 overflow-y-auto scrollbar-thin p-4 md:p-6 max-w-2xl mx-auto w-full">
              <h2 className="text-lg font-semibold text-slate-200 mb-4">Document Management</h2>
              <div className="mb-6">
                <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-3">Upload</p>
                <DocumentUpload onComplete={onIngestionComplete} />
              </div>
              <DocumentList refreshTrigger={refreshTrigger} />
            </div>
          )}

          {tab === 'graph' && (
            <div className="flex-1 flex flex-col min-h-0">
              <KnowledgeGraph />
            </div>
          )}
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="md:hidden border-t border-slate-800 flex shrink-0">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex flex-col items-center gap-1 py-3 text-xs font-medium transition-colors ${
              tab === t.id ? 'text-industrial-400' : 'text-slate-500'
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

import { useEffect, useState } from 'react'
import { FileText, Download, RefreshCw, Layers } from 'lucide-react'
import { listDocuments, type DocumentMeta } from '../lib/api'

const DOC_TYPE_COLORS: Record<string, string> = {
  'Work Order': 'bg-blue-500/20 text-blue-300 border-blue-500/20',
  'Inspection Report': 'bg-purple-500/20 text-purple-300 border-purple-500/20',
  'Safety Procedure': 'bg-red-500/20 text-red-300 border-red-500/20',
  'Equipment Data Sheet': 'bg-cyan-500/20 text-cyan-300 border-cyan-500/20',
  'Incident Report': 'bg-orange-500/20 text-orange-300 border-orange-500/20',
  'Operating Procedure': 'bg-green-500/20 text-green-300 border-green-500/20',
  'General Document': 'bg-slate-500/20 text-slate-300 border-slate-500/20',
}

interface Props {
  refreshTrigger?: number
}

export function DocumentList({ refreshTrigger }: Props) {
  const [docs, setDocs] = useState<DocumentMeta[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const data = await listDocuments()
      setDocs(data.sort((a, b) => b.upload_time.localeCompare(a.upload_time)))
    } catch {
      setDocs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [refreshTrigger])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-500 text-sm gap-2">
        <RefreshCw size={16} className="animate-spin" />
        Loading documents...
      </div>
    )
  }

  if (!docs.length) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-slate-500 gap-3">
        <Layers size={32} className="opacity-40" />
        <p className="text-sm">No documents ingested yet</p>
        <p className="text-xs">Upload documents using the panel above</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-slate-300 font-medium">{docs.length} document{docs.length !== 1 ? 's' : ''} in knowledge base</p>
        <button onClick={load} className="text-slate-500 hover:text-slate-300 transition-colors">
          <RefreshCw size={14} />
        </button>
      </div>
      {docs.map(doc => {
        const typeColor = DOC_TYPE_COLORS[doc.doc_type] ?? DOC_TYPE_COLORS['General Document']
        const date = new Date(doc.upload_time).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
        return (
          <div key={doc.id} className="flex items-start gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/40 hover:border-slate-600/60 transition-colors group">
            <FileText size={16} className="text-slate-500 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-200 truncate font-medium">{doc.name.replace(/_/g, ' ')}</p>
              <div className="flex items-center flex-wrap gap-2 mt-1.5">
                <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${typeColor}`}>
                  {doc.doc_type}
                </span>
                <span className="text-xs text-slate-500">{doc.chunk_count} chunks</span>
                <span className="text-xs text-slate-500">{doc.entity_count} entities</span>
                <span className="text-xs text-slate-600">{date}</span>
              </div>
            </div>
            <a
              href={`/api/documents/${doc.id}/download`}
              target="_blank"
              rel="noopener noreferrer"
              className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-slate-300 transition-all shrink-0"
              title="Download original"
            >
              <Download size={14} />
            </a>
          </div>
        )
      })}
    </div>
  )
}

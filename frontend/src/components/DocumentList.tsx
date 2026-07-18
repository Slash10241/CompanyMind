import { useEffect, useState } from 'react'
import { FileText, Download, RefreshCw, Layers } from 'lucide-react'
import { listDocuments, type DocumentMeta } from '../lib/api'

const DOC_TYPE_COLORS: Record<string, string> = {
  'Work Order':           'bg-blue-50 text-blue-700 border-blue-200',
  'Inspection Report':    'bg-purple-50 text-purple-700 border-purple-200',
  'Safety Procedure':     'bg-red-50 text-red-700 border-red-200',
  'Equipment Data Sheet': 'bg-cyan-50 text-cyan-700 border-cyan-200',
  'Incident Report':      'bg-orange-50 text-orange-700 border-orange-200',
  'Operating Procedure':  'bg-emerald-50 text-emerald-700 border-emerald-200',
  'General Document':     'bg-rm-gray-ultra text-rm-gray border-rm-gray-light',
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
      <div className="flex items-center justify-center h-32 text-rm-gray text-sm gap-2">
        <RefreshCw size={14} className="animate-spin" />
        Loading documents...
      </div>
    )
  }

  if (!docs.length) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-rm-gray gap-3">
        <Layers size={28} className="opacity-30" />
        <p className="text-sm">No documents ingested yet</p>
        <p className="text-xs text-rm-gray">Upload documents using the panel above</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-rm-gray font-semibold uppercase tracking-wider">
          {docs.length} document{docs.length !== 1 ? 's' : ''}
        </p>
        <button onClick={load} className="text-rm-gray hover:text-rm-navy transition-colors">
          <RefreshCw size={13} />
        </button>
      </div>
      {docs.map(doc => {
        const typeColor = DOC_TYPE_COLORS[doc.doc_type] ?? DOC_TYPE_COLORS['General Document']
        const date = new Date(doc.upload_time).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
        return (
          <div key={doc.id} className="flex items-start gap-2.5 p-2.5 rounded-xl bg-white border border-rm-gray-light hover:border-rm-navy/30 hover:shadow-sm transition-all group">
            <FileText size={14} className="text-rm-gray shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-xs text-rm-text truncate font-medium">{doc.name.replace(/_/g, ' ')}</p>
              <div className="flex items-center flex-wrap gap-1.5 mt-1">
                <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${typeColor}`}>
                  {doc.doc_type}
                </span>
                <span className="text-xs text-rm-gray">{doc.chunk_count} chunks</span>
                <span className="text-xs text-rm-gray">{doc.entity_count} entities</span>
                <span className="text-xs text-rm-gray">{date}</span>
              </div>
            </div>
            <a
              href={`/api/documents/${doc.id}/download`}
              target="_blank"
              rel="noopener noreferrer"
              className="opacity-0 group-hover:opacity-100 text-rm-gray hover:text-rm-navy transition-all shrink-0"
              title="Download original"
            >
              <Download size={13} />
            </a>
          </div>
        )
      })}
    </div>
  )
}

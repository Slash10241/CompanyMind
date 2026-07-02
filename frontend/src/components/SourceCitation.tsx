import { useState } from 'react'
import { ChevronDown, FileText, ExternalLink } from 'lucide-react'
import type { SourceCitation as Citation } from '../lib/api'

interface Props {
  citations: Citation[]
}

const DOC_TYPE_COLORS: Record<string, string> = {
  'Work Order': 'bg-blue-500/20 text-blue-300',
  'Inspection Report': 'bg-purple-500/20 text-purple-300',
  'Safety Procedure': 'bg-red-500/20 text-red-300',
  'Equipment Data Sheet': 'bg-cyan-500/20 text-cyan-300',
  'Incident Report': 'bg-orange-500/20 text-orange-300',
  'Operating Procedure': 'bg-green-500/20 text-green-300',
  'General Document': 'bg-slate-500/20 text-slate-300',
}

export function SourceCitations({ citations }: Props) {
  const [open, setOpen] = useState(false)

  if (!citations.length) return null

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
      >
        <FileText size={12} />
        <span>{citations.length} source{citations.length > 1 ? 's' : ''}</span>
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {citations.map((c, i) => {
            const colorClass = DOC_TYPE_COLORS[c.doc_name] ??
              (Object.entries(DOC_TYPE_COLORS).find(([k]) => c.doc_name.toLowerCase().includes(k.toLowerCase()))?.[1] ??
              'bg-slate-500/20 text-slate-300')
            return (
              <div key={i} className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-3">
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${colorClass}`}>
                      p.{c.page_number}
                    </span>
                    <span className="text-xs text-slate-300 font-medium truncate max-w-[200px]">
                      {c.doc_name.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-slate-500">
                      {Math.round(c.relevance_score * 100)}% match
                    </span>
                    <a
                      href={`/api/documents/${c.doc_id}/download`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-500 hover:text-slate-300 transition-colors"
                    >
                      <ExternalLink size={11} />
                    </a>
                  </div>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                  {c.snippet}
                </p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

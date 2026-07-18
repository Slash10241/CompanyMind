import { useState } from 'react'
import { ChevronDown, FileText, ExternalLink } from 'lucide-react'
import type { SourceCitation as Citation } from '../lib/api'

interface Props {
  citations: Citation[]
}

const DOC_TYPE_COLORS: Record<string, string> = {
  'Work Order':          'bg-blue-50 text-blue-700 border-blue-200',
  'Inspection Report':   'bg-purple-50 text-purple-700 border-purple-200',
  'Safety Procedure':    'bg-red-50 text-red-700 border-red-200',
  'Equipment Data Sheet':'bg-cyan-50 text-cyan-700 border-cyan-200',
  'Incident Report':     'bg-orange-50 text-orange-700 border-orange-200',
  'Operating Procedure': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  'General Document':    'bg-rm-gray-ultra text-rm-gray border-rm-gray-light',
}

export function SourceCitations({ citations }: Props) {
  const [open, setOpen] = useState(false)

  if (!citations.length) return null

  return (
    <div className="mt-1.5">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-xs text-rm-gray hover:text-rm-navy transition-colors"
      >
        <FileText size={12} />
        <span>{citations.length} source{citations.length > 1 ? 's' : ''}</span>
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {citations.map((c, i) => {
            const colorClass =
              DOC_TYPE_COLORS[c.doc_name] ??
              (Object.entries(DOC_TYPE_COLORS).find(([k]) =>
                c.doc_name.toLowerCase().includes(k.toLowerCase())
              )?.[1] ?? DOC_TYPE_COLORS['General Document'])
            return (
              <div key={i} className="rounded-xl border border-rm-gray-light bg-white p-3 shadow-sm">
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${colorClass}`}>
                      p.{c.page_number}
                    </span>
                    <span className="text-xs text-rm-text font-medium truncate max-w-[200px]">
                      {c.doc_name.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-rm-gray">
                      {Math.round(c.relevance_score * 100)}% match
                    </span>
                    <a
                      href={`/api/documents/${c.doc_id}/download`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-rm-gray hover:text-rm-navy transition-colors"
                    >
                      <ExternalLink size={11} />
                    </a>
                  </div>
                </div>
                <p className="text-xs text-rm-gray leading-relaxed line-clamp-3">
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

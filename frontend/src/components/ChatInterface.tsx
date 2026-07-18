import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Brain, FileText, Layers, Network } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { streamChat, listDocuments, getHealth, type ChatMessage, type SourceCitation } from '../lib/api'
import { ConfidenceBadge } from './ConfidenceBadge'
import { SourceCitations } from './SourceCitation'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: SourceCitation[]
  confidence?: number | null
  streaming?: boolean
  ragUsed?: boolean
}

interface KBSummary {
  totalDocs: number
  totalChunks: number
  graphNodes: number
  byType: { type: string; count: number }[]
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [kbSummary, setKbSummary] = useState<KBSummary | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    Promise.all([listDocuments(), getHealth()])
      .then(([docs, health]) => {
        const typeCounts: Record<string, number> = {}
        for (const d of docs) typeCounts[d.doc_type] = (typeCounts[d.doc_type] ?? 0) + 1
        const byType = Object.entries(typeCounts)
          .sort((a, b) => b[1] - a[1])
          .map(([type, count]) => ({ type, count }))
        setKbSummary({ totalDocs: docs.length, totalChunks: health.total_chunks, graphNodes: health.graph_nodes, byType })
      })
      .catch(() => setKbSummary(null))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = (query: string) => {
    if (!query.trim() || loading) return

    const userMsg: Message = { role: 'user', content: query }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    const history: ChatMessage[] = messages
      .filter(m => !m.streaming)
      .map(m => ({ role: m.role, content: m.content }))

    let assistantContent = ''
    let msgIndex = -1

    setMessages(prev => {
      msgIndex = prev.length
      return [...prev, { role: 'assistant', content: '', streaming: true }]
    })

    streamChat(
      query, history,
      (token) => {
        assistantContent += token
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) updated[msgIndex] = { ...updated[msgIndex], content: assistantContent }
          return updated
        })
      },
      (confidence, citations) => {
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) updated[msgIndex] = { ...updated[msgIndex], confidence, citations }
          return updated
        })
      },
      () => {
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) updated[msgIndex] = { ...updated[msgIndex], streaming: false }
          return updated
        })
        setLoading(false)
      },
      (err) => {
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) updated[msgIndex] = { ...updated[msgIndex], content: `Error: ${err}`, streaming: false }
          return updated
        })
        setLoading(false)
      },
      (needsRag) => {
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) updated[msgIndex] = { ...updated[msgIndex], ragUsed: needsRag }
          return updated
        })
      },
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div className="w-16 h-16 rounded-2xl bg-rm-navy flex items-center justify-center shadow-lg">
              <Brain size={32} className="text-rm-gold" />
            </div>

            <div>
              <h2 className="text-xl font-bold text-rm-text mb-1">Knowledge Copilot</h2>
              <p className="text-sm text-rm-gray max-w-sm">
                Ask anything across the ingested knowledge base — equipment, invoices, reports, procedures.
              </p>
            </div>

            {kbSummary && kbSummary.totalDocs > 0 ? (
              <div className="w-full max-w-md space-y-4">
                {/* Stats row */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-white rounded-xl border border-rm-gray-light p-3 shadow-sm">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                      <FileText size={14} className="text-rm-navy" />
                      <span className="text-xs font-semibold text-rm-gray uppercase tracking-wide">Documents</span>
                    </div>
                    <p className="text-2xl font-bold text-rm-navy text-center">{kbSummary.totalDocs}</p>
                  </div>
                  <div className="bg-white rounded-xl border border-rm-gray-light p-3 shadow-sm">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                      <Layers size={14} className="text-rm-navy" />
                      <span className="text-xs font-semibold text-rm-gray uppercase tracking-wide">Chunks</span>
                    </div>
                    <p className="text-2xl font-bold text-rm-navy text-center">{kbSummary.totalChunks}</p>
                  </div>
                  <div className="bg-white rounded-xl border border-rm-gray-light p-3 shadow-sm">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                      <Network size={14} className="text-rm-navy" />
                      <span className="text-xs font-semibold text-rm-gray uppercase tracking-wide">KG Nodes</span>
                    </div>
                    <p className="text-2xl font-bold text-rm-navy text-center">{kbSummary.graphNodes}</p>
                  </div>
                </div>

                {/* Doc type breakdown */}
                <div className="bg-white rounded-xl border border-rm-gray-light p-4 shadow-sm text-left">
                  <p className="text-xs font-semibold text-rm-gray uppercase tracking-wider mb-2.5">Document Types</p>
                  <div className="space-y-1.5">
                    {kbSummary.byType.map(({ type, count }) => (
                      <div key={type} className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-rm-gray-ultra rounded-full overflow-hidden">
                          <div
                            className="h-full bg-rm-navy rounded-full"
                            style={{ width: `${Math.round((count / kbSummary.totalDocs) * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-rm-text w-24 shrink-0">{type}</span>
                        <span className="text-xs font-medium text-rm-navy w-6 text-right shrink-0">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-rm-gray">No documents ingested yet. Upload documents to get started.</p>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-rm-navy flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                <Brain size={16} className="text-rm-gold" />
              </div>
            )}
            <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-rm-navy text-white rounded-tr-sm'
                    : 'bg-white text-rm-text border border-rm-gray-light rounded-tl-sm'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className={`prose prose-sm max-w-none prose-headings:text-rm-text prose-a:text-rm-navy ${msg.streaming && !msg.content ? 'cursor-blink' : ''}`}>
                    <ReactMarkdown>{msg.content || ''}</ReactMarkdown>
                    {msg.streaming && msg.content && <span className="cursor-blink" />}
                  </div>
                ) : msg.content}
              </div>
              {msg.role === 'assistant' && !msg.streaming && (
                <div className="mt-1.5 px-1 space-y-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    {msg.ragUsed !== undefined && (
                      <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                        msg.ragUsed
                          ? 'bg-rm-navy/10 text-rm-navy border border-rm-navy/20'
                          : 'bg-gray-100 text-gray-500 border border-gray-200'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${msg.ragUsed ? 'bg-rm-navy' : 'bg-gray-400'}`} />
                        {msg.ragUsed ? 'KB searched' : 'Direct reply'}
                      </span>
                    )}
                    {msg.confidence != null && <ConfidenceBadge score={msg.confidence} />}
                  </div>
                  {msg.citations && msg.citations.length > 0 && <SourceCitations citations={msg.citations} />}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-rm-gray-light bg-white p-4">
        <div className="flex gap-2 items-end bg-rm-gray-ultra rounded-2xl border border-rm-gray-light focus-within:border-rm-navy focus-within:ring-2 focus-within:ring-rm-navy/10 transition-all p-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about equipment, invoices, reports, procedures..."
            rows={1}
            className="flex-1 bg-transparent text-sm text-rm-text placeholder-rm-gray resize-none outline-none px-2 py-1 max-h-32 scrollbar-thin"
            style={{ minHeight: '36px' }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="w-9 h-9 rounded-xl bg-rm-navy hover:bg-rm-navy-dark disabled:bg-rm-gray-light disabled:cursor-not-allowed flex items-center justify-center transition-colors shrink-0"
          >
            {loading
              ? <Loader2 size={16} className="animate-spin text-rm-gray" />
              : <Send size={16} className="text-white" />}
          </button>
        </div>
        <p className="text-xs text-rm-gray text-center mt-2">
          Answers drawn from ingested documents only · Always verify safety-critical information
        </p>
      </div>
    </div>
  )
}

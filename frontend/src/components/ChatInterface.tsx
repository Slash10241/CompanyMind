import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Brain } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { streamChat, type ChatMessage, type SourceCitation } from '../lib/api'
import { ConfidenceBadge } from './ConfidenceBadge'
import { SourceCitations } from './SourceCitation'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: SourceCitation[]
  confidence?: number
  streaming?: boolean
}

const EXAMPLE_QUERIES = [
  'What is the maintenance history of pump P-101?',
  'What PPE is required for hot work in the CDU area?',
  'Has C-401 compressor had any unplanned shutdowns?',
  'What are the compliance gaps identified in the latest audit?',
  'What is the maximum operating pressure of heat exchanger HE-201?',
]

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

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

    // Add streaming placeholder
    let assistantContent = ''
    let msgIndex = -1

    setMessages(prev => {
      msgIndex = prev.length
      return [...prev, { role: 'assistant', content: '', streaming: true }]
    })

    streamChat(
      query,
      history,
      (token) => {
        assistantContent += token
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) {
            updated[msgIndex] = { ...updated[msgIndex], content: assistantContent }
          }
          return updated
        })
      },
      (confidence, citations) => {
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) {
            updated[msgIndex] = { ...updated[msgIndex], confidence, citations }
          }
          return updated
        })
      },
      () => {
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) {
            updated[msgIndex] = { ...updated[msgIndex], streaming: false }
          }
          return updated
        })
        setLoading(false)
      },
      (err) => {
        setMessages(prev => {
          const updated = [...prev]
          if (updated[msgIndex]) {
            updated[msgIndex] = {
              ...updated[msgIndex],
              content: `Error: ${err}`,
              streaming: false,
            }
          }
          return updated
        })
        setLoading(false)
      }
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div className="w-16 h-16 rounded-2xl bg-industrial-900 border border-industrial-700/50 flex items-center justify-center">
              <Brain size={32} className="text-industrial-500" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-200 mb-1">Knowledge Copilot</h2>
              <p className="text-sm text-slate-400 max-w-sm">
                Ask anything about Sunrise Refinery equipment, maintenance history, safety procedures, and compliance status.
              </p>
            </div>
            <div className="grid gap-2 w-full max-w-lg">
              {EXAMPLE_QUERIES.map((q, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(q)}
                  className="text-left px-4 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 text-sm text-slate-300 hover:bg-slate-700/60 hover:border-slate-600 transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-industrial-900 border border-industrial-700/50 flex items-center justify-center shrink-0 mt-0.5">
                <Brain size={16} className="text-industrial-400" />
              </div>
            )}
            <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-industrial-600 text-white rounded-tr-sm'
                    : 'bg-slate-800 text-slate-200 rounded-tl-sm'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className={`prose prose-invert prose-sm max-w-none ${msg.streaming && !msg.content ? 'cursor-blink' : ''}`}>
                    <ReactMarkdown>{msg.content || ''}</ReactMarkdown>
                    {msg.streaming && msg.content && <span className="cursor-blink" />}
                  </div>
                ) : (
                  msg.content
                )}
              </div>
              {msg.role === 'assistant' && !msg.streaming && (
                <div className="mt-1.5 px-1 space-y-1.5">
                  {msg.confidence !== undefined && (
                    <ConfidenceBadge score={msg.confidence} />
                  )}
                  {msg.citations && <SourceCitations citations={msg.citations} />}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-slate-800 p-4">
        <div className="flex gap-2 items-end bg-slate-800 rounded-2xl border border-slate-700 focus-within:border-industrial-500 transition-colors p-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about equipment, maintenance, safety procedures..."
            rows={1}
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 resize-none outline-none px-2 py-1 max-h-32 scrollbar-thin"
            style={{ minHeight: '36px' }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="w-9 h-9 rounded-xl bg-industrial-600 hover:bg-industrial-500 disabled:bg-slate-700 disabled:cursor-not-allowed flex items-center justify-center transition-colors shrink-0"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin text-slate-400" />
            ) : (
              <Send size={16} className="text-white" />
            )}
          </button>
        </div>
        <p className="text-xs text-slate-600 text-center mt-2">
          Answers drawn from ingested documents only · Always verify safety-critical information
        </p>
      </div>
    </div>
  )
}

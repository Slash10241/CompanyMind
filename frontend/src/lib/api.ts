const BASE = '/api'

export interface DocumentMeta {
  id: string
  name: string
  doc_type: string
  file_path: string
  upload_time: string
  chunk_count: number
  entity_count: number
  page_count: number
}

export interface IngestionResult {
  doc_id: string
  doc_name: string
  chunk_count: number
  entity_count: number
  graph_nodes_added: number
  graph_edges_added: number
}

export interface SourceCitation {
  doc_id: string
  doc_name: string
  page_number: number
  snippet: string
  relevance_score: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface GraphNode {
  id: string
  label: string
  type: string
  doc_count: number
  color: string
}

export interface GraphEdge {
  source: string
  target: string
  weight: number
  relation: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface HealthData {
  status: string
  graph_nodes: number
  graph_edges: number
  total_chunks: number
}

export async function uploadDocuments(files: File[]): Promise<IngestionResult[]> {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  const res = await fetch(`${BASE}/ingest`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function listDocuments(): Promise<DocumentMeta[]> {
  const res = await fetch(`${BASE}/documents`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getGraphData(entity?: string): Promise<GraphData> {
  const url = entity
    ? `${BASE}/graph/entity/${encodeURIComponent(entity)}`
    : `${BASE}/graph`
  const res = await fetch(url)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getHealth(): Promise<HealthData> {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function streamChat(
  query: string,
  history: ChatMessage[],
  onToken: (text: string) => void,
  onMeta: (confidence: number, citations: SourceCitation[]) => void,
  onDone: () => void,
  onError: (err: string) => void,
) {
  fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history }),
  }).then(async (res) => {
    if (!res.ok) {
      onError(await res.text())
      return
    }
    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'metadata') {
            onMeta(event.confidence, event.citations)
          } else if (event.type === 'token') {
            onToken(event.text)
          } else if (event.type === 'done') {
            onDone()
          }
        } catch {
          // skip malformed events
        }
      }
    }
    onDone()
  }).catch(e => onError(String(e)))
}

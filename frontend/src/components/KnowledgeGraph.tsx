import { useEffect, useRef, useState, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { RefreshCw, Search, Info, Zap } from 'lucide-react'
import { getGraphData, type GraphData } from '../lib/api'

const ENTITY_ICONS: Record<string, string> = {
  EQUIPMENT_TAG: '⚙',
  PERSON: '👤',
  DATE: '📅',
  REGULATION: '📋',
  PARAMETER: '📊',
  LOCATION: '📍',
  FAILURE_MODE: '⚠',
}

const LEGEND = [
  { type: 'EQUIPMENT_TAG', color: '#3B82F6', label: 'Equipment' },
  { type: 'PERSON',        color: '#10B981', label: 'Personnel' },
  { type: 'DATE',          color: '#F59E0B', label: 'Date' },
  { type: 'REGULATION',    color: '#EF4444', label: 'Regulation' },
  { type: 'PARAMETER',     color: '#8B5CF6', label: 'Parameter' },
  { type: 'LOCATION',      color: '#F97316', label: 'Location' },
  { type: 'FAILURE_MODE',  color: '#EC4899', label: 'Failure Mode' },
  { type: 'ORDER_ID',      color: '#06B6D4', label: 'Order / Invoice' },
  { type: 'PRODUCT',       color: '#84CC16', label: 'Product / Material' },
  { type: 'ORGANISATION',  color: '#00529F', label: 'Organisation' },
]

export function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphData['nodes'][0] | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dims, setDims] = useState({ width: 800, height: 600 })
  const [rebuilding, setRebuilding] = useState(false)
  const [rebuildProgress, setRebuildProgress] = useState<{ processed: number; total: number; nodes: number } | null>(null)

  const load = useCallback(async (entity?: string) => {
    setLoading(true)
    try {
      const data = await getGraphData(entity)
      setGraphData({ nodes: data.nodes, edges: data.edges })
    } catch {
      setGraphData({ nodes: [], edges: [] })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    const obs = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setDims({ width, height: Math.max(height, 400) })
    })
    if (containerRef.current) obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (search.trim()) load(search.trim())
    else load()
  }

  const handleRebuild = async () => {
    setRebuilding(true)
    setRebuildProgress({ processed: 0, total: 0, nodes: 0 })
    try {
      const res = await fetch('/api/graph/rebuild', { method: 'POST' })
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = JSON.parse(line.slice(6))
          if (payload.done) { await load(); break }
          setRebuildProgress({ processed: payload.processed, total: payload.total, nodes: payload.nodes ?? 0 })
        }
      }
    } finally {
      setRebuilding(false)
      setRebuildProgress(null)
    }
  }

  const fgData = {
    nodes: graphData.nodes.map(n => ({
      ...n,
      id: n.id,
      name: n.label,
      color: n.color,
      val: Math.max(1, n.doc_count * 2),
    })),
    links: graphData.edges.map(e => ({
      source: e.source,
      target: e.target,
      value: e.weight,
    })),
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Controls */}
      <div className="px-4 py-3 border-b border-rm-gray-light flex items-center gap-3 flex-wrap bg-white">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1 min-w-0">
          <div className="relative flex-1 min-w-0">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-rm-gray" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Filter by entity (e.g. P-101, OISD)"
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-rm-gray-ultra border border-rm-gray-light text-sm text-rm-text placeholder-rm-gray outline-none focus:border-rm-navy transition-colors"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-rm-navy hover:bg-rm-navy-dark text-white text-sm transition-colors"
          >
            Filter
          </button>
          {search && (
            <button
              type="button"
              onClick={() => { setSearch(''); load() }}
              className="px-3 py-1.5 rounded-xl bg-rm-gray-ultra hover:bg-rm-gray-light text-rm-text text-sm transition-colors"
            >
              All
            </button>
          )}
        </form>
        <button onClick={() => load()} className="text-rm-gray hover:text-rm-navy transition-colors">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
        </button>
        <span className="text-xs text-rm-gray shrink-0">
          {graphData.nodes.length} nodes · {graphData.edges.length} edges
        </span>
      </div>

      {/* Graph canvas */}
      <div ref={containerRef} className="flex-1 relative bg-rm-cream">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-rm-cream/70">
            <RefreshCw size={24} className="animate-spin text-rm-navy" />
          </div>
        )}
        {!loading && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-rm-gray gap-4">
            <Info size={32} className="opacity-30" />
            <div className="text-center">
              <p className="text-sm font-medium text-rm-text">Knowledge graph is empty</p>
              <p className="text-xs mt-1">Entity extraction may not have run during ingestion</p>
            </div>
            {rebuildProgress && (
              <div className="text-center">
                <p className="text-xs text-rm-navy font-medium">
                  Extracting entities… {rebuildProgress.processed}/{rebuildProgress.total} docs · {rebuildProgress.nodes} nodes so far
                </p>
                <div className="mt-2 w-48 h-1.5 bg-rm-gray-light rounded-full overflow-hidden">
                  <div
                    className="h-full bg-rm-navy rounded-full transition-all"
                    style={{ width: rebuildProgress.total ? `${(rebuildProgress.processed / rebuildProgress.total) * 100}%` : '0%' }}
                  />
                </div>
              </div>
            )}
            {!rebuilding && (
              <button
                onClick={handleRebuild}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rm-navy hover:bg-rm-navy-dark text-white text-sm font-medium transition-colors"
              >
                <Zap size={14} />
                Build Knowledge Graph
              </button>
            )}
            {rebuilding && !rebuildProgress && (
              <RefreshCw size={16} className="animate-spin text-rm-navy" />
            )}
          </div>
        )}
        {graphData.nodes.length > 0 && (
          <ForceGraph2D
            width={dims.width}
            height={dims.height}
            graphData={fgData}
            nodeLabel={(n: any) =>
              `${ENTITY_ICONS[n.type] || '●'} ${n.name} (${n.type?.replace('_', ' ')} · ${n.doc_count} doc${n.doc_count !== 1 ? 's' : ''})`
            }
            nodeColor={(n: any) => n.color || '#6B7280'}
            nodeVal={(n: any) => n.val || 2}
            linkWidth={(l: any) => Math.min(Math.sqrt(l.value || 1), 4)}
            linkColor={() => 'rgba(0,82,159,0.15)'}
            backgroundColor="#F8F8F6"
            onNodeClick={(node: any) => setSelectedNode(node)}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.name || ''
              const fontSize = Math.max(10, 12 / globalScale)
              const r = Math.max(4, (node.val || 2) * 1.5)

              ctx.beginPath()
              ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false)
              ctx.fillStyle = node.color || '#6B7280'
              ctx.fill()

              if (globalScale > 1.5) {
                ctx.font = `${fontSize}px sans-serif`
                ctx.fillStyle = 'rgba(26,39,68,0.85)'
                ctx.textAlign = 'center'
                ctx.textBaseline = 'middle'
                ctx.fillText(label.slice(0, 20), node.x, node.y + r + fontSize * 0.8)
              }
            }}
          />
        )}
      </div>

      {/* Selected node panel */}
      {selectedNode && (
        <div className="border-t border-rm-gray-light bg-white px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span style={{ color: selectedNode.color }} className="text-lg shrink-0">
              {ENTITY_ICONS[selectedNode.type] || '●'}
            </span>
            <div className="min-w-0">
              <p className="text-sm text-rm-text font-semibold truncate">{selectedNode.label}</p>
              <p className="text-xs text-rm-gray">
                {selectedNode.type?.replace('_', ' ')} · {selectedNode.doc_count} document{selectedNode.doc_count !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <button
            onClick={() => { setSearch(selectedNode.label); load(selectedNode.label) }}
            className="px-3 py-1.5 rounded-lg bg-rm-navy hover:bg-rm-navy-dark text-white text-xs shrink-0 transition-colors"
          >
            Subgraph
          </button>
        </div>
      )}

      {/* Legend */}
      <div className="border-t border-rm-gray-light bg-white px-4 py-2.5">
        <div className="flex flex-wrap gap-x-4 gap-y-1.5">
          {LEGEND.map(l => (
            <div key={l.type} className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: l.color }} />
              <span className="text-xs text-rm-gray">{l.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

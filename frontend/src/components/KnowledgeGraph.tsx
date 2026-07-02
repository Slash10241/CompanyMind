import { useEffect, useRef, useState, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { RefreshCw, Search, Info } from 'lucide-react'
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
  { type: 'PERSON', color: '#10B981', label: 'Personnel' },
  { type: 'DATE', color: '#F59E0B', label: 'Date' },
  { type: 'REGULATION', color: '#EF4444', label: 'Regulation' },
  { type: 'PARAMETER', color: '#8B5CF6', label: 'Parameter' },
  { type: 'LOCATION', color: '#F97316', label: 'Location' },
  { type: 'FAILURE_MODE', color: '#EC4899', label: 'Failure Mode' },
  { type: 'ORDER_ID', color: '#06B6D4', label: 'Order / Invoice' },
  { type: 'PRODUCT', color: '#84CC16', label: 'Product / Material' },
  { type: 'ORGANISATION', color: '#A78BFA', label: 'Organisation' },
]

export function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphData['nodes'][0] | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dims, setDims] = useState({ width: 800, height: 600 })

  const load = useCallback(async (entity?: string) => {
    setLoading(true)
    try {
      const data = await getGraphData(entity)
      // Transform edges to use source/target as node ids (react-force-graph expects this)
      setGraphData({
        nodes: data.nodes,
        edges: data.edges,
      })
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

  // Build graph-compatible format
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
    <div className="flex flex-col h-full">
      {/* Controls */}
      <div className="p-4 border-b border-slate-800 flex items-center gap-3 flex-wrap">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1 min-w-0">
          <div className="relative flex-1 min-w-0">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Filter by entity (e.g. P-101, OISD)"
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-industrial-500 transition-colors"
            />
          </div>
          <button type="submit" className="px-3 py-2 rounded-xl bg-industrial-600 hover:bg-industrial-500 text-white text-sm transition-colors">
            Filter
          </button>
          {search && (
            <button type="button" onClick={() => { setSearch(''); load() }} className="px-3 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-sm transition-colors">
              All
            </button>
          )}
        </form>
        <button onClick={() => load()} className="text-slate-500 hover:text-slate-300 transition-colors">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
        <span className="text-xs text-slate-500 shrink-0">
          {graphData.nodes.length} nodes · {graphData.edges.length} edges
        </span>
      </div>

      {/* Graph */}
      <div ref={containerRef} className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-slate-950/50">
            <RefreshCw size={24} className="animate-spin text-slate-400" />
          </div>
        )}
        {!loading && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 gap-3">
            <Info size={32} className="opacity-40" />
            <p className="text-sm">No knowledge graph data yet</p>
            <p className="text-xs">Ingest documents to build the graph</p>
          </div>
        )}
        {graphData.nodes.length > 0 && (
          <ForceGraph2D
            width={dims.width}
            height={dims.height}
            graphData={fgData}
            nodeLabel={(n: any) => `${ENTITY_ICONS[n.type] || '●'} ${n.name} (${n.type?.replace('_', ' ')} · ${n.doc_count} doc${n.doc_count !== 1 ? 's' : ''})`}
            nodeColor={(n: any) => n.color || '#6B7280'}
            nodeVal={(n: any) => n.val || 2}
            linkWidth={(l: any) => Math.min(Math.sqrt(l.value || 1), 4)}
            linkColor={() => 'rgba(100,116,139,0.3)'}
            backgroundColor="#020617"
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
                ctx.fillStyle = 'rgba(226,232,240,0.9)'
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
        <div className="border-t border-slate-800 p-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span style={{ color: selectedNode.color }} className="text-lg shrink-0">
              {ENTITY_ICONS[selectedNode.type] || '●'}
            </span>
            <div className="min-w-0">
              <p className="text-sm text-slate-200 font-medium truncate">{selectedNode.label}</p>
              <p className="text-xs text-slate-500">{selectedNode.type?.replace('_', ' ')} · {selectedNode.doc_count} document{selectedNode.doc_count !== 1 ? 's' : ''}</p>
            </div>
          </div>
          <button
            onClick={() => { setSearch(selectedNode.label); load(selectedNode.label) }}
            className="px-3 py-1.5 rounded-lg bg-industrial-700 hover:bg-industrial-600 text-white text-xs shrink-0 transition-colors"
          >
            Subgraph
          </button>
        </div>
      )}

      {/* Legend */}
      <div className="border-t border-slate-800 p-3">
        <div className="flex flex-wrap gap-x-4 gap-y-1.5">
          {LEGEND.map(l => (
            <div key={l.type} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: l.color }} />
              <span className="text-xs text-slate-400">{l.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

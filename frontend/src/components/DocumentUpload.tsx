import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, AlertCircle, Loader2, FileText, X } from 'lucide-react'
import { uploadDocuments, type IngestionResult } from '../lib/api'

interface Props {
  onComplete: () => void
}

export function DocumentUpload({ onComplete }: Props) {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState<IngestionResult[]>([])
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...accepted.filter(f => !names.has(f.name))]
    })
    setResults([])
    setError(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'text/markdown': ['.md'],
    },
    multiple: true,
  })

  const removeFile = (name: string) => {
    setFiles(prev => prev.filter(f => f.name !== name))
  }

  const handleUpload = async () => {
    if (!files.length) return
    setUploading(true)
    setError(null)
    try {
      const res = await uploadDocuments(files)
      setResults(res)
      setFiles([])
      onComplete()
    } catch (e) {
      setError(String(e))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-industrial-500 bg-industrial-900/20'
            : 'border-slate-700 hover:border-slate-600 bg-slate-800/30'
        }`}
      >
        <input {...getInputProps()} />
        <Upload size={32} className="mx-auto mb-3 text-slate-500" />
        <p className="text-sm text-slate-300 font-medium">
          {isDragActive ? 'Drop files here' : 'Drag & drop industrial documents'}
        </p>
        <p className="text-xs text-slate-500 mt-1">PDF, TXT, CSV, MD — up to 50 MB each</p>
      </div>

      {/* Selected files */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map(f => (
            <div key={f.name} className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50">
              <FileText size={16} className="text-slate-400 shrink-0" />
              <span className="text-sm text-slate-300 truncate flex-1">{f.name}</span>
              <span className="text-xs text-slate-500 shrink-0">{(f.size / 1024).toFixed(0)} KB</span>
              <button onClick={() => removeFile(f.name)} className="text-slate-600 hover:text-slate-400">
                <X size={14} />
              </button>
            </div>
          ))}

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full py-2.5 rounded-xl bg-industrial-600 hover:bg-industrial-500 disabled:bg-slate-700 text-white text-sm font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {uploading ? (
              <><Loader2 size={16} className="animate-spin" /> Ingesting & building knowledge graph...</>
            ) : (
              <><Upload size={16} /> Ingest {files.length} document{files.length > 1 ? 's' : ''}</>
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex gap-2 p-3 rounded-xl bg-red-900/20 border border-red-800/50 text-red-300 text-sm">
          <AlertCircle size={16} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Ingestion Results</p>
          {results.map(r => (
            <div key={r.doc_id} className="flex items-start gap-3 p-3 rounded-xl bg-emerald-900/20 border border-emerald-800/30">
              <CheckCircle size={16} className="text-emerald-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 truncate font-medium">{r.doc_name}</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {r.chunk_count} chunks · {r.entity_count} entities · +{r.graph_nodes_added} graph nodes · +{r.graph_edges_added} edges
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

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
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-rm-gold bg-amber-50'
            : 'border-rm-gray-light hover:border-rm-navy bg-rm-gray-ultra'
        }`}
      >
        <input {...getInputProps()} />
        <Upload size={24} className={`mx-auto mb-2 ${isDragActive ? 'text-rm-gold' : 'text-rm-gray'}`} />
        <p className="text-sm text-rm-text font-medium">
          {isDragActive ? 'Drop files here' : 'Drag & drop documents'}
        </p>
        <p className="text-xs text-rm-gray mt-0.5">PDF, TXT, CSV, MD</p>
      </div>

      {/* Selected files */}
      {files.length > 0 && (
        <div className="space-y-1.5">
          {files.map(f => (
            <div key={f.name} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-rm-gray-light">
              <FileText size={14} className="text-rm-gray shrink-0" />
              <span className="text-xs text-rm-text truncate flex-1">{f.name}</span>
              <span className="text-xs text-rm-gray shrink-0">{(f.size / 1024).toFixed(0)} KB</span>
              <button onClick={() => removeFile(f.name)} className="text-rm-gray hover:text-rm-text transition-colors">
                <X size={13} />
              </button>
            </div>
          ))}

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full py-2 rounded-xl bg-rm-navy hover:bg-rm-navy-dark disabled:bg-rm-gray-light disabled:cursor-not-allowed text-white text-sm font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {uploading ? (
              <><Loader2 size={14} className="animate-spin" /> Building knowledge graph...</>
            ) : (
              <><Upload size={14} /> Ingest {files.length} document{files.length > 1 ? 's' : ''}</>
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex gap-2 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs text-rm-gray font-semibold uppercase tracking-wider">Ingestion Results</p>
          {results.map(r => (
            <div key={r.doc_id} className="flex items-start gap-2 p-2.5 rounded-xl bg-emerald-50 border border-emerald-200">
              <CheckCircle size={14} className="text-emerald-600 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-rm-text truncate font-medium">{r.doc_name}</p>
                <p className="text-xs text-rm-gray mt-0.5">
                  {r.chunk_count} chunks · {r.entity_count} entities · +{r.graph_nodes_added} nodes
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

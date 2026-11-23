import { useEffect, useState } from 'react'

const get = (u) => fetch(u).then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${u}: ${r.status}`))))
const fmt = (v) => (typeof v === 'number' ? (Math.abs(v) <= 1 ? v.toFixed(3) : v.toLocaleString()) : String(v))

export default function App() {
  const [metrics, setMetrics] = useState(null)
  const [figs, setFigs] = useState([])
  const [tables, setTables] = useState({})
  const [tab, setTab] = useState('Overview')
  const [error, setError] = useState('')
  useEffect(() => {
    get('/api/metrics').then(setMetrics).catch((e) => setError(e.message))
    get('/api/figures').then(setFigs).catch(() => {})
    get('/api/tables').then(setTables).catch(() => {})
  }, [])
  return (
    <div className="max-w-6xl mx-auto p-4 space-y-4">
      <h1 className="text-xl font-semibold">Results dashboard</h1>
      <div className="flex gap-2 border-b">{['Overview', 'Figures', 'Tables'].map((t) => (
        <button key={t} onClick={() => setTab(t)} className={`px-3 py-1.5 text-sm ${tab === t ? 'border-b-2 border-indigo-600 text-indigo-700 font-medium' : 'text-slate-600'}`}>{t}</button>))}</div>
      {error && <div className="bg-amber-50 border border-amber-300 text-amber-800 text-sm rounded p-2">{error}. Run <code>scripts/run_pipeline.sh</code> and start the backend with <code>scripts/run_app.sh</code>.</div>}
      {tab === 'Overview' && metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(metrics.headline || {}).map(([k, v]) => (
            <div key={k} className="bg-white border rounded-lg p-3"><div className="text-xs text-slate-500">{k}</div><div className="text-2xl font-semibold">{fmt(v)}</div></div>))}
        </div>)}
      {tab === 'Figures' && (
        <div className="grid md:grid-cols-2 gap-4">
          {figs.map((f) => (
            <figure key={f.name} className="bg-white border rounded-lg p-3"><img src={f.url} alt={f.name} className="w-full" />
              <figcaption className="text-sm text-slate-600 mt-2 whitespace-pre-wrap">{f.explanation || f.name}</figcaption></figure>))}
          {!figs.length && <div className="text-sm text-slate-500">No figures yet.</div>}
        </div>)}
      {tab === 'Tables' && Object.entries(tables).map(([name, rows]) => (
        <div key={name} className="bg-white border rounded-lg p-3 overflow-x-auto"><div className="font-medium text-sm mb-2">{name}</div>
          <table className="text-sm w-full"><thead><tr>{rows[0]?.map((h) => <th key={h} className="text-left px-2 py-1 bg-slate-100">{h}</th>)}</tr></thead>
            <tbody>{rows.slice(1).map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j} className="px-2 py-1 border-t">{c}</td>)}</tr>)}</tbody></table></div>))}
    </div>
  )
}

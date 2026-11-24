import React, { useState } from 'react'
import { Search, ShieldAlert } from 'lucide-react'
import { size, when } from './api.js'

export default function ActivityResults({ rows, synthetic = false }) {
  const [query, setQuery] = useState(''), [filter, setFilter] = useState('all')
  const source = synthetic ? 'sample activity' : 'real activity'
  const filtered = rows.filter(row => `${row.actor} ${row.signals}`.toLowerCase().includes(query.trim().toLowerCase()) && (filter === 'all' || (filter === 'review' ? row.anomalous : !row.anomalous)))
    .sort((a,b) => b.start - a.start)
  return <div className="activity-results">
    <div className="activity-controls"><label className="search-field"><Search size={17}/><input aria-label={'Search ' + source} placeholder="Search actor or signal…" value={query} onChange={e=>setQuery(e.target.value)}/></label><select aria-label={'Filter ' + source} value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All windows</option><option value="review">Needs review</option><option value="normal">Within baseline</option></select><span className="subtle" role="status">{filtered.length} of {rows.length} windows</span></div>
    {!filtered.length ? <div className="empty"><ShieldAlert size={28}/><h3>No matching activity</h3><p>{rows.length ? 'Change the actor search or review filter.' : 'Completed activity windows will appear here after analysis.'}</p>{rows.length > 0 && <button className="btn" onClick={()=>{setQuery('');setFilter('all')}}>Clear filters</button>}</div> : <div className="table-scroll"><table className="activity-table"><caption className="sr-only">{synthetic ? 'Synthetic demonstration windows' : 'Analyzed vault activity windows'}</caption><thead><tr><th scope="col">ACTOR / WINDOW</th><th scope="col">ASSESSMENT</th><th scope="col">DOWNLOADS</th><th scope="col">FAILED LOGINS</th><th scope="col">DENIED</th><th scope="col">EVIDENCE</th></tr></thead><tbody>{filtered.map((row,i)=><tr key={`${row.actor}-${row.start}-${i}`}>
      <td><strong>{row.actor}</strong><small className="activity-window">{synthetic ? `Sample window ${Math.floor(row.start / 300)}` : when(row.start)}<br/>{synthetic ? 'Synthetic · 5 minutes' : `to ${when(row.start + 300)}`}</small></td>
      <td><span className={'tag tag-' + (row.anomalous ? 'red' : 'green')}>{row.anomalous ? 'REVIEW ACTIVITY' : 'WITHIN BASELINE'}</span></td><td className="mono">{row.downloads}</td><td className="mono">{row.failed_logins}</td><td className="mono">{row.denied_actions}</td>
      <td><details className="activity-evidence"><summary>Inspect evidence</summary><div><p>{row.signals}</p><dl><div><dt>Transferred</dt><dd>{size(row.download_bytes)}</dd></div><div><dt>Distinct files</dt><dd>{row.distinct_files}</dd></div><div><dt>Decision score</dt><dd className="mono">{row.decision_score}</dd></div></dl></div></details></td>
    </tr>)}</tbody></table></div>}
    <p className="score-explanation">Negative scores indicate model outliers, not attack probabilities. Signals compare observed counts with baseline medians; review the audit trail before taking action.</p>
  </div>
}

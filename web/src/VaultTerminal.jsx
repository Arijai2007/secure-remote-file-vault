import React, { useEffect, useState } from 'react'
import { Check, FileText, Fingerprint, KeyRound, LockKeyhole, Pause, Play, RotateCcw } from 'lucide-react'

const steps = [
  [FileText, 'Validate access', 'Role and upload permissions checked', 'RBAC'],
  [LockKeyhole, 'Encrypt file', 'A fresh key for every upload', 'AES-256-GCM'],
  [KeyRound, 'Wrap the key', 'Protect the file key with the vault public key', 'RSA-OAEP'],
  [Fingerprint, 'Verify on retrieval', 'Authenticate and compare the plaintext digest', 'SHA-256'],
]

export default function VaultTerminal({ compact = false }) {
  const [reduced, setReduced] = useState(() => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? true)
  const [step, setStep] = useState(() => reduced ? steps.length : 0)
  const [paused, setPaused] = useState(false)
  const completed = reduced ? steps.length : step

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-reduced-motion: reduce)')
    const change = event => { setReduced(event.matches); if (event.matches) setStep(steps.length) }
    media?.addEventListener('change', change)
    return () => media?.removeEventListener('change', change)
  }, [])

  useEffect(() => {
    if (reduced || paused || step >= steps.length) return
    const timer = setTimeout(() => setStep(value => value + 1), 900)
    return () => clearTimeout(timer)
  }, [step, paused, reduced])

  return <section className={'vault-terminal' + (compact ? ' compact' : '')} aria-label="Illustrative file protection walkthrough">
    <div className="terminal-bar"><span className="terminal-lights" aria-hidden="true"><i/><i/><i/></span><span className="mono">vault / file-protection</span><span className="terminal-sample">SAMPLE</span></div>
    <div className="terminal-command mono"><span>$</span> vault.protect <span className="terminal-filename">project-notes.pdf</span></div>
    <div className="terminal-file"><span className="terminal-file-icon"><FileText size={23}/></span><div><strong>project-notes.pdf</strong><span>Sample document · private access</span></div><LockKeyhole size={17}/></div>
    <ol className="terminal-steps">{steps.map(([Icon, title, detail, protocol], index) => <li key={title} className={index < completed ? 'done' : index === completed ? 'current' : ''}>
      <span className="terminal-step-icon">{index < completed ? <Check size={17}/> : <Icon size={17}/>}</span><div><strong>{title}</strong><small>{detail}</small></div><code>{protocol}</code>
    </li>)}</ol>
    <div className="terminal-result"><span className="mono"><span className="live-dot"/> {completed === 4 ? 'Walkthrough complete' : paused ? 'Walkthrough paused' : 'File protection sequence'}</span><span className="mono">{completed} / 4</span></div>
    <footer className="terminal-footer"><span>Illustrative walkthrough · no file is processed</span>{!reduced && <button className="terminal-control" aria-label={step === 4 ? 'Replay walkthrough' : paused ? 'Resume walkthrough' : 'Pause walkthrough'} onClick={() => step === 4 ? (setStep(0), setPaused(false)) : setPaused(value => !value)}>{step === 4 ? <RotateCcw size={14}/> : paused ? <Play size={14}/> : <Pause size={14}/>}<span>{step === 4 ? 'Replay' : paused ? 'Resume' : 'Pause'}</span></button>}</footer>
  </section>
}

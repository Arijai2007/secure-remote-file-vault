import React from 'react'

// Presentation examples only. These are deliberately not benchmark timings.
const approaches = [
  { name: 'RSA', tone: 'rsa', wrap: 1, unwrap: 1 },
  { name: 'ML-KEM', tone: 'mlkem', wrap: .18, unwrap: .16 },
  { name: 'RSA + ML-KEM', tone: 'hybrid', wrap: .20, unwrap: .18 },
]

function Figure({ title, metric }) {
  return <figure className="crypto-figure"><figcaption>{title}<span>Illustrative index · lower is less work</span></figcaption>
    <div className="crypto-bars">{approaches.map(item => <div className="crypto-bar-row" key={item.name}>
      <span>{item.name}</span><div className="crypto-track"><div className={'crypto-bar ' + item.tone} style={{ width: `${item[metric] * 100}%` }}/></div><strong className="mono">{item[metric].toFixed(2)}</strong>
    </div>)}</div><div className="crypto-axis mono"><span>0</span><span>0.5</span><span>1.0</span></div>
  </figure>
}

export default function CryptoComparison() {
  return <div className="crypto-comparison">
    <div className="comparison-heading"><div><h2>Three approaches. One protected file.</h2><p>Compare classical RSA, post-quantum ML-KEM, and a combined approach to protecting file keys.</p></div><span className="tag tag-cyan">RSA ACTIVE</span></div>
    <p className="comparison-context">CipherVault currently encrypts files with AES-256-GCM and wraps each file key with RSA-3072 OAEP. ML-KEM and the combined approach below are architecture comparisons.</p>
    <div className="crypto-figures"><Figure title="Protecting a file key" metric="wrap"/><Figure title="Recovering a file key" metric="unwrap"/></div>
    <p className="comparison-caption">Illustrative performance indices — example values for visual comparison, not measured timings or speedup claims. RSA is normalized to 1.00; the combined example is placed close to ML-KEM. Actual cost depends on implementation, hardware, and how both algorithms are combined.</p>
    <div className="table-scroll"><table className="comparison-table"><caption>File-key protection approaches</caption><thead><tr><th scope="col">Capability</th><th scope="col">RSA</th><th scope="col">ML-KEM</th><th scope="col">RSA + ML-KEM</th></tr></thead><tbody>
      <tr><th scope="row">Role</th><td>Wraps a file key with RSA-OAEP</td><td>Establishes a shared secret for key protection</td><td>Combines classical and ML-KEM key material</td></tr>
      <tr><th scope="row">Security foundation</th><td>Integer factorization</td><td>Module Learning with Errors</td><td>Classical + lattice assumptions</td></tr>
      <tr><th scope="row">Post-quantum design</th><td>No</td><td>Yes</td><td>Depends on a secure combiner and protocol</td></tr>
      <tr><th scope="row">File encryption</th><td>AES-256-GCM</td><td>AES-256-GCM in the proposed design</td><td>AES-256-GCM in the proposed design</td></tr>
      <tr><th scope="row">Vault integration</th><td><span className="tag tag-green">Active in this vault</span></td><td>Comparison option</td><td>Comparison option</td></tr>
      <tr><th scope="row">Protection index (illustrative)</th>{approaches.map(item=><td className="mono" key={item.name}>{item.wrap.toFixed(2)}</td>)}</tr>
      <tr><th scope="row">Recovery index (illustrative)</th>{approaches.map(item=><td className="mono" key={item.name}>{item.unwrap.toFixed(2)}</td>)}</tr>
    </tbody></table></div>
    <p className="comparison-source">ML-KEM reference: <a href="https://csrc.nist.gov/pubs/fips/203/final" target="_blank" rel="noreferrer">NIST FIPS 203 <span aria-hidden="true">↗</span></a>. Combining algorithms requires a defined key derivation and authenticated protocol; it is not achieved by simply selecting both names.</p>
  </div>
}

"""Small, escaped presentation helpers; all actions remain native Streamlit widgets."""
from html import escape
from pathlib import Path
from base64 import b64encode

import streamlit as st
import streamlit.components.v1 as components


def load_styles():
    root = Path(__file__).parent
    fonts = ''.join(
        '@font-face{font-family:"' + family + '";font-style:normal;font-weight:100 900;'
        'font-display:swap;src:url(data:font/woff2;base64,' + b64encode(path.read_bytes()).decode() + ') format("woff2");}'
        for family, path in [('Space Grotesk', root / 'assets/space-grotesk.woff2'),
                             ('Inter', root / 'assets/inter.woff2'),
                             ('JetBrains Mono', root / 'assets/jetbrains-mono.woff2')]
        if path.exists())
    st.html('<style>' + fonts + root.joinpath('ui.css').read_text(encoding='utf-8') + '</style>')


def brand():
    st.html('''<div class="brand-line"><span class="brand-symbol">'''+ icon('lock') +'''</span>
      <div><div class="brand-word">CipherVault</div><div class="brand-sub">SECURE FILE WORKSPACE</div></div></div>''')


def icon(name):
    paths = {'lock': '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
             'file': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
             'shield': '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6Z"/><path d="m8 12 3 3 5-6"/>'}
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#8aebff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' + paths[name] + '</svg>'
    return '<img alt="" width="24" height="24" src="data:image/svg+xml;base64,' + b64encode(svg.encode()).decode() + '">'


def signin_art():
    st.html('''<section class="signin-story"><h2>Your files. <em>Encrypted.</em><br>Under control.</h2>
      <p>Secure storage, deliberate access, and a record of every action across your workspace.</p></section>''')
    assets = Path(__file__).parent / 'assets'
    # This isolated scene receives no credentials, session token or vault data.
    components.html('''<!doctype html><html lang="en"><head><meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <style>*{box-sizing:border-box}body{margin:0;background:#121c30;color:#dee2f6;font:12px monospace}
      #vault-scene{width:100%;height:320px;background:radial-gradient(ellipse at center,#17344c,#121c30 65%);border:1px solid #30394e;border-radius:18px;overflow:hidden}
      canvas{display:block}button{position:absolute;right:14px;bottom:14px;padding:8px 10px;border-radius:8px;border:1px solid #51647c;background:#090e1c;color:#a2eeff;cursor:pointer}
      button:focus-visible{outline:2px solid #22d3ee;outline-offset:3px}.label{position:absolute;top:14px;left:14px;color:#8aebff;pointer-events:none}
      #fallback{position:absolute;inset:100px 20px;text-align:center;font:16px sans-serif;color:#a2eeff}
      </style></head><body><div id="vault-scene" role="img" aria-label="Illustrative 3D encrypted vault with orbiting rings and document tiles"></div>
      <span class="label">AES-256-GCM · RSA-3072 OAEP</span><p id="fallback" hidden>Encrypted storage<br><br>AES-256-GCM / RSA-3072 OAEP</p>
      <button id="motion-toggle" type="button">Pause animation</button><script>''' +
      assets.joinpath('three.min.js').read_text(encoding='utf-8') + '</script><script>' +
      assets.joinpath('vault-scene.js').read_text(encoding='utf-8') + '</script></body></html>', height=320, scrolling=False)
    st.html('''<section class="signin-story"><div class="protocol-strip"><span>AES-256-GCM<small>Encrypted storage</small></span>
      <span>Six-digit TOTP<small>Two-factor sign-in</small></span><span>Role-based access<small>Admin / Employee / Guest</small></span></div>
      <p class="signin-note">No public signup. No third-party trackers. Your administrator controls workspace access.</p></section>''')


def workspace_identity(username, role):
    st.html(f'<div class="workspace-identity"><span>{icon("shield")} Password + TOTP authenticated</span>'
            f'<div><strong>{escape(username)}</strong><span class="file-badge team">{escape(role)}</span></div></div>')


def inspector_metadata(file, timestamp):
    st.html(f'<div class="inspector-heading">{icon("shield")}<h3>Cryptographic Inspector</h3></div>')
    st.caption('Stored metadata · verify integrity to check current file content.')
    rows = [('Filename', file['name']), ('File ID', file['id']), ('Owner', file['uploaded_by']),
            ('Original size', format_size(file['size'])), ('Encryption', 'AES-256-GCM'),
            ('Key wrapping', 'RSA-3072 OAEP'), ('Uploaded', timestamp)]
    st.html('<dl class="inspector-metadata">' + ''.join(
        f'<div><dt>{escape(label)}</dt><dd>{escape(str(value))}</dd></div>' for label, value in rows) + '</dl>')


def banner(kicker, title, description, tag='PRIVATE BY DESIGN'):
    st.html(f'''<div class="workspace-banner"><div class="banner-content">
      <div class="eyebrow">{escape(kicker)}</div><h2>{escape(title)}</h2>
      <p>{escape(description)}</p><span class="banner-tag"><i></i>{escape(tag)}</span>
      </div><div class="vault-art" aria-hidden="true"><div class="orbit orbit-one"></div>
      <div class="orbit orbit-two"></div><div class="lock-tile">
      <div class="lock-shape"><div class="lock-shackle"></div><div class="lock-body"><i></i></div></div>
      </div><span class="art-spark spark-one">+</span><span class="art-spark spark-two">+</span></div></div>''')


def eyebrow(text):
    st.html(f'<div class="section-eyebrow">{escape(text)}</div>')


def empty_state(title, description):
    st.html(f'<div class="empty-state"><div class="empty-icon">{icon("file")}</div><h3>{escape(title)}</h3><p>{escape(description)}</p></div>')


def protection_card(number, title, description):
    st.html(f'<div class="protection-card"><span>{escape(number)}</span><h4>{escape(title)}</h4><p>{escape(description)}</p></div>')


def file_heading(name, kind, shared):
    st.html(f'<div class="file-heading"><span class="file-icon">{icon("file")}</span>'
            f'<div class="file-heading-text"><h3>{escape(name)}</h3><span>{escape(kind)}</span></div>'
            f'<span class="file-badge {"team" if shared else "private"}">{"Team shared" if shared else "Private"}</span></div>')


def activity_item(action, actor, when, outcome):
    label = action.replace('_', ' ').capitalize()
    st.html(f'<div class="activity-item"><span class="event-dot {"denied" if outcome == "denied" else ""}"></span>'
            f'<div><strong>{escape(label)}</strong><p>{escape(actor)} · {escape(when)}</p></div>'
            f'<span class="outcome {"denied" if outcome == "denied" else ""}">{escape(outcome)}</span></div>')


def format_size(size):
    if size < 1024:
        return f'{size} B'
    if size < 1048576:
        return f'{size/1024:.1f} KB'
    return f'{size/1048576:.1f} MB'


def file_kind(name):
    ext = Path(name).suffix.lower()
    groups = {'Document': {'.pdf', '.doc', '.docx', '.txt', '.md', '.odt', '.ppt', '.pptx'},
              'Spreadsheet': {'.csv', '.xlsx', '.xls', '.tsv'},
              'Image': {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'},
              'Archive': {'.zip', '.7z', '.rar', '.tar', '.gz'},
              'Code': {'.py', '.js', '.ts', '.html', '.css', '.json', '.java', '.c', '.cpp'}}
    return next((kind for kind, extensions in groups.items() if ext in extensions), 'Other')

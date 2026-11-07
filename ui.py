"""Small, escaped presentation helpers; all actions remain native Streamlit widgets."""
from html import escape
from pathlib import Path

import streamlit as st


def load_styles():
    st.html('<style>' + Path(__file__).with_name('ui.css').read_text(encoding='utf-8') + '</style>')


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
    st.html(f'<div class="empty-state"><div class="empty-icon">◇</div><h3>{escape(title)}</h3><p>{escape(description)}</p></div>')


def protection_card(number, title, description):
    st.html(f'<div class="protection-card"><span>{escape(number)}</span><h4>{escape(title)}</h4><p>{escape(description)}</p></div>')


def file_heading(name, kind, shared):
    st.html(f'<div class="file-heading"><span class="file-icon">{escape(kind[:3].upper())}</span>'
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

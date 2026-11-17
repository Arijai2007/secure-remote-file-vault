export async function api(path, { method = 'GET', body, csrf, raw = false } = {}) {
  const headers = {}
  if (csrf) headers['X-CSRF-Token'] = csrf
  if (body && !(body instanceof FormData)) headers['Content-Type'] = 'application/json'
  const response = await fetch('/api' + path, {
    method, credentials: 'same-origin', headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    let message = 'Request failed'
    try { message = (await response.json()).detail || message } catch { /* server error without JSON */ }
    const error = new Error(message)
    error.status = response.status
    throw error
  }
  return raw ? response : response.json()
}

export function size(bytes = 0) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

export function when(value) {
  return new Date(value * 1000).toLocaleString()
}

export function kind(name = '') {
  const ext = name.split('.').pop()?.toLowerCase()
  if (['pdf', 'doc', 'docx', 'txt', 'md', 'ppt', 'pptx'].includes(ext)) return 'Document'
  if (['csv', 'xlsx', 'xls', 'tsv'].includes(ext)) return 'Spreadsheet'
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return 'Image'
  if (['zip', '7z', 'rar', 'tar', 'gz'].includes(ext)) return 'Archive'
  if (['py', 'js', 'ts', 'html', 'css', 'json'].includes(ext)) return 'Code'
  return 'Other'
}

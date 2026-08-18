import axios from 'axios'

const GITHUB_API = 'https://api.github.com'
const OWNER = 'zhan-zip'
const REPO = 'bookkeeping'

let token = ''

export function setToken(t) {
  token = t
}

function getHeaders() {
  return {
    Authorization: `token ${token}`,
    Accept: 'application/vnd.github.v3+json',
  }
}

export async function getFile(path) {
  const url = `${GITHUB_API}/repos/${OWNER}/${REPO}/contents/${path}`
  const resp = await axios.get(url, { headers: getHeaders() })
  if (resp.status === 404) return null
  const content = atob(resp.data.content.replace(/\n/g, ''))
  return {
    content: JSON.parse(content),
    sha: resp.data.sha,
  }
}

export async function putFile(path, content, sha, message) {
  const url = `${GITHUB_API}/repos/${OWNER}/${REPO}/contents/${path}`
  const payload = {
    message,
    content: btoa(JSON.stringify(content, null, 2)),
  }
  if (sha) payload.sha = sha
  const resp = await axios.put(url, payload, { headers: getHeaders() })
  return resp.data.content.sha
}

export async function ensureFile(path, defaultContent, message) {
  const existing = await getFile(path)
  if (existing) return existing
  return putFile(path, defaultContent, null, message)
}
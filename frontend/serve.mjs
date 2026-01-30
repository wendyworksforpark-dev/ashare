// Lightweight production server: static files + API proxy
import { createServer, request as httpRequest } from 'node:http'
import { readFile, stat } from 'node:fs/promises'
import { join, extname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const DIST = join(__dirname, 'dist')
const API_HOST = '127.0.0.1'
const API_PORT = 8000
const PORT = 5173

const MIME = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.map': 'application/json',
}

function proxyToApi(req, res) {
  const opts = {
    hostname: API_HOST,
    port: API_PORT,
    path: req.url,
    method: req.method,
    headers: { ...req.headers, host: `${API_HOST}:${API_PORT}` },
  }
  const proxy = httpRequest(opts, (upstream) => {
    res.writeHead(upstream.statusCode, upstream.headers)
    upstream.pipe(res)
  })
  proxy.on('error', () => {
    res.writeHead(502)
    res.end('API backend unavailable')
  })
  req.pipe(proxy)
}

async function serveStatic(req, res) {
  let filePath = join(DIST, req.url === '/' ? 'index.html' : req.url.split('?')[0])
  try {
    const s = await stat(filePath)
    if (s.isDirectory()) filePath = join(filePath, 'index.html')
    const data = await readFile(filePath)
    const ext = extname(filePath)
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=31536000',
    })
    res.end(data)
  } catch {
    // SPA fallback
    const index = await readFile(join(DIST, 'index.html'))
    res.writeHead(200, { 'Content-Type': 'text/html', 'Cache-Control': 'no-cache' })
    res.end(index)
  }
}

createServer((req, res) => {
  if (req.url.startsWith('/api/')) {
    proxyToApi(req, res)
  } else {
    serveStatic(req, res)
  }
}).listen(PORT, () => {
  console.log(`A-Share Monitor running at http://localhost:${PORT}`)
  console.log(`API proxy → http://${API_HOST}:${API_PORT}`)
})

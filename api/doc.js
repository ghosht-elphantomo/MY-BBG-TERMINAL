// Documents anciens (archive web) servis à l'adresse du site : /doc/a/<horodatage>/<jeton> et /doc/c/<horodatage>/<jeton>
// (jeton = chemin d'origine en base64url, écrit par le relais des données). La fonction va chercher le document à la volée
// (redirections de l'archive suivies ici, jamais par le navigateur), ne renvoie que des documents (jamais une page de l'archive)
// et répond par une page neutre si le document n'est pas disponible. Rien n'est stocké.
const HOSTS = { a: 'http://www.brvm.org/', c: 'http://bfin.brvm.org/' };
const MAX = 4400000;  // limite de réponse des fonctions (4,5 Mo)

function page(res, code, msg) {
  res.statusCode = code;
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=3600');
  res.setHeader('Vercel-CDN-Cache-Control', 'max-age=86400');
  res.end(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Document</title><style>body{margin:0;background:#000;color:#ffb000;font:15px/1.5 system-ui,sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center;padding:24px;box-sizing:border-box}p{color:#ccc;max-width:420px}</style></head>
<body><div><h1 style="font-size:18px;font-weight:600">Document indisponible</h1><p>${msg}</p></div></body></html>`);
}

module.exports = async (req, res) => {
  const q = req.query || {};
  const k = String(q.k || ''), ts = String(q.ts || ''), tok = String(q.t || '');
  if (!HOSTS[k] || !/^\d{8,14}$/.test(ts) || !/^[A-Za-z0-9_-]{2,3000}$/.test(tok)) return page(res, 400, 'Adresse de document invalide.');
  const path = Buffer.from(tok, 'base64url').toString('utf8');
  if (!path || /[\s"<>\\]/.test(path) || /(^|\/)\.\.(\/|$)/.test(path)) return page(res, 400, 'Adresse de document invalide.');
  let r;
  try {
    r = await fetch(`https://web.archive.org/web/${ts}id_/${HOSTS[k]}${path}`, {
      redirect: 'follow', headers: { 'User-Agent': 'Mozilla/5.0 (fqt-terminal)' }, signal: AbortSignal.timeout(25000) });
  } catch (e) { return page(res, 504, 'Ce document ancien ne répond pas pour le moment. Réessayez plus tard.'); }
  if (!r.ok) return page(res, 404, 'Ce document ancien n’a pas pu être retrouvé.');
  const len = Number(r.headers.get('content-length') || 0);
  if (len > MAX) return page(res, 413, 'Ce document ancien est trop volumineux pour être affiché ici.');
  const buf = Buffer.from(await r.arrayBuffer());
  if (buf.length > MAX) return page(res, 413, 'Ce document ancien est trop volumineux pour être affiché ici.');
  const ct = (r.headers.get('content-type') || '').toLowerCase();
  const head = buf.subarray(0, 8).toString('latin1');
  const isPdf = head.startsWith('%PDF');
  // une page HTML est une page de l'archive ou du site d'origine (erreur, liste), jamais un document : pas affichée
  if (!isPdf && (/html|xml/.test(ct) || /^\s*</.test(head))) return page(res, 404, 'Ce document ancien n’a pas pu être retrouvé.');
  const ext = isPdf ? 'pdf' : (/word|msword/.test(ct) ? 'doc' : /excel|spreadsheet/.test(ct) ? 'xls' : 'bin');
  res.statusCode = 200;
  res.setHeader('Content-Type', isPdf ? 'application/pdf' : (ct.split(';')[0] || 'application/octet-stream'));
  res.setHeader('Content-Disposition', `inline; filename="document-${ts.slice(0, 8)}.${ext}"`);
  res.setHeader('Cache-Control', 'public, max-age=86400');
  res.setHeader('Vercel-CDN-Cache-Control', 'max-age=2592000');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.end(buf);
};

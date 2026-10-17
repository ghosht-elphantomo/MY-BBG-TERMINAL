// Relais des données du terminal : le site lit /data/<fichier>.json ; ce relais les prend sur la branche « data »
// du dépôt (réécrite toutes les 15 minutes par GitHub Actions) sans redéployer le site. Cache CDN : 60 s.
// Secours : si GitHub ne répond plus (ou ne connaît plus le dépôt), lecture de la copie de secours quotidienne
// (dépôt privé hors GitHub, clé de lecture seule dans la variable GITLAB_READ_TOKEN de Vercel) ; données au plus d'un jour.
const REPOS = ['ghosht-elphantomo/noodleloop'];
const ORIGINS = [
  ...REPOS.map(r => p => `https://raw.githubusercontent.com/${r}/data/data/${p}?v=${Math.floor(Date.now() / 60000)}`),
  ...REPOS.map(r => p => `https://cdn.jsdelivr.net/gh/${r}@data/data/${p}`),
];
const GL_TOKEN = process.env.GITLAB_READ_TOKEN || '';
const GL_PROJECT = encodeURIComponent(process.env.GITLAB_PROJECT || 'loopvault/archive-vault');
const glUrl = p => `https://gitlab.com/api/v4/projects/${GL_PROJECT}/repository/files/${encodeURIComponent('data/' + p)}/raw?ref=data`;

// GitHub en panne ? (un 404 peut venir d'un fichier absent ou d'un dépôt devenu inaccessible) : un fichier témoin
// toujours présent est vérifié, résultat gardé 5 minutes par instance.
let ghState = { t: 0, down: false };
async function githubDown() {
  if (Date.now() - ghState.t < 300000) return ghState.down;
  let down = true;
  try {
    const r = await fetch(ORIGINS[0]('live.json'), { headers: { 'User-Agent': 'fqt-terminal' }, signal: AbortSignal.timeout(8000) });
    down = !r.ok;
  } catch (e) { down = true; }
  ghState = { t: Date.now(), down };
  return down;
}

async function send(res, r, cdn) {
  const buf = Buffer.from(await r.arrayBuffer());
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate');
  res.setHeader('Vercel-CDN-Cache-Control', cdn);
  res.statusCode = 200; res.end(buf);
}

async function fromGitLab(res, p) {
  if (!GL_TOKEN) return false;
  try {
    const r = await fetch(glUrl(p), { headers: { 'PRIVATE-TOKEN': GL_TOKEN, 'User-Agent': 'fqt-terminal' }, signal: AbortSignal.timeout(15000) });
    if (!r.ok) return false;
    await send(res, r, 'max-age=300, stale-while-revalidate=3600');
    return true;
  } catch (e) { return false; }
}

module.exports = async (req, res) => {
  const p = String((req.query && req.query.p) || '').replace(/^\/+/, '');
  if (!p || p.includes('..') || !/^[A-Za-z0-9_\-./]+\.json$/.test(p)) { res.statusCode = 400; res.end('bad path'); return; }
  if (String((req.query && req.query.via) || '') === '2') {  // essai du secours seul
    if (await fromGitLab(res, p)) return;
    res.statusCode = 503; res.setHeader('Cache-Control', 'no-store'); res.end('unavailable'); return;
  }
  let last = 502;
  for (const [i, url] of ORIGINS.map((f, i) => [i, f(p)])) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': 'fqt-terminal' }, signal: AbortSignal.timeout(15000) });
      if (r.status === 404) { last = 404; continue; }
      if (!r.ok) { last = r.status; continue; }
      await send(res, r, i < REPOS.length ? 'max-age=60, stale-while-revalidate=600' : 'max-age=30');
      return;
    } catch (e) { last = 504; }
  }
  if (GL_TOKEN && (last !== 404 || await githubDown()) && await fromGitLab(res, p)) return;
  res.statusCode = last; res.setHeader('Cache-Control', 'no-store'); res.end('unavailable');
};

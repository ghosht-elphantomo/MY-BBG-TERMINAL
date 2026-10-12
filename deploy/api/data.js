// Relais des données du terminal : le site lit /data/<fichier>.json ; ce relais les prend sur la branche « data »
// du dépôt (réécrite toutes les 15 minutes par GitHub Actions) sans redéployer le site. Cache CDN : 60 s.
const ORIGINS = [
  p => `https://raw.githubusercontent.com/ghosht-elphantomo/MY-BBG-TERMINAL/data/data/${p}?v=${Math.floor(Date.now() / 60000)}`,
  p => `https://cdn.jsdelivr.net/gh/ghosht-elphantomo/MY-BBG-TERMINAL@data/data/${p}`,
];
module.exports = async (req, res) => {
  const p = String((req.query && req.query.p) || '').replace(/^\/+/, '');
  if (!p || p.includes('..') || !/^[A-Za-z0-9_\-./]+\.json$/.test(p)) { res.statusCode = 400; res.end('bad path'); return; }
  let last = 502;
  for (const [i, url] of ORIGINS.map((f, i) => [i, f(p)])) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': 'fqt-terminal' }, signal: AbortSignal.timeout(15000) });
      if (r.status === 404) { last = 404; continue; }
      if (!r.ok) { last = r.status; continue; }
      const buf = Buffer.from(await r.arrayBuffer());
      res.setHeader('Content-Type', 'application/json; charset=utf-8');
      res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate');
      res.setHeader('Vercel-CDN-Cache-Control', i === 0 ? 'max-age=60, stale-while-revalidate=600' : 'max-age=30');
      res.statusCode = 200; res.end(buf); return;
    } catch (e) { last = 504; }
  }
  res.statusCode = last; res.setHeader('Cache-Control', 'no-store'); res.end('unavailable');
};

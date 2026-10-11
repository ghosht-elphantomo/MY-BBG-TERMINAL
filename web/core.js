/* ================= FQT — data, formatting, command line, router ================= */
'use strict';
const $ = id => document.getElementById(id);
const Q = { base: 'data/', sum: null, by: {}, ser: {}, M: {}, json: {}, live: null, quotes: null };
const ST = { fn: 'MON', sec: 'QQQ', gp: { range: '1A', type: 'candle', ov: { sma50: true, sma200: true }, st: { vol: true }, log: false, cmp: [] }, corr: { u: 'BRVMW', win: 104, pair: null },
  brvm: { sort: { k: 'mcap', dir: -1 }, sector: 'ALL' }, dvd: { sort: { k: 'yld', dir: -1 } }, ev: { cat: '', tk: '', q: '', page: 0 }, bt: null, qlab: {} };
/* Registre des fonctions : code -> [libellé, portée (sec = titre, mkt = marché), groupe, description] */
const FN = {
  MON: ['Marchés', 'mkt', 'Marchés', 'Tous les titres, règle SMA 200, séance BRVM, carte des capitalisations'],
  BRVM: ['BRVM', 'mkt', 'Marchés', '48 actions, 17 indices, largeur du marché, secteurs'],
  IMAP: ['Carte de chaleur', 'mkt', 'Marchés', 'BRVM, Nasdaq-100 et ETF : surface = capitalisation, couleur = performance, par secteur'],
  US: ['Nasdaq-100 & ETF', 'mkt', 'Marchés', 'Nasdaq-100, ETF secteurs, facteurs, pays, obligations, matières, crypto'],
  TOP: ['Actualités', 'mkt', 'Marchés', 'Fil d’actualités BRVM, UEMOA, marchés mondiaux, banques centrales'],
  FG: ['Fear & Greed', 'mkt', 'Sentiment', 'Indice peur/avidité US (CNN + réplique) et BRVM (calculé)'],
  ECO: ['Macro US', 'mkt', 'Macro', 'FRED : courbe des taux, crédit, liquidité, emploi, inflation, récession'],
  UEMOA: ['UEMOA', 'mkt', 'Macro', 'Les 8 économies de l’Union : croissance, inflation, dette, BRVM par pays'],
  MACRO: ['Macro & Or', 'mkt', 'Macro', 'Or depuis 1833, krachs, CAPE, inflation, pétrole, VIX'],
  FX: ['Franc CFA', 'mkt', 'Macro', 'USD/XOF, EUR/USD, effet de change, simulateur'],
  CORR: ['Corrélations', 'mkt', 'Quant', 'Matrice BRVM × monde, paire au choix, ACP'],
  RRG: ['Rotation (RRG)', 'mkt', 'Quant', 'Graphe de rotation relative : secteurs, facteurs, pays, BRVM'],
  PER: ['Valorisation BRVM', 'mkt', 'Fondamentaux', 'PER du marché (BRVM officiel), PER prévisionnel des sources, historique'],
  EQS: ['Screener', 'mkt', 'Fondamentaux', 'Filtrer US et BRVM par ratios : FCF, croissance, qualité, valorisation'],
  LIQ: ['Liquidité BRVM', 'mkt', 'Marchés', 'Montants échangés, jours cotés, Amihud, délai pour constituer une position'],
  ALRT: ['Alertes', 'mkt', 'Fondamentaux', 'Marges, FCF, dette, révisions, seuils de valorisation, résultats à venir'],
  DIVC: ['Calendrier dividendes', 'mkt', 'Fondamentaux', 'BRVM : prochains détachements, classement par rendement, historique'],
  EVTS: ['Avis BRVM', 'mkt', 'Marchés', 'Avis officiels depuis 2000'],
  HELP: ['Aide', 'mkt', 'Aide', 'Fonctions, sources, raccourcis'],
  MENU: ['Menu du titre', 'sec', 'Titre', 'Toutes les fonctions disponibles pour ce titre'],
  DES: ['Fiche', 'sec', 'Description', 'Profil, comptes sur 10 exercices, dividendes, avis officiels'],
  CN: ['Actualités du titre', 'sec', 'Description', 'Articles qui citent la société et avis officiels'],
  GP: ['Graphique', 'sec', 'Cours', 'Bougies, moyennes, Bollinger, RSI, MACD, comparaison'],
  HP: ['Historique des cours', 'sec', 'Cours', 'Cours quotidiens, hebdomadaires, mensuels avec variations et volumes'],
  COMP: ['Comparaison', 'sec', 'Cours', 'Performance contre d’autres titres et un indice, dividendes réinvestis'],
  SEAS: ['Saisonnalité', 'sec', 'Cours', 'Rendements années × mois, jour de semaine, Sell in May'],
  FA: ['Analyse financière', 'sec', 'Fondamentaux', 'Revenus, EBITDA, résultat, BPA, marges, flux, FCF, croissance, dette, ROE, ROIC'],
  RV: ['Valorisation relative', 'sec', 'Fondamentaux', 'PER, VE/EBITDA, VE/CA, P/B, rendement FCF contre pairs et historique'],
  WACC: ['Création de valeur', 'sec', 'Fondamentaux', 'Coût du capital, ROIC, écart ROIC − WACC'],
  DVD: ['Dividendes du titre', 'sec', 'Fondamentaux', 'Historique, rendement, croissance, taux de distribution, couverture par le FCF'],
  DDM: ['Valeur par les dividendes', 'sec', 'Fondamentaux', 'Gordon-Shapiro, croissance implicite, sensibilité'],
  EE: ['Estimations', 'sec', 'Analystes', 'Consensus du BPA, révisions, croissance attendue'],
  SURP: ['Surprises', 'sec', 'Analystes', 'BPA publié contre consensus, réaction du cours'],
  BETA: ['Risque & bêta', 'sec', 'Risque', 'Bêta sur plusieurs fenêtres, volatilité, corrélation, drawdown, pairs'],
  QLAB: ['Quant Lab', 'sec', 'Risque', 'Distribution, VaR, Hurst, momentum, analogues, probabilité bayésienne'],
  BTST: ['Backtest', 'sec', 'Risque', '8 stratégies, levier, Monte Carlo, durée des drawdowns'],
};
const MKT_KEYS = ['MON', 'BRVM', 'IMAP', 'US', 'TOP', 'FG', 'ECO', 'UEMOA', 'CORR', 'RRG', 'PER', 'EQS', 'LIQ', 'ALRT', 'DIVC', 'MACRO', 'FX', 'EVTS', 'HELP'];
const SEC_TABS = ['DES', 'GP', 'HP', 'FA', 'RV', 'WACC', 'DVD', 'DDM', 'EE', 'SURP', 'COMP', 'BETA', 'QLAB', 'BTST', 'SEAS', 'CN'];
const MENU_GROUPS = [['Description', ['DES', 'CN']], ['Cours', ['GP', 'HP', 'COMP', 'SEAS']], ['Fondamentaux', ['FA', 'RV', 'WACC', 'DVD', 'DDM']],
  ['Analystes', ['EE', 'SURP']], ['Risque & quant', ['BETA', 'QLAB', 'BTST']]];
const FNS = Object.entries(FN).map(([k, v]) => [k, v[0]]);
const SECFN = new Set(Object.keys(FN).filter(k => FN[k][1] === 'sec'));
/* Pourquoi une fonction n'est pas disponible pour un titre (null = disponible). */
function avail(code, s) {
  if (!s) return 'aucun titre';
  const eq = s.cls === 'Equity' && s.typ !== 'ETF', brvm = s.mkt === 'BRVM';
  if (['FA', 'RV', 'WACC'].includes(code)) return eq ? (brvm || s.fa ? null : 'comptes SEC non disponibles pour ce titre') : 'réservé aux actions';
  if (['EE', 'SURP'].includes(code)) return brvm ? 'aucun consensus d’analystes public pour la BRVM' : s.mkt === 'US' && eq ? (s.ee === false ? 'pas de consensus publié pour ce titre' : null) : 'réservé aux actions US';
  if (code === 'DVD' || code === 'DDM') return s.cls === 'Equity' || s.typ === 'ETF' ? null : 'pas de dividende';
  if (code === 'BTST' || code === 'QLAB') return s.f === 'D' ? null : 'série mensuelle';
  return null;
}

const TRIGGER_ID = '__TRIGGER_ID__';

/* ---------- formatting (French conventions) ---------- */
const NF = {}; const nf = d => NF[d] || (NF[d] = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: d, maximumFractionDigits: d }));
const num = (v, d = 2) => v == null || !isFinite(v) ? '—' : nf(d).format(v).replace(/ /g, ' ');
const pxd = s => s && (s.ccy === 'XOF' && s.cls === 'Equity') ? 0 : s && s.last < 1 ? 4 : 2;
const px = (s, v) => num(v, pxd(s));
const sgn = (v, d = 2, suf = '%', mul = 100) => v == null || !isFinite(v) ? '<span class="fl">—</span>' : `<span class="${v > 0 ? 'up' : v < 0 ? 'dn' : 'fl'}">${v > 0 ? '+' : ''}${num(v * mul, d)}${suf}</span>`;
const pc = (v, d = 2) => sgn(v, d);
const big = v => { if (v == null || !isFinite(v)) return '—'; const a = Math.abs(v); return a >= 1e12 ? num(v / 1e12, 2) + ' T' : a >= 1e9 ? num(v / 1e9, 1) + ' Md' : a >= 1e6 ? num(v / 1e6, 1) + ' M' : a >= 1e3 ? num(v / 1e3, 1) + ' k' : num(v, 0); };
const fd = d => d ? fmtD(d) : '—';
const fds = s => s ? s.slice(8, 10) + '/' + s.slice(5, 7) + '/' + s.slice(0, 4) : '—';
const i2s = d => `${Math.floor(d / 10000)}-${String(Math.floor(d / 100) % 100).padStart(2, '0')}-${String(d % 100).padStart(2, '0')}`;
const s2i = s => +s.replace(/-/g, '');
const cls = v => v > 0 ? 'up' : v < 0 ? 'dn' : 'fl';

/* ---------- data ---------- */
async function getJSON(path) { if (!Q.json[path]) Q.json[path] = fetch(Q.base + path, { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error(path + ' ' + r.status); return r.json(); }); return Q.json[path]; }
async function series(id) {
  if (!Q.ser[id]) Q.ser[id] = getJSON('s/' + id.replace('.', '_') + '.json').then(b => {
    const n = b.d.length; const s = { id, f: b.f, x: b.d, d: b.d.map(i2s), c: b.c, o: b.o || b.c, h: b.h || b.c, l: b.l || b.c, v: b.v || new Array(n).fill(0), val: b.val || null, div: b.div || new Array(n).fill(0) };
    applyQuoteToSeries(s); return s; });
  return Q.ser[id];
}
async function market(id) { if (!Q.M[id]) { const s = await series(id); Q.M[id] = buildMarket({ d: s.d, o: s.o, h: s.h, l: s.l, c: s.c, v: s.v, div: s.div }); } return Q.M[id]; }
function sec(id) { return Q.by[id]; }
function secsWhere(f) { return Q.sum.secs.filter(f); }
function applyQuotes() {
  const q = Q.quotes && Q.quotes.q; if (!q) return;
  for (const [id, r] of Object.entries(q)) { const s = Q.by[id]; if (!s || !r.last) continue; const day = r.d ? s2i(r.d) : s.dt;
    if (day > s.dt) { s.prev = s.last; s.dt = day; } s.last = r.last; s.pct = r.pct != null ? r.pct : s.last / s.prev - 1; if (r.vol != null) s.shd = r.vol; s.live = true; }
}
function applyQuoteToSeries(s) {
  const q = Q.quotes && Q.quotes.q && Q.quotes.q[s.id]; if (!q || !q.last || !q.d) return; const day = s2i(q.d), n = s.x.length;
  if (day > s.x[n - 1]) { s.x.push(day); s.d.push(q.d); s.c.push(q.last); s.o.push(q.o || q.last); s.h.push(Math.max(q.h || q.last, q.last)); s.l.push(Math.min(q.l || q.last, q.last)); s.v.push(q.vol || 0); s.div.push(0); if (s.val) s.val.push(q.val || 0); s.prov = true; }
  else if (day === s.x[n - 1]) { s.c[n - 1] = q.last; s.h[n - 1] = Math.max(s.h[n - 1], q.last); s.l[n - 1] = Math.min(s.l[n - 1], q.last); if (q.vol != null) s.v[n - 1] = q.vol; }
}

/* ---------- command line ---------- */
function searchSecs(qs) {
  const q = qs.trim().toUpperCase(); if (!q) return [];
  const out = []; for (const s of Q.sum.secs) { const id = s.id.toUpperCase(), tk = s.tk.toUpperCase(), n = (s.n || '').toUpperCase(), sh = (s.short || '').toUpperCase();
    const sc = id === q ? 0 : tk.startsWith(q) ? 1 : id.startsWith(q) ? 2 : n.startsWith(q) || sh.startsWith(q) ? 3 : n.includes(q) || sh.includes(q) ? 4 : 9; if (sc < 9) out.push([sc, s]); }
  return out.sort((a, b) => a[0] - b[0] || (b[1].liq || 0) - (a[1].liq || 0)).map(x => x[1]);
}
function parseCmd(txt) {
  const toks = txt.trim().toUpperCase().replace(/<GO>|\bGO\b|EQUITY|INDEX|CURNCY|COMDTY/g, ' ').split(/\s+/).filter(Boolean);
  let fn = null, s = null; for (const t of toks) { if (!fn && FN[t]) { fn = t; continue; } if (t === 'AIDE') { fn = 'HELP'; continue; } if (!s) { const m = Q.by[t] || searchSecs(t)[0]; if (m) s = m.id; } }
  if (!s && toks.length > 1 && !fn) { const m = searchSecs(toks.join(' '))[0]; if (m) s = m.id; }
  return { fn, s };
}
function runCmd(txt) {
  const t = txt.trim(); if (ST.fn === 'MENU' && /^\d{1,2}$/.test(t)) { const it = menuItems(sec(ST.sec))[+t - 1]; if (it) { go(it, ST.sec); return; } }
  const { fn, s } = parseCmd(txt); if (!fn && !s) { toast('Commande inconnue. Exemples : SNTS (menu du titre) · SNTS FA · QQQ BTST · FG · TOP'); return; }
  if (fn && FN[fn][1] === 'mkt') { go(fn, s); return; }
  go(fn || 'MENU', s || ST.sec);
}
function menuItems(s) { return MENU_GROUPS.flatMap(g => g[1]); }
/* Saisie façon Bloomberg : « SNTS » propose les titres ; « SNTS » + espace (ou Tab) propose les fonctions du titre. */
function exactSec(t) { const u = (t || '').toUpperCase(); return Q.by[u] || Q.sum.secs.find(s => s.tk.toUpperCase().split(' ')[0] === u) || null; }
function initCmd() {
  const inp = $('cmd'), ac = $('ac'); let sel = 0, items = [];
  const show = () => {
    const v = inp.value, toks = v.trim().split(/\s+/).filter(Boolean), sp = /\s$/.test(v); const S = toks.length ? exactSec(toks[0]) : null;
    if (S && (toks.length > 1 || sp)) {
      const part = (toks.length > 1 ? toks[toks.length - 1] : '').toUpperCase();
      items = menuItems(S).concat(['CORR']).filter(c => !part || c.startsWith(part) || FN[c][0].toUpperCase().includes(part))
        .map(c => { const why = avail(c, S); return { k: 'sfn', id: c, sec: S.id, a: `${S.id} ${c}`, b: FN[c][0] + ' — ' + FN[c][3], c: why ? 'n.d.' : FN[c][2], off: !!why }; });
    } else {
      const last = toks[toks.length - 1] || '', L = last.toUpperCase();
      const fns = Object.keys(FN).filter(k => k !== 'MENU' && L && (k.startsWith(L) || FN[k][0].toUpperCase().startsWith(L)))
        .map(k => ({ k: 'fn', id: k, a: k, b: FN[k][0] + ' — ' + FN[k][3], c: FN[k][1] === 'sec' ? 'TITRE' : 'FONCTION' }));
      const ss = searchSecs(last).slice(0, 12).map(s => ({ k: 'sec', id: s.id, a: s.tk, b: s.n, c: s.cls === 'Equity' ? (s.mkt === 'BRVM' ? 'BRVM' : s.typ) : s.cls }));
      items = (ss.length && ss[0].id.toUpperCase() === L ? ss.concat(fns) : fns.concat(ss)).slice(0, 16);
    }
    sel = Math.max(0, items.findIndex(it => !it.off)); ac.hidden = !items.length;
    ac.innerHTML = items.map((it, i) => `<div class="${i === sel ? 'on' : ''}${it.off ? ' off' : ''}" data-i="${i}"><b>${esc(it.a)}</b><span>${esc(it.b)}</span><span>${it.c}</span></div>`).join('') +
      (items.length && items[0].k !== 'sfn' && items.some(it => it.k === 'sec') ? '<p class="hint">Entrée : menu du titre · Tab : ses fonctions</p>' : '');
  };
  const pick = (i, tab) => { const it = items[i]; if (!it) return;
    if (it.k === 'sec' && tab) { inp.value = it.id + ' '; show(); return; }
    ac.hidden = true; inp.value = ''; inp.blur();
    if (it.k === 'sfn') go(it.id, it.sec); else if (it.k === 'fn') go(it.id, ST.sec); else go('MENU', it.id); };
  inp.addEventListener('input', show); inp.addEventListener('focus', () => { if (inp.value) show(); });
  inp.addEventListener('keydown', e => { if (ac.hidden) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length; [...ac.querySelectorAll('div')].forEach((c, i) => c.classList.toggle('on', i === sel)); c0(); }
    if (e.key === 'Tab') { e.preventDefault(); pick(sel, true); } if (e.key === 'Escape') { ac.hidden = true; } });
  const c0 = () => { const d = ac.querySelector('div.on'); if (d) d.scrollIntoView({ block: 'nearest' }); };
  ac.addEventListener('mousedown', e => { const d = e.target.closest('[data-i]'); if (d) { e.preventDefault(); pick(+d.dataset.i); } });
  $('cmdForm').addEventListener('submit', e => { e.preventDefault(); const v = inp.value.trim();
    if (!ac.hidden && items.length && !/^\d{1,2}$/.test(v)) { const exactFn = v.toUpperCase().split(/\s+/); const typedFn = exactFn.length === 1 && FN[exactFn[0]];
      if (!typedFn || items[sel].a === exactFn[0]) { pick(sel); return; } }
    ac.hidden = true; inp.value = ''; inp.blur(); runCmd(v); });
  inp.addEventListener('blur', () => setTimeout(() => { ac.hidden = true; }, 150));
  document.addEventListener('keydown', e => { if (e.target.matches('input,select,textarea') || e.metaKey || e.ctrlKey || e.altKey) return; if (/^[a-zA-Z0-9]$/.test(e.key)) { inp.focus(); } if (e.key === 'Escape') go('MON'); });
}

/* ---------- router ---------- */
let renderSeq = 0;
function go(fn, s) { if (fn && FN[fn]) ST.fn = fn; if (s && Q.by[s]) ST.sec = s; try { history.replaceState(null, '', '#' + ST.fn + (SECFN.has(ST.fn) ? '~' + ST.sec : '')); } catch (e) { } render(); window.scrollTo(0, 0); }
function fromHash() { const h = decodeURIComponent(location.hash.slice(1)); if (!h) return; const [f, s] = h.split('~'); if (FN[f]) ST.fn = f; if (s && Q.by[s]) ST.sec = s; }
async function render() {
  const seq = ++renderSeq; untip(); renderKeys(); renderSecbar(); renderStatus();
  const m = $('main'); m.innerHTML = '<div class="empty">Chargement…</div>';
  const why = SECFN.has(ST.fn) && ST.fn !== 'MENU' ? avail(ST.fn, sec(ST.sec)) : null;
  if (why) { m.innerHTML = `<div class="pn"><div class="pt">${sec(ST.sec).tk} · ${FN[ST.fn][0]}<span class="code">${ST.fn}</span></div><div class="pb"><div class="empty">Non disponible pour ce titre : ${esc(why)}.<br><br><button class="tb" data-fn="MENU">Voir les fonctions disponibles</button></div></div></div>`; return; }
  if (!PAGES[ST.fn]) { m.innerHTML = '<div class="empty">Fonction en préparation.</div>'; return; }
  try { await PAGES[ST.fn](m, () => seq === renderSeq); }
  catch (e) { console.error(e); if (seq === renderSeq) m.innerHTML = `<div class="empty">Impossible d'afficher cette fonction : ${esc(e.message)}</div>`; }
}
function renderKeys() { $('fkeys').innerHTML = MKT_KEYS.map((k, i) => `<button class="fk ${ST.fn === k ? 'on' : ''}" data-fn="${k}" title="${esc(FN[k][3])}"><em>${i + 1})</em><b>${k}</b>${FN[k][0]}</button>`).join(''); }
function renderSecbar() {
  const b = $('secbar'); if (!SECFN.has(ST.fn)) { b.hidden = true; $('stabs').hidden = true; return; } b.hidden = false; const s = sec(ST.sec);
  b.innerHTML = `<span class="tk">${s.tk}<small>${s.cls === 'Equity' ? 'Equity' : s.cls}</small></span><span class="nm">${esc(s.n)}</span>
    <span class="px">${px(s, s.last)}</span><span class="kv">${s.ccy}</span><span>${sgn(s.last - s.prev, pxd(s), '', 1)} ${pc(s.pct)}</span>
    <span class="kv">Date<b>${fd(s.dt)}${s.live ? ' · séance' : ''}</b></span>
    ${s.shd != null ? `<span class="kv">Vol<b>${num(s.shd, 0)}</b></span>` : ''}
    <span class="kv">52 sem.<b>${px(s, s.lo52)} – ${px(s, s.hi52)}</b></span><span class="kv">YTD<b>${pc(s.ytd, 1)}</b></span><span class="kv">1 an<b>${pc(s.r1y, 1)}</b></span>
    ${s.mcap ? `<span class="kv">Capi<b>${big(s.mcap)} XOF</b></span>` : ''}${s.per ? `<span class="kv">PER<b>${num(s.per, 1)}</b></span>` : ''}${s.yld ? `<span class="kv">Rdt<b>${num(s.yld * 100, 2)}%</b></span>` : ''}
    <span class="kv">${s.grp ? esc(s.grp) : ''}${s.cty ? ' · ' + esc(Q.sum.cty[s.cty] || s.cty) : ''}</span>`;
  const t = $('stabs'); t.hidden = false;
  t.innerHTML = `<button class="st ${ST.fn === 'MENU' ? 'on' : ''}" data-fn="MENU">MENU</button>` + SEC_TABS.map(k => { const why = avail(k, s); return `<button class="st ${ST.fn === k ? 'on' : ''}${why ? ' off' : ''}" data-fn="${k}" title="${esc(FN[k][0] + (why ? ' — ' + why : ''))}">${k}<small>${FN[k][0]}</small></button>`; }).join('');
}
function renderStatus() {
  const L = Q.live && Q.live.qqq, ss = Q.sum.session;
  $('status').innerHTML = `<span>Données au <b>${fd(Q.sum.asof)}</b> · ${Q.sum.secs.length} titres · séance BRVM <b>${ss ? fds(ss.asof) : '—'}</b>${L ? ` · QQQ <b>${num(L.price, 2)}</b> (${L.state === 'REGULAR' ? 'séance' : L.state === 'CLOSED' ? 'clôturé' : L.state}, ${new Date(L.time * 1000).toISOString().slice(11, 16)} UTC)` : ''}</span>
    <span>Ticker + <b>Entrée</b> : menu du titre · ticker + <b>espace</b> : ses fonctions · graphiques : trackpad / molette, double-clic = vue initiale</span>
    <span>Sources : brvm.org · BRVMetrics · SikaFinance · Nasdaq · Yahoo Finance · SEC · FRED · CBOE · CNN · Coinbase · Banque mondiale · datasets.io — outil d'analyse, pas un conseil en investissement</span>`;
}
function clocks() { const z = [['ABJ', 'Africa/Abidjan'], ['PAR', 'Europe/Paris'], ['NY', 'America/New_York'], ['TPE', 'Asia/Taipei']];
  const t = () => { $('clocks').innerHTML = z.map(([k, tz]) => `<span>${k} <b>${new Date().toLocaleTimeString('fr-FR', { timeZone: tz, hour: '2-digit', minute: '2-digit', second: k === 'ABJ' ? '2-digit' : undefined })}</b></span>`).join(''); };
  t(); setInterval(t, 1000); }
function feedState() { const L = Q.live && Q.live.qqq, f = $('feed'); const age = Q.live ? Date.now() / 1000 - (Q.live.ts || 0) : 1e9;
  const live = L && L.state === 'REGULAR' && age < 40 * 60; f.classList.toggle('live', !!live);
  $('feedTxt').textContent = live ? 'FLUX 15 MIN' : Q.live ? 'MAJ ' + new Date(Q.live.ts * 1000).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : 'EOD ' + fd(Q.sum.asof); }
function toast(msg, ms = 6000) { const t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => { t.hidden = true; }, ms); }

/* ---------- live feed (artifact db written by the sync task) + polling (static hosting) ---------- */
async function initFeed() {
  if (!window.claude || !window.claude.use) { setInterval(pollStatic, 5 * 60 * 1000); return; }
  let db = null; try { db = await window.claude.use('db'); } catch (e) { } if (!db) return;
  const apply = () => { applyQuotes(); for (const p of Object.values(Q.ser)) p.then(applyQuoteToSeries); Q.M = {}; feedState(); renderSecbar(); renderStatus(); if (['MON', 'BRVM', 'IMAP', 'US'].includes(ST.fn)) render(); };
  try { db.doc('feed/live').onSnapshot(sn => { if (sn.exists) { const d = sn.data(); if (!Q.live || (d.ts || 0) >= (Q.live.ts || 0)) { Q.live = d; apply(); } } }, () => { }); } catch (e) { }
  try { db.doc('feed/quotes').onSnapshot(sn => { if (sn.exists) { const d = sn.data(); if (!Q.quotes || (d.ts || 0) >= (Q.quotes.ts || 0)) { Q.quotes = d; apply(); } } }, () => { }); } catch (e) { }
  try { db.doc('feed/news').onSnapshot(async sn => { if (!sn.exists) return; const d = sn.data(); const cur = await (Q.json['news.json'] || Promise.resolve(null)).catch(() => null);
    if (!cur || (d.ts || 0) > (cur.ts || 0)) { Q.json['news.json'] = Promise.resolve(d); if (['TOP', 'CN'].includes(ST.fn)) render(); } }, () => { }); } catch (e) { }
}
async function pollStatic() { try { const [l, q] = await Promise.all([fetch(Q.base + 'live.json?t=' + Date.now()).then(r => r.ok ? r.json() : null), fetch(Q.base + 'quotes.json?t=' + Date.now()).then(r => r.ok ? r.json() : null)]);
  if (l) Q.live = l; if (q) { Q.quotes = q; applyQuotes(); Q.ser = {}; Q.M = {}; } delete Q.json['news.json']; feedState(); renderSecbar(); renderStatus(); if (['MON', 'BRVM', 'IMAP', 'US', 'TOP'].includes(ST.fn)) render(); } catch (e) { } }
async function initSync() {
  if (!/^trig_/.test(TRIGGER_ID) || !window.claude || !window.claude.use) return; let mcp = null; try { mcp = await window.claude.use('mcp'); } catch (e) { } if (!mcp) return;
  const b = $('syncBtn'); b.hidden = false;
  b.addEventListener('click', async () => { b.disabled = true; b.textContent = '…';
    try { await mcp.callTool('Claude Code Remote', 'fire_trigger', { trigger_id: TRIGGER_ID }, { cache: false }); toast('Synchronisation lancée : le dernier relevé GitHub (15 min) arrive dans 2 à 4 minutes, sans recharger la page.', 9000); b.textContent = 'OK'; }
    catch (e) { const c = e && e.code; b.textContent = 'SYNC'; toast(c === 'rate_limited' ? 'Trop de demandes rapprochées : réessaie dans quelques minutes.' : c === 'not_granted' || c === 'consent_required' ? 'Autorisation refusée : ouvre le menu Autorisations de la page.' : 'La synchro n’a pas pu être lancée (' + (c || 'erreur') + '). La mise à jour planifiée tourne quand même.', 9000); }
    finally { setTimeout(() => { b.disabled = false; b.textContent = 'SYNC'; }, 60000); } });
}

/* ---------- boot ---------- */
async function boot() {
  readCL(); renderKeysSkeleton();
  try { Q.sum = await getJSON('summary.json'); } catch (e) { $('main').innerHTML = `<div class="empty">Données introuvables (data/summary.json).</div>`; return; }
  for (const s of Q.sum.secs) Q.by[s.id] = s;
  try { Q.live = await getJSON('live.json'); } catch (e) { } try { Q.quotes = await getJSON('quotes.json'); applyQuotes(); } catch (e) { }
  fromHash(); initCmd(); clocks(); feedState();
  document.addEventListener('click', e => { const f = e.target.closest('[data-fn]'); if (f) { go(f.dataset.fn, f.dataset.s); return; }
    const s = e.target.closest('[data-sec]'); if (s && !e.target.closest('a')) { const id = s.dataset.sec; go(s.dataset.to || (SECFN.has(ST.fn) && ST.fn !== 'MENU' && !avail(ST.fn, sec(id)) ? ST.fn : 'MENU'), id); } });
  render(); initFeed(); initSync();
}
function renderKeysSkeleton() { $('fkeys').innerHTML = MKT_KEYS.map((k, i) => `<button class="fk" data-fn="${k}"><em>${i + 1})</em><b>${k}</b>${FN[k][0]}</button>`).join(''); }
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

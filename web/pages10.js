/* ================= FQT — actualités reliées, cartes de chaleur mondiales, macro BCEAO, obligations et courbes UEMOA, carte du pétrole ================= */
'use strict';
const EV_COL = { 'Résultats': '#f9a33a', 'Dividende': '#2fd26a', 'Assemblée': '#5fd0ea', 'Dirigeants': '#b69cff', 'Analystes': '#ff7ab2', 'Notation': '#ffd200', 'Émission': '#3fd3c0', 'Opération': '#ff9e2b', 'Régulation': '#ff3d4d',
  'Banques centrales': '#7fb3ff', 'Macro': '#9a9a9a', 'Matières premières': '#c8a24a', 'Crypto': '#b69cff', 'Marchés': '#6a6a6a' };
const evBadge = ev => ev ? `<b class="evb" style="background:${EV_COL[ev] || '#555'}">${esc(ev)}</b>` : '';
function newsRow2(x, o = {}) {
  const d = new Date(x.t * 1000), tk = (x.tk || []).filter(t => Q.by[t]);
  return `<div class="nw${o.short ? ' s' : ''}"><span class="d">${d.toLocaleString('fr-FR', { timeZone: 'Africa/Abidjan', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span><span class="c">${esc(srcCode(x))}</span><span>${evBadge(x.ev)}<a href="${esc(x.u)}" target="_blank" rel="noopener">${esc(deent(x.ti))}</a> <span class="src">${esc(deent(x.s || ''))}</span>${tk.length ? `<span class="tags">${tk.map(t => `<b data-sec="${t}" data-to="CN" title="${esc(Q.by[t].n)}">${t}</b>`).join('')}</span>` : ''}${x.x && !o.short ? `<small>${esc(deent(x.x))}</small>` : ''}</span></div>`;
}

/* ------------------------------------------------------------------ TOP : fil relié aux titres, typé par événement */
PAGES.TOP = async (m, alive) => {
  const N = await getJSON('news.json').catch(() => null); if (!alive()) return; const st = ST.top = ST.top || { c: 'ALL', ev: 'ALL', mk: 'ALL', q: '' }; setTitle('Top News');
  if (!N || !N.items || !N.items.length) { m.innerHTML = pn('Actualités', 'TOP', '<div class="empty">Fil d’actualités en cours de constitution.</div>'); return; }
  const its = N.items, cats = [...new Set(its.map(x => x.c).filter(Boolean))], evs = Object.keys(EV_COL).filter(e => its.some(x => x.ev === e));
  const mkOf = x => (x.tk || []).map(t => Q.by[t] && Q.by[t].mkt).filter(Boolean);
  let L = its.filter(x => (st.c === 'ALL' || x.c === st.c) && (st.ev === 'ALL' || x.ev === st.ev) && (st.mk === 'ALL' || (st.mk === 'LINK' ? (x.tk || []).length : mkOf(x).includes(st.mk))));
  if (st.q) { const q = st.q.toLowerCase(); L = L.filter(x => (x.ti + ' ' + (x.x || '') + ' ' + (x.s || '') + ' ' + (x.tk || []).join(' ')).toLowerCase().includes(q)); }
  const age = Math.round((Date.now() / 1000 - N.ts) / 60), nLinked = its.filter(x => (x.tk || []).length).length;
  setTabs([['ALL', 'Tout'], ['BRVM', 'Sociétés BRVM'], ['US', 'Sociétés US'], ['LINK', 'Toutes les sociétés citées']], st.mk, k => { st.mk = k; render(); });
  m.innerHTML = `<div class="tools"><span class="tlab">Rubrique</span><select class="ofld" id="tpC"><option value="ALL">Toutes (${its.length})</option>${cats.map(c => `<option value="${esc(c)}" ${st.c === c ? 'selected' : ''}>${esc(c)} (${its.filter(x => x.c === c).length})</option>`).join('')}</select>
      <span class="tlab">Événement</span><select class="ofld" id="tpE"><option value="ALL">Tous</option>${evs.map(e => `<option value="${esc(e)}" ${st.ev === e ? 'selected' : ''}>${esc(e)} (${its.filter(x => x.ev === e).length})</option>`).join('')}</select>
      <form id="tpF" style="display:inline-flex;gap:4px;margin-left:6px"><input id="tpQ" value="${esc(st.q)}" placeholder="mot-clé, ticker…" style="width:200px"><button class="tb">Filtrer</button></form><span class="tlab">relevé il y a ${age < 120 ? age + ' min' : Math.round(age / 60) + ' h'} · ${nLinked} articles reliés à un titre</span></div>
    ${pn(`Fil d’actualités · ${L.length} articles`, 'TOP', L.slice(0, 300).map(x => newsRow2(x)).join('') || '<div class="empty">Aucun article pour ces filtres.</div>',
      { lect: `Flux publics : ${Object.values(N.feeds || {}).filter((v, i, a) => a.indexOf(v) === i).join(', ')}. Chaque article est relié automatiquement aux sociétés citées (nom usuel, nom officiel ou code ; clic = actualités et historique de la société) et classé par type d’événement d’après son titre. Ce classement automatique peut se tromper : la source fait foi. Les articles restent la propriété de leurs éditeurs.` })}`;
  $('tpC').onchange = e => { st.c = e.target.value; render(); }; $('tpE').onchange = e => { st.ev = e.target.value; render(); }; $('tpF').onsubmit = e => { e.preventDefault(); st.q = $('tpQ').value.trim(); render(); };
};

/* ------------------------------------------------------------------ CN : actualités de la société + historique des événements */
PAGES.CN = async (m, alive) => {
  const s = sec(ST.sec), brvm = isBRVM(s); setTitle('Company News');
  const [N, EV, RP, DV, AN] = await Promise.all([getJSON('news.json').catch(() => ({ items: [] })), brvm ? getJSON('events.json').catch(() => []) : [], brvm ? getJSON('reports.json').catch(() => null) : null, brvm ? getJSON('dividends.json').catch(() => []) : [], getJSON('anomalies.json').catch(() => null)]); if (!alive()) return;
  const al = aliasesOf(s).map(a => a.toLowerCase());
  const its = (N.items || []).filter(x => (x.tk || []).includes(s.id) || (() => { const t = (x.ti + ' ' + (x.x || '')).toLowerCase(); return al.some(a => a === s.id.toLowerCase() ? new RegExp('\\b' + a + '\\b').test(t) : a.length > 3 && t.includes(a)); })());
  const docs = RP ? Object.entries(RP.issuers || {}).filter(([, x]) => x.t === s.id).flatMap(([slug]) => (RP.docs || {})[slug] || []) : [];
  const H = [];
  for (const x of its) H.push({ d: new Date(x.t * 1000).toISOString().slice(0, 10), k: x.ev || 'Actualité', t: deent(x.ti), u: x.u, s: srcCode(x) });
  for (const e of EV.filter(x => x.t === s.id)) H.push({ d: e.d, k: 'Avis BRVM · ' + (e.c || ''), t: e.ti, u: e.u, s: 'BRVM' });
  for (const d of docs) if (d.d) H.push({ d: i2s(+d.d), k: /etats? financiers/i.test(d.ti) ? 'États financiers' : /activit/i.test(d.ti) ? 'Rapport d’activité' : 'Publication', t: d.ti, u: d.u, s: 'BRVM' });
  for (const x of DV.filter(x => x.t === s.id && x.dps)) { if (x.det) H.push({ d: x.det, k: 'Dividende', t: `Détachement du dividende de l’exercice ${x.ex} : ${num(x.dps, 2)} FCFA net`, s: 'BRVM' }); }
  for (const a of ((AN && AN.by && AN.by[s.id]) || []).filter(a => a.d)) H.push({ d: i2s(a.d), k: 'Anomalie · ' + a.k, t: a.m, s: 'FQT', an: true });
  H.sort((a, b) => (b.d || '').localeCompare(a.d || ''));
  const types = [...new Set(H.map(h => h.k.split(' · ')[0]))]; const st = ST.cnh = ST.cnh || { k: 'ALL' }; if (st.k !== 'ALL' && !types.includes(st.k)) st.k = 'ALL';
  const HL = H.filter(h => st.k === 'ALL' || h.k.split(' · ')[0] === st.k);
  m.innerHTML = `<div class="grid c2">${pn(`${esc(s.tk)} · articles qui citent la société (${its.length})`, 'CN', its.length ? its.slice(0, 150).map(x => newsRow2(x)).join('') : `<div class="empty">Aucun article récent ne cite ${esc(s.short || s.n)} dans les flux suivis (45 derniers jours).</div>`,
      { lect: `Articles reliés automatiquement à la société (« ${al.map(esc).join(' », « ')} ») dans les flux d’actualités, mis à jour toutes les 15 minutes. Fil complet : TOP.` })}
    ${pn(`Historique des événements · ${H.length}`, 'CN', `<div class="tw" style="max-height:72vh"><table class="t" style="table-layout:fixed;width:100%"><colgroup><col style="width:82px"><col style="width:150px"><col><col style="width:62px"></colgroup><thead><tr><th class="l">Date</th><th class="l">Type</th><th class="l">Événement</th><th class="l">Source</th></tr></thead><tbody>${HL.slice(0, 400).map(h => `<tr><td class="l" style="vertical-align:top">${fds(h.d)}</td><td class="l" style="white-space:normal;vertical-align:top;color:${h.an ? 'var(--dn)' : EV_COL[h.k] || 'var(--amber)'}">${esc(h.k)}</td><td class="l" style="white-space:normal;vertical-align:top">${h.u ? `<a href="${esc(h.u)}" target="_blank" rel="noopener" style="color:var(--white)">${esc(h.t || '')}</a>` : esc(h.t || '')}</td><td class="l dm" style="vertical-align:top;overflow:hidden;text-overflow:ellipsis">${esc(h.s || '')}</td></tr>`).join('') || '<tr><td class="l dm" colspan="4">Aucun événement.</td></tr>'}</tbody></table></div>`,
      { np: true, tools: `<span class="tlab">Type</span><select class="ofld" id="cnK"><option value="ALL">Tous</option>${types.map(t => `<option ${st.k === t ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select>`, lect: `Réunit les articles (typés automatiquement), ${brvm ? 'les avis officiels de la BRVM, les publications de la société sur brvm.org, les détachements de dividendes et ' : ''}les anomalies statistiques détectées (ANOM). Sources indiquées ligne par ligne.` })}</div>`;
  if ($('cnK')) $('cnK').onchange = e => { st.k = e.target.value; render(); };
};

/* ------------------------------------------------------------------ IMAP : Europe, Royaume-Uni, Asie, Afrique, Moyen-Orient (capitalisations mondiales) */
const WREG = {
  EU: ['Europe (hors R.-U.)', { Germany: 'Allemagne', France: 'France', Netherlands: 'Pays-Bas', Switzerland: 'Suisse', Italy: 'Italie', Spain: 'Espagne', Sweden: 'Suède', Denmark: 'Danemark', Belgium: 'Belgique', Finland: 'Finlande', Norway: 'Norvège', Ireland: 'Irlande', Austria: 'Autriche', Portugal: 'Portugal', Poland: 'Pologne', Luxembourg: 'Luxembourg', Greece: 'Grèce', 'Czech Republic': 'Tchéquie' }, 90],
  UK: ['Royaume-Uni', { 'United Kingdom': 'Royaume-Uni' }, 60],
  ASIA: ['Asie', { Japan: 'Japon', China: 'Chine', 'Hong Kong': 'Hong Kong', Taiwan: 'Taïwan', 'South Korea': 'Corée du Sud', India: 'Inde', Singapore: 'Singapour', Indonesia: 'Indonésie', Thailand: 'Thaïlande', Malaysia: 'Malaisie', Philippines: 'Philippines', Vietnam: 'Viêt Nam' }, 120],
  AFR: ['Afrique', { 'South Africa': 'Afrique du Sud', Nigeria: 'Nigeria', Morocco: 'Maroc', Egypt: 'Égypte', Kenya: 'Kenya', Ghana: 'Ghana', "Cote d'Ivoire": "Côte d'Ivoire", Senegal: 'Sénégal', Mauritius: 'Maurice', Tanzania: 'Tanzanie', Zimbabwe: 'Zimbabwe', Botswana: 'Botswana', Tunisia: 'Tunisie' }, 60],
  ME: ['Moyen-Orient', { 'Saudi Arabia': 'Arabie saoudite', 'United Arab Emirates': 'Émirats arabes unis', Qatar: 'Qatar', Israel: 'Israël', Kuwait: 'Koweït', Turkey: 'Turquie' }, 60] };
const PAGES_IMAP_LOCAL = PAGES.IMAP;
PAGES.IMAP = async (m, alive) => {
  const st = ST.imap = ST.imap || { u: 'BRVM', c: 'pct', sz: 'mcap' }; setTitle('Intraday Market Map');
  setTabs([['BRVM', 'BRVM'], ['NDX', 'Nasdaq-100'], ['ETF', 'ETF US'], ['EU', 'Europe'], ['UK', 'Royaume-Uni'], ['ASIA', 'Asie'], ['AFR', 'Afrique'], ['ME', 'Moyen-Orient']], st.u, k => { st.u = k; if (!WREG[k] && k !== 'BRVM') st.sz = 'mcap'; render(); });
  if (!WREG[st.u]) { await PAGES_IMAP_LOCAL(m, alive); const tb = m.querySelector('.tools'); if (tb) { const b = [...tb.children]; let i = b.findIndex(x => x.classList && x.classList.contains('tlab') && /Couleur/.test(x.textContent)); if (i > 0) b.slice(0, i).forEach(x => x.remove()); } return; }
  const W = await getJSON('world.json').catch(() => null); if (!alive()) return;
  const [title, CTY, nTop] = WREG[st.u];
  if (!W || !W.rows) { m.innerHTML = pn(`Carte de chaleur · ${title}`, 'IMAP', '<div class="empty">Capitalisations mondiales en cours de collecte (relevé toutes les 15 minutes).</div>'); return; }
  const rows = W.rows.filter(r => CTY[r[2]]).slice(0, nTop).map(r => ({ sym: r[0], n: r[1], cty: CTY[r[2]], mc: r[3], px: r[4], p: r[5] }));
  const G = {}; for (const r of rows) (G[r.cty] = G[r.cty] || []).push(r);
  const col = v => v == null || !isFinite(v) ? '#262626' : (() => { const a = Math.min(1, Math.abs(v) / .03); return v >= 0 ? `rgb(${Math.round(30 - 10 * a)},${Math.round(70 + 120 * a)},${Math.round(45 + 30 * a)})` : `rgb(${Math.round(90 + 140 * a)},${Math.round(40 - 10 * a)},${Math.round(40 - 5 * a)})`; })();
  const wavg = a => { let s = 0, w = 0; for (const x of a) if (x.p != null) { s += x.p * x.mc; w += x.mc; } return w ? s / w : null; };
  const sect = Object.entries(G).map(([g, a]) => ({ g, list: a, v: a.reduce((t, x) => t + x.mc, 0), p: wavg(a), n: a.length })).sort((a, b) => b.v - a.v);
  const mov = rows.filter(r => r.p != null).sort((a, b) => b.p - a.p); const hasCh = mov.length > 0;
  m.innerHTML = `<div class="grid side">${pn(`Carte de chaleur · ${title} · ${rows.length} premières capitalisations`, 'IMAP', `<div id="imM" class="imap" style="height:${innerWidth < 700 ? 520 : 640}px"></div><div class="imleg">${[-1, -.66, -.33, 0, .33, .66, 1].map(t => `<span style="background:${col(t * .03)}">${t > 0 ? '+' : ''}${num(t * 3, 1)}%</span>`).join('')}</div>`,
      { lect: `Regroupement par pays ; surface = capitalisation boursière en dollars ; couleur = variation ${hasCh ? `depuis le relevé de référence du ${esc(W.ref || '')} UTC (cours en dollars : inclut l’effet de change)` : '— <b>non encore disponible</b> : elle se calcule à partir du relevé de référence du soir (22 h 35 UTC)'}. Source : companiesmarketcap.com (classement mondial des sociétés cotées, prix en USD), relevé ${new Date(W.ts * 1000).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}. Ces sociétés ne sont pas des titres suivis par le terminal : pas de fiche ni de graphique.` })}
    <div class="grid" style="align-content:start">${pn('Pays (pondérés)', 'IMAP', `<table class="t"><thead><tr><th class="l">Pays</th><th>Sociétés</th><th>Capi. ($)</th><th>Var.</th></tr></thead><tbody>${sect.map(x => `<tr><td class="l am">${esc(x.g)}</td><td>${x.n}</td><td>${big(x.v)}</td><td>${x.p != null ? pc(x.p) : '—'}</td></tr>`).join('')}</tbody></table>`, { np: true })}
      ${hasCh ? pn('Plus fortes hausses et baisses', 'IMAP', `<table class="t"><tbody>${mov.slice(0, 6).concat(mov.slice(-6)).map((r, i) => `<tr class="${i === 6 ? 'sep2' : ''}"><td class="l nm">${esc(r.n)}</td><td class="l dm">${esc(r.cty)}</td><td>${pc(r.p)}</td></tr>`).join('')}</tbody></table>`, { np: true }) : ''}</div></div>`;
  const host = $('imM'), Wd = host.getBoundingClientRect().width, Hd = host.getBoundingClientRect().height; const boxes = squarify(sect.map(x => ({ ...x })), { x: 0, y: 0, w: Wd, h: Hd }); let html = '';
  for (const b of boxes) { const head = b.h > 40 && b.w > 60 ? 16 : 0; html += `<div class="ims" style="left:${b.x}px;top:${b.y}px;width:${b.w}px;height:${b.h}px">${head ? `<div class="imh">${esc(b.g)} <span>${b.p != null ? (b.p > 0 ? '+' : '') + num(b.p * 100, 2) + '%' : ''}</span></div>` : ''}</div>`;
    for (const t of squarify(b.list.map(r => ({ r, v: r.mc })), { x: b.x + 1, y: b.y + head + 1, w: b.w - 2, h: b.h - head - 2 })) { const r = t.r;
      html += `<div class="imt" data-w="${esc(r.sym)}" style="left:${t.x}px;top:${t.y}px;width:${Math.max(0, t.w - 1)}px;height:${Math.max(0, t.h - 1)}px;background:${col(r.p)};cursor:default">${t.w > 40 && t.h > 22 ? `<b style="font-size:${U.clamp(Math.sqrt(t.w * t.h) / 7, 9, 18)}px">${esc(r.n.length > 14 && t.w < 120 ? r.sym : r.n.slice(0, 22))}</b>${t.h > 36 ? `<span>${r.p != null ? (r.p > 0 ? '+' : '') + num(r.p * 100, 2) + '%' : ''}</span>` : ''}` : ''}</div>`; } }
  host.innerHTML = html; const by = new Map(rows.map(r => [r.sym, r]));
  host.onmousemove = e => { const d = e.target.closest('.imt'); if (!d) { untip(); return; } const r = by.get(d.dataset.w); tip(e, `<b>${esc(r.n)}</b> (${esc(r.sym)}) · ${esc(r.cty)}<br>capitalisation ${big(r.mc)} $ · cours ${num(r.px, 2)} $<br>variation ${r.p != null ? pc(r.p) : 'n.d.'}`); };
  host.onmouseleave = untip;
};

/* ------------------------------------------------------------------ UEMOA : tableau de bord BCEAO + indicateurs Banque mondiale */
const PAGES_UEMOA_WB = PAGES.UEMOA;
const MOISF = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
const mLab = k => /^\d{4}-\d{2}$/.test(k) ? MOISF[+k.slice(5) - 1] + ' ' + k.slice(2, 4) : k;
PAGES.UEMOA = async (m, alive) => {
  const tab = tabState('UEMOA', 'bc'); setTabs([['bc', 'BCEAO : taux, inflation, crédit'], ['tp', 'Titres publics'], ['wb', 'Indicateurs annuels (Banque mondiale)']], tab, k => { ST.tab.UEMOA = k; render(); }); setTitle('WAEMU Economic Dashboard');
  if (tab === 'wb') return PAGES_UEMOA_WB(m, alive);
  const B = await getJSON('bceao.json').catch(() => null); if (!alive()) return;
  if (!B || !B.infl) { m.innerHTML = pn('BCEAO', 'UEMOA', '<div class="empty">Bulletin mensuel des statistiques de la BCEAO en attente de la collecte du soir.</div>'); return; }
  const srcL = `Source : BCEAO, Bulletin mensuel des statistiques — ${esc(B.label || '')} (relevé le ${fds(B.d)}), <a href="${esc(B.url)}" target="_blank" rel="noopener">PDF</a>.`;
  if (tab === 'tp') {
    const I = (B.issues || []).slice(); const byC = {}; for (const x of I) if (x.t != null) { const k = x.c.replace(/^la |^le |^l'/i, ''); (byC[k] = byC[k] || []).push(x); }
    const avg = (a, f) => { const v = a.filter(f); const w = v.reduce((s, x) => s + x.amt, 0); return w ? v.reduce((s, x) => s + x.t * x.amt, 0) / w : null; };
    m.innerHTML = `<div class="grid c2">${pn('Émissions par appel public à l’épargne (période du bulletin)', 'UEMOA', `<div class="tw" style="max-height:70vh"><table class="t"><thead><tr><th class="l">Titre</th><th class="l">Émetteur</th><th>Montant (M FCFA)</th><th class="l">Émission</th><th>Durée (mois)</th><th class="l">Échéance</th><th>Taux</th></tr></thead><tbody>
        ${I.map(x => `<tr><td class="l">${esc(x.k)}</td><td class="l nm">${esc(x.c)}</td><td>${num(x.amt, 0)}</td><td class="l">${esc(x.d)}</td><td>${x.mois}</td><td class="l">${esc(x.ech)}</td><td class="yl">${x.t != null ? num(x.t, 2) + ' %' : 'multiples'}</td></tr>`).join('')}</tbody></table></div>`, { np: true, lect: srcL + ' Taux = taux d’intérêt (moyen pondéré) à l’émission publié par la BCEAO.' })}
      ${pn('Taux moyen pondéré par émetteur', 'UEMOA', `<table class="t"><thead><tr><th class="l">Émetteur</th><th>Émissions</th><th>Montant (Md FCFA)</th><th>Taux moyen</th><th>dont 12 mois</th></tr></thead><tbody>${Object.entries(byC).sort((a, b) => (avg(b[1], () => true) || 0) - (avg(a[1], () => true) || 0)).map(([c, a]) => `<tr><td class="l am">${esc(c)}</td><td>${a.length}</td><td>${num(a.reduce((s, x) => s + x.amt, 0) / 1e3, 1)}</td><td class="yl">${num(avg(a, () => true), 2)} %</td><td>${avg(a, x => x.mois === 12) != null ? num(avg(a, x => x.mois === 12), 2) + ' %' : '—'}</td></tr>`).join('')}</tbody></table>${cvb('ueTP', 240)}`, { np: true, lect: 'Moyenne des taux pondérée par les montants levés. Courbes complètes par pays : <b data-fn="GC" class="am" style="cursor:pointer">GC</b> ; obligations cotées : <b data-fn="SRCH" class="am" style="cursor:pointer">SRCH</b>.' })}</div>`;
    const ent = Object.entries(byC).map(([c, a]) => [c, avg(a, () => true)]).sort((a, b) => b[1] - a[1]);
    barChart($('ueTP'), { labels: ent.map(e => e[0].slice(0, 10)), values: ent.map(e => e[1]), fmt: v => num(v, 2) + '%', labelsOnBars: true, pos: '#3d7cc9', padB: 22 });
    return;
  }
  const pol = B.policy || [], pl = pol[pol.length - 1] || {}, home = B.home || {}; const minR = home.min ?? pl.min, pretR = home.pret ?? pl.pret;
  const IU = (B.infl || {}).UEMOA || {}, ik = Object.keys(IU).filter(k => k.length === 7).sort(), il = ik[ik.length - 1];
  const mm = B.mm || [], mml = mm[mm.length - 1] || {}; const CR = B.credit || {}; const crK = k => { const o = CR[k] || {}; const ks = Object.keys(o).filter(x => x.length === 7).sort(); return [o[ks[ks.length - 1]], ks[ks.length - 1]]; };
  const [deb, debM] = crK("credits.taux.Taux d'intérêt moyen (%)"), [cred] = crK("depots.taux.Taux d'intérêt moyen (%)"), MO = (B.money || {}).rows || {};
  const tile = (n, v, sub) => `<div class="tile"><div class="tn">${n}</div><div class="tv">${v}</div><div class="tc">${sub || ''}</div></div>`;
  const cty = Object.keys(B.infl || {}); const months = ik.slice(-8);
  m.innerHTML = `<div class="tiles">${tile('Taux minimum de soumission aux appels d’offres', minR != null ? num(minR, 2) + ' %' : '—', pl.d ? 'depuis le ' + fds(pl.d) : '')}${tile('Taux du guichet de prêt marginal', pretR != null ? num(pretR, 2) + ' %' : '—', pl.d ? 'depuis le ' + fds(pl.d) : '')}
      ${tile('Inflation UEMOA (sur un an)', il ? num(IU[il], 1) + ' %' : '—', il ? mLab(il) : '')}${tile('Taux moyen du marché monétaire', mml.t != null ? num(mml.t, 2) + ' %' : '—', mml.m ? 'adjudications, ' + mLab(mml.m) : '')}
      ${tile('Taux débiteur moyen des banques', deb != null ? num(deb, 2) + ' %' : '—', debM ? 'crédits mis en place, ' + mLab(debM) : '')}${tile('Taux créditeur moyen', cred != null ? num(cred, 2) + ' %' : '—', 'nouveaux dépôts')}
      ${tile('Masse monétaire M2 (Union)', MO['Masse monétaire (M2)'] ? num(MO['Masse monétaire (M2)'].Union / 1e3, 1) + ' T FCFA' : '—', B.money && B.money.asof ? 'fin ' + mLab(B.money.asof) : '')}${tile('Crédit aux autres secteurs (Union)', MO['Créances sur les autres secteurs'] ? num(MO['Créances sur les autres secteurs'].Union / 1e3, 1) + ' T FCFA' : '—', 'créances des banques et de la BCEAO')}</div>
    <div class="grid c2">${pn('Taux directeurs de la BCEAO et inflation de l’UEMOA', 'UEMOA', cvb('ueR', 290), { lect: 'Paliers = taux directeurs (historique des modifications publié dans le bulletin) ; ligne ambre = inflation sur un an de l’Union (mois connus). ' + srcL })}
      ${pn('Inflation par pays (glissement annuel, %)', 'UEMOA', `<table class="t"><thead><tr><th class="l">Pays</th>${Object.keys(B.infl[cty[0]] || {}).map(k => `<th>${mLab(k)}</th>`).join('')}</tr></thead><tbody>${cty.map(c => `<tr class="${c === 'UEMOA' ? 'sep2' : ''}"><td class="l am">${esc(c)}</td>${Object.values(B.infl[c]).map(v => `<td style="background:${heatBg(v / 100, .06)}">${num(v, 1)}</td>`).join('')}</tr>`).join('')}</tbody></table>`, { np: true, lect: 'Années = moyennes annuelles ; mois = glissement annuel. Sources : Instituts nationaux de la statistique, BCEAO. Critère de convergence de l’UEMOA : inflation ≤ 3 %.' })}</div>
    <div class="grid c2">${pn('Crédits et dépôts bancaires', 'UEMOA', `<div class="tw"><table class="t acc"><thead><tr><th class="l"></th>${Object.keys(CR["credits.taux.Taux d'intérêt moyen (%)"] || {}).map(k => `<th>${mLab(k)}</th>`).join('')}</tr></thead><tbody>${Object.entries(CR).map(([k, o]) => { const [sec_, sub, lab] = k.split('.'); return `<tr class="${sub === 'vol' && /Volume/.test(lab) || sec_ === 'marge' ? '' : 'sub'}"><td class="l">${sec_ === 'credits' ? 'Crédits' : sec_ === 'depots' ? 'Dépôts' : ''} ${esc(lab.replace(/\(en milliards de FCFA\)/, '(Md FCFA)'))}</td>${Object.values(o).map(v => `<td>${num(v, 2)}</td>`).join('')}</tr>`; }).join('')}</tbody></table></div>`, { np: true, lect: 'Crédits nouvellement mis en place et nouveaux dépôts : volumes (moyenne mensuelle sur l’année ou mois) et taux d’intérêt moyens. ' + srcL })}
      ${pn('Monnaie et crédit par pays (milliards de FCFA)', 'UEMOA', `<div class="tw"><table class="t"><thead><tr><th class="l"></th>${Object.keys(MO['Masse monétaire (M2)'] || {}).map(c => `<th>${esc(c.slice(0, 8))}</th>`).join('')}</tr></thead><tbody>${Object.entries(MO).map(([k, o]) => `<tr><td class="l am">${esc(k)}</td>${Object.values(o).map(v => `<td>${num(v, 0)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
        ${B.act ? `<h4 class="sub">Activité (glissement annuel, %)</h4><table class="t"><thead><tr><th class="l"></th>${Object.keys(Object.values(B.act)[0] || {}).map(k => `<th>${mLab(k)}</th>`).join('')}</tr></thead><tbody>${Object.entries(B.act).map(([k, o]) => `<tr><td class="l am">${esc(k)}</td>${Object.values(o).map(v => `<td>${num(v, 1)}</td>`).join('')}</tr>`).join('')}</tbody></table>` : ''}`, { np: true, lect: `Situation à fin ${B.money && B.money.asof ? mLab(B.money.asof) : '—'}. Créances sur les autres secteurs = crédit à l’économie (hors administration centrale). ` + srcL })}</div>`;
  /* graphique : paliers des taux directeurs + inflation */
  const dts = new Set(); const today = new Date().toISOString().slice(0, 10); pol.forEach(p => dts.add(p.d)); ik.forEach(k => dts.add(k + '-15')); dts.add(today);
  const X = [...dts].filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d) && d >= '2016-01-01').sort(); const stepAt = (d, k) => { let v = null; for (const p of pol) if (p.d <= d) v = p[k]; return v; };
  const inflAt = d => { const k = d.slice(0, 7); return d.endsWith('-15') && IU[k] != null ? IU[k] : null; };
  new TSChart($('ueR'), { panes: [{ h: 1, fmt: v => num(v, 1) + '%' }], grid: 'dot', xticks: bbgTicks }).set({ x: X.map(s2i), series: [{ y: X.map(d => stepAt(d, 'pret')), color: '#ff3d4d', w: 1.6, label: 'Prêt marginal', fmt: v => num(v, 2) + '%' }, { y: X.map(d => stepAt(d, 'min')), color: '#5fd0ea', w: 1.6, label: 'Taux minimum de soumission', fmt: v => num(v, 2) + '%' }, { y: X.map(inflAt), color: '#f9a33a', w: 1.4, connect: true, label: 'Inflation UEMOA', fmt: v => num(v, 1) + '%' }] }, [0, X.length - 1]);
};

/* ------------------------------------------------------------------ SRCH : obligations cotées à la BRVM (rendement, duration, sensibilité) */
const CTY_OBL = { TPCI: "Côte d'Ivoire", TPSN: 'Sénégal', TPBJ: 'Bénin', TPBF: 'Burkina Faso', TPML: 'Mali', TPNE: 'Niger', TPTG: 'Togo', TPGB: 'Guinée-Bissau', EOM: 'Mali', EOS: 'Sénégal', SNTS: 'Sénégal' };
const parseFr = d => { const m = String(d || '').match(/(\d{2})\/(\d{2})\/(\d{4})/); return m ? new Date(Date.UTC(+m[3], +m[2] - 1, +m[1])) : null; };
/* Hypothèses explicites : coupon sur le nominal restant (estimé = dernier coupon ÷ taux, semestriel si le cours vaut ~2 fois ce nominal), remboursement in fine du nominal restant
   à la date anniversaire du dernier coupon, l'année d'échéance indiquée dans le nom ; base exact/365, taux actuariel annuel. */
function bondCalc(b, today = new Date()) {
  const o = { ok: false };
  if (!b.cpn || !b.y1 || !b.px) { o.why = b.cpn ? 'échéance ou cours absent' : 'taux variable ou coupon non publié'; return o; }
  const lp = parseFr(b.lp_d); let N = b.lp_v && b.cpn ? b.lp_v / b.cpn : null, f = 1;
  /* un cours se situe entre ~75 % et ~130 % du nominal : un rapport voisin de 2 signale un coupon semestriel */
  if (N) { /* nominal ≤ nominal d'émission usuel (10 000) ; cours entre 75 % et 130 % du nominal */
    const cand = [[N, 1], [2 * N, 2]].filter(([n]) => n <= 10150 && b.px / n >= .75 && b.px / n <= 1.3);
    if (cand.length !== 1) { Object.assign(o, { N, why: 'cours et coupon incohérents avec un nominal unique (amortissement ou cours ancien)' }); return o; }
    [N, f] = cand[0]; if (Math.abs(N - 10000) < 150) N = 10000; }
  if (!N) N = 10000;
  o.amort = N < 9900;
  /* obligation amortissable : l'échéancier (et donc le nominal restant après le dernier amortissement) n'est pas publié — pas de rendement calculé */
  if (o.amort) { Object.assign(o, { N, f, why: 'amortissable : échéancier non publié' }); return o; }
  const day = lp ? [lp.getUTCMonth(), lp.getUTCDate()] : [11, 31]; const T = new Date(Date.UTC(b.y1, day[0], day[1]));
  o.N = N; o.f = f; o.T = T; o.nomEst = !!b.lp_v;
  if (T <= today) { o.why = 'arrivée à échéance'; o.matured = true; return o; }
  const flows = []; let d = new Date(T); while (d > today) { flows.unshift(new Date(d)); d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - 12 / f, d.getUTCDate())); }
  const cf = flows.map((t, i) => ({ t: (t - today) / 864e5 / 365, v: N * b.cpn / f + (i === flows.length - 1 ? N : 0) }));
  const dirty = b.px + (b.cc || 0); const pv = r => cf.reduce((s, c) => s + c.v / Math.pow(1 + r, c.t), 0);
  let lo = -0.5, hi = 1.5; for (let k = 0; k < 120; k++) { const mid = (lo + hi) / 2; if (pv(mid) > dirty) lo = mid; else hi = mid; } const y = (lo + hi) / 2;
  const mac = cf.reduce((s, c) => s + c.t * c.v / Math.pow(1 + y, c.t), 0) / pv(y);
  if (y > .25 || y < -.05) { Object.assign(o, { why: 'cours non représentatif (rendement hors norme)' }); return o; }
  Object.assign(o, { ok: true, ytm: y, cy: N * b.cpn / b.px, mac, mod: mac / (1 + y), sens: -mac / (1 + y) * b.px / 100, life: (T - today) / 864e5 / 365, cf, par: Math.abs(b.px / N - 1) < .005, pctN: b.px / N });
  return o;
}
PAGES.SRCH = async (m, alive) => {
  const B = await getJSON('bonds.json').catch(() => null); if (!alive()) return; setTitle('Fixed Income Search');
  if (!B || !B.rows) { m.innerHTML = pn('Obligations UEMOA', 'SRCH', '<div class="empty">Cotations obligataires de la BRVM en attente du prochain relevé (toutes les 15 minutes).</div>'); return; }
  const st = ST.srch = ST.srch || { t: 'ALL', live: true, sort: 'ytm', dir: -1, sel: null, q: '' };
  setTabs([['ALL', 'Toutes'], ['État', 'États'], ['Régional', 'Organismes régionaux'], ['Privé', 'Émetteurs privés']], st.t, k => { st.t = k; render(); });
  const now = new Date(); const rows = B.rows.map(b => ({ b, c: bondCalc(b, now), cty: CTY_OBL[b.code.split('.')[0]] || (b.typ === 'État' ? '—' : '') }));
  let L = rows.filter(r => (st.t === 'ALL' || r.b.typ === st.t) && (!st.live || !r.c.matured) && (!st.q || (r.b.code + ' ' + r.b.n).toLowerCase().includes(st.q.toLowerCase())));
  const key = { ytm: r => r.c.ytm, cpn: r => r.b.cpn, mat: r => r.c.T ? +r.c.T : null, px: r => r.c.pctN, dur: r => r.c.mod, code: r => r.b.code };
  L.sort((a, b) => { const A = key[st.sort](a), Bv = key[st.sort](b); if (A == null) return 1; if (Bv == null) return -1; return (typeof A === 'string' ? A.localeCompare(Bv) : A - Bv) * st.dir; });
  const sel = rows.find(r => r.b.code === st.sel) || L[0];
  const th = (k, l) => `<th data-k="${k}" class="${st.sort === k ? 'on' : ''}" style="cursor:pointer">${l}</th>`;
  const okN = rows.filter(r => r.c.ok && !r.c.matured);
  m.innerHTML = `<div class="tools"><button class="tb ${st.live ? 'on' : ''}" id="obLive">${st.live ? 'En vie seulement' : 'Toutes, y compris échues'}</button><span class="tlab">Rechercher</span><form id="obF" style="display:inline-flex;gap:4px"><input id="obQ" value="${esc(st.q)}" placeholder="TPCI, BOAD, SONATEL…"><button class="tb">OK</button></form>
      <span class="tlab">${L.length} lignes · relevé ${new Date(B.ts * 1000).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })} · source brvm.org</span></div>
    <div class="grid side"><div class="pn"><div class="pt">Obligations cotées à la BRVM<span class="code">SRCH</span></div><div class="tw" style="max-height:calc(100vh - 290px)"><table class="t"><thead><tr>${th('code', 'Code')}<th class="l">Nom</th><th class="l">Type</th>${th('cpn', 'Coupon')}${th('mat', 'Échéance estimée')}${th('px', 'Cours / nominal')}<th>Coupon couru</th>${th('ytm', 'Rendement est.')}<th>Rdt courant</th>${th('dur', 'Sensibilité')}</tr></thead><tbody>
      ${L.map(r => `<tr data-ob="${esc(r.b.code)}" class="${sel && r.b.code === sel.b.code ? 'cur' : ''}" style="cursor:pointer"><td class="l tk">${esc(r.b.code)}</td><td class="l nm" style="max-width:280px;overflow:hidden;text-overflow:ellipsis" title="${esc(r.b.n)}">${esc(r.b.n)}</td><td class="l dm">${esc(r.b.typ || '')}</td><td>${r.b.cpn != null ? num(r.b.cpn * 100, 2) + '%' : '<span class="dm">var.</span>'}</td>
        <td>${r.c.T ? fds(r.c.T.toISOString().slice(0, 10)) : '—'}</td><td>${r.c.pctN ? num(r.c.pctN * 100, 2) + '%' : '—'}</td><td>${num(r.b.cc, 2)}</td><td class="yl">${r.c.ok ? num(r.c.ytm * 100, 2) + '%' : `<span class="dm" title="${esc(r.c.why || '')}">n.d.</span>`}</td><td>${r.c.ok ? num(r.c.cy * 100, 2) + '%' : '—'}</td><td>${r.c.ok ? num(r.c.mod, 2) : '—'}</td></tr>`).join('')}</tbody></table></div>
      <div class="lect"><b>Rendement estimé</b> : la BRVM ne publie ni la date exacte d’échéance ni l’échéancier d’amortissement. Hypothèses : nominal restant = dernier coupon ÷ taux du coupon (× 2 si le cours indique un coupon semestriel), remboursement in fine à la date anniversaire du dernier coupon dans l’année d’échéance du nom, base exact/365. <b>Obligations amortissables</b> (nominal restant inférieur au nominal d’émission) : rendement non calculé, faute d’échéancier publié. Un amortissement futur non connu raccourcit la vraie duration. <strong>Quand le cours égale le nominal, le rendement est égal au coupon</strong> ; beaucoup de lignes cotent au pair faute d’échanges : le rendement reflète alors le coupon d’émission, pas un prix de marché.</div></div>
      <div class="grid" style="align-content:start" id="obD"></div></div>`;
  const yas = r => { if (!r) return ''; const c = r.c, b = r.b;
    return pn(`${esc(b.code)} · ${esc(b.n)}`, 'YAS', `<div class="kv2"><span>Émetteur</span><b>${esc(b.iss || '')}${r.cty ? ' · ' + esc(r.cty) : ''}</b><span>Type</span><b>${esc(b.typ || '—')}</b><span>Coupon</span><b>${b.cpn != null ? num(b.cpn * 100, 2) + ' %' : 'variable'}</b><span>Date d’émission (cotation)</span><b>${esc(b.em || '—')}</b>
      <span>Dernier coupon payé</span><b>${b.lp_d ? esc(b.lp_d) + ' · ' + num(b.lp_v, 2) : '—'}</b><span>Cours (FCFA)</span><b>${num(b.px, 0)}</b><span>Coupon couru</span><b>${num(b.cc, 2)}</b>
      <span class="h">Calcul (hypothèses ci-contre)</span><span>Nominal restant estimé</span><b class="est">${c.N ? num(c.N, 0) : '—'}${c.f === 2 ? ' · coupon semestriel' : ''}${c.amort ? ' · amortissable' : ''}${!b.lp_v ? ' (nominal d’émission usuel supposé)' : ''}</b><span>Échéance estimée</span><b class="est">${c.T ? fds(c.T.toISOString().slice(0, 10)) : '—'}</b><span>Vie résiduelle</span><b>${c.life ? num(c.life, 2) + ' ans' : '—'}</b>
      <span>Rendement actuariel estimé</span><b class="yl">${c.ok ? num(c.ytm * 100, 3) + ' %' : 'n.d. (' + esc(c.why || '') + ')'}</b><span>Rendement courant</span><b>${c.ok ? num(c.cy * 100, 2) + ' %' : '—'}</b><span>Duration de Macaulay</span><b>${c.ok ? num(c.mac, 2) + ' ans' : '—'}</b><span>Sensibilité (duration modifiée)</span><b>${c.ok ? num(c.mod, 2) : '—'}</b>
      <span>Variation du cours pour +1 % de taux</span><b>${c.ok ? num(-c.mod, 2) + ' %' : '—'}</b></div>
      ${c.ok ? `<div class="form" style="margin-top:6px"><label>Rendement visé (%)<input id="ysY" value="${num(c.ytm * 100, 2)}"></label><label>Cours correspondant<input id="ysP" disabled></label></div>` : ''}`, { lect: 'YAS : prix ↔ rendement sur les mêmes flux estimés. ' + (c.par ? 'Cours = nominal restant : le rendement est égal au coupon.' : '') }); };
  const show = code => { const r = rows.find(x => x.b.code === code); st.sel = code; $('obD').innerHTML = yas(r) + pn('Répartition des rendements estimés (lignes en vie)', 'SRCH', cvb('obH', 170));
    m.querySelectorAll('[data-ob]').forEach(tr => tr.classList.toggle('cur', tr.dataset.ob === code));
    const y = $('ysY'); if (y && r.c.ok) { const upd = () => { const v = parseFloat(y.value.replace(',', '.')) / 100; if (!isFinite(v)) return; const p = r.c.cf.reduce((s, c) => s + c.v / Math.pow(1 + v, c.t), 0) - (r.b.cc || 0); $('ysP').value = num(p, 0) + ' FCFA (' + num(p / r.c.N * 100, 2) + ' %)'; }; y.oninput = upd; upd(); }
    const ys = okN.map(r_ => r_.c.ytm * 100).filter(v => v > -5 && v < 20); const bins = {}; for (const v of ys) { const k = Math.floor(v * 2) / 2; bins[k] = (bins[k] || 0) + 1; } const ks = Object.keys(bins).map(Number).sort((a, b) => a - b);
    barChart($('obH'), { labels: ks.map(k => num(k, 1)), values: ks.map(k => bins[k]), fmt: v => num(v, 0), pos: '#3d7cc9', extra: i => 'rendement ' + num(ks[i], 1) + ' – ' + num(ks[i] + .5, 1) + ' %' }); };
  m.querySelectorAll('[data-ob]').forEach(tr => tr.onclick = () => show(tr.dataset.ob)); if (sel) show(sel.b.code);
  m.querySelectorAll('th[data-k]').forEach(t => t.onclick = () => { const k = t.dataset.k; st.dir = st.sort === k ? -st.dir : -1; st.sort = k; render(); });
  $('obLive').onclick = () => { st.live = !st.live; render(); }; $('obF').onsubmit = e => { e.preventDefault(); st.q = $('obQ').value.trim(); render(); };
};

/* ------------------------------------------------------------------ GC : courbes des taux souveraines de l'UEMOA (UMOA-Titres) */
const ctyName = c => ({ "Cote d'ivoire": "Côte d'Ivoire", "Cote d'Ivoire": "Côte d'Ivoire", 'Burkina': 'Burkina Faso' })[c] || c;
PAGES.GC = async (m, alive) => {
  const [C, B, OB] = await Promise.all([getJSON('umoa_curves.json').catch(() => null), getJSON('bceao.json').catch(() => null), getJSON('bonds.json').catch(() => null)]); if (!alive()) return; setTitle('Graph Curves');
  if (!C || !C.curves || !Object.keys(C.curves).length) { m.innerHTML = pn('Courbes souveraines', 'GC', '<div class="empty">Courbes UMOA-Titres en attente de la collecte du soir.</div>'); return; }
  const ds = Object.keys(C.curves).sort(), dL = ds[ds.length - 1], cur = C.curves[dL].c, ctys = Object.keys(cur);
  const st = ST.gc = ST.gc || { sel: ctys.slice(0, 4), cmp: null, cty: ctys.includes("Cote d'ivoire") ? "Cote d'ivoire" : ctys[0], kind: 3 }; if (!ctys.includes(st.cty)) st.cty = ctys[0];
  const COLS = ['#f9a33a', '#5fd0ea', '#2fd26a', '#ff7ab2', '#b69cff', '#ffd200', '#ff3d4d', '#3fd3c0'];
  const mats = [...new Set(ctys.flatMap(c => cur[c].map(p => p[0])))].sort((a, b) => { const y = s => { const m_ = s.match(/(\d+)\s*(mois|an)/); return m_ ? +m_[1] / (m_[2] === 'mois' ? 12 : 1) : 99; }; return y(a) - y(b); });
  const at = (c, lab, k = st.kind) => { const p = (cur[c] || []).find(q => q[0] === lab); return p ? p[k] : null; };
  setTabs([['c', 'Courbes par pays'], ['h', 'Évolution d’un pays']], tabState('GC', 'c'), k => { ST.tab.GC = k; render(); });
  if (ST.tab.GC === 'h') {
    const lines = ds.map((d, i) => ({ d, c: C.curves[d].c[st.cty] })).filter(o => o.c);
    m.innerHTML = `<div class="tools"><span class="tlab">Pays</span><select class="ofld" id="gcC">${ctys.map(c => `<option value="${esc(c)}" ${c === st.cty ? 'selected' : ''}>${esc(ctyName(c))}</option>`).join('')}</select><span class="tlab">Taux</span><button class="tb ${st.kind === 3 ? 'on' : ''}" data-kd="3">Après lissage</button><button class="tb ${st.kind === 2 ? 'on' : ''}" data-kd="2">Zéro-coupon</button></div>
      ${pn(`${esc(ctyName(st.cty))} · courbe au ${esc(C.curves[dL].asof || dL)} et à des dates antérieures`, 'GC', cvb('gcH', 380), { lect: `Courbes publiées par UMOA-Titres (fichiers hebdomadaires « Courbes des taux »). Dates disponibles : ${lines.map(o => fds(o.d)).join(', ')}.` })}`;
    gcDraw($('gcH'), lines.map((o, i) => ({ lab: fds(o.d), col: i === lines.length - 1 ? '#f9a33a' : `rgba(200,200,200,${.25 + .5 * i / lines.length})`, pts: o.c.map(p => [p[1], p[st.kind]]), w: i === lines.length - 1 ? 2.2 : 1.2 })));
  } else {
    const iss = OB && OB.rows ? OB.rows.filter(b => b.typ === 'État' && b.cpn && b.y0 && b.y1 && b.y1 - b.y0 >= 2).map(b => ({ cty: CTY_OBL[b.code.split('.')[0]], y: b.y0, mat: b.y1 - b.y0, cpn: b.cpn })).filter(x => x.cty) : [];
    m.innerHTML = `<div class="tools"><span class="tlab">Pays affichés</span>${ctys.map((c, i) => `<button class="tb ${st.sel.includes(c) ? 'on' : ''}" data-cy="${esc(c)}"><i class="dot" style="background:${COLS[i % 8]}"></i>${esc(ctyName(c))}</button>`).join('')}<span class="tlab">Taux</span><button class="tb ${st.kind === 3 ? 'on' : ''}" data-kd="3">Après lissage</button><button class="tb ${st.kind === 2 ? 'on' : ''}" data-kd="2">Zéro-coupon</button></div>
      <div class="grid c2">${pn(`Courbes souveraines UEMOA au ${esc(C.curves[dL].asof || dL)}`, 'GC', cvb('gcC', 380), { lect: 'Source : UMOA-Titres, « Courbes des taux » (zéro-coupon et taux après lissage, par État). Abscisse = maturité.' })}
      ${pn('Taux par maturité (%)', 'GC', `<div class="tw"><table class="t"><thead><tr><th class="l">Maturité</th>${ctys.map(c => `<th>${esc(ctyName(c).replace('Guinée-Bissau', 'G.-Bissau').replace('Burkina Faso', 'Burkina').replace("Côte d'Ivoire", 'C. d’Iv.'))}</th>`).join('')}</tr></thead><tbody>${mats.map(l => `<tr><td class="l am">${esc(l)}</td>${ctys.map(c => { const v = at(c, l); return `<td style="background:${v == null ? '' : `hsl(${Math.round(220 - U.clamp((v - .03) / .07, 0, 1) * 220)},55%,22%)`}">${v == null ? '—' : num(v * 100, 2)}</td>`; }).join('')}</tr>`).join('')}</tbody></table></div>`, { np: true, lect: 'Couleur : bleu = taux bas, rouge = taux élevé. Le spread entre États mesure la prime de risque perçue par les investisseurs du marché régional.' })}</div>
      ${iss.length ? pn('Coupons à l’émission des obligations d’État cotées à la BRVM (par année d’émission)', 'GC', cvb('gcI', 260), { lect: `Chaque point = une obligation d’État cotée : coupon fixé à l’émission (donnée publiée) selon l’année d’émission. ${[...new Set(iss.map(x => x.cty))].map((c, i) => `<i class="dot" style="background:${COLS[i % 8]}"></i>${esc(c)}`).join(' ')}. Ce ne sont pas des rendements de marché.` }) : ''}`;
    gcDraw($('gcC'), st.sel.map(c => ({ lab: ctyName(c), col: COLS[ctys.indexOf(c) % 8], pts: (cur[c] || []).map(p => [p[1], p[st.kind]]), w: 1.8 })));
    if (iss.length) { const cc = [...new Set(iss.map(x => x.cty))]; scatterL($('gcI'), { pts: iss.map((x, i) => ({ x: x.y + (i % 7) / 14, y: x.cpn, label: '', color: COLS[cc.indexOf(x.cty) % 8], id: null })), fx: v => String(Math.round(v)), fy: v => num(v * 100, 1) + '%', xlab: 'année d’émission', ylab: 'coupon', tipf: p => num(p.y * 100, 2) + ' %' }); }
    m.querySelectorAll('[data-cy]').forEach(b => b.onclick = () => { const c = b.dataset.cy; st.sel = st.sel.includes(c) ? st.sel.filter(x => x !== c) : st.sel.concat([c]); render(); });
  }
  m.querySelectorAll('[data-kd]').forEach(b => b.onclick = () => { st.kind = +b.dataset.kd; render(); }); if ($('gcC') && $('gcC').tagName === 'SELECT') { } const sc = document.getElementById('gcC'); if (sc && sc.tagName === 'SELECT') sc.onchange = e => { st.cty = e.target.value; render(); };
};
function gcDraw(host, lines) {
  const { x, w, h } = setupCanvas(host); const padL = 46, padB = 22, padT = 10, W = w - padL - 12, H = h - padT - padB; const all = lines.flatMap(l => l.pts.map(p => p[1])).filter(v => v != null && isFinite(v));
  if (!all.length) return; let lo = Math.min(...all), hi = Math.max(...all); const pd = (hi - lo) * .1 || .005; lo -= pd; hi += pd;
  const tmax = Math.max(10, ...lines.flatMap(l => l.pts.map(p => p[0]))) * 1.04;
  const X = t => padL + Math.log(t * 12) / Math.log(tmax * 12) * W, Y = v => padT + (hi - v) / (hi - lo) * H; x.font = FNUM;
  x.setLineDash([1, 3]); for (const t of niceTicks(lo * 100, hi * 100, 5)) { const yy = Math.round(Y(t / 100)) + .5; x.strokeStyle = 'rgba(160,160,160,.35)'; x.beginPath(); x.moveTo(padL, yy); x.lineTo(w - 12, yy); x.stroke(); x.fillStyle = '#ddd'; x.textAlign = 'right'; x.fillText(num(t, 1) + '%', padL - 4, yy + 3); }
  const ticks = [[1 / 12, '1M'], [.25, '3M'], [.5, '6M'], [1, '1A'], [2, '2A'], [3, '3A'], [5, '5A'], [7, '7A'], [10, '10A'], [15, '15A'], [20, '20A'], [30, '30A']].filter(t => t[0] <= tmax); for (const [t, l] of ticks) { const xx = Math.round(X(t)) + .5; x.beginPath(); x.moveTo(xx, padT); x.lineTo(xx, padT + H); x.stroke(); x.fillStyle = '#ddd'; x.textAlign = 'center'; x.fillText(l, xx, h - 6); } x.setLineDash([]);
  lines.forEach((l, k) => { x.strokeStyle = l.col; x.lineWidth = l.w || 1.6; x.beginPath(); l.pts.forEach((p, i) => { if (p[1] == null) return; i ? x.lineTo(X(p[0]), Y(p[1])) : x.moveTo(X(p[0]), Y(p[1])); }); x.stroke(); x.fillStyle = l.col; l.pts.forEach(p => { if (p[1] == null) return; x.beginPath(); x.arc(X(p[0]), Y(p[1]), 2.4, 0, 7); x.fill(); }); });
  let ly = padT + 4; x.font = FUI; x.textAlign = 'left'; for (const l of lines.slice(-9)) { x.fillStyle = 'rgba(0,0,0,.75)'; x.fillRect(padL + 6, ly - 1, x.measureText(l.lab).width + 22, 14); x.fillStyle = l.col; x.fillRect(padL + 9, ly + 3, 8, 6); x.fillStyle = '#e6e6e6'; x.fillText(l.lab, padL + 21, ly + 9); ly += 15; }
  host.onmousemove = e => { const r = host.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top; let best = null, bd = 100; for (const l of lines) for (const p of l.pts) { const d = (X(p[0]) - mx) ** 2 + (Y(p[1]) - my) ** 2; if (d < bd) { bd = d; best = [l, p]; } }
    if (best) tip(e, `<b>${esc(best[0].lab)}</b> · ${best[1][0] < 1 ? num(best[1][0] * 12, 0) + ' mois' : num(best[1][0], 0) + ' an(s)'} : <b>${num(best[1][1] * 100, 2)} %</b>`); else untip(); }; host.onmouseleave = untip;
}

/* ------------------------------------------------------------------ BMAP : carte des flux pétroliers (détroits EIA, cours, stocks US, actualités) */
PAGES.BMAP = async (m, alive) => {
  setTitle('Oil Flow Map'); const [G, CP, WP, N] = await Promise.all([getJSON('geo_world.json').catch(() => null), getJSON('chokepoints.json').catch(() => null), getJSON('eia_wpsr.json').catch(() => null), getJSON('news.json').catch(() => ({ items: [] }))]); if (!alive()) return;
  if (!G || !CP) { m.innerHTML = pn('Carte du pétrole', 'BMAP', '<div class="empty">Fond de carte en attente du prochain relevé.</div>'); return; }
  const st = ST.bmap = ST.bmap || { y: CP.years.length - 1 }; const yi = st.y, yr = CP.years[yi];
  const oil = ['BRENT', 'WTI', 'NATGAS', 'USO', 'XLE'].map(id => Q.by[id]).filter(Boolean);
  const onews = (N.items || []).filter(x => /p[ée]trol(e|i[eè]re?s?)\b|\bbrent\b|\bwti\b|\boil\b|\bcrude\b|opep|opec|baril|barrel|ormuz|hormuz|tanker|raffinerie|refiner/i.test(x.ti)).slice(0, 40);
  const R = WP && WP.rows || {}; const wr = k => R[k] || null;
  setTabs(CP.years.map((y, i) => [String(i), String(y)]), String(yi), k => { st.y = +k; render(); });
  m.innerHTML = `<div class="grid side"><div class="pn"><div class="pt">Flux pétroliers maritimes · détroits stratégiques · ${yr}<span class="sel">${esc(CP.unit)}</span><span class="code">BMAP</span></div><div class="cv" id="bmC" style="height:max(420px, calc(100vh - 300px - var(--nwh, 90px)))"></div>
      <div class="lect">Cercles = volumes ${yr} par détroit (source : <b>EIA</b>, World Oil Transit Chokepoints, mise à jour du 25/06/2024, données 2018-2023 — la prochaine édition n’est pas encore relevée). Traits = principales routes, <b>schématiques</b> (épaisseur = volume du détroit traversé) : ce ne sont pas des positions de navires. Commerce maritime mondial de pétrole ${yr} : <strong>${num(CP.world.maritime[yi], 1)} Mb/j</strong> pour une offre mondiale de ${num(CP.world.supply[yi], 1)} Mb/j. Survol = historique.</div></div>
    <div class="grid" style="align-content:start">${pn('Cours', 'BMAP', `<table class="t"><tbody><thead><tr><th class="l"></th><th>Dernier</th><th>Var.</th><th>1 mois</th><th>Date</th></tr></thead>${oil.map(s => `<tr data-sec="${s.id}" data-to="GP" title="${esc(s.n)}" style="cursor:pointer"><td class="l tk">${s.id}</td><td>${px(s, s.last)}</td><td>${pc(s.pct)}</td><td>${pc(s.r1m, 1)}</td><td class="dm">${fd(s.dt).slice(0, 5)}</td></tr>`).join('')}</tbody></table>`, { np: true, lect: 'Brent, WTI, gaz : prix au comptant publiés (FRED, quotidien, J-1). USO, XLE : ETF cotés, différé de 15 min en séance. Clic = graphique.' })}
      ${WP ? pn('Stocks pétroliers des États-Unis (Mb)', 'BMAP', `<table class="t"><thead><tr><th class="l"></th><th>${esc((WP.hdr || [])[1] || '')}</th><th>sem. préc.</th><th>Var.</th><th>il y a 1 an</th></tr></thead><tbody>${['Crude Oil', 'Commercial (Excluding SPR)', 'Strategic Petroleum Reserve (SPR)', 'Total Motor Gasoline', 'Distillate Fuel Oil'].map(k => wr(k) ? `<tr><td class="l am">${{ 'Crude Oil': 'Brut (total)', 'Commercial (Excluding SPR)': 'Brut commercial', 'Strategic Petroleum Reserve (SPR)': 'Réserve stratégique', 'Total Motor Gasoline': 'Essence', 'Distillate Fuel Oil': 'Distillats' }[k]}</td><td>${num(wr(k)[0], 1)}</td><td>${num(wr(k)[1], 1)}</td><td class="${cls(wr(k)[2])}">${num(wr(k)[2], 1)}</td><td>${num(wr(k)[4], 1)}</td></tr>` : '').join('')}</tbody></table>`, { np: true, lect: `Source : ${esc(WP.src || 'EIA')}, relevé le ${fds(WP.d)}. Publication hebdomadaire (mercredi).` }) : ''}
      ${pn(`Actualités du pétrole (${onews.length})`, 'TOP', `<div style="max-height:360px;overflow:auto">${onews.map(x => newsRow2(x, { short: true })).join('') || '<div class="dm">Aucune dépêche récente.</div>'}</div>`)}</div></div>`;
  /* dessin : projection équirectangulaire (latitudes 72 N à 56 S), routes animées */
  const host = $('bmC'); const cv = document.createElement('canvas'); host.appendChild(cv); const ctx = cv.getContext('2d');
  const byK = Object.fromEntries(CP.pts.map(p => [p.k, p])), vmax = Math.max(...CP.pts.map(p => p.v[yi]));
  let W = 0, H = 0, dpr = 1, land = null, t0 = performance.now(), hover = null;
  const PJ = (lon, lat) => [(lon + 180) / 360 * W, (72 - lat) / 128 * H];
  const size = () => { const r = host.getBoundingClientRect(); dpr = Math.min(2, devicePixelRatio || 1); W = r.width; H = r.height; cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + 'px'; cv.style.height = H + 'px';
    land = document.createElement('canvas'); land.width = cv.width; land.height = cv.height; const g = land.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.fillStyle = '#020b1a'; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(80,110,150,.18)'; g.lineWidth = 1; for (let lo = -180; lo <= 180; lo += 30) { const [x0] = PJ(lo, 0); g.beginPath(); g.moveTo(x0, 0); g.lineTo(x0, H); g.stroke(); } for (let la = -60; la <= 60; la += 30) { const [, y0] = PJ(0, la); g.beginPath(); g.moveTo(0, y0); g.lineTo(W, y0); g.stroke(); }
    g.fillStyle = '#1b2433'; g.strokeStyle = '#2f3b4f'; g.lineWidth = .7;
    for (const c of G.c) for (const r of c.r) { g.beginPath(); let px0 = null; r.forEach((p, i) => { const [x, y] = PJ(p[0], p[1]); if (i && Math.abs(x - px0) > W / 2) { g.moveTo(x, y); } else i ? g.lineTo(x, y) : g.moveTo(x, y); px0 = x; }); g.closePath(); g.fill(); g.stroke(); } };
  const draw = now => { if (!document.body.contains(cv)) return; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.drawImage(land, 0, 0, W, H); const ph = ((now - t0) / 60) % 24;
    for (const rt of CP.routes) { const v = Math.max(...rt.via.map(k => byK[k].v[yi])); const lw = 1 + 7 * v / vmax; ctx.strokeStyle = 'rgba(249,163,58,.28)'; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.beginPath(); rt.p.forEach((p, i) => { const [x, y] = PJ(p[0], p[1]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.stroke();
      ctx.strokeStyle = 'rgba(255,214,140,.85)'; ctx.lineWidth = Math.max(1, lw / 3); ctx.setLineDash([3, 21]); ctx.lineDashOffset = -ph; ctx.stroke(); ctx.setLineDash([]); }
    for (const p of CP.pts) { const [x, y] = PJ(p.lon, p.lat), r = 4 + 22 * Math.sqrt(p.v[yi] / vmax); ctx.fillStyle = p === hover ? 'rgba(255,61,77,.55)' : 'rgba(255,61,77,.35)'; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.strokeStyle = '#ff3d4d'; ctx.lineWidth = 1.2; ctx.stroke();
      ctx.font = '400 11.5px ' + MONO; ctx.fillStyle = '#fff'; ctx.textAlign = 'left'; ctx.fillText(`${p.n.split(' (')[0].replace(' et oléoduc SUMED', ' + SUMED')} ${num(p.v[yi], 1)}`, x + r + 3, y + 4); }
    requestAnimationFrame(draw); };
  size(); requestAnimationFrame(draw); new ResizeObserver(() => size()).observe(host);
  cv.onmousemove = e => { const r = cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top; hover = null; for (const p of CP.pts) { const [x, y] = PJ(p.lon, p.lat); if ((x - mx) ** 2 + (y - my) ** 2 < 26 * 26) hover = p; }
    if (hover) tip(e, `<b>${esc(hover.n)}</b><br>${CP.years.map((y, i) => `${y} : ${num(hover.v[i], 1)}`).join(' · ')} Mb/j<br>part du commerce maritime ${yr} : ${num(hover.v[yi] / CP.world.maritime[yi] * 100, 0)} %`); else untip(); };
  cv.onmouseleave = () => { hover = null; untip(); };
};

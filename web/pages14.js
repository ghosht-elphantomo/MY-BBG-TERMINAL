/* ================= FQT — WCRS (classement mondial des devises) et FXC (matrice des changes croisés) ================= */
'use strict';

/* drapeaux supplémentaires pour les devises (les 22 premiers sont dans pages12.js) */
Object.assign(FLAG_N, { NZ: 'Nouvelle-Zélande', SE: 'Suède', NO: 'Norvège', DK: 'Danemark', MX: 'Mexique', AR: 'Argentine', IL: 'Israël', TR: 'Turquie', HK: 'Hong Kong', KR: 'Corée du Sud', TW: 'Taïwan', SG: 'Singapour', MY: 'Malaisie', UM: 'UEMOA' });
function flag2(c, w = 22, h = 14) {
  const cross = (bg, fg, inner) => `<rect width="22" height="14" fill="${bg}"/><rect x="6" width="4" height="14" fill="${fg}"/><rect y="5" width="22" height="4" fill="${fg}"/>${inner ? `<rect x="7" width="2" height="14" fill="${inner}"/><rect y="6" width="22" height="2" fill="${inner}"/>` : ''}`;
  const st = (cx, cy, r, col) => { let p = ''; for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr = k % 2 ? r * .42 : r; p += `${(cx + rr * Math.cos(a)).toFixed(2)},${(cy + rr * Math.sin(a)).toFixed(2)} `; } return `<polygon points="${p}" fill="${col}"/>`; };
  let b = null;
  switch (c) {
    case 'SE': b = cross('#006aa7', '#fecc00'); break;
    case 'NO': b = cross('#ba0c2f', '#fff', '#00205b'); break;
    case 'DK': b = cross('#c8102e', '#fff'); break;
    case 'NZ': b = '<rect width="22" height="14" fill="#00247d"/><rect width="11" height="7" fill="#00247d"/><path d="M0 0L11 7M11 0L0 7" stroke="#fff" stroke-width="1.5"/><path d="M5.5 0V7M0 3.5H11" stroke="#fff" stroke-width="2.2"/><path d="M5.5 0V7M0 3.5H11" stroke="#cc142b" stroke-width="1.2"/>' + st(16, 3.4, 1, '#cc142b') + st(18.6, 6.4, 1, '#cc142b') + st(14.2, 7.6, 1, '#cc142b') + st(16.4, 11, 1.1, '#cc142b'); break;
    case 'MX': b = '<rect width="7.34" height="14" fill="#006847"/><rect x="7.33" width="7.34" height="14" fill="#fff"/><rect x="14.66" width="7.34" height="14" fill="#ce1126"/><circle cx="11" cy="7" r="1.6" fill="#8c5a2b"/>'; break;
    case 'AR': b = '<rect width="22" height="14" fill="#74acdf"/><rect y="4.67" width="22" height="4.67" fill="#fff"/><circle cx="11" cy="7" r="1.5" fill="#f6b40e"/>'; break;
    case 'IL': b = '<rect width="22" height="14" fill="#fff"/><rect y="1.4" width="22" height="1.6" fill="#0038b8"/><rect y="11" width="22" height="1.6" fill="#0038b8"/><path d="M11 4.1L13.6 8.6H8.4ZM11 9.9L8.4 5.4H13.6Z" fill="none" stroke="#0038b8" stroke-width=".7"/>'; break;
    case 'TR': b = '<rect width="22" height="14" fill="#e30a17"/><circle cx="8.4" cy="7" r="3.6" fill="#fff"/><circle cx="9.3" cy="7" r="2.9" fill="#e30a17"/>' + st(13.2, 7, 1.5, '#fff'); break;
    case 'HK': b = '<rect width="22" height="14" fill="#de2910"/>' + st(11, 7, 3.4, '#fff'); break;
    case 'KR': b = '<rect width="22" height="14" fill="#fff"/><circle cx="11" cy="7" r="3.4" fill="#0047a0"/><path d="M7.6 7A3.4 3.4 0 0 1 14.4 7A1.7 1.7 0 0 1 11 7A1.7 1.7 0 0 0 7.6 7Z" fill="#cd2e3a"/><path d="M3 3.2L5 1.6M3.6 4L5.6 2.4M17 10.8L19 12.4M16.4 11.6L18.4 13.2" stroke="#000" stroke-width=".7"/>'; break;
    case 'TW': b = '<rect width="22" height="14" fill="#fe0000"/><rect width="11" height="7" fill="#000095"/><circle cx="5.5" cy="3.5" r="1.9" fill="#fff"/>'; break;
    case 'SG': b = '<rect width="22" height="7" fill="#ef3340"/><rect y="7" width="22" height="7" fill="#fff"/><circle cx="4.6" cy="3.5" r="2.4" fill="#fff"/><circle cx="5.5" cy="3.5" r="2.2" fill="#ef3340"/>' + [[7.2, 2], [8.4, 3], [8, 4.5], [6.4, 4.5], [6, 3]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r=".38" fill="#fff"/>`).join(''); break;
    case 'MY': b = Array.from({ length: 14 }, (_, k) => `<rect y="${k}" width="22" height="1" fill="${k % 2 ? '#fff' : '#cc0001'}"/>`).join('') + '<rect width="11" height="8" fill="#010066"/><circle cx="4.4" cy="4" r="2.6" fill="#fc0"/><circle cx="5.2" cy="4" r="2.2" fill="#010066"/>' + st(8.4, 4, 1.5, '#fc0'); break;
    case 'UM': b = '<rect width="22" height="14" fill="#0b6b3a"/><circle cx="11" cy="7" r="4.3" fill="none" stroke="#f2c500" stroke-width="1"/><circle cx="11" cy="7" r="1.6" fill="#f2c500"/>'; break;
  }
  if (b == null) return flagSVG(c, w, h);
  return `<svg class="flg" width="${w}" height="${h}" viewBox="0 0 22 14" aria-label="${esc(FLAG_N[c] || c)}"><title>${esc(FLAG_N[c] || c)}</title>${b}</svg>`;
}

/* devises suivies : code -> [nom, pays (drapeau), région, symbole de la paire contre USD] */
const CCY = {
  USD: ['Dollar américain', 'US', 'G10', null], EUR: ['Euro', 'EU', 'G10', 'EUR='], JPY: ['Yen japonais', 'JP', 'G10', 'JPY='], GBP: ['Livre sterling', 'GB', 'G10', 'GBP='],
  CHF: ['Franc suisse', 'CH', 'G10', 'CHF='], CAD: ['Dollar canadien', 'CA', 'G10', 'CAD='], AUD: ['Dollar australien', 'AU', 'G10', 'AUD='], NZD: ['Dollar néo-zélandais', 'NZ', 'G10', 'NZD='],
  SEK: ['Couronne suédoise', 'SE', 'G10', 'SEK='], NOK: ['Couronne norvégienne', 'NO', 'G10', 'NOK='], DKK: ['Couronne danoise', 'DK', 'EUR', 'DKK='],
  XOF: ['Franc CFA (BCEAO)', 'UM', 'AF', 'XOF='], NGN: ['Naira nigérian', 'NG', 'AF', 'NGN='], GHS: ['Cedi ghanéen', 'GH', 'AF', 'GHS='], ZAR: ['Rand sud-africain', 'ZA', 'AF', 'ZAR='],
  EGP: ['Livre égyptienne', 'EG', 'AF', 'EGP='], MAD: ['Dirham marocain', 'MA', 'AF', 'MAD='], KES: ['Shilling kényan', 'KE', 'AF', 'KES='],
  CNY: ['Yuan chinois', 'CN', 'AS', 'CNY='], HKD: ['Dollar de Hong Kong', 'HK', 'AS', 'HKD='], KRW: ['Won sud-coréen', 'KR', 'AS', 'KRW='], TWD: ['Dollar de Taïwan', 'TW', 'AS', 'TWD='],
  INR: ['Roupie indienne', 'IN', 'AS', 'INR='], SGD: ['Dollar de Singapour', 'SG', 'AS', 'SGD='], MYR: ['Ringgit malaisien', 'MY', 'AS', 'MYR='],
  MXN: ['Peso mexicain', 'MX', 'AM', 'MXN='], BRL: ['Réal brésilien', 'BR', 'AM', 'BRL='], ARS: ['Peso argentin', 'AR', 'AM', 'ARS='],
  ILS: ['Shekel israélien', 'IL', 'EM', 'ILS='], TRY: ['Livre turque', 'TR', 'EM', 'TRY='],
};
const CCY_REG = [['ALL', 'Toutes les régions'], ['G10', 'G10'], ['AF', 'Afrique'], ['AS', 'Asie'], ['AM', 'Amériques'], ['EM', 'Europe émergente et Moyen-Orient']];
/* XOF_EUR (parité fixe 655,957) est défini dans pages1.js */

/* valeur en dollars d'une unité de chaque devise : maintenant, veille, il y a une semaine, fin d'année précédente */
function fxUsd(W) {
  const R = Object.fromEntries((W.fx || []).map(r => [r.s, r])), YB = (W.yb && W.yb.v) || {}, H = W.h || {};
  const today = new Date().toISOString().slice(0, 10), wk = new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10);
  const inv = s => FX_INV.has(s), u = (s, q) => q == null || !(q > 0) ? null : inv(s) ? q : 1 / q;
  const out = { USD: { now: 1, d: 1, w: 1, y: 1, t: null } };
  for (const [c, meta] of Object.entries(CCY)) {
    const s = meta[3]; if (!s || !R[s] || !(R[s].last > 0)) continue; const r = R[s];
    const prev = r.prev > 0 ? r.prev : r.pct != null ? r.last / (1 + r.pct) : null;
    const hs = H[s] || {}, wd = Object.keys(hs).filter(d => d <= wk).sort().pop();
    out[c] = { now: u(s, r.last), d: u(s, prev), w: wd ? u(s, hs[wd]) : null, y: u(s, YB[s]), t: r.t, lo: u(s, inv(s) ? r.lo52 : r.hi52), hi: u(s, inv(s) ? r.hi52 : r.lo52), q: r, stale: r.t && String(r.t).slice(0, 10) < today };
  }
  /* FCFA : parité fixe avec l'euro, la cotation de marché du dollar n'en est que le reflet */
  if (out.EUR) { const e = out.EUR, f = v => v == null ? null : v / XOF_EUR; out.XOF = { now: f(e.now), d: f(e.d), w: f(e.w), y: f(e.y), t: e.t, lo: f(e.lo), hi: f(e.hi), peg: true, stale: e.stale }; }
  return out;
}
const fxDec = v => v == null ? 2 : v >= 1000 ? 2 : v >= 100 ? 3 : v >= 1 ? 4 : 5;
/* cotation « au certain » : la devise la plus forte en premier (EUR/USD 1,16 ; USD/JPY 151,20) */
function fxPair(a, b, U) {
  const x = U[a].now / U[b].now; if (!(x > 0)) return ['—', null];
  const prefer = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF'], ia = prefer.indexOf(a), ib = prefer.indexOf(b);
  const aFirst = ia >= 0 && (ib < 0 || ia < ib) ? true : ib >= 0 && (ia < 0 || ib < ia) ? false : x >= 1;
  return aFirst ? [`${a}/${b}`, x] : [`${b}/${a}`, 1 / x];
}

/* ------------------------------------------------------------------ WCRS : classement mondial des devises */
PAGES.WCRS = async (m, alive) => {
  const W = await WMKT(); if (!alive()) return; setTitle('World Currency Ranker');
  if (!W || !W.fx) { m.innerHTML = pn('Devises', 'WCRS', '<div class="empty">Cotations des changes en attente du prochain relevé (toutes les 15 minutes).</div>'); return; }
  const st = ST.wcrs = ST.wcrs || { b: 'USD', p: 'd', r: 'ALL' }, U_ = fxUsd(W);
  if (!U_[st.b]) st.b = 'USD';
  const P = [['d', '1 jour'], ['w', '1 semaine'], ['y', 'Depuis janv.']], B = U_[st.b];
  const ch = c => { const x = U_[c]; if (!x || x[st.p] == null || B[st.p] == null) return null; return (x.now / B.now) / (x[st.p] / B[st.p]) - 1; };
  const L = Object.keys(U_).filter(c => c !== st.b && (st.r === 'ALL' || CCY[c][2] === st.r || (st.r === 'G10' && c === 'USD'))).map(c => ({ c, v: ch(c) })).sort((a, b) => (b.v ?? -9) - (a.v ?? -9));
  const mx = Math.max(1e-6, ...L.map(x => Math.abs(x.v || 0))), up = L.filter(x => x.v > 0).length, dn = L.filter(x => x.v < 0).length;
  const dxy = (W.fx || []).find(r => r.s === '.DXY');
  const ctl = `<div class="tools weic"><span class="tlab">Devise de référence</span><select class="ofld" id="wcB">${Object.keys(U_).map(c => `<option value="${c}" ${st.b === c ? 'selected' : ''}>${c} · ${esc(CCY[c][0])}</option>`).join('')}</select>
    <span class="tlab">Période</span><select class="ofld" id="wcP">${P.map(([k, l]) => `<option value="${k}" ${st.p === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
    <span class="tlab">Région</span><select class="ofld" id="wcR">${CCY_REG.map(([k, l]) => `<option value="${k}" ${st.r === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
    <span class="gsp"></span><span class="dm">${up} en hausse · ${dn} en baisse contre ${st.b}</span></div>`;
  const rows = L.map((x, i) => { const c = x.c, u = U_[c], [pl, pv] = fxPair(c, st.b, U_), w = x.v == null ? 0 : Math.abs(x.v) / mx * 100;
    return `<tr data-fxc="${c}"><td class="l"><span class="rn">${i + 1})</span>${flag2(CCY[c][1], 18, 12)} <b class="wh">${c}</b></td><td class="l am">${esc(CCY[c][0])}</td><td class="l dm">${pl}</td><td class="wh">${num(pv, fxDec(pv))}${u.peg ? '<i class="qd">f</i>' : '<i class="qd">d</i>'}</td>
      <td>${x.v == null ? '<span class="dm">—</span>' : pc(x.v)}</td><td class="wcb"><span class="z"></span>${x.v == null ? '' : `<i class="${x.v >= 0 ? 'p' : 'n'}" style="width:${(w / 2).toFixed(1)}%"></i>`}</td><td class="dm">${qTime(u.t)}<i class="qd">${u.stale ? 'c' : ''}</i></td></tr>`; }).join('');
  const per = P.find(p => p[0] === st.p)[1].toLowerCase();
  m.innerHTML = ctl + `<div class="grid side">${pn(`Performance des devises contre ${st.b} · ${per}`, 'WCRS', `<div class="tw"><table class="t wcr"><thead><tr><th class="l">Devise</th><th class="l">Nom</th><th class="l">Paire</th><th>Cours</th><th>Var. %</th><th class="c">Appréciation / dépréciation contre ${st.b}</th><th>Heure</th></tr></thead><tbody>${rows || '<tr><td class="l dm" colspan="7">Aucune devise pour cette sélection.</td></tr>'}</tbody></table></div>`,
      { np: true, lect: `Variation de la valeur de chaque devise exprimée en ${st.b} : une barre verte signifie que la devise s’est appréciée contre ${st.b}. d = cotation différée ; c = dernière cotation d’une séance précédente ; f = parité fixe (le franc CFA vaut 1/655,957 euro). « 1 semaine » et « depuis janv. » : affichés quand la clôture de référence a été relevée. Clic sur une ligne : matrice des changes (FXC).` })}
    <div>${pn('Indice dollar et synthèse', 'WCRS', `<div class="kv2"><span>Indice dollar (DXY)</span><b class="wh">${dxy ? num(dxy.last, 3) : '—'}</b><span>Variation du jour</span><b>${dxy ? pc(dxy.pct) : '—'}</b><span>Depuis janv.</span><b>${dxy && W.yb && W.yb.v && W.yb.v['.DXY'] ? pc(dxy.last / W.yb.v['.DXY'] - 1) : '—'}</b><span>Plus forte hausse</span><b>${L[0] && L[0].v != null ? `${L[0].c} ${pc(L[0].v)}` : '—'}</b><span>Plus forte baisse</span><b>${(() => { const z = L.filter(x => x.v != null).slice(-1)[0]; return z ? `${z.c} ${pc(z.v)}` : '—'; })()}</b><span>Devises cotées</span><b>${Object.keys(U_).length}</b></div>`)}
      ${pn('Franc CFA', 'FX', `<div class="kv2"><span>EUR / XOF</span><b class="wh">655,957 <i class="qd">f</i></b>${U_.XOF ? `<span>USD / XOF</span><b class="wh">${num(1 / U_.XOF.now, 2)}</b><span>Var. du jour (XOF contre USD)</span><b>${U_.XOF.d ? pc(U_.XOF.now / U_.XOF.d - 1) : '—'}</b><span>Depuis janv. (XOF contre USD)</span><b>${U_.XOF.y ? pc(U_.XOF.now / U_.XOF.y - 1) : '—'}</b>` : ''}${U_.NGN ? `<span>XOF / NGN</span><b class="wh">${num(U_.XOF ? U_.XOF.now / U_.NGN.now : null, 4)}</b>` : ''}${U_.GHS ? `<span>1 000 XOF en GHS</span><b class="wh">${num(U_.XOF ? U_.XOF.now / U_.GHS.now * 1000 : null, 3)}</b>` : ''}</div>`, { lect: 'Le franc CFA suit l’euro : contre le dollar, il évolue exactement comme l’euro.' })}</div></div>`;
  $('wcB').onchange = e => { st.b = e.target.value; render(); }; $('wcP').onchange = e => { st.p = e.target.value; render(); }; $('wcR').onchange = e => { st.r = e.target.value; render(); };
  m.querySelectorAll('[data-fxc]').forEach(tr => tr.onclick = () => { ST.fxc = Object.assign(ST.fxc || {}, { hl: tr.dataset.fxc }); go('FXC'); });
};

/* ------------------------------------------------------------------ FXC : matrice des changes croisés */
const FXC_SETS = { G10: ['USD', 'EUR', 'JPY', 'GBP', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK'], AF: ['USD', 'EUR', 'XOF', 'NGN', 'GHS', 'ZAR', 'EGP', 'MAD', 'KES'], AS: ['USD', 'EUR', 'JPY', 'CNY', 'HKD', 'KRW', 'TWD', 'INR', 'SGD', 'MYR'],
  AM: ['USD', 'EUR', 'CAD', 'MXN', 'BRL', 'ARS'], UE: ['USD', 'EUR', 'XOF', 'GBP', 'JPY', 'CNY', 'CHF', 'NGN', 'GHS', 'ZAR'] };
PAGES.FXC = async (m, alive) => {
  const W = await WMKT(); if (!alive()) return; setTitle('Currency Rates Matrix');
  if (!W || !W.fx) { m.innerHTML = pn('Changes croisés', 'FXC', '<div class="empty">Cotations des changes en attente du prochain relevé (toutes les 15 minutes).</div>'); return; }
  const st = ST.fxc = Object.assign({ set: 'UE', v: 'q', hl: null }, ST.fxc || {}), U_ = fxUsd(W);
  const C = (FXC_SETS[st.set] || FXC_SETS.UE).filter(c => U_[c]);
  const V = [['q', 'Cours'], ['d', 'Var. % du jour'], ['y', 'Var. % depuis janv.']];
  const cell = (a, b) => { if (a === b) return '<td class="dg">—</td>'; const x = U_[a].now / U_[b].now;
    if (st.v === 'q') return `<td class="wh${st.hl && (a === st.hl || b === st.hl) ? ' hx' : ''}">${num(x, fxDec(x))}</td>`;
    const A = U_[a][st.v], Bv = U_[b][st.v]; if (A == null || Bv == null) return '<td class="dm">—</td>'; const v = x / (A / Bv) - 1, k = Math.min(1, Math.abs(v) / (st.v === 'd' ? .01 : .1));
    return `<td style="background:${v >= 0 ? `rgba(50,199,76,${(.12 + .5 * k).toFixed(2)})` : `rgba(255,67,61,${(.12 + .5 * k).toFixed(2)})`}" class="wh">${v > 0 ? '+' : ''}${num(v * 100, 2)}%</td>`; };
  m.innerHTML = `<div class="tools weic"><span class="tlab">Groupe</span><select class="ofld" id="fxS">${[['UE', 'Franc CFA et partenaires'], ['G10', 'G10'], ['AF', 'Afrique'], ['AS', 'Asie'], ['AM', 'Amériques']].map(([k, l]) => `<option value="${k}" ${st.set === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <span class="tlab">Afficher</span><select class="ofld" id="fxV">${V.map(([k, l]) => `<option value="${k}" ${st.v === k ? 'selected' : ''}>${l}</option>`).join('')}</select><span class="gsp"></span><span class="dm">relevé ${new Date(W.ts * 1000).toLocaleString('fr-FR', { timeZone: 'Africa/Abidjan', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })} GMT</span></div>
    ${pn(`Matrice des changes croisés · ${V.find(x => x[0] === st.v)[1]}`, 'FXC', `<div class="tw"><table class="t fxm"><thead><tr><th class="l"></th>${C.map(c => `<th class="c${c === st.hl ? ' hx' : ''}" data-fxh="${c}">${flag2(CCY[c][1], 16, 10)}<br>${c}</th>`).join('')}</tr></thead><tbody>${C.map(a => `<tr><td class="l${a === st.hl ? ' hx' : ''}" data-fxh="${a}">${flag2(CCY[a][1], 16, 10)} <b class="am">${a}</b></td>${C.map(b => cell(a, b)).join('')}</tr>`).join('')}</tbody></table></div>`,
      { np: true, lect: `Lecture : 1 unité de la devise en ligne vaut le nombre indiqué d’unités de la devise en colonne. Taux croisés calculés à partir des cotations différées de chaque devise contre le dollar ; le franc CFA est calculé à la parité fixe de 655,957 FCFA pour 1 euro. En variation : appréciation (vert) ou dépréciation (rouge) de la devise en ligne contre la devise en colonne. Classement : WCRS.` })}`;
  $('fxS').onchange = e => { st.set = e.target.value; render(); }; $('fxV').onchange = e => { st.v = e.target.value; render(); };
  m.querySelectorAll('[data-fxh]').forEach(x => x.onclick = () => { st.hl = st.hl === x.dataset.fxh ? null : x.dataset.fxh; render(); });
};

/* ------------------------------------------------------------------ GC : écran « Graph Curves » — courbes, courbe de comparaison en pointillés,
   histogramme des variations en points de base sous le graphique, légende numérotée des courbes à droite */
const GC_OLD = PAGES.GC;
/* points de base signés, sans « −0,0 » */
const bpS = (v, d = 1) => { if (v == null || !isFinite(v)) return '<span class="dm">—</span>'; const r = +v.toFixed(d) || 0; return `<span class="${cls(r)}">${r > 0 ? '+' : ''}${num(r, d)}</span>`; };
PAGES.GC = async (m, alive) => {
  if (tabState('GC', 'c') === 'h') return GC_OLD(m, alive);
  const C = await getJSON('umoa_curves.json').catch(() => null); if (!alive()) return; setTitle('Graph Curves');
  if (!C || !C.curves || !Object.keys(C.curves).length) { m.innerHTML = pn('Courbes souveraines', 'GC', '<div class="empty">Courbes des États de l’UEMOA en attente de la collecte du soir.</div>'); return; }
  setTabs([['c', 'Courbes par pays'], ['h', 'Évolution d’un pays']], 'c', k => { ST.tab.GC = k; render(); });
  const ds = Object.keys(C.curves).sort(), dL = ds[ds.length - 1], cur = C.curves[dL].c, ctys = Object.keys(cur);
  const st = ST.gc = ST.gc || {}; st.sel = (st.sel || ctys.slice(0, 4)).filter(c => ctys.includes(c)); if (!st.sel.length) st.sel = ctys.slice(0, 1);
  st.kind = st.kind || 3; if (!ctys.includes(st.foc)) { st.foc = ctys.find(c => gcNorm(c) === "cote d'ivoire") || st.sel[0]; if (!st.sel.includes(st.foc)) st.sel = [st.foc].concat(st.sel).slice(0, 4); } if (!ds.includes(st.cmp) || st.cmp === dL) st.cmp = ds.length > 1 ? ds[ds.length - 2] : null;
  st.cty = st.foc; const COLS = ['#f9a33a', '#5fd0ea', '#2fd26a', '#ff7ab2', '#b69cff', '#ffd200', '#ff3d4d', '#3fd3c0'], col = c => COLS[ctys.indexOf(c) % 8];
  const yrs = s => { const m_ = String(s).match(/(\d+)\s*(mois|an)/); return m_ ? +m_[1] / (m_[2] === 'mois' ? 12 : 1) : 99; };
  const mats = [...new Set(ctys.flatMap(c => cur[c].map(p => p[0])))].sort((a, b) => yrs(a) - yrs(b));
  const at = (d, c, lab) => { const p = gcFind((C.curves[d] || {}).c, c); const q = p && p.find(x => x[0] === lab); return q ? q[st.kind] : null; };
  const ten = c => at(dL, c, '10 ans') ?? (cur[c].filter(p => p[1] <= 10).slice(-1)[0] || [])[st.kind] ?? null;
  const tenLab = c => (cur[c].find(p => p[0] === '10 ans') || cur[c].filter(p => p[1] <= 10).slice(-1)[0] || [])[0];
  const cmpLab = d => { if (!d) return '—'; const days = Math.round((new Date(dL) - new Date(d)) / 864e5); return `${fds(d)} (${days < 45 ? '−1 mois' : days < 120 ? '−3 mois' : days < 250 ? '−6 mois' : '−1 an'})`; };
  const foc = st.foc, chg = mats.map(l => { const a = at(dL, foc, l), b = st.cmp ? at(st.cmp, foc, l) : null; return a != null && b != null ? (a - b) * 1e4 : NaN; });
  const legend = ctys.map((c, i) => { const on = st.sel.includes(c), t = ten(c), tl = tenLab(c), tp = st.cmp && tl ? at(st.cmp, c, tl) : null;
    return `<tr class="${c === foc ? 'cur' : ''}"><td class="l"><span class="rn">${i + 1})</span><label class="gck"><input type="checkbox" data-cy="${esc(c)}" ${on ? 'checked' : ''}><i></i></label><span class="gsw" style="background:${col(c)}"></span></td><td class="l am" data-fo="${esc(c)}" style="cursor:pointer">${esc(ctyName(c))}</td><td class="dm">${esc(tl || '')}</td><td class="wh">${t != null ? num(t * 100, 3) : '—'}</td><td>${t != null && tp != null ? bpS((t - tp) * 1e4) : '<span class="dm">—</span>'}</td></tr>`; }).join('');
  const c2 = st.sel.find(c => c !== foc), act = mats.filter(l => at(dL, foc, l) != null);
  const tbl = `<table class="t"><thead><tr><th class="l">Maturité</th><th>Taux %</th><th>au ${st.cmp ? fds(st.cmp) : '—'}</th><th>Var. pb</th>${c2 ? `<th>Écart vs ${esc(ctyName(c2))} (pb)</th>` : ''}</tr></thead><tbody>${act.map(l => { const a = at(dL, foc, l), b = st.cmp ? at(st.cmp, foc, l) : null, o = c2 ? at(dL, c2, l) : null;
    return `<tr><td class="l am">${esc(l)}</td><td class="wh">${num(a * 100, 3)}</td><td class="dm">${b == null ? '—' : num(b * 100, 3)}</td><td>${b != null ? bpS((a - b) * 1e4) : '—'}</td>${c2 ? `<td>${o != null ? bpS((a - o) * 1e4, 0) : '—'}</td>` : ''}</tr>`; }).join('')}</tbody></table>`;
  m.innerHTML = `<div class="tools weic"><span class="tlab">Taux</span><select class="ofld" id="gcK"><option value="3" ${st.kind === 3 ? 'selected' : ''}>Après lissage</option><option value="2" ${st.kind === 2 ? 'selected' : ''}>Zéro-coupon</option></select>
      <span class="tlab">Comparer avec</span><select class="ofld" id="gcD">${ds.filter(d => d !== dL).reverse().map(d => `<option value="${d}" ${st.cmp === d ? 'selected' : ''}>${cmpLab(d)}</option>`).join('')}</select>
      <span class="tlab">Courbe de référence</span><span class="wh">${esc(ctyName(foc))}</span><span class="gsp"></span><span class="dm">courbes au ${esc(C.curves[dL].asof || fds(dL))} · ${ds.length} dates</span></div>
    <div class="grid side gcg"><div>${pn(`Courbes souveraines UEMOA (FCFA) · ${st.kind === 3 ? 'taux après lissage' : 'taux zéro-coupon'}`, 'GC', cvb('gcC', 330), { np: true })}
      ${pn(`Variation de la courbe ${esc(ctyName(foc))} depuis le ${st.cmp ? fds(st.cmp) : '—'} (points de base)`, 'GC', cvb('gcB', 150), { np: true, lect: `Trait plein : courbes au ${esc(C.curves[dL].asof || fds(dL))}. Pointillés : courbe de ${esc(ctyName(foc))} à la date de comparaison. 1 pb = 0,01 %.` })}</div>
      <div>${pn('Courbes', 'GC', `<table class="t gcl"><thead><tr><th class="l"></th><th class="l">État</th><th class="l">Pt.</th><th>Taux %</th><th>Var. pb</th></tr></thead><tbody>${legend}</tbody></table>`, { np: true, lect: 'Case : afficher la courbe. Clic sur le nom : courbe de référence (pointillés et histogramme).' })}
      ${pn(`${esc(ctyName(foc))} : taux par maturité`, 'GC', `<div class="tw">${tbl}</div>`, { np: true })}</div></div>`;
  gcDraw($('gcC'), st.sel.map(c => ({ lab: ctyName(c), col: col(c), pts: (cur[c] || []).map(p => [p[1], p[st.kind]]), w: c === foc ? 2.2 : 1.6 }))
    .concat(st.cmp && gcFind(C.curves[st.cmp].c, foc) ? [{ lab: `${ctyName(foc)} ${fds(st.cmp)}`, col: col(foc), pts: gcFind(C.curves[st.cmp].c, foc).map(p => [p[1], p[st.kind]]), w: 1.2, dash: [4, 3] }] : []));
  const mxc = Math.max(0, ...chg.filter(isFinite).map(Math.abs)), dch = mxc < 5 ? 1 : 0;
  barChart($('gcB'), { labels: mats.map(l => l.replace(' mois', 'M').replace(/ ans?/, 'A')), values: chg, fmt: v => { const r = +v.toFixed(dch) || 0; return (r > 0 ? '+' : '') + num(r, dch); }, axisFmt: v => num(v, dch), labelsOnBars: true, padB: 18 });
  if (mxc < .05 && chg.some(isFinite)) $('gcB').insertAdjacentHTML('beforeend', `<div class="gcz">Courbe ${esc(ctyName(foc))} inchangée entre le ${fds(st.cmp)} et le ${fds(dL)}.</div>`);
  $('gcK').onchange = e => { st.kind = +e.target.value; render(); }; const gd = $('gcD'); if (gd) gd.onchange = e => { st.cmp = e.target.value; render(); };
  m.querySelectorAll('input[data-cy]').forEach(b => b.onchange = () => { const c = b.dataset.cy; st.sel = b.checked ? st.sel.concat([c]) : st.sel.filter(x => x !== c); if (!st.sel.length) st.sel = [c]; render(); });
  m.querySelectorAll('[data-fo]').forEach(b => b.onclick = () => { st.foc = b.dataset.fo; if (!st.sel.includes(st.foc)) st.sel = [st.foc].concat(st.sel); else st.sel = [st.foc].concat(st.sel.filter(x => x !== st.foc)); render(); });
};

/* ------------------------------------------------------------------ SRCH : écran « Fixed Income Search » — critères numérotés avec le nombre de
   titres retenus après chacun, tableau de résultats numéroté et trié, fiche prix ↔ rendement (YAS) du titre choisi */
PAGES.SRCH = async (m, alive) => {
  const B = await getJSON('bonds.json').catch(() => null); if (!alive()) return; setTitle('Fixed Income Search');
  if (!B || !B.rows) { m.innerHTML = pn('Obligations UEMOA', 'SRCH', '<div class="empty">Cotations obligataires en attente du prochain relevé (toutes les 15 minutes).</div>'); return; }
  const D = { live: '1', typ: 'ALL', cty: 'ALL', iss: '', c0: '', c1: '', y0: '', y1: '', r0: '', par: 'ALL' };
  const st = ST.srch2 = ST.srch2 || { f: Object.assign({}, D), sort: 'mat', dir: 1, sel: null };
  const now = new Date(), rows = B.rows.map(b => ({ b, c: bondCalc(b, now), cty: CTY_OBL[b.code.split('.')[0]] || '' }));
  const F = st.f, nb = v => { const x = parseFloat(String(v).replace(',', '.')); return isFinite(x) ? x : null; };
  const ctys = [...new Set(rows.map(r => r.cty).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'fr'));
  const CR = [
    ['live', 'Statut', `<select class="ofld" data-f="live"><option value="1" ${F.live === '1' ? 'selected' : ''}>En vie</option><option value="0" ${F.live === '0' ? 'selected' : ''}>Toutes, y compris échues</option></select>`, r => F.live !== '1' || !r.c.matured],
    ['typ', 'Type d’émetteur', `<select class="ofld" data-f="typ">${[['ALL', 'Tous'], ['État', 'États'], ['Régional', 'Organismes régionaux'], ['Privé', 'Émetteurs privés']].map(([k, l]) => `<option value="${k}" ${F.typ === k ? 'selected' : ''}>${l}</option>`).join('')}</select>`, r => F.typ === 'ALL' || r.b.typ === F.typ],
    ['cty', 'Pays', `<select class="ofld" data-f="cty"><option value="ALL">Tous</option>${ctys.map(c => `<option ${F.cty === c ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select>`, r => F.cty === 'ALL' || r.cty === F.cty],
    ['iss', 'Émetteur ou code', `<input class="ofld" data-f="iss" value="${esc(F.iss)}" placeholder="TPCI, BOAD, SONATEL…">`, r => !F.iss || (r.b.code + ' ' + r.b.n + ' ' + (r.b.iss || '')).toLowerCase().includes(F.iss.toLowerCase())],
    ['cpn', 'Coupon (%)', `<input class="ofld n" data-f="c0" value="${esc(F.c0)}" placeholder="min"> à <input class="ofld n" data-f="c1" value="${esc(F.c1)}" placeholder="max">`, r => (nb(F.c0) == null || (r.b.cpn != null && r.b.cpn * 100 >= nb(F.c0))) && (nb(F.c1) == null || (r.b.cpn != null && r.b.cpn * 100 <= nb(F.c1)))],
    ['mat', 'Échéance (année)', `<input class="ofld n" data-f="y0" value="${esc(F.y0)}" placeholder="de"> à <input class="ofld n" data-f="y1" value="${esc(F.y1)}" placeholder="à">`, r => (nb(F.y0) == null || (r.b.y1 && r.b.y1 >= nb(F.y0))) && (nb(F.y1) == null || (r.b.y1 && r.b.y1 <= nb(F.y1)))],
    ['ytm', 'Rendement estimé ≥ (%)', `<input class="ofld n" data-f="r0" value="${esc(F.r0)}" placeholder="min">`, r => nb(F.r0) == null || (r.c.ok && r.c.ytm * 100 >= nb(F.r0))],
    ['par', 'Cours / nominal', `<select class="ofld" data-f="par">${[['ALL', 'Tous'], ['eq', 'Au pair'], ['lo', 'Sous le pair'], ['hi', 'Au-dessus du pair']].map(([k, l]) => `<option value="${k}" ${F.par === k ? 'selected' : ''}>${l}</option>`).join('')}</select>`, r => F.par === 'ALL' || (r.c.pctN != null && (F.par === 'eq' ? Math.abs(r.c.pctN - 1) < .005 : F.par === 'lo' ? r.c.pctN < .995 : r.c.pctN > 1.005))]];
  let L = rows; const cnt = CR.map(c => (L = L.filter(c[3])).length);
  const key = { iss: r => r.b.iss || r.b.code, code: r => r.b.code, cpn: r => r.b.cpn, mat: r => r.c.T ? +r.c.T : r.b.y1 ? r.b.y1 * 1e10 : null, px: r => r.c.pctN, ytm: r => r.c.ytm, dur: r => r.c.mod, cy: r => r.c.cy };
  L.sort((a, b) => { const A = key[st.sort](a), Bv = key[st.sort](b); if (A == null) return 1; if (Bv == null) return -1; return (typeof A === 'string' ? A.localeCompare(Bv, 'fr') : A - Bv) * st.dir; });
  const sel = rows.find(r => r.b.code === st.sel) || L[0];
  const th = (k, l, c = '') => `<th data-k="${k}" class="${c}${st.sort === k ? ' on' : ''}" style="cursor:pointer">${l}${st.sort === k ? (st.dir > 0 ? ' ▲' : ' ▼') : ''}</th>`;
  const ok = L.filter(r => r.c.ok), avg = ok.length ? ok.reduce((s, r) => s + r.c.ytm, 0) / ok.length : null;
  const crit = `<table class="t scr"><thead><tr><th class="l">Critère</th><th class="l">Valeur</th><th>Titres</th></tr></thead><tbody>${CR.map((c, i) => `<tr><td class="l"><span class="rn">${i + 1})</span>${c[1]}</td><td class="l">${c[2]}</td><td class="wh">${num(cnt[i], 0)}</td></tr>`).join('')}</tbody></table>`;
  const res = `<table class="t srt"><thead><tr><th class="l">#</th>${th('iss', 'Émetteur', 'l')}${th('code', 'Code', 'l')}${th('cpn', 'Cpn')}${th('mat', 'Échéance')}<th class="l">Type</th><th class="l">Pays</th><th class="l">Dev.</th>${th('px', 'Cours %')}${th('ytm', 'Rdt est.')}${th('cy', 'Rdt cour.')}${th('dur', 'Sensib.')}</tr></thead><tbody>
    ${L.map((r, i) => `<tr data-ob="${esc(r.b.code)}" class="${sel && r.b.code === sel.b.code ? 'cur' : ''}" style="cursor:pointer"><td class="l dm">${i + 1})</td><td class="l am" title="${esc(r.b.n)}">${esc(r.b.iss || r.b.code.split('.')[0])}</td><td class="l wh">${esc(r.b.code)}</td><td>${r.b.cpn != null ? num(r.b.cpn * 100, 3) : '<span class="dm">var.</span>'}</td>
      <td>${r.c.T ? fds(r.c.T.toISOString().slice(0, 10)) : r.b.y1 ? r.b.y1 : '—'}</td><td class="l dm">${esc(r.b.typ || '—')}</td><td class="l dm">${esc(r.cty || '—')}</td><td class="l dm">XOF</td><td class="wh">${r.c.pctN ? num(r.c.pctN * 100, 2) : '—'}</td><td class="yl">${r.c.ok ? num(r.c.ytm * 100, 3) : `<span class="dm" title="${esc(r.c.why || '')}">n.d.</span>`}</td><td>${r.c.ok ? num(r.c.cy * 100, 2) : '—'}</td><td>${r.c.ok ? num(r.c.mod, 2) : '—'}</td></tr>`).join('') || '<tr><td class="l dm" colspan="12">Aucune obligation ne remplit tous les critères.</td></tr>'}</tbody></table>`;
  m.innerHTML = `<div class="tools ttb"><span class="tlab">Résultats</span><b class="wh">${L.length}</b><span class="dm">titres sur ${rows.length}</span><span class="tlab">Rendement estimé moyen</span><b class="yl">${avg != null ? num(avg * 100, 2) + ' %' : '—'}</b><span class="gsp"></span><button class="tb" id="srR">2) Réinitialiser les critères</button><span class="dm">relevé ${new Date(B.ts * 1000).toLocaleString('fr-FR', { timeZone: 'Africa/Abidjan', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })} GMT</span></div>
    <div class="grid srg"><div>${pn('Critères de recherche', 'SRCH', crit, { np: true, lect: 'Chaque critère s’ajoute aux précédents ; la colonne « Titres » donne le nombre d’obligations encore retenues.' })}<div id="obD"></div></div>
      ${pn(`Obligations cotées · ${L.length} résultats`, 'SRCH', `<div class="tw" style="max-height:calc(100vh - 250px - var(--nwh, 90px))">${res}</div>`, { np: true, lect: '<b>Rendement estimé</b> : ni la date exacte d’échéance ni l’échéancier d’amortissement ne sont publiés. Hypothèses : nominal restant = dernier coupon ÷ taux du coupon (× 2 si le cours indique un coupon semestriel), remboursement in fine à la date anniversaire du dernier coupon dans l’année d’échéance du nom, base exact/365. Obligations amortissables : rendement non calculé. Quand le cours égale le nominal, le rendement est égal au coupon : beaucoup de lignes cotent au pair faute d’échanges.' })}</div>`;
  const yas = r => { const c = r.c, b = r.b;
    return pn(`${esc(b.code)} · ${esc(b.n)}`, 'YAS', `<div class="kv2"><span>Émetteur</span><b>${esc(b.iss || '')}${r.cty ? ' · ' + esc(r.cty) : ''}</b><span>Coupon</span><b>${b.cpn != null ? num(b.cpn * 100, 3) + ' %' : 'variable'}</b><span>Cotation depuis le</span><b>${esc(b.em || '—')}</b><span>Dernier coupon payé</span><b>${b.lp_d ? esc(b.lp_d) + ' · ' + num(b.lp_v, 2) : '—'}</b><span>Cours (FCFA)</span><b class="wh">${num(b.px, 0)}</b><span>Coupon couru</span><b>${num(b.cc, 2)}</b>
      <span>Nominal restant estimé</span><b class="est">${c.N ? num(c.N, 0) : '—'}${c.f === 2 ? ' · semestriel' : ''}</b><span>Échéance estimée</span><b class="est">${c.T ? fds(c.T.toISOString().slice(0, 10)) : '—'}</b><span>Vie résiduelle</span><b>${c.life ? num(c.life, 2) + ' ans' : '—'}</b>
      <span>Rendement actuariel estimé</span><b class="yl">${c.ok ? num(c.ytm * 100, 3) + ' %' : 'n.d. (' + esc(c.why || '') + ')'}</b><span>Duration de Macaulay</span><b>${c.ok ? num(c.mac, 2) + ' ans' : '—'}</b><span>Sensibilité</span><b>${c.ok ? num(c.mod, 2) : '—'}</b></div>
      ${c.ok ? `<div class="form" style="margin-top:6px"><label>Rendement visé (%)<input id="ysY" value="${num(c.ytm * 100, 2)}"></label><label>Cours correspondant<input id="ysP" disabled></label></div>` : ''}`, { lect: 'Prix ↔ rendement sur les mêmes flux estimés.' }); };
  const show = code => { const r = rows.find(x => x.b.code === code); if (!r) return; st.sel = code; $('obD').innerHTML = yas(r); m.querySelectorAll('[data-ob]').forEach(tr => tr.classList.toggle('cur', tr.dataset.ob === code));
    const y = $('ysY'); if (y && r.c.ok) { const upd = () => { const v = parseFloat(y.value.replace(',', '.')) / 100; if (!isFinite(v)) return; const p = r.c.cf.reduce((s, c) => s + c.v / Math.pow(1 + v, c.t), 0) - (r.b.cc || 0); $('ysP').value = num(p, 0) + ' FCFA (' + num(p / r.c.N * 100, 2) + ' %)'; }; y.oninput = upd; upd(); } };
  m.querySelectorAll('[data-ob]').forEach(tr => tr.onclick = () => show(tr.dataset.ob)); if (sel) show(sel.b.code);
  m.querySelectorAll('th[data-k]').forEach(t => t.onclick = () => { const k = t.dataset.k; st.dir = st.sort === k ? -st.dir : (k === 'ytm' || k === 'cpn' ? -1 : 1); st.sort = k; render(); });
  m.querySelectorAll('[data-f]').forEach(x => { const ap = () => { F[x.dataset.f] = x.value.trim(); render(); }; if (x.tagName === 'SELECT') x.onchange = ap; else x.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); ap(); } }; if (x.tagName === 'INPUT') x.onblur = () => { if (x.value.trim() !== F[x.dataset.f]) ap(); }; });
  $('srR').onclick = () => { st.f = Object.assign({}, D); render(); };
};

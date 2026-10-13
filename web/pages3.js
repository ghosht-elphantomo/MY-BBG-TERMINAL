/* ================= FQT — menu du titre, aide, fonctions transverses ================= */

/* ------------------------------------------------------------------ MENU (ticker + Entrée) */
PAGES.MENU = async m => {
  const s = sec(ST.sec); let n = 0;
  const groups = MENU_GROUPS.map(([g, codes]) => `<div class="mg"><h4>${g}</h4>${codes.map(c => { n++; const why = avail(c, s);
    return `<button class="mi${why ? ' off' : ''}" data-fn="${c}"><em>${n})</em><b>${c}</b><span>${FN[c][0]}</span><small>${why ? 'Non disponible : ' + esc(why) : esc(FN[c][3])}</small></button>`; }).join('')}</div>`).join('');
  const kv = [['Dernier', `${px(s, s.last)} ${s.ccy}`], ['Variation', pc(s.pct)], ['1 mois', pc(s.r1m, 1)], ['YTD', pc(s.ytd, 1)], ['1 an', pc(s.r1y, 1)], ['3 ans', pc(s.r3y, 1)],
    ['Plus haut / bas 52 sem.', `${px(s, s.hi52)} / ${px(s, s.lo52)}`], ['Écart au record', pc(s.dd, 1)], ['Volatilité 1 an', s.vol != null ? num(s.vol * 100, 1) + ' %' : '—'],
    ['Bêta / ' + (s.bench || '—'), num(s.beta, 2)], s.mcap ? ['Capitalisation', big(s.mcap) + ' ' + (s.mkt === 'BRVM' ? 'XOF' : 'USD')] : null, s.per ? ['PER', num(s.per, 1)] : null,
    s.yld ? ['Rendement', num(s.yld * 100, 2) + ' %'] : null, ['Historique', `${fd(s.first)} → ${fd(s.dt)}`]].filter(Boolean);
  m.innerHTML = `<div class="grid side">${pn(`${s.tk} · menu des fonctions`, 'MENU', `<div class="mgrid">${groups}</div>`, { lect: 'Cliquez une fonction, ou tapez son numéro puis <b>Entrée</b>. Depuis n’importe où : <b>' + esc(s.id) + '</b> + espace affiche cette liste dans la ligne de commande.' })}
    ${pn('Aperçu', s.id, `<div class="kv2">${kv.map(([a, b]) => `<span>${a}</span><b>${b}</b>`).join('')}</div><div class="cv" id="mnS" style="height:120px;margin-top:8px"></div>`, { lect: `${esc(s.n)}${s.grp ? ' · ' + esc(s.grp) : ''}${s.cty ? ' · ' + esc(Q.sum.cty[s.cty] || s.cty) : ''}` })}</div>`;
  const S = await series(s.id); const k = Math.max(0, S.c.length - 260);
  new TSChart($('mnS'), { panes: [{ h: 1 }], padR: 50, padB: 16 }).set({ x: S.x.slice(k), series: [{ type: 'area', y: S.c.slice(k), color: CL.amber }] });
};

/* ------------------------------------------------------------------ HELP */
PAGES.HELP = async m => {
  const row = k => `<tr data-fn="${k}" style="cursor:pointer"><td class="l tk">${k}</td><td class="l wh">${FN[k][0]}</td><td class="l nm">${esc(FN[k][3])}</td><td class="l am">${FN[k][1] === 'sec' ? 'SNTS ' + k : k} &lt;GO&gt;</td></tr>`;
  const t = (title, keys) => pn(title, 'HELP', `<table class="t"><thead><tr><th class="l">Code</th><th class="l">Fonction</th><th class="l">Contenu</th><th class="l">À taper</th></tr></thead><tbody>${keys.map(row).join('')}</tbody></table>`, { np: true });
  /* écrans regroupés : onglets (cliquables) et anciens codes encore acceptés */
  const exOf = (f, k) => Object.entries(FN_ALIAS).filter(([, a]) => a[0] === f && (k == null ? !a[1] : a[1] === k)).map(([c]) => c);
  const grp = Object.entries(FN_TABS).map(([f, L]) => `<tr><td class="l tk" data-fn="${f}" style="cursor:pointer">${f}</td><td class="l wh">${esc(FN[f][4])}</td><td class="l">${L.map(([k, l], i) => { const ex = exOf(f, k); const sc = Object.entries(FN_SHORT).filter(([, a]) => a[0] === f && a[1] === k).map(([c]) => c); return `<span class="cfl" data-fn="${f}" data-t="${k}" style="cursor:pointer">${i + 1}) ${esc(l)}</span>${ex.length ? ` <span class="dm">(ex-${ex.join(', ex-')})</span>` : ''}${sc.length ? ` <span class="dm">· raccourci ${sc.join(', ')}</span>` : ''}`; }).join('<br>')}</td></tr>`).join('')
    + Object.keys(FN).filter(f => !FN_TABS[f] && exOf(f).length).map(f => `<tr><td class="l tk" data-fn="${f}" style="cursor:pointer">${f}</td><td class="l wh">${esc(FN[f][4])}</td><td class="l"><span class="dm">nouveau nom de ${exOf(f).join(', ')}</span></td></tr>`).join('');
  m.innerHTML = `<div class="grid c2">${t('Fonctions de marché (touches du haut)', ['MONITOR', 'NEWS'].concat(MKT_KEYS.filter(k => k !== 'NEWS' && k !== 'MONITOR')))}${t('Fonctions d’un titre (onglets sous la cotation)', ['MENU'].concat(SEC_TABS))}</div>
    ${pn('Écrans regroupés · onglets et anciens codes', 'HELP', `<table class="t"><thead><tr><th class="l">Code</th><th class="l">Écran</th><th class="l">Onglets (clic pour ouvrir)</th></tr></thead><tbody>${grp}</tbody></table>`, { np: true, lect: `Ces écrans réunissent des fonctions qui faisaient doublon : l’onglet 1 est la vue principale, les autres sont des options. Les anciens codes (${Object.keys(FN_ALIAS).join(', ')}) restent acceptés dans la ligne de commande et dans les liens : ils ouvrent directement le bon écran et le bon onglet. Dans un écran à onglets, le numéro de l’onglet + Entrée l’ouvre aussi.` })}
    ${pn('Utilisation', 'HELP', `<div class="lectb">
      <p><b>Ligne de commande.</b> Tapez n’importe où : le texte va dans la ligne de commande. <b>SNTS</b> + Entrée ouvre le menu du titre ; <b>SNTS</b> + espace (ou Tab) affiche ses fonctions ; <b>SNTS FA</b> + Entrée ouvre directement l’analyse financière. Une fonction de marché seule (<b>FG</b>, <b>NEWS</b>, <b>CORR</b>…) s’ouvre telle quelle. Dans un menu, un numéro + Entrée ouvre la fonction correspondante. <b>Échap</b> revient à MONITOR.</p>
      <p><b>Graphiques.</b> Trackpad : deux doigts à l’horizontale = défilement, à la verticale = zoom doux, pincer = zoom. Souris : molette = zoom, glisser = défilement. Double-clic = vue initiale.</p>
      <p><b>Données.</b> Chaque écran indique sa source et sa date. Une donnée absente est marquée « n.d. » avec la raison ; aucune valeur n’est extrapolée sans être signalée comme estimation.</p></div>`)}`;
};

/* ------------------------------------------------------------------ CORR (BRVM × monde, paire au choix, valeur de référence) */
function weeklyReturns(W) {
  if (W._R) return W._R; const R = {};
  for (const [id, col] of Object.entries(W.s)) R[id] = col.map((v, i) => i && v != null && col[i - 1] != null && col[i - 1] > 0 && v > 0 ? Math.log(v / col[i - 1]) : null);
  return (W._R = R);
}
/* Corrélation de deux séries de rendements ; lag = 1 ajoute les covariances décalées d'une semaine (correction de Dimson pour cotations non synchrones). */
function corrPair(x, y, a, b, lag) {
  const m = (u, v, s) => { let sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0, k = 0; for (let t = Math.max(a, 1); t < b; t++) { const p = u[t], q = v[t + s]; if (p == null || q == null) continue; sx += p; sy += q; sxx += p * p; syy += q * q; sxy += p * q; k++; }
    return k ? { cv: sxy / k - sx * sy / k / k, vx: sxx / k - sx * sx / k / k, vy: syy / k - sy * sy / k / k, k, mx: sx / k, my: sy / k } : null; };
  const z = m(x, y, 0); if (!z || z.k < Math.max(20, (b - a) * .45) || z.vx <= 0 || z.vy <= 0) return null;
  let cv = z.cv; if (lag) { const l1 = m(x, y, -1), l2 = m(x, y, 1); cv += (l1 ? l1.cv : 0) + (l2 ? l2.cv : 0); }
  return { r: U.clamp(cv / Math.sqrt(z.vx * z.vy), -1, 1), beta: cv / z.vy, n: z.k, alpha: z.mx - (cv / z.vy) * z.my };
}
PAGES.CORR = async (m, alive) => {
  const W = await getJSON('weekly.json'); if (!alive()) return; const cs = ST.corr, T = W.w.length, R = weeklyReturns(W), has = id => !!W.s[id];
  if (!['BRVMW', 'BRVM', 'MIX', 'US', 'REF'].includes(cs.u)) cs.u = 'BRVMW'; cs.ord = cs.ord || 'grp';
  const main = ['BRVMC', 'BRVM30', 'BRVMPR', 'BRVMPA'].filter(has);
  const bIdx = main.concat(secsWhere(s => s.mkt === 'BRVM' && s.cls === 'Index' && !main.includes(s.id) && has(s.id) && !/ancien/i.test(s.n || '')).map(s => s.id));
  const bStk = secsWhere(s => s.mkt === 'BRVM' && s.cls === 'Equity' && has(s.id)).sort((p, q) => (q.mcap || 0) - (p.mcap || 0)).map(s => s.id);
  const world = ['SPY', 'QQQ', 'VTI', 'IWM', 'EFA', 'EEM', 'AFK', 'EZA', 'NGE', 'FXI', 'INDA', 'EWZ', 'GLD', 'SLV', 'BRENT', 'WTI', 'NATGAS', 'DBA', 'CPER', 'TLT', 'HYG', 'UUP', 'EURUSD', 'USDXOF', 'VIX', 'BTC', 'SOXX', 'NVDA', '0050'].filter(has);
  const usU = secsWhere(s => (s.mkt === 'US' || s.mkt === 'TW') && has(s.id) && (s.typ === 'Equity' || ['QQQ', 'VTI', 'SPY', 'SOXX', '0050'].includes(s.id))).map(s => s.id).slice(0, 80);
  const mix = ['QQQ', 'SPY', 'VTI', 'EFA', 'EEM', 'AFK', 'SOXX', 'NVDA', 'TSM', '0050', 'BRVMC', 'BRVM30', 'SNTS', 'ORAC', 'SGBC', 'GLD', 'BRENT', 'WTI', 'NATGAS', 'TLT', 'HYG', 'VIX', 'EURUSD', 'USDXOF', 'BTC'].filter(has);
  const a = Math.max(1, T - cs.win), b = T, lag = !!cs.lag;
  const sqr = cs.u === 'BRVM' ? bIdx.concat(bStk) : cs.u === 'MIX' ? mix : cs.u === 'US' ? usU : null;
  const rows = cs.u === 'BRVMW' ? bIdx.concat(bStk) : sqr, cols = cs.u === 'BRVMW' ? world : sqr;
  const allIds = Object.keys(W.s).filter(id => Q.by[id]).sort();
  const pick = (id, def) => has(id) ? id : def;
  cs.ref = pick(cs.ref, 'BRVMC'); let pair = cs.pair && has(cs.pair[0]) && has(cs.pair[1]) ? cs.pair : null;
  const flat = id => { const r = R[id]; let z = 0, k = 0; for (let t = a; t < b; t++) if (r[t] != null) { k++; if (r[t] === 0) z++; } return k ? z / k : 1; };
  const nm = id => { const s = Q.by[id]; return s ? esc(s.short || s.n || id) : id; };
  const tools = `<span class="tlab">Univers</span>${[['BRVMW', 'BRVM × monde'], ['BRVM', 'BRVM (indices + 48 actions)'], ['MIX', 'Multi-actifs'], ['US', 'États-Unis & Taïwan'], ['REF', 'Une valeur face à tout']].map(([k, l]) => `<button class="tb ${cs.u === k ? 'on' : ''}" data-cu="${k}">${l}</button>`).join('')}
    <span class="tlab">Fenêtre</span>${[[52, '1 an'], [104, '2 ans'], [260, '5 ans'], [520, '10 ans']].map(([k, l]) => `<button class="tb ${cs.win === k ? 'on' : ''}" data-cw="${k}">${l}</button>`).join('')}
    <button class="tb ${lag ? 'on' : ''}" data-lag="1" title="Ajoute les covariances décalées d'une semaine : corrige le retard de cotation des titres peu liquides">Correction Dimson</button>
    ${sqr ? `<span class="tlab">Tri</span><button class="tb ${cs.ord === 'grp' ? 'on' : ''}" data-co="grp">${cs.u === 'BRVM' ? 'Indices puis actions' : 'Liste'}</button><button class="tb ${cs.ord === 'pc1' ? 'on' : ''}" data-co="pc1">1re composante</button>` : ''}`;
  let body = '', lectM = '', afterPca = null;
  if (cs.u === 'REF') {
    const x = R[cs.ref]; const res = allIds.filter(id => id !== cs.ref).map(id => { const c = corrPair(x, R[id], a, b, lag), c5 = corrPair(x, R[id], Math.max(1, T - 260), T, lag); return c ? { id, c, c5, fl: flat(id) } : null; }).filter(Boolean).sort((p, q) => q.c.r - p.c.r);
    if (!pair) pair = [cs.ref, res[0] ? res[0].id : 'QQQ'];
    body = `<form class="pairf" id="crF"><span class="tlab">Valeur de référence</span><input list="cpL" id="cr1" value="${esc(cs.ref)}" spellcheck="false"><button class="tb">Calculer</button></form>
      <div class="tw" style="max-height:66vh"><table class="t" id="cRT"><thead><tr><th class="l">Titre</th><th class="l">Nom</th><th class="l">Marché</th><th>Corrélation</th><th style="width:140px"></th><th>Corr. 5 ans</th><th>Bêta</th><th>Semaines</th><th>Sans variation</th></tr></thead><tbody>
      ${res.map(r => { const s = Q.by[r.id], w = Math.abs(r.c.r) * 60; return `<tr data-p="${cs.ref}|${r.id}" style="cursor:pointer"><td class="l tk">${r.id}</td><td class="l nm">${nm(r.id)}</td><td class="l dm">${s ? s.mkt : ''}</td><td class="${r.c.r > 0 ? 'up' : 'dn'}">${num(r.c.r, 2)}</td>
        <td><div class="zbar"><i style="${r.c.r >= 0 ? `left:50%;width:${w}%` : `right:50%;width:${w}%`};background:${r.c.r >= 0 ? 'var(--up)' : 'var(--dn)'}"></i></div></td><td>${r.c5 ? num(r.c5.r, 2) : '—'}</td><td>${num(r.c.beta, 2)}</td><td>${r.c.n}</td><td class="${r.fl > .4 ? 'dn' : 'dm'}">${num(r.fl * 100, 0)} %</td></tr>`; }).join('')}</tbody></table></div>`;
    lectM = `Corrélation des rendements hebdomadaires de <b>${cs.ref}</b> (${nm(cs.ref)}) avec chacun des ${res.length} autres actifs, du plus lié au plus opposé. Bêta = sensibilité de l’actif aux mouvements de ${cs.ref}. « Sans variation » = part des semaines où le cours n’a pas bougé : au-delà de 40 %, la corrélation est sous-estimée (titre peu échangé) — activez la correction Dimson.`;
  } else {
    let rr = rows.slice(), cc = cols.slice(); const C = rr.map(p => cc.map(q => p === q ? { r: 1 } : corrPair(R[p], R[q], a, b, lag)));
    if (sqr && cs.ord === 'pc1') { const Cf = C.map(r => r.map(v => v ? v.r : 0)); const E = eigTop(Cf, 1); const sg = Math.sign(E.vecs[0].reduce((x, y) => x + y, 0)) || 1; const o = rr.map((id, i) => [i, E.vecs[0][i] * sg]).sort((p, q) => q[1] - p[1]).map(x => x[0]); rr = o.map(i => rr[i]); cc = rr.slice(); }
    const CC = rr.map(p => cc.map(q => { if (p === q) return { r: 1 }; const i = rows.indexOf(p), j = cols.indexOf(q); return C[i][j]; }));
    if (!pair) pair = [rr[0], cc.find(id => id !== rr[0] && id !== 'USDXOF') || cc[0]];
    const isIdx = id => Q.by[id] && Q.by[id].cls === 'Index' && Q.by[id].mkt === 'BRVM';
    body = `<div class="tw" style="max-height:70vh"><table class="t hm" id="cT"><thead><tr><th class="l">Titre</th>${cs.u === 'BRVMW' ? '<th class="l">Nom</th>' : ''}${cc.map(id => `<th class="vh" title="${nm(id)}">${id}</th>`).join('')}${cs.u === 'BRVMW' ? '<th>Moy.</th>' : ''}</tr></thead><tbody>
      ${rr.map((p, i) => { const vals = CC[i].filter((v, j) => v && cc[j] !== p).map(v => v.r); const fl = flat(p);
        return `<tr class="${isIdx(p) && !isIdx(rr[i + 1]) ? 'sep' : ''}"><td class="l tk ${isIdx(p) ? 'am' : ''}" data-sec="${p}" data-to="GP" style="cursor:pointer" title="${nm(p)}${fl > .4 ? ' — ' + num(fl * 100, 0) + ' % de semaines sans variation' : ''}">${p}${fl > .4 ? '<sup>*</sup>' : ''}</td>${cs.u === 'BRVMW' ? `<td class="l nm" style="max-width:150px;overflow:hidden;text-overflow:ellipsis">${nm(p)}</td>` : ''}
        ${CC[i].map((v, j) => `<td data-p="${p}|${cc[j]}" style="cursor:pointer;background:${p === cc[j] ? '#222' : heatBg(v ? v.r : null, 1)};color:${v && Math.abs(v.r) > .6 ? '#fff' : 'var(--txt)'}">${p === cc[j] ? '' : v ? num(v.r, 2).replace('0,', ',') : '·'}</td>`).join('')}
        ${cs.u === 'BRVMW' ? `<td class="wh">${vals.length ? num(U.mean(vals), 2) : '—'}</td>` : ''}</tr>`; }).join('')}</tbody></table></div>`;
    const all = []; CC.forEach((r, i) => r.forEach((v, j) => { if (v && rr[i] !== cc[j]) all.push(v.r); }));
    lectM = `${cs.u === 'BRVMW' ? `Lignes : les indices BRVM puis les ${bStk.length} actions (par capitalisation). Colonnes : marchés mondiaux.` : `${rr.length} actifs.`} Corrélation des rendements hebdomadaires sur la fenêtre ; <b>vert</b> = mouvements communs, <b>rouge</b> = opposés. Moyenne : <strong>${num(U.mean(all), 2)}</strong>. <sup>*</sup> = titre sans variation plus de 40 % des semaines (corrélation sous-estimée). Cliquer une case pour étudier la paire.`;
    if (sqr) afterPca = rr;
  }
  const pairForm = `<form class="pairf" id="cpF"><span class="tlab">Paire</span><input list="cpL" id="cp1" value="${esc((pair || [])[0] || '')}" placeholder="BRVMC" spellcheck="false"><span class="tlab">/</span><input list="cpL" id="cp2" value="${esc((pair || [])[1] || '')}" placeholder="QQQ" spellcheck="false"><button class="tb">Comparer</button>
    <datalist id="cpL">${allIds.map(id => `<option value="${id}">${nm(id)}</option>`).join('')}</datalist></form>`;
  m.innerHTML = `<div class="tools" style="border:1px solid var(--line2)">${tools}<span class="tlab">rendements hebdomadaires · ${fd(W.w[a])} → ${fd(W.w[b - 1])}</span></div>
    <div class="grid c2">${pn(cs.u === 'REF' ? `Corrélations de ${cs.ref}` : 'Matrice de corrélation', 'CORR', body, { np: true, lect: lectM })}
    <div class="grid" style="align-content:start">${pn(`Paire · ${pair[0]} / ${pair[1]}`, 'CORR', `${pairForm}<div class="grid c2b"><div class="cv" id="cS" style="height:230px"></div><div class="kv2" id="cK"></div></div>${cvb('cR', 190)}`, { lect: '<span id="cL"></span>' })}
      ${afterPca ? pn('Analyse en composantes principales', 'CORR', `<div class="grid c2b">${cvb('cE', 170)}${cvb('cA', 170)}</div>`, { lect: '<span id="cPl"></span>' }) : ''}</div></div>`;
  m.querySelectorAll('[data-cu]').forEach(x => x.onclick = () => { cs.u = x.dataset.cu; cs.pair = null; render(); });
  m.querySelectorAll('[data-cw]').forEach(x => x.onclick = () => { cs.win = +x.dataset.cw; render(); });
  m.querySelectorAll('[data-co]').forEach(x => x.onclick = () => { cs.ord = x.dataset.co; render(); });
  m.querySelector('[data-lag]').onclick = () => { cs.lag = !cs.lag; render(); };
  $('cpF').onsubmit = e => { e.preventDefault(); const p = $('cp1').value.trim().toUpperCase(), q = $('cp2').value.trim().toUpperCase(); if (has(p) && has(q) && p !== q) { cs.pair = [p, q]; render(); } else toast('Choisissez deux actifs de la liste.'); };
  if ($('crF')) $('crF').onsubmit = e => { e.preventDefault(); const p = $('cr1').value.trim().toUpperCase(); if (has(p)) { cs.ref = p; cs.pair = null; render(); } else toast('Actif inconnu.'); };
  const tbl = $('cT') || $('cRT');
  tbl.addEventListener('click', e => { const td = e.target.closest('[data-p]'); if (!td) return; const [p, q] = td.dataset.p.split('|'); if (p !== q) { cs.pair = [p, q]; render(); } });
  if ($('cT')) { $('cT').addEventListener('mousemove', e => { const td = e.target.closest('[data-p]'); if (!td) { untip(); return; } const [p, q] = td.dataset.p.split('|'); tip(e, `${p} / ${q} : <b>${td.textContent || '—'}</b><br>${nm(p)} · ${nm(q)}`); }); $('cT').addEventListener('mouseleave', untip); }
  // paire
  const [p, q] = pair, xs = [], ys = []; for (let t = a; t < b; t++) if (R[p][t] != null && R[q][t] != null) { xs.push(R[q][t]); ys.push(R[p][t]); }
  const cp = corrPair(R[p], R[q], a, b, lag) || { r: NaN, beta: NaN, alpha: NaN, n: xs.length };
  scatter($('cS'), { pts: xs.map((v, i) => [v, ys[i]]), line: [cp.alpha, cp.beta], xlab: q, ylab: p, fx: fmtPctAxis, fy: fmtPctAxis });
  $('cK').innerHTML = `<span>Corrélation${lag ? ' (Dimson)' : ''}</span><b>${num(cp.r, 2)}</b><span>Bêta ${p} / ${q}</span><b>${num(cp.beta, 2)}</b><span>R²</span><b>${num(cp.r * cp.r, 2)}</b><span>Observations</span><b>${cp.n}</b><span>Vol. ${p}</span><b>${num(U.std(ys) * Math.sqrt(52) * 100, 1)}%</b><span>Vol. ${q}</span><b>${num(U.std(xs) * Math.sqrt(52) * 100, 1)}%</b><span>Sans variation ${p}</span><b>${num(flat(p) * 100, 0)} %</b>`;
  const rc = []; for (let t = 0; t < T; t++) { if (t < 26) { rc.push(null); continue; } const c = corrPair(R[p], R[q], t - 25, t + 1, lag); rc.push(c ? c.r : null); }
  new TSChart($('cR'), { panes: [{ h: 1, fixed: [-1, 1], refs: [{ v: 0, color: CL.dim2, dash: [] }, { v: cp.r, color: CL.amber }] }] }).set({ x: W.w, series: [{ y: rc, color: CL.cyan, label: 'Corrélation glissante 26 sem.', fmt: v => num(v, 2) }] }, [0, T - 1]);
  const rcv = rc.filter(v => v != null); $('cL').innerHTML = rcv.length ? `Nuage : rendements hebdomadaires de ${p} (vertical) contre ${q} (horizontal), pente = bêta. Corrélation glissante sur 26 semaines : entre <strong>${num(Math.min(...rcv), 2)}</strong> et <strong>${num(Math.max(...rcv), 2)}</strong>, dernière <strong>${num(rcv[rcv.length - 1], 2)}</strong>. Pointillé ambre = valeur sur la fenêtre.` : 'Historique commun insuffisant.';
  if (afterPca) {
    const ids = afterPca.filter(id => R[id]); const Cf = ids.map(x => ids.map(y => { if (x === y) return 1; const c = corrPair(R[x], R[y], a, b, lag); return c ? c.r : 0; }));
    const E = eigTop(Cf, Math.min(8, ids.length)); const varEx = E.vals.map(v => v / ids.length);
    barChart($('cE'), { labels: varEx.map((_, i) => 'CP' + (i + 1)), values: varEx.map(v => v * 100), fmt: v => num(v, 0) + '%', pos: CL.cyan, labelsOnBars: true });
    const ab = [], abx = []; for (let t = 52; t < T; t += 4) { const Cw = corrMat(R, ids, t - 52, t).map(r => r.map(v => v == null ? 0 : v)); const e = eigTop(Cw, 1); ab.push(e.vals[0] / ids.length); abx.push(W.w[t]); }
    new TSChart($('cA'), { panes: [{ h: 1, fmt: fmtPctAxis }], padR: 44 }).set({ x: abx, series: [{ y: ab, color: CL.amber, label: 'Ratio d’absorption CP1 (52 sem.)', fmt: fmtPctAxis }] }, [0, abx.length - 1]);
    $('cPl').innerHTML = `La 1re composante explique <strong>${num(varEx[0] * 100, 0)} %</strong> de la variance commune (facteur « marché »). Ratio d’absorption (à droite) : part de la 1re composante sur 52 semaines glissantes ; quand il monte, tout bouge ensemble et la diversification disparaît.`;
  }
};

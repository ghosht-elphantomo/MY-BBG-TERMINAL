/* ================= FQT — HP, DVD, BETA structurés comme les écrans du terminal Bloomberg ================= */
const JOUR2 = ['Di', 'Lu', 'Ma', 'Me', 'Je', 'Ve', 'Sa'];
const dWk = d => { const t = new Date(Date.UTC(Math.floor(d / 10000), Math.floor(d / 100) % 100 - 1, d % 100)); return JOUR2[t.getUTCDay()] + ' ' + fmtD(d).slice(0, 6) + fmtD(d).slice(8); };

/* ------------------------------------------------------------------ HP : tableau des cours historiques (blocs de colonnes + synthèse à droite) */
PAGES.HP = async (m, alive) => {
  const s = sec(ST.sec); const S = await series(s.id); if (!alive()) return; setTitle('Historical Price Table');
  const st = ST.hp2 = ST.hp2 || {}; if (st.id !== s.id) Object.assign(st, { id: s.id, f: S.f === 'M' ? 'M' : 'D', rg: S.f === 'M' ? '5A' : '3M', mk: 'c', v: 'P', d0: null, d1: null, page: 0 });
  /* agrégation hebdomadaire / mensuelle : dernier jour de la période */
  const key = d => st.f === 'D' ? d : st.f === 'W' ? isoWeekKey(d) : Math.floor(d / 100); const R = []; let cur = null;
  for (let i = 0; i < S.x.length; i++) { const k = key(S.x[i]); if (!cur || cur.k !== k) { if (cur) R.push(cur); cur = { k, d: S.x[i], o: S.o[i], h: S.h[i], l: S.l[i], c: S.c[i], v: S.v[i] || 0, val: S.val ? S.val[i] || 0 : 0 }; }
    else { cur.d = S.x[i]; cur.h = Math.max(cur.h, S.h[i]); cur.l = Math.min(cur.l, S.l[i]); cur.c = S.c[i]; cur.v += S.v[i] || 0; if (S.val) cur.val += S.val[i] || 0; } }
  if (cur) R.push(cur);
  const vma = U.sma(R.map(r => r.v), 15); R.forEach((r, i) => { r.vm = vma[i]; r.ch = i ? r.c - R[i - 1].c : null; r.pc = i && R[i - 1].c ? r.c / R[i - 1].c - 1 : null; });
  const last = R[R.length - 1].d, back = { '1M': 100, '3M': 300, '6M': 600, '1A': 10000, '2A': 20000, '5A': 50000, '10A': 100000 };
  let d0 = st.d0, d1 = st.d1 || last; if (!d0) d0 = st.rg === 'YTD' ? Math.floor(last / 10000) * 10000 + 101 : st.rg === 'MAX' ? R[0].d : last - back[st.rg];
  const W = R.filter(r => r.d >= d0 && r.d <= d1), hasV = W.some(r => r.v > 0), mk = { c: 'Dernier', o: 'Ouverture', h: 'Plus haut', l: 'Plus bas' }[st.mk];
  const V = r => r[st.mk];
  /* synthèse de la période (colonne de droite du terminal) */
  let hi = null, lo = null, sum = 0; for (const r of W) { if (!hi || V(r) > V(hi)) hi = r; if (!lo || V(r) < V(lo)) lo = r; sum += V(r); }
  const first = W[0], lastR = W[W.length - 1], net = first && lastR ? V(lastR) - V(first) : null, avgV = W.length ? W.reduce((a, r) => a + r.v, 0) / W.length : null;
  /* blocs de colonnes : remplit la largeur de l'écran, du plus récent au plus ancien */
  const vw = Math.max(320, (m.getBoundingClientRect().width || 1200) - 300), bw = st.v === 'P' ? (hasV ? 330 : 200) : 560, nb = Math.max(1, Math.floor(vw / bw));
  const rowsPer = Math.max(12, Math.floor((window.innerHeight - 330 - (PREF.nonews ? 0 : 90)) / 19)), per = nb * rowsPer, L = W.slice().reverse(), np = Math.max(1, Math.ceil(L.length / per)); st.page = U.clamp(st.page, 0, np - 1);
  const pg = L.slice(st.page * per, st.page * per + per), blocks = []; for (let b = 0; b < nb; b++) blocks.push(pg.slice(b * rowsPer, b * rowsPer + rowsPer));
  const head = st.v === 'P' ? `<tr><th class="l">Date</th><th>${mk}</th>${hasV ? '<th>Volume</th><th>MMV (15)</th>' : ''}</tr>` : `<tr><th class="l">Date</th><th>Ouverture</th><th>Plus haut</th><th>Plus bas</th><th>Dernier</th><th>Var. %</th>${hasV ? '<th>Volume</th>' : ''}</tr>`;
  const row = r => st.v === 'P' ? `<tr><td class="l">${dWk(r.d)}</td><td class="wh">${px(s, V(r))}</td>${hasV ? `<td>${r.v ? num(r.v, 0) : '—'}</td><td>${r.vm != null && isFinite(r.vm) ? num(r.vm, 0) : '—'}</td>` : ''}</tr>`
    : `<tr><td class="l">${dWk(r.d)}</td><td>${px(s, r.o)}</td><td>${px(s, r.h)}</td><td>${px(s, r.l)}</td><td class="wh">${px(s, r.c)}</td><td>${pc(r.pc)}</td>${hasV ? `<td>${r.v ? num(r.v, 0) : '—'}</td>` : ''}</tr>`;
  setActs([{ n: 1, l: 'Actions', menu: () => [{ l: 'Exporter le tableau (CSV)', run: exportCSV }, { l: 'Ouvrir le graphique (GP)', run: () => go('GP', s.id) }, { l: 'Imprimer', run: () => window.print() }] }]);
  const rg = ['1M', '3M', '6M', 'YTD', '1A', '2A', '5A', '10A', 'MAX'];
  m.innerHTML = `<div class="tools hpt"><span class="tlab">Période</span><input class="ofld dt" id="hpD0" value="${fd(d0)}"><span class="cal">▦</span><span class="dm">–</span><input class="ofld dt" id="hpD1" value="${fd(d1)}"><span class="cal">▦</span>
      ${rg.map(r => `<button class="tb ${!st.d0 && st.rg === r ? 'on' : ''}" data-rg="${r}">${r === 'MAX' ? 'Max' : r}</button>`).join('')}
      <span class="tlab">Fréquence</span><select class="ofld dk" id="hpF">${[['D', 'Quotidienne'], ['W', 'Hebdomadaire'], ['M', 'Mensuelle']].filter(([k]) => S.f !== 'M' || k === 'M').map(([k, l]) => `<option value="${k}" ${st.f === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <span class="tlab">Donnée</span><select class="ofld" id="hpM">${[['c', 'Dernier cours'], ['o', 'Ouverture'], ['h', 'Plus haut'], ['l', 'Plus bas']].map(([k, l]) => `<option value="${k}" ${st.mk === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <span class="tlab">Vue</span><select class="ofld" id="hpV"><option value="P" ${st.v === 'P' ? 'selected' : ''}>Tableau des cours${hasV ? ' et volumes' : ''}</option><option value="O" ${st.v === 'O' ? 'selected' : ''}>Ouverture / haut / bas / dernier</option></select>
      <span class="gsp"></span><span class="tlab">Devise</span><span class="wh">${esc(s.ccy || '')}</span></div>
    <div class="hpg"><div class="hpb" style="grid-template-columns:repeat(${nb},minmax(0,1fr))">${blocks.map(b => `<div>${b.length ? `<table class="t hp"><thead>${head}</thead><tbody>${b.map(row).join('')}</tbody></table>` : ''}</div>`).join('')}</div>
      <div class="hps"><div class="kv2">${[['Plage', `${fd(d0)} – ${fd(d1)}`], ['Période', { D: 'Quotidienne', W: 'Hebdomadaire', M: 'Mensuelle' }[st.f]], ['Devise', esc(s.ccy || '—')], ['Observations', num(W.length, 0)]].map(([a, b]) => `<span>${a}</span><b>${b}</b>`).join('')}
        <span class="h">${esc(mk)}</span>${hi ? [['Plus haut le ' + fd(hi.d), px(s, V(hi))], ['Moyenne', num(sum / W.length, pxd(s) + 2)], ['Plus bas le ' + fd(lo.d), px(s, V(lo))], ['Var. nette', `<span class="${cls(net)}">${net > 0 ? '+' : ''}${px(s, net)}</span>`], ['Var. %', pc(V(first) ? net / V(first) : null)]].map(([a, b]) => `<span>${a}</span><b>${b}</b>`).join('') : ''}
        ${hasV ? `<span class="h">Volume</span><span>Volume moyen</span><b>${num(avgV, 0)}</b><span>Volume total</span><b>${num(W.reduce((a, r) => a + r.v, 0), 0)}</b>` : ''}</div>
        <div class="hpn"><button class="tb" data-p="-1" ${st.page ? '' : 'disabled'}>◀ Plus récent</button><span class="dm">Page ${st.page + 1} / ${np}</span><button class="tb" data-p="1" ${st.page < np - 1 ? '' : 'disabled'}>Plus ancien ▶</button></div></div></div>
    <div class="lect">${isBRVM(s) ? '' : 'Source : ' + esc(s.src || (s.mkt === 'US' ? 'Nasdaq / Yahoo Finance' : s.mkt === 'CRYPTO' ? 'Coinbase' : 'FRED / CBOE / bourses')) + '. '}MMV (15) = moyenne mobile du volume sur 15 périodes. Semaine = semaine ISO.</div>`;
  m.querySelectorAll('[data-rg]').forEach(b => b.onclick = () => { st.rg = b.dataset.rg; st.d0 = st.d1 = null; st.page = 0; render(); });
  m.querySelectorAll('[data-p]').forEach(b => b.onclick = () => { st.page += +b.dataset.p; render(); });
  $('hpF').onchange = e => { st.f = e.target.value; st.page = 0; if (st.f !== 'D' && ['1M', '3M'].includes(st.rg) && !st.d0) st.rg = st.f === 'W' ? '1A' : '5A'; render(); };
  $('hpM').onchange = e => { st.mk = e.target.value; render(); }; $('hpV').onchange = e => { st.v = e.target.value; st.page = 0; render(); };
  const dIn = () => { const a = parseDMY($('hpD0').value), b = parseDMY($('hpD1').value); if (!a || !b || b <= a) { toast('Dates au format jj/mm/aaaa, la fin après le début.'); return; } st.d0 = a; st.d1 = b; st.page = 0; render(); };
  ['hpD0', 'hpD1'].forEach(id => { $(id).onchange = dIn; $(id).onkeydown = e => { if (e.key === 'Enter') dIn(); }; });
};

/* ------------------------------------------------------------------ DVD : historique des dividendes au format du terminal (onglet 1), analyse (onglet 2) */
const DVD_ANALYSE = PAGES.DVD;
PAGES.DVD = async (m, alive) => {
  const s = sec(ST.sec); setTitle('Dividend/Split Summary'); const tab = tabState('DVD', 'h');
  setTabs([['h', 'Historique'], ['a', 'Analyse et graphiques']], tab, k => { ST.tab.DVD = k; render(); });
  if (tab === 'a') return DVD_ANALYSE(m, alive);
  const [S, DV, PR] = await Promise.all([series(s.id), isBRVM(s) ? getJSON('dividends.json') : null, isBRVM(s) ? null : getJSON('profiles.json').catch(() => ({}))]); if (!alive()) return;
  const today = new Date().toISOString().slice(0, 10), last = S.c[S.c.length - 1];
  let H = [];
  if (isBRVM(s)) H = DV.filter(x => x.t === s.id && x.dps).map(x => ({ ann: x.ann, det: x.det, pay: x.pay, amt: x.dps, ex: x.ex, ccy: 'XOF' }));
  else for (let i = 0; i < S.x.length; i++) if (S.div[i]) H.push({ det: i2s(S.x[i]), amt: S.div[i], ccy: s.ccy || 'USD' });
  H.sort((a, b) => (b.det || b.pay || b.ann || '').localeCompare(a.det || a.pay || a.ann || ''));
  /* fréquence : nombre de versements par an (calculée sur les 3 dernières années complètes) */
  const yrs = {}; H.forEach(h => { const y = (h.det || h.pay || '').slice(0, 4); if (y) yrs[y] = (yrs[y] || 0) + 1; }); const cy = +today.slice(0, 4);
  const cnt = [cy - 1, cy - 2, cy - 3].map(y => yrs[y] || 0).filter(Boolean), fq = cnt.length ? Math.round(cnt.reduce((a, b) => a + b, 0) / cnt.length) : 0;
  const fqL = { 1: 'Annuelle', 2: 'Semestrielle', 3: 'Irrégulière', 4: 'Trimestrielle', 12: 'Mensuelle' }[fq] || (fq ? fq + ' par an' : '—');
  const past = H.filter(h => (h.det || h.pay || '') <= today), y1 = new Date(Date.now() - 365 * 864e5).toISOString().slice(0, 10);
  const ttm = past.filter(h => (h.det || h.pay) > y1).reduce((a, h) => a + h.amt, 0), ind = past.length && fq ? past[0].amt * fq : null;
  const byY = {}; past.forEach(h => { const y = h.ex || +(h.det || h.pay).slice(0, 4); byY[y] = (byY[y] || 0) + h.amt; }); const ys = Object.keys(byY).map(Number).sort((a, b) => a - b).filter(y => isBRVM(s) || y < cy);
  const g5 = ys.length > 5 && byY[ys[ys.length - 6]] > 0 ? Math.pow(byY[ys[ys.length - 1]] / byY[ys[ys.length - 6]], 1 / 5) - 1 : null;
  const next = H.filter(h => (h.det || '') > today).slice(-1)[0];
  const net = isBRVM(s) ? 'net' : 'brut';
  /* actions US sans historique de versements dans la source : dernier versement connu (Nasdaq) */
  const NQ = !isBRVM(s) && !H.length && PR && PR[s.id] && PR[s.id].divA ? PR[s.id] : null;
  if (NQ) { const ex = parseNqDate(NQ.exdiv), pay = parseNqDate(NQ.paydiv), dA = nqNum(NQ.divA), y = nqNum(NQ.yld);
    m.innerHTML = `<div class="grid">${pn(`${esc(ykey(s))} · dividendes`, 'DVD', `<div class="dvk">${[['Dividende annualisé (brut)', dA != null ? num(dA, 4) + ' ' + esc(s.ccy || 'USD') : '—'], ['Rendement indicatif (brut)', y != null ? num(y, 2) + ' %' : '—'], ['Dernier détachement', ex ? fd(ex) : '—'], ['Dernier paiement', pay ? fd(pay) : '—']].map(([a, b]) => `<span>${a}</span><b>${b}</b>`).join('')}</div>`)}
      ${pn('Historique des versements', 'DVD', `<table class="t"><thead><tr><th class="l">Annonce</th><th class="l">Détachement</th><th class="l">Enregistrement</th><th class="l">Paiement</th><th>Montant</th><th class="l">Fréquence</th><th class="l">Type</th></tr></thead><tbody><tr><td class="l dm">—</td><td class="l am">${ex ? fd(ex) : '—'}</td><td class="l dm">—</td><td class="l">${pay ? fd(pay) : '—'}</td><td class="dm">n.d.</td><td class="l dm">—</td><td class="l">Dernier versement connu</td></tr></tbody></table>`,
        { np: true, lect: 'La source (Nasdaq, relevé du ' + fds(NQ.d) + ') ne donne que le dernier versement et le dividende annualisé, pas le montant unitaire ni l’historique détaillé. Dividendes par année tirés des comptes publiés : onglet 2.' })}</div>`; return; }
  const kv = [[`Rendement indicatif (${net})`, ind && last ? P1(ind / last, 2) : '—'], [`Rendement 12 mois (${net})`, ttm && last ? P1(ttm / last, 2) : '—'], ['Croissance annuelle 5 ans', P1(g5, 1)], ['Fréquence', fqL],
    ['Dernier dividende', past[0] ? `${num(past[0].amt, isBRVM(s) ? 0 : 4)} ${past[0].ccy}` : '—'], ['Prochain détachement annoncé', next ? fds(next.det) + ' · ' + num(next.amt, isBRVM(s) ? 0 : 4) + ' ' + next.ccy : '—']];
  m.innerHTML = `<div class="grid">${pn(`${esc(ykey(s))} · dividendes`, 'DVD', `<div class="dvk">${kv.map(([a, b]) => `<span>${a}</span><b>${b}</b>`).join('')}</div>`, { np: false })}
    ${pn(`Historique des versements (${H.length})`, 'DVD', H.length ? `<div class="tw" style="max-height:calc(100vh - 330px - var(--nwh, 90px))"><table class="t"><thead><tr><th class="l">Annonce</th><th class="l">Détachement</th><th class="l">Enregistrement</th><th class="l">Paiement</th><th>Montant</th><th class="l">Fréquence</th><th class="l">Type</th>${isBRVM(s) ? '<th>Exercice</th>' : ''}</tr></thead><tbody>
      ${H.map(h => `<tr${(h.det || '') > today ? ' class="hl"' : ''}><td class="l">${fds(h.ann)}</td><td class="l am">${fds(h.det)}</td><td class="l dm">—</td><td class="l">${fds(h.pay)}</td><td class="wh">${num(h.amt, isBRVM(s) ? 2 : 4)} ${h.ccy}</td><td class="l">${fqL}</td><td class="l">${isBRVM(s) ? 'Dividende net' : 'Dividende'}</td>${isBRVM(s) ? `<td>${h.ex || '—'}</td>` : ''}</tr>`).join('')}</tbody></table></div>` : '<div class="empty">Aucun dividende recensé pour ce titre.</div>',
      { np: true, lect: `${isBRVM(s) ? 'Montants nets par action, tels qu’annoncés par la société.' : 'Montants par action à la date de détachement (Yahoo Finance) ; date d’annonce et de paiement non fournies par la source.'} En surbrillance : versement à venir. Date d’enregistrement non publiée. Rendement indicatif = dernier dividende × fréquence ÷ cours ; rendement 12 mois = dividendes détachés sur 12 mois ÷ cours. Analyse détaillée : onglet 2.` })}</div>`;
};

/* ------------------------------------------------------------------ BETA : régression (nuage, droite, statistiques) comme l'écran du terminal ; onglet 2 = analyse */
const BETA_ANALYSE = PAGES.BETA;
PAGES.BETA = async (m, alive) => {
  const s = sec(ST.sec); setTitle('Historical Beta'); const tab = tabState('BETA', 'r');
  setTabs([['r', 'Régression'], ['a', 'Fenêtres, pairs et risque']], tab, k => { ST.tab.BETA = k; render(); });
  if (tab === 'a') return BETA_ANALYSE(m, alive);
  const st = ST.beta = ST.beta || {}; if (st.base !== s.id) { st.base = s.id; st.bench = s.bench && Q.by[s.bench] && s.bench !== s.id ? s.bench : isBRVM(s) ? 'BRVMC' : 'SPY'; if (!Q.by[st.bench]) st.bench = 'QQQ'; }
  st.f = st.f || 'W'; st.rg = st.rg || '2A';
  const [S, B] = await Promise.all([series(s.id), series(st.bench)]); if (!alive()) return;
  const end = Math.min(S.x[S.x.length - 1], B.x[B.x.length - 1]), y0 = end - { '1A': 10000, '2A': 20000, '3A': 30000, '5A': 50000 }[st.rg];
  const a = retsBy(S, st.f), b = retsBy(B, st.f), kd = d => st.f === 'D' ? d : st.f === 'W' ? isoWeekKey(d) : Math.floor(d / 100);
  const ks = [...a.keys()].filter(k => b.has(k) && k >= kd(y0)).sort((p, q) => p - q), P = ks.map(k => [(Math.exp(a.get(k)) - 1) * 100, (Math.exp(b.get(k)) - 1) * 100]);
  const o = olsBeta(P); const benches = isBRVM(s) ? ['BRVMC', 'BRVM30', 'SPY', 'QQQ', 'EEM', 'AFK'] : ['SPY', 'QQQ', 'VTI', 'SOXX', 'EEM', 'BRVMC'];
  let stats = '<div class="empty">Historique commun insuffisant pour cette période.</div>';
  if (o) { const n = o.n, mx = U.mean(P.map(p => p[1])), sxx = P.reduce((t, p) => t + (p[1] - mx) ** 2, 0), res = P.reduce((t, [y, x]) => t + (y - o.a - o.b * x) ** 2, 0), sde = Math.sqrt(res / (n - 2)), sea = sde * Math.sqrt(1 / n + mx * mx / sxx);
    const pval = (() => { const t = Math.abs(o.t), z = t * (1 - 1 / (4 * (n - 2))) / Math.sqrt(1 + t * t / (2 * (n - 2))); const e = Math.exp(-z * z / 2) / Math.sqrt(2 * Math.PI), k = 1 / (1 + .2316419 * z); return 2 * e * k * (.31938153 + k * (-.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429)))); })();
    stats = `<div class="kv2 bst">${[['Bêta brut', num(o.b, 3), 'yl'], ['Bêta ajusté', num(o.b * 2 / 3 + 1 / 3, 3), 'yl'], ['Alpha (ordonnée, % par période)', num(o.a, 3)], ['R² (corrélation²)', num(o.r2, 3)], ['R (corrélation)', num(o.r, 3)],
      ['Écart type de l’erreur', num(sde, 3)], ['Erreur type de l’alpha', num(sea, 3)], ['Erreur type du bêta', num(o.se, 3)], ['Test t (bêta)', num(o.t, 3)], ['Significativité (valeur p)', pval < .0001 ? '< 0,0001' : num(pval, 4)], ['Nombre de points', num(n, 0)]]
      .map(([l, v, c]) => `<span>${l}</span><b class="${c || ''}">${v}</b>`).join('')}</div>`; }
  m.innerHTML = `<div class="tools bt1"><span class="tlab">Titre</span><span class="wh">${esc(ykey(s))}</span><span class="tlab">Indice</span><select class="ofld" id="btB">${benches.filter(x => Q.by[x] && x !== s.id).map(x => `<option value="${x}" ${st.bench === x ? 'selected' : ''}>${esc(ykey(Q.by[x]))}</option>`).join('')}</select>
      <span class="tlab">Période</span><select class="ofld dk" id="btF">${[['D', 'Quotidienne'], ['W', 'Hebdomadaire'], ['M', 'Mensuelle']].map(([k, l]) => `<option value="${k}" ${st.f === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <span class="tlab">Plage</span>${['1A', '2A', '3A', '5A'].map(r => `<button class="tb ${st.rg === r ? 'on' : ''}" data-rg="${r}">${r}</button>`).join('')}<span class="tlab">Donnée</span><span class="wh">Dernier cours (variation %)</span></div>
    <div class="grid side"><div class="pn"><div class="cv" id="btS" style="height:max(380px, calc(100vh - 300px - var(--nwh, 90px)))"></div></div>${pn('Statistiques de la régression', 'BETA', stats, { lect: `Régression des variations ${{ D: 'quotidiennes', W: 'hebdomadaires', M: 'mensuelles' }[st.f]} (%) de ${esc(s.id)} (axe vertical) sur celles de ${esc(st.bench)} (axe horizontal), ${ks.length ? fd(ks.length && st.f === 'D' ? ks[0] : y0) : ''} – ${fd(end)}. Bêta ajusté = 0,67 × bêta brut + 0,33 (convention Blume). Valeur p &lt; 0,05 = bêta significatif.` })}</div>`;
  $('btB').onchange = e => { st.bench = e.target.value; render(); }; $('btF').onchange = e => { st.f = e.target.value; render(); }; m.querySelectorAll('[data-rg]').forEach(x => x.onclick = () => { st.rg = x.dataset.rg; render(); });
  if (o) scatter($('btS'), { pts: P.map(([y, x]) => [x, y]), line: [o.a, o.b], color: rgba(CL.cyan, .7), lineColor: CL.amber, fx: v => num(v, 1) + ' %', fy: v => num(v, 1) + ' %', xlab: `${st.bench} (%)`, ylab: `${s.id} (%) · y = ${num(o.b, 3)} x ${o.a >= 0 ? '+' : '−'} ${num(Math.abs(o.a), 3)}` });
};

/* ------------------------------------------------------------------ TOP : « Top News » du terminal (sections numérotées, colonne de droite) */
const TOP_PAGES = [['HOME', 'À la une', null], ['AF', 'Afrique, UEMOA et BRVM', x => ['Afrique', 'UEMOA', 'BRVM'].includes(x.c)], ['MKT', 'Marchés', x => x.c === 'Marchés'], ['TECH', 'Tech US', x => x.c === 'Tech US'],
  ['CMD', 'Matières premières', x => x.c === 'Matières premières' || x.ev === 'Matières premières'], ['CB', 'Banques centrales et macro', x => x.c === 'Banques centrales' || ['Banques centrales', 'Macro'].includes(x.ev)],
  ['CO', 'Sociétés citées', x => (x.tk || []).length], ['ERN', 'Résultats et analystes', x => ['Résultats', 'Analystes'].includes(x.ev)]];
PAGES.TOP = async (m, alive) => {
  const N = await getJSON('news.json').catch(() => null); if (!alive()) return; setTitle('Top News');
  const st = ST.top2 = ST.top2 || { pg: 'HOME', q: '', off: {} };
  if (!N || !N.items || !N.items.length) { m.innerHTML = pn('Top News', 'TOP', '<div class="empty">Fil d’actualités en cours de constitution.</div>'); return; }
  const q = st.q.trim().toLowerCase(), seenT = new Set(), all = N.items.filter(x => { const k = deent(x.ti || '').toLowerCase().replace(/[^a-z0-9àâçéèêëîïôûùüÿœ]+/g, ' ').trim().slice(0, 70); if (!k || seenT.has(k)) return false; seenT.add(k); return true; })
    .filter(x => !q || (x.ti + ' ' + (x.x || '') + ' ' + (x.s || '') + ' ' + (x.tk || []).join(' ')).toLowerCase().includes(q));
  const hm = t => new Date(t * 1000).toLocaleTimeString('fr-FR', { timeZone: 'Africa/Abidjan', hour: '2-digit', minute: '2-digit' });
  const day = t => new Date(t * 1000).toLocaleDateString('fr-FR', { timeZone: 'Africa/Abidjan', day: '2-digit', month: '2-digit' }), today = day(Date.now() / 1000);
  let n = 0; const used = new Set();
  const row = x => { n++; used.add(x.u); const tk = (x.tk || []).filter(t => Q.by[t]).slice(0, 3);
    return `<div class="tn" data-n="${n}" data-u="${esc(x.u || '')}"><span class="no">${n})</span><span class="h">${evBadge(x.ev && x.ev !== 'Marchés' ? x.ev : '')}${esc(deent(x.ti))}${tk.map(t => ` <b class="tg" data-sec="${t}" data-to="CN">${t}</b>`).join('')}</span><span class="s">${esc(srcCode(x)) || '—'}</span><span class="t">${day(x.t) === today ? hm(x.t) : day(x.t)}</span></div>`; };
  const sect = (key, title, list, per) => { const off = st.off[key] || 0, np = Math.max(1, Math.ceil(list.length / per)), pg = list.slice(off * per, off * per + per);
    return `<div class="ts"><div class="tsh">${title}${np > 1 ? ` <span class="pgr"><b data-sk="${key}" data-d="-1">◀</b> ${off + 1} sur ${np} <b data-sk="${key}" data-d="1">▶</b></span>` : ''} <span class="mo" data-pg="${key}">Plus »</span></div>${pg.map(row).join('') || '<div class="dm" style="padding:2px 8px">—</div>'}</div>`; };
  let left = '';
  if (st.pg === 'HOME') {
    const pick = (f, k) => all.filter(x => !used.has(x.u) && f(x)).slice(0, k);
    const top = pick(x => x.ev && !['Marchés'].includes(x.ev) || (x.tk || []).length, 4); left += sect('T', 'Dépêches sélectionnées', top, 4);
    left += sect('AF', 'Afrique, UEMOA et BRVM', all.filter(x => !used.has(x.u) && TOP_PAGES[1][2](x)), 8);
    left += sect('MKT', 'Marchés', all.filter(x => !used.has(x.u) && TOP_PAGES[2][2](x)), 8);
    left += sect('CO', 'Sociétés', all.filter(x => !used.has(x.u) && (x.tk || []).length), 6);
  } else { const P = TOP_PAGES.find(p => p[0] === st.pg); left += sect(st.pg, P[1], all.filter(P[2]), 28); }
  /* colonne de droite : graphique de l'heure (QQQ en séance, sinon BRVM Composite) et « First Word » (dépêches brèves) */
  const fw = all.filter(x => !used.has(x.u) && (x.c === 'Marchés' || x.ev === 'Macro')).slice(0, 9);
  const intra = Q.live && Q.live.intraday && Q.live.intraday.t && Q.live.intraday.t.length > 10;
  m.innerHTML = `<div class="tools ttb"><span class="tnar"><input id="tpQ" value="${esc(st.q)}" placeholder="&lt;Filtrer&gt;"><b>⌕</b></span><button class="tb ${st.pause ? 'on' : ''}" id="tpP">‖ ${st.pause ? 'En pause' : 'Pause'}</button>
      ${TOP_PAGES.map(([k, l]) => `<button class="tb alt ${st.pg === k ? 'on' : ''}" data-pg="${k}">${l}</button>`).join('')}<span class="gsp"></span><span class="dm">${all.length} dépêches · heure GMT (Abidjan) · relevé ${hm(N.ts)}</span></div>
    <div class="grid tpg"><div class="pn tpl">${left}</div>
      <div class="grid" style="align-content:start"><div class="pn"><div class="tsh">Graphique de l’heure <span class="mo" data-fn="${intra ? 'GP' : 'GP'}" data-s="${intra ? 'QQQ' : 'BRVMC'}">Plus »</span></div><div class="tch">${intra ? 'QQQ · séance du jour, 5 minutes (heure de New York)' : 'BRVM Composite · 3 mois'}</div>${cvb('tpC', 190)}</div>
        <div class="pn"><div class="tsh">First Word <span class="mo" data-pg="MKT">Plus »</span></div>${fw.map(x => `<div class="fw" data-u="${esc(x.u || '')}">${esc(deent(x.ti))} <span class="dm">[${hm(x.t)}]</span></div>`).join('') || '<div class="dm" style="padding:4px 8px">—</div>'}</div></div></div>`;
  setActs([{ n: 1, l: 'Toutes les dépêches', run: () => { st.pg = 'HOME'; st.q = ''; render(); } }, { n: 2, l: 'Pages', menu: () => [{ h: 'Pages d’actualités' }].concat(TOP_PAGES.map(([k, l], i) => ({ n: i + 1, l: (st.pg === k ? '● ' : '') + l, run: () => { st.pg = k; render(); } }))) },
    { n: 3, l: 'Recherche', run: () => $('tpQ').focus() }]);
  m.querySelectorAll('[data-u]').forEach(r => r.onclick = e => { if (e.target.closest('[data-sec]')) return; if (r.dataset.u) window.open(r.dataset.u, '_blank', 'noopener'); });
  m.querySelectorAll('[data-pg]').forEach(b => b.onclick = () => { st.pg = b.dataset.pg === 'T' ? 'HOME' : b.dataset.pg; st.off = {}; render(); });
  m.querySelectorAll('[data-sk]').forEach(b => b.onclick = () => { const k = b.dataset.sk; st.off[k] = Math.max(0, (st.off[k] || 0) + +b.dataset.d); render(); });
  $('tpP').onclick = () => { st.pause = !st.pause; render(); };
  $('tpQ').onkeydown = e => { if (e.key === 'Enter') { st.q = e.target.value; st.off = {}; render(); } };
  if (intra) { const I = Q.live.intraday, tt = I.t.map(t => { const d = new Date(t * 1000); return d.getUTCFullYear() * 1e8 + (d.getUTCMonth() + 1) * 1e6 + d.getUTCDate() * 1e4 + d.getUTCHours() * 100 + d.getUTCMinutes(); });
    const ny = t => new Date(t * 1000).toLocaleTimeString('fr-FR', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit' });
    new TSChart($('tpC'), { panes: [{ h: 1, noLegend: true, fmt: v => num(v, 2) }], padR: 56, grid: 'dot', xfmt: v => { const i = tt.indexOf(v); return i >= 0 ? ny(I.t[i]) : ''; } }).set({ x: tt, series: [{ type: 'area', y: I.c, color: '#ffffff', w: 1.1, grad: ['rgba(7,42,82,.97)', 'rgba(3,29,56,.97)'] }] }, [0, tt.length - 1]); }
  else { const S = await series('BRVMC').catch(() => null); if (!alive() || !S) return; const k = Math.max(0, S.x.length - 63);
    new TSChart($('tpC'), { panes: [{ h: 1, noLegend: true, fmt: v => num(v, 1) }], padR: 56, grid: 'dot', xticks: bbgTicks }).set({ x: S.x.slice(k), series: [{ type: 'area', y: S.c.slice(k), color: '#ffffff', w: 1.1, grad: ['rgba(7,42,82,.97)', 'rgba(3,29,56,.97)'] }] }); }
};

/* ------------------------------------------------------------------ MOST : « Most Active » du terminal (classements numérotés, une table) */
PAGES.MOST = async (m, alive) => {
  setTitle('Most Active Securities'); const st = ST.most2 = ST.most2 || { u: 'BRVM', k: 'val' };
  const U0 = st.u === 'BRVM' ? secsWhere(s => s.mkt === 'BRVM' && s.cls === 'Equity') : st.u === 'NDX' ? secsWhere(s => s.mkt === 'US' && s.ndx) : secsWhere(s => s.mkt === 'US' && s.typ === 'ETF');
  const val = s => s.mkt === 'BRVM' ? (s.vday || 0) : (s.shd || 0) * (s.last || 0), avat = s => s.liq > 0 && val(s) > 0 ? val(s) / s.liq - 1 : null, ccy = st.u === 'BRVM' ? 'XOF' : 'USD';
  const K = [['val', 'Montant échangé', (a, b) => val(b) - val(a), s => val(s) > 0], ['vol', 'Volume', (a, b) => (b.shd || 0) - (a.shd || 0), s => s.shd > 0], ['up', 'Hausses', (a, b) => b.pct - a.pct, s => s.pct > 0], ['dn', 'Baisses', (a, b) => a.pct - b.pct, s => s.pct < 0],
    ['av', 'Activité inhabituelle', (a, b) => (avat(b) ?? -9) - (avat(a) ?? -9), s => avat(s) != null], ['hi', 'Près du plus haut 52 s.', (a, b) => b.last / b.hi52 - a.last / a.hi52, s => s.hi52 > 0], ['lo', 'Près du plus bas 52 s.', (a, b) => a.last / a.lo52 - b.last / b.lo52, s => s.lo52 > 0]];
  const cur = K.find(x => x[0] === st.k) || K[0], L = U0.filter(s => s.last && cur[3](s)).sort(cur[2]).slice(0, 40), live = U0.filter(s => s.pct != null);
  m.innerHTML = `<div class="tools mst"><span class="tlab">Marché</span><select class="ofld" id="moU">${[['BRVM', 'BRVM · actions'], ['NDX', 'Nasdaq-100'], ['ETF', 'ETF US']].map(([k, l]) => `<option value="${k}" ${st.u === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <span class="tlab">Devise</span><span class="wh">${ccy}</span><span class="gsp"></span><span class="dm">${U0.length} titres · ${live.filter(s => s.pct > 0).length} en hausse, ${live.filter(s => s.pct < 0).length} en baisse</span></div>
    ${subTabs(K.map(([k, l]) => [k, l]), st.k, 'data-mk', 1)}
    <div class="grid side">${pn(`${cur[1]} · ${L.length} titres`, 'MOST', `<div class="tw" style="max-height:calc(100vh - 290px - var(--nwh, 90px))"><table class="t"><thead><tr><th class="l">Titre</th><th class="l">Nom</th><th>Dernier</th><th>Var. nette</th><th>Var. %</th><th>Volume</th><th>Montant (${ccy})</th><th title="Montant du jour contre la moyenne quotidienne sur 3 mois">Δ moy. 3 mois</th><th>Fourchette 52 s.</th></tr></thead><tbody>
      ${L.map((s, i) => `<tr data-sec="${s.id}" data-to="GP" style="cursor:pointer"><td class="l"><span class="rn">${i + 1})</span><b class="wh">${s.id}</b></td><td class="l am">${esc(s.short || s.n)}</td><td class="wh">${px(s, s.last)}</td><td class="${cls(s.last - s.prev)}">${s.prev ? (s.last - s.prev > 0 ? '+' : '') + px(s, s.last - s.prev) : '—'}</td><td>${pc(s.pct)}</td><td>${s.shd ? num(s.shd, 0) : '—'}</td><td>${val(s) ? big(val(s)) : '—'}</td><td>${avat(s) != null ? pc(avat(s), 0) : '—'}</td><td>${rangeBar3(s.last, s.lo52, s.hi52)}</td></tr>`).join('') || '<tr><td class="l dm" colspan="9">Aucun titre pour ce classement.</td></tr>'}</tbody></table></div>`, { np: true, lect: 'Δ moy. 3 mois = montant échangé du jour contre la moyenne quotidienne des trois derniers mois. Clic sur une ligne : graphique du titre.' })}
      ${pn('Largeur du jour', 'MOST', `<div class="kv2"><span>Titres en hausse</span><b class="up">${live.filter(s => s.pct > 0).length}</b><span>Titres en baisse</span><b class="dn">${live.filter(s => s.pct < 0).length}</b><span>Inchangés</span><b>${live.filter(s => !s.pct).length}</b><span>Montant total échangé</span><b>${big(U0.reduce((a, s) => a + val(s), 0))} ${ccy}</b><span>Variation médiane</span><b>${pc(U.median ? U.median(live.map(s => s.pct)) : live.map(s => s.pct).sort((a, b) => a - b)[Math.floor(live.length / 2)])}</b></div>${cvb('moH', 200)}`, { lect: 'Répartition des variations du jour (%).' })}</div>`;
  $('moU').onchange = e => { st.u = e.target.value; render(); }; m.querySelectorAll('[data-mk]').forEach(b => b.onclick = () => { st.k = b.dataset.mk; render(); });
  const bins = [-.1, -.05, -.03, -.02, -.01, 0, .01, .02, .03, .05, .1], cnt = new Array(bins.length + 1).fill(0); live.forEach(s => { let i = bins.findIndex(b => s.pct < b); if (i < 0) i = bins.length; cnt[i]++; });
  barChart($('moH'), { labels: ['<-10', '-10/-5', '-5/-3', '-3/-2', '-2/-1', '-1/0', '0/1', '1/2', '2/3', '3/5', '5/10', '>10'], values: cnt, fmt: v => num(v, 0), labelsOnBars: true, colors: cnt.map((_, i) => i < 6 ? '#ff433d' : '#32c74c'), padB: 22 });
};

/* FA : petite icône graphique devant chaque ligne (comme le terminal) → GF sur l'indicateur */
const GF_ICO = '<svg width="11" height="9" viewBox="0 0 11 9"><rect x=".5" y=".5" width="10" height="8" fill="none" stroke="#8a8a8a"/><path d="M2 7V5M4.5 7V3M7 7V4.5M9 7V2" stroke="#ffa028" stroke-width="1.4"/></svg>';
document.addEventListener('click', e => { const g = e.target.closest('[data-gf]'); if (!g) return; e.stopPropagation(); ST.gf = { k: g.dataset.gf, k2: '' }; go('GF', ST.sec); });

/* ------------------------------------------------------------------ RV, onglet 1 : tableau de comparables comme l'écran Relative Valuation */
async function RV_COMPS(m, alive) {
  const s = sec(ST.sec); setTitle('Relative Valuation'); const IDX = await getJSON('fa_index.json').catch(() => null); if (!alive()) return;
  const FI = Object.fromEntries(((IDX && IDX.rows) || []).map(r => [r.id, r]));
  const peers = secsWhere(x => x.id !== s.id && x.mkt === s.mkt && x.cls === 'Equity' && x.typ !== 'ETF' && x.grp === s.grp && !legacy(x)).sort((a, b) => (b.mcap || 0) - (a.mcap || 0)).slice(0, 24);
  const C = [['mcap', 'Capi.', x => x.mcap, v => big(v)], ['last', 'Dernier', x => x.last, (v, x) => px(x, v)], ['pct', 'Var. 1J', x => x.pct, v => pc(v)], ['ytd', 'Var. YTD', x => x.ytd, v => pc(v, 1)],
    ['rev_g', 'Croiss. CA 1 an', x => (FI[x.id] || {}).rev_g, v => pc(v, 1)], ['eps_g', 'Croiss. BPA 1 an', x => (FI[x.id] || {}).eps_g, v => pc(v, 1)], ['pe', 'PER', x => (FI[x.id] || {}).pe ?? x.per, v => num(v, 1)],
    ['pb', 'Cours / actif net', x => (FI[x.id] || {}).pb, v => num(v, 2)], ['ev_ebitda', 'VE / EBITDA', x => (FI[x.id] || {}).ev_ebitda, v => num(v, 1)], ['roe', 'ROE', x => (FI[x.id] || {}).roe, v => P1(v, 1)],
    ['nm', 'Marge nette', x => (FI[x.id] || {}).nm, v => P1(v, 1)], ['dy', 'Rdt div.', x => (FI[x.id] || {}).dy ?? x.yld, v => P1(v, 2)]];
  const st = ST.rvc = ST.rvc || { k: 'mcap', d: -1 }; const sorted = peers.slice().sort((a, b) => { const c = C.find(c => c[0] === st.k), A = c[2](a), B = c[2](b); if (A == null) return 1; if (B == null) return -1; return (A - B) * st.d; });
  const ok = v => v != null && isFinite(v), stat = (f, x) => { const v = peers.concat([s]).map(x).filter(ok).sort((a, b) => a - b); if (!v.length) return null; return f === 'avg' ? v.reduce((a, b) => a + b, 0) / v.length : v[Math.floor((v.length - 1) / 2)] * (v.length % 2 ? 1 : .5) + (v.length % 2 ? 0 : v[v.length / 2] * .5); };
  const cell = (c, x) => { const v = c[2](x); return ok(v) ? c[3](v, x) : '<span class="dm">—</span>'; };
  const sRow = (lab, f) => `<tr class="rvs"><td class="l">${lab}</td><td class="l"></td>${C.map(c => { const v = ['last', 'mcap'].includes(c[0]) ? null : stat(f, c[2]); return `<td>${ok(v) ? c[3](v, s) : ''}</td>`; }).join('')}</tr>`;
  m.innerHTML = `<div class="tools rvt"><span class="tlab">Comparables</span><span class="wh">${esc(s.grp || '—')} · ${s.mkt === 'BRVM' ? 'BRVM' : 'États-Unis'} (${peers.length})</span><span class="tlab">Devise</span><span class="wh">${esc(s.ccy || '')}</span><span class="gsp"></span><span class="dm">Tri : cliquer un en-tête</span></div>
    ${pn(`${esc(ykey(s))} · valorisation relative`, 'RV', `<div class="tw" style="max-height:calc(100vh - 290px - var(--nwh, 90px))"><table class="t rvc"><thead><tr><th class="l">Titre</th><th class="l">Nom</th>${C.map(c => `<th data-rk="${c[0]}" class="${st.k === c[0] ? 'on' : ''}" style="cursor:pointer">${c[1]}${st.k === c[0] ? (st.d > 0 ? ' ▲' : ' ▼') : ''}</th>`).join('')}</tr></thead><tbody>
      <tr class="rvme"><td class="l"><b>${s.id}</b></td><td class="l">${esc(s.short || s.n)}</td>${C.map(c => `<td>${cell(c, s)}</td>`).join('')}</tr>${sRow('Moyenne', 'avg')}${sRow('Médiane', 'med')}
      ${sorted.map((x, i) => `<tr data-sec="${x.id}" data-to="RV" style="cursor:pointer"><td class="l"><span class="rn">${i + 1})</span><b class="wh">${x.id}</b></td><td class="l am">${esc(x.short || x.n)}</td>${C.map(c => `<td>${cell(c, x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`,
      { np: true, lect: `Sociétés du même secteur sur le même marché, classées par capitalisation. Ratios sur le dernier exercice publié ; moyenne et médiane incluent ${esc(s.id)}. Analyse des multiples dans le temps : onglet 2 ; juste valeur : onglet 3.` })}`;
  m.querySelectorAll('[data-rk]').forEach(th => th.onclick = () => { const k = th.dataset.rk; st.d = st.k === k ? -st.d : -1; st.k = k; render(); });
}

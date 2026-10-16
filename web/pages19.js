/* ================= FQT — QLAB : onglet « Prévisions » (moteur QLAB-P, scripts/qlab_prev.py) =================
   Prévision des résultats des sociétés cotées à la BRVM (chiffre d'affaires ou PNB, résultat d'exploitation, résultat net, bénéfice
   par action, marges), annuels et cumulés en cours d'exercice. Aucune prévision du cours, aucun objectif de cours.
   Chiffres publiés en blanc, chiffres prévus en bleu clair et en italique. Styles propres (préfixe qp-). */
const QP = { sub: 'f' };
(function qpStyle() {
  if (document.getElementById('qp-style')) return;
  const st = document.createElement('style'); st.id = 'qp-style';
  st.textContent = `
.qp-t td.fc,.qp-t th.fc{color:#8fd3ff;font-style:italic;background:rgba(77,167,253,.07)}
.qp-t th.pub{color:var(--white)}
.qp-t td small{display:block;color:#7fa9c9;font-size:10.5px;font-style:normal;line-height:12px}
.qp-leg{display:flex;gap:14px;font-size:11px;padding:2px 6px;color:var(--dim)}.qp-leg b.p{color:var(--white)}.qp-leg b.f{color:#8fd3ff;font-style:italic}
.qp-svg{width:100%;height:190px;display:block}
.qp-tag{display:inline-block;font-size:10.5px;padding:0 4px;border:1px solid currentColor;border-radius:2px;line-height:14px;color:#8fd3ff}`;
  document.head.appendChild(st);
})();
const QP_SUBS = [['f', 'Prévisions'], ['r', 'Révisions et événements'], ['m', 'Méthode et fiabilité']];
const QP_PER = { T1: '1er trimestre', S1: '1er semestre', '9M': '9 mois', A: 'exercice' };
const QP_M = { rev: 'Chiffre d’affaires', ebit: 'Résultat d’exploitation', ni: 'Résultat net' };
const QP_METH = { naive: 'exercice précédent reconduit', drift: 'tendance : croissance médiane des derniers exercices', ytd_g: 'croissance du cumul de l’exercice appliquée à l’exercice précédent',
  ytd_s: 'cumul de l’exercice ÷ part saisonnière habituelle de la période', ytd_d: 'écart du cumul de l’exercice ajouté à l’exercice précédent', margin: 'chiffre d’affaires prévu × marge médiane des 3 derniers exercices',
  trend: 'tendance de la société rapprochée de la croissance de long terme ; marge ramenée vers sa médiane',
  damped: 'croissance récente amortie vers la croissance de long terme ; marge ramenée progressivement vers sa médiane',
  comb: 'moyenne de deux méthodes (niveau reconduit et tendance)', sector: 'marge qui rejoint en cinq ans la médiane des sociétés du même secteur' };
const QP_MS = { naive: 'naïve', drift: 'tendance', ytd_g: 'croissance du cumul', ytd_s: 'part saisonnière', ytd_d: 'écart du cumul', margin: 'marge médiane', trend: 'tendance et marge',
  damped: 'croissance amortie', comb: 'combinaison', sector: 'marge du secteur' };
const QP_VT = { initiale: 'Version initiale', publication: 'Mise à jour (résultats publiés)', exceptionnelle: 'Révision exceptionnelle', trimestrielle: 'Mise à jour trimestrielle', methode: 'Révision de méthode' };
const QP_DISC = '<div class="qv-disc">QLAB Prévisions estime les résultats des entreprises à partir de leurs publications ; il ne prévoit pas le cours de l’action, ne donne aucun objectif de cours et ne promet aucun rendement. Montants en millions de francs CFA ; bénéfice par action en francs CFA, sur la base du nombre d’actions actuel ; fourchettes à 80 % mesurées sur les erreurs passées de la méthode.</div>';
const qpM = v => v == null || !isFinite(v) ? '—' : num(v, Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 10 ? 1 : 2);

async function qpPage(m, alive, s) {
  setTitle(`QLAB Prévisions · ${(s.short || s.n || s.id).toUpperCase()}`);
  m.innerHTML = '<div class="empty">Chargement des prévisions…</div>';
  const [IX, C] = await Promise.all([getJSON('qlabp/index.json').catch(() => null), getJSON(`qlabp/${s.id}.json`).catch(() => null)]); if (!alive()) return;
  if (!IX) { m.innerHTML = pn('Prévisions QLAB', 'QLAB', '<div class="empty">Le moteur de prévisions n’a pas encore produit de résultats. Il est calculé chaque soir après la clôture.</div>') + QP_DISC; return; }
  const sub = QP_SUBS.some(x => x[0] === QP.sub) ? QP.sub : (QP.sub = 'f');
  const bar = subTabs(QP_SUBS, sub, 'data-qp');
  const bind = () => m.querySelectorAll('[data-qp]').forEach(b => b.onclick = () => { QP.sub = b.dataset.qp; qpPage(m, alive, s); });
  if (!C || !C.cur) {
    const why = C && C.fail ? C.fail.why : 'aucune prévision n’a encore été produite pour ce titre';
    m.innerHTML = bar + pn('Prévisions QLAB', 'QLAB', `<div class="empty">Pas de prévision pour ${esc(s.short || s.n)} : ${esc(why)}.<br>Nouvel essai automatique à chaque passage du soir.</div>`) + QP_DISC; bind(); return;
  }
  const body = sub === 'f' ? qpFc(C, IX) : sub === 'r' ? qpRev(C, IX) : qpMeth(C, IX);
  m.innerHTML = bar + qpHead(C) + body + QP_DISC; bind();
}

function qpHead(C) {
  const F = C.cur.fc, nx = C.next || {};
  const st = F.state ? `${QP_PER[F.state]} ${F.fy} publié` : `comptes ${F.fy_last} publiés`;
  return `<div class="qv-head"><span><span class="l">Exercice prévu</span><span class="v">${F.fy}</span></span><span><span class="l">Dernière publication intégrée</span>${st}</span>
    <span><span class="l">${esc(QP_VT[C.cur.type] || C.cur.type)}</span>${qvD(C.cur.date)}</span>
    <span><span class="l">Prochaine publication attendue</span>${nx.per ? QP_PER[nx.per] + ' ' + nx.fy : '—'}${nx.d ? ' <span class="dm">(vers le ' + qvD(nx.d) + ')</span>' : ''}</span></div>
    ${(C.alerts || []).map(a => `<div class="qv-info">${esc(a)}</div>`).join('')}
    ${C.cur.widen ? `<div class="qv-warn">Révision exceptionnelle en cours : des documents récents peuvent modifier le résultat net d’environ ${qvP(C.cur.widen.imp, 0)}${C.cur.widen.neg ? ', plutôt à la baisse' : ''} ; la fourchette du résultat net est élargie en conséquence jusqu’à la publication des chiffres.</div>` : ''}`;
}

/* 11) Prévisions */
function qpFc(C, IX) {
  const F = C.cur.fc, P = C.pub || { annual: [], periods: [] }, bank = F.grp === 'banque';
  const pubA = P.annual.slice(-4), fcA = F.annual;
  const cellP = v => `<td>${qpM(v)}</td>`;
  const cellF = x => x && x.v != null ? `<td class="fc">${qpM(x.v)}${x.lo != null ? `<small>${qpM(x.lo)} – ${qpM(x.hi)}</small>` : ''}</td>` : '<td class="fc">—</td>';
  const rows = [['rev', bank ? 'Produit net bancaire' : 'Chiffre d’affaires'], ['ebit', 'Résultat d’exploitation'], ['ni', 'Résultat net'], ['eps', 'Bénéfice par action (FCFA)']];
  const pct = v => v == null || !isFinite(v) ? '—' : num(v * 100, 1) + ' %';
  const tA = `<div class="tw"><table class="t qp-t"><thead><tr><th class="l"></th>${pubA.map(a => `<th class="pub">${a.fy}${a.ver ? '' : '*'}</th>`).join('')}${fcA.map(a => `<th class="fc">${a.fy}${a.h === 1 ? ' (en cours)' : ''}</th>`).join('')}</tr></thead><tbody>
    ${rows.map(([k, l]) => `<tr><td class="l am">${l}</td>${pubA.map(a => cellP(a[k])).join('')}${fcA.map(a => cellF(a[k])).join('')}</tr>`).join('')}
    <tr><td class="l am">Marge nette</td>${pubA.map(a => `<td>${a.ni != null && a.rev ? pct(a.ni / a.rev) : '—'}</td>`).join('')}${fcA.map(a => `<td class="fc">${pct(a.nm)}</td>`).join('')}</tr>
    ${bank ? '' : `<tr><td class="l am">Marge d’exploitation</td>${pubA.map(a => `<td>${a.ebit != null && a.rev ? pct(a.ebit / a.rev) : '—'}</td>`).join('')}${fcA.map(a => `<td class="fc">${pct(a.om)}</td>`).join('')}</tr>`}</tbody></table></div>
    <div class="qp-leg"><span><b class="p">blanc</b> : publié</span><span><b class="f">bleu, en italique</b> : prévu, avec la fourchette à 80 % en dessous</span><span>* exercice non vérifié dans les états financiers publiés</span></div>`;
  // cumuls intermédiaires : 3 derniers exercices publiés et exercice en cours (publié ou prévu)
  const yrs = [...new Set(P.periods.map(p => p.fy))].filter(y => y < F.fy).slice(-3);
  const per = ['T1', 'S1', '9M'].filter(p => P.periods.some(x => x.per === p) || F.periods.some(x => x.per === p));
  const pv = (y, p, k) => (P.periods.find(x => x.fy === y && x.per === p) || {})[k];
  const fv = (p, k) => F.periods.find(x => x.per === p && x.m === k);
  const tP = per.length ? `<div class="tw"><table class="t qp-t"><thead><tr><th class="l">Cumul depuis le début de l’exercice</th>${yrs.map(y => `<th class="pub">${y}</th>`).join('')}<th class="fc">${F.fy}</th></tr></thead><tbody>
      ${per.flatMap(p => ['rev', 'ni'].map(k => { const cur = pv(F.fy, p, k), f = fv(p, k);
        return `<tr><td class="l am">${QP_PER[p]} · ${k === 'rev' ? (bank ? 'PNB' : 'chiffre d’affaires') : 'résultat net'}</td>${yrs.map(y => cellP(pv(y, p, k))).join('')}${cur != null ? `<td><b>${qpM(cur)}</b></td>` : cellF(f)}</tr>`; })).join('')}</tbody></table></div>
      <div class="qp-leg"><span>Publications lues : ${P.periods.length} cumuls ; chaque chiffre est contrôlé par la variation publiée sur la même ligne du document.</span></div>`
    : '<div class="empty">Aucune publication intermédiaire lue pour cette société : la prévision repose sur les comptes annuels.</div>';
  // scénarios de l'exercice en cours
  const a1 = fcA[0] || {};
  const sc = `<div class="tw"><table class="t"><thead><tr><th class="l">Exercice ${F.fy}</th><th>Défavorable</th><th>Central</th><th>Favorable</th></tr></thead><tbody>
    ${rows.map(([k, l]) => a1[k] ? `<tr><td class="l am">${l}</td><td>${qpM(a1[k].lo)}</td><td class="fc">${qpM(a1[k].v)}</td><td>${qpM(a1[k].hi)}</td></tr>` : '').join('')}</tbody></table></div>`;
  // ce qui fait évoluer la prévision
  const why = ['rev', 'ebit', 'ni'].filter(k => a1[k]).map(k => { const x = a1[k], alts = x.alts || {};
    const x2 = (fcA[1] || {})[k];
    return `<p><b>${k === 'rev' && bank ? 'Produit net bancaire' : QP_M[k]}</b> : ${F.fy} — ${esc(QP_METH[x.meth] || x.meth)}${x.n ? ` <span class="dm">(fourchette mesurée sur ${x.n} prévisions passées)</span>` : ''}.${Object.keys(alts).length > 1 ? ` Autres méthodes : ${Object.entries(alts).filter(([mm]) => mm !== x.meth).map(([mm, v]) => `${esc(QP_METH[mm] || mm)} ${qpM(v)}`).join(' ; ')}.` : ''}${x2 ? ` Exercices suivants — ${esc(QP_METH[x2.meth] || x2.meth)}.` : ''}</p>`; }).join('');
  const lastP = P.periods.filter(p => p.fy === F.fy).slice(-1)[0];
  const ytd = lastP ? `<p><b>Dernier cumul publié</b> : ${QP_PER[lastP.per]} ${lastP.fy}${lastP.rev != null ? ` — ${bank ? 'PNB' : 'chiffre d’affaires'} ${qpM(lastP.rev)}` : ''}${lastP.ni != null ? `, résultat net ${qpM(lastP.ni)}` : ''}${(() => { const pr = P.periods.find(x => x.fy === lastP.fy - 1 && x.per === lastP.per); return pr && pr.rev && lastP.rev ? ` (${lastP.rev >= pr.rev ? '+' : ''}${num((lastP.rev / pr.rev - 1) * 100, 1)} % sur un an)` : ''; })()}${lastP.src ? ` <span class="dm">· ${esc(lastP.src)}${lastP.d ? ', ' + qvD(lastP.d) : ''}</span>` : ''}.</p>` : '';
  const chart = qpChart(P.annual, fcA, 'ni', 'Résultat net') + qpChart(P.annual, fcA, 'rev', bank ? 'Produit net bancaire' : 'Chiffre d’affaires');
  const B = (C.bench || []).slice(-1)[0];
  const bench = B ? pn(`Dernière publication jugée (${qvD(B.date)})`, 'QLAB', `${!B.rows.length ? '<div class="dm" style="padding:6px">La version précédente ne prévoyait pas encore ce chiffre (publication intégrée pour la première fois) : la comparaison prévu / publié commencera avec la publication suivante.</div>' : ''}<div class="tw"${B.rows.length ? '' : ' style="display:none"'}><table class="t"><thead><tr><th class="l">Publication</th><th class="l">Poste</th><th>Prévu avant publication</th><th>Fourchette</th><th>Publié</th><th>Écart</th><th>Dans la fourchette</th></tr></thead><tbody>
      ${B.rows.map(r => `<tr><td class="l am">${QP_PER[r.per]} ${r.fy}</td><td class="l">${r.m === 'rev' && bank ? 'Produit net bancaire' : QP_M[r.m]}</td><td class="fc">${qpM(r.f)}</td><td class="fc">${r.lo != null ? qpM(r.lo) + ' – ' + qpM(r.hi) : '—'}</td><td><b>${qpM(r.a)}</b></td><td>${qvS(r.e, 1)}</td><td>${r.in ? '<span class="up">oui</span>' : '<span class="dn">non</span>'}</td></tr>`).join('')}</tbody></table></div>
      <div class="lectb">${Object.entries(B.dec || {}).map(([m, d]) => `<p><b>${m === 'rev' && bank ? 'Produit net bancaire' : QP_M[m]} ${B.fy}</b> : prévision ${d.word}${d.word !== 'maintenue' ? ` de ${qvS(d.chg, 1)}` : ''} (${qpM(d.before)} → <span class="fc" style="color:#8fd3ff;font-style:italic">${qpM(d.after)}</span>) — ${esc(QP_METH[d.meth] || d.meth || '')}.</p>`).join('')}</div>`,
      { lect: 'À chaque publication (trimestre, semestre, 9 mois, exercice), le chiffre publié est comparé à ce que prévoyait la version précédente ; la prévision de l’exercice est alors relevée, abaissée ou maintenue selon la méthode qui, sur les exercices passés, a le mieux utilisé ce type de publication.' }) : '';
  return `${bench}<div class="grid c2"><div>${pn('Résultats annuels : publiés et prévus', 'QLAB', tA, { lect: 'Exercice en cours puis quatre exercices suivants. Plus l’horizon est long, plus la fourchette s’élargit : elle reprend les erreurs réellement mesurées à cet horizon.' })}
    ${pn('Résultats intermédiaires', 'QLAB', tP, { lect: 'Montants cumulés depuis le début de l’exercice (3, 6 ou 9 mois). En gras : publié pour l’exercice en cours.' })}
    ${pn('Scénarios de l’exercice ' + F.fy, 'QLAB', sc, { lect: 'Défavorable et favorable : 10e et 90e centiles des erreurs passées de la méthode retenue, appliqués à la prévision centrale (une chance sur dix de faire moins bien, une sur dix de faire mieux). Ce ne sont pas des objectifs.' })}</div>
    <div>${pn('Évolution et prévision', 'QLAB', chart)}${pn('Ce qui fait évoluer la prévision', 'QLAB', `<div class="lectb">${ytd}${why}<p class="dm">Facteurs sectoriels (matières premières, change, inflation, météo) : à développer — ils ne seront intégrés que s’ils réduisent l’erreur mesurée sur les exercices passés.</p></div>`)}</div></div>`;
}

function qpChart(pub, fc, k, label) {
  const P = pub.filter(a => a[k] != null).map(a => [a.fy, a[k]]), F = fc.filter(a => a[k] && a[k].v != null).map(a => [a.fy, a[k].v, a[k].lo, a[k].hi]);
  if (P.length < 2 && !F.length) return '';
  const xs = [...P.map(p => p[0]), ...F.map(f => f[0])], all = [...P.map(p => p[1]), ...F.flatMap(f => [f[1], f[2], f[3]])].filter(v => v != null && isFinite(v));
  const x0 = Math.min(...xs), x1 = Math.max(...xs), lo = Math.min(0, ...all), hi = Math.max(...all) * 1.05 || 1;
  const W = 600, H = 170, pl = 58, pb = 18, X = y => pl + (y - x0) / (x1 - x0 || 1) * (W - pl - 12), Y = v => 6 + (hi - v) / (hi - lo || 1) * (H - pb - 8);
  const band = F.filter(f => f[2] != null && f[3] != null);
  const last = P.length ? P[P.length - 1] : null;
  const poly = band.length ? `<polygon points="${[...(last ? [[last[0], last[1], last[1], last[1]]] : []), ...band].map(f => `${X(f[0])},${Y(f[3])}`).join(' ')} ${[...(last ? [[last[0], last[1], last[1], last[1]]] : []), ...band].reverse().map(f => `${X(f[0])},${Y(f[2])}`).join(' ')}" fill="rgba(77,167,253,.16)"/>` : '';
  return `<div class="dm" style="font-size:11.5px;padding:2px 6px">${label} (millions de FCFA)</div><svg class="qp-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
    ${niceTicks(lo, hi, 4).map(t => `<line x1="${pl}" x2="${W - 10}" y1="${Y(t)}" y2="${Y(t)}" stroke="#262626"/><text x="${pl - 4}" y="${Y(t) + 3}" fill="#a5a5a5" font-size="10" text-anchor="end">${num(t, 0)}</text>`).join('')}
    ${xs.filter((y, i, a) => a.indexOf(y) === i).map(y => `<text x="${X(y)}" y="${H - 4}" fill="#a5a5a5" font-size="10" text-anchor="middle">${y}</text>`).join('')}${poly}
    <polyline fill="none" stroke="#ffffff" stroke-width="1.6" points="${P.map(p => `${X(p[0])},${Y(p[1])}`).join(' ')}"/>
    ${F.length ? `<polyline fill="none" stroke="#8fd3ff" stroke-width="1.6" stroke-dasharray="5 3" points="${[...(last ? [last] : []), ...F].map(p => `${X(p[0])},${Y(p[1])}`).join(' ')}"/>` : ''}</svg>
    <div class="qp-leg"><span><b class="p">—</b> publié</span><span><b class="f">- -</b> prévu</span><span>bande : fourchette à 80 %</span></div>`;
}

/* 12) Révisions et événements */
function qpRev(C, IX) {
  const V = (C.vers || []).slice().reverse();
  const vt = `<div class="tw"><table class="t"><thead><tr><th class="l">Version</th><th class="l">Type</th><th>Date</th><th>Exercice prévu</th><th class="l">Dernière publication intégrée</th><th>Chiffre d’affaires prévu</th><th>Résultat net prévu</th><th class="l">Décision sur l’exercice</th><th class="l">Motif</th></tr></thead><tbody>
    ${V.map(v => `<tr${v.id === C.cur.id ? ' class="cur"' : ''}><td class="l">${esc(v.id)}</td><td class="l">${esc(QP_VT[v.type] || v.type)}</td><td>${qvD(v.date)}</td><td>${v.fy}</td><td class="l">${v.state ? QP_PER[v.state] : 'comptes annuels'}</td><td class="fc">${qpM(v.rev)}</td><td class="fc">${qpM(v.ni)}</td><td class="l" style="white-space:normal">${v.dec ? Object.entries(v.dec).filter(([m]) => m !== 'ebit').map(([m, d]) => `${m === 'rev' ? 'CA' : 'RN'} ${d.word}${d.word !== 'maintenue' ? ' ' + qvS(d.chg, 1) : ''}`).join(' · ') : '—'}</td><td class="l dm" style="white-space:normal">${esc(v.reason)}</td></tr>`).join('')}</tbody></table></div>`;
  const E = (C.events || []).slice().reverse();
  const ev = E.length ? `<div class="tw"><table class="t"><thead><tr><th>Examen</th><th class="l">Documents</th><th>Portée cumulée</th><th class="l">Décision</th></tr></thead><tbody>${E.map(e => `<tr><td>${qvD(e.d)}</td>
      <td class="l" style="white-space:normal;max-width:420px">${(e.docs || []).map(d => `${esc(d.kn)} · ${esc(d.ti)} <span class="dm">(${qvD(d.d)}${d.imp != null ? ', portée ' + qvP(d.imp, 0) : ''})</span>`).join('<br>')}</td>
      <td>${qvP(e.acc, 0)}</td><td class="l" style="white-space:normal;max-width:320px">${esc(e.dec || '')}</td></tr>`).join('')}</tbody></table></div>`
    : '<div class="dm" style="padding:6px">Aucun document nouveau examiné depuis la version en vigueur.</div>';
  const R = (C.errors || []).slice().reverse();
  const er = R.length ? `<div class="tw"><table class="t"><thead><tr><th class="l">Version</th><th>Exercice</th><th>Période</th><th class="l">Poste</th><th>Prévu</th><th>Publié</th><th>Écart</th><th>Dans la fourchette</th></tr></thead><tbody>${R.slice(0, 60).map(e => `<tr><td class="l">${esc(e.ver)}</td><td>${e.fy}</td><td>${e.per ? QP_PER[e.per] : 'exercice'}</td><td class="l">${QP_M[e.m] || e.m}</td><td class="fc">${qpM(e.f)}</td><td>${qpM(e.a)}</td><td>${qvS(e.e, 1)}</td><td>${e.in ? '<span class="up">oui</span>' : '<span class="dn">non</span>'}</td></tr>`).join('')}</tbody></table></div>`
    : '<div class="dm" style="padding:6px">Aucun résultat publié depuis les premières versions : les écarts seront mesurés automatiquement à chaque publication.</div>';
  return `${pn('Historique des prévisions', 'QLAB', vt, { lect: 'Chaque version est conservée telle qu’elle a été publiée (données disponibles à sa date, méthode, prévisions et fourchettes), horodatée et chaînée à la précédente par une empreinte : aucune prévision passée n’est réécrite. Mise à jour à chaque publication de résultats et au moins une fois par trimestre.' })}
    <div class="grid c2">${pn('Documents examinés', 'QLAB', ev, { lect: `Chaque document publié par la société (communiqué, changement de dirigeant, opération sur le capital, notation, assemblée…) reçoit la portée mesurée de sa nature sur le résultat net des exercices passés. Une portée d’au moins ${qvP(IX.mat_ni || .05, 0)} du résultat net prévu — seule ou par cumul depuis la dernière version — déclenche une révision exceptionnelle : c’est un déclencheur d’analyse, pas une variation automatique. Les publications de résultats sont intégrées directement par la mise à jour des chiffres.` })}
    ${pn('Écarts mesurés (prévu / publié)', 'QLAB', er, { lect: 'Écart = (publié − prévu) ÷ publié. Mesuré pour chaque version dès que le résultat réel est publié.' })}</div>`;
}

/* 13) Méthode et fiabilité */
function qpMeth(C, IX) {
  const g = C.cur.fc.grp, sel = IX.sel || {};
  const keys = Object.keys(sel).filter(k => k.endsWith('|' + g) || k.endsWith('|tous'));
  const lab = k => { const [m, c] = k.split('|'); return `${QP_M[m] || m} · ${c.startsWith('A:') ? 'exercice en cours, ' + (c === 'A:aucune' ? 'aucune publication de l’exercice' : QP_PER[c.slice(2)] + ' publié') : c.startsWith('H') ? 'exercice +' + (+c.slice(1) - 1) : 'cumul ' + QP_PER[c.split(':')[1]] + (c.split(':')[2] !== 'aucune' ? ' après le ' + QP_PER[c.split(':')[2]] : '')}`; };
  const rowsK = keys.filter(k => k.endsWith('|' + g) || !sel[k.replace('|tous', '|' + g)]).filter(k => !k.includes('|P:') || sel[k].n >= 10);
  const tb = `<div class="tw"><table class="t"><thead><tr><th class="l">Prévision</th><th class="l">Erreur médiane par méthode (nombre de cas)</th><th class="l">Retenue</th><th>Fourchette à 80 %</th><th>Couverture hors échantillon</th></tr></thead><tbody>
    ${rowsK.sort().map(k => { const c = sel[k]; return `<tr><td class="l am">${lab(k)}${k.endsWith('|tous') && g !== 'tous' ? ' <span class="dm">(toutes sociétés)</span>' : ''}</td>
      <td class="l dm" style="white-space:normal;min-width:220px">${Object.entries(c.stats).map(([mm, x]) => `${esc(QP_MS[mm] || mm)} ${num(x.mae, 2)} (${x.n})`).join(' · ')}</td><td class="l">${esc(QP_MS[c.best] || c.best)}</td>
      <td>${num(c.q10, 2)} à +${num(c.q90, 2)}</td><td>${c.cov != null ? num(c.cov * 100, 0) + ' %' : '—'}</td></tr>`; }).join('')}</tbody></table></div>`;
  const EF = IX.effects || {}, EVN = { res: 'Publication de résultats', ef: 'États financiers', ra: 'Rapport d’activité', rann: 'Rapport annuel', dir: 'Changement de dirigeant', ost: 'Opération sur le capital', not: 'Notation financière', com: 'Communiqué', ag: 'Assemblée générale', div: 'Dividende', kw: 'Intitulé signalant un événement exceptionnel (perte, incendie, grève, cession…)' };
  const ef = `<div class="tw"><table class="t"><thead><tr><th class="l">Nature du document</th><th>Exercices concernés</th><th>Sociétés comparées</th><th>Écart d’erreur médian</th><th>Portée retenue</th></tr></thead><tbody>${Object.keys(EVN).filter(k => EF[k]).map(k => `<tr><td class="l am">${EVN[k]}</td><td>${EF[k].n}</td><td>${EF[k].co}</td><td>${qvS(EF[k].d, 0)}</td><td><b>${num(EF[k].imp * 100, 0)} %</b></td></tr>`).join('')}</tbody></table></div>`;
  const L = IX.live || {}, lk = Object.keys(L).filter(k => k.endsWith('|' + g));
  const live = lk.length ? `<div class="tw"><table class="t"><thead><tr><th class="l">Poste · horizon</th><th>Cas</th><th>Biais médian</th><th>Erreur médiane</th><th>Dans la fourchette</th></tr></thead><tbody>${lk.sort().map(k => { const [m, h] = k.split('|'); return `<tr><td class="l am">${QP_M[m] || m} · ${h.startsWith('H') ? 'exercice +' + (+h.slice(1) - 1) : 'cumul ' + QP_PER[h.split(':')[1]]}</td><td>${L[k].n}</td><td>${qvS(L[k].bias, 1)}</td><td>${qvP(L[k].mae, 1)}</td><td>${qvP(L[k].cover, 0)}</td></tr>`; }).join('')}</tbody></table></div>`
    : '<div class="dm" style="padding:6px">Le suivi des versions publiées commence : il se remplira à chaque publication de résultats.</div>';
  const st0 = ['aucune', 'T1', 'S1', '9M'];
  const cellG = (m, st) => sel[`${m}|A:${st}|${g}`] && sel[`${m}|A:${st}|${g}`].n >= 15 ? sel[`${m}|A:${st}|${g}`] : sel[`${m}|A:${st}|tous`];
  const ap = `<div class="tw"><table class="t"><thead><tr><th class="l">Erreur médiane sur l’exercice en cours</th>${st0.map(x => `<th>${x === 'aucune' ? 'avant toute publication' : 'après le ' + QP_PER[x]}</th>`).join('')}</tr></thead><tbody>
    ${['rev', 'ebit', 'ni'].map(m => `<tr><td class="l am">${QP_M[m]}</td>${st0.map(x => { const c = cellG(m, x); const b = c && c.stats[c.best]; return `<td>${b ? num(b.mae, 2) + ` <span class="dm">(${esc(QP_MS[c.best] || c.best)}, ${b.n})</span>` : '—'}</td>`; }).join('')}</tr>`).join('')}</tbody></table></div>`;
  return `${pn('Apport des publications trimestrielles et semestrielles', 'QLAB', ap, { lect: 'Erreur médiane de la prévision de l’exercice en cours (en variations annuelles habituelles de la société) selon l’information publiée à la date de la prévision, avec la méthode retenue et le nombre de cas passés. Chaque publication intermédiaire est ainsi jugée : elle ne fait bouger la prévision annuelle que dans la mesure où ce type de publication a amélioré les prévisions par le passé. Les colonnes se rempliront à mesure que les rapports trimestriels restants sont lus.' })}
    ${pn('Validation point-in-time des méthodes', 'QLAB', tb, { lect: `Chaque prévision passée est refaite à la date de chaque publication, avec les seules informations publiées à cette date (${num(IX.bt_n || 0, 0)} prévisions refaites). Erreurs exprimées en « variations annuelles habituelles » de la société (moyenne des variations d’une année sur l’autre sur 5 ans), ce qui rend les sociétés comparables. Une méthode ne remplace la prévision naïve que si elle réduit l’erreur médiane d’au moins 10 % sur au moins 15 cas. Couverture : part des résultats 2020-2025 tombés dans les fourchettes calibrées sur 2008-2019 (80 % visés). Type d’entreprise retenu : ${g === 'banque' ? 'banques' : 'autres sociétés'}.` })}
    ${pn('Portée mesurée des documents publiés', 'QLAB', ef, { lect: 'Pour chaque société, erreur de la prévision du résultat net (en part du résultat publié) les exercices où un document de cette nature a été publié, comparée à ses autres exercices ; médiane des écarts entre sociétés. Un écart positif est la portée retenue : un document de cette nature peut modifier le résultat net d’autant. Les publications de résultats sont intégrées directement.' })}
    ${pn('Suivi des prévisions publiées', 'QLAB', live, { lect: 'Erreurs des versions publiées par le moteur, mesurées automatiquement quand les résultats réels paraissent (par poste et horizon, pour ce type d’entreprise).' })}`;
}

/* ================= FQT — QLAB : onglet « Valorisation » (moteur QLAB-V) =================
   Fichier autonome de la fonction QLAB : l'onglet « Statistiques » existant (pages2.js) est repris tel quel ; l'onglet
   « Valorisation » affiche les estimations calculées chaque soir après la clôture par scripts/qlab.py (données data/qlab/).
   Styles propres à cet onglet injectés ici (préfixe qv-) : aucun fichier partagé n'est modifié. */
const QLAB_STATS = PAGES.QLAB;
const QV = { sub: 's', h: 1, cmpA: null, cmpB: null, sort: 'up', desc: true };
(function qvStyle() {
  if (document.getElementById('qv-style')) return;
  const st = document.createElement('style'); st.id = 'qv-style';
  st.textContent = `
.qv-head{display:flex;flex-wrap:wrap;gap:4px 18px;align-items:baseline;padding:5px 8px;background:#0b0b0b;border:1px solid var(--line);margin-bottom:4px}
.qv-head .v{font-size:20px;color:var(--white)}.qv-head .l{color:var(--amber);font-size:11.5px;margin-right:4px}
.qv-warn{padding:3px 8px;margin:0 0 4px;border-left:3px solid var(--dn);background:#1a0606;color:#ffc9c6;font-size:12px}
.qv-info{padding:3px 8px;margin:0 0 4px;border-left:3px solid var(--amber);background:#160f02;color:#ffd9a6;font-size:12px}
.qv-rng{position:relative;height:46px;margin:6px 10px 2px}
.qv-rng .ax{position:absolute;left:0;right:0;top:22px;height:1px;background:var(--line2)}
.qv-rng .b1{position:absolute;top:15px;height:15px;background:rgba(77,167,253,.18)}
.qv-rng .b2{position:absolute;top:15px;height:15px;background:rgba(77,167,253,.38)}
.qv-rng .c{position:absolute;top:9px;width:2px;height:27px;background:var(--white)}
.qv-rng .p{position:absolute;top:5px;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:9px solid var(--yel);margin-left:-6px}
.qv-rng .m{position:absolute;top:19px;width:7px;height:7px;border-radius:50%;margin-left:-3px;border:1px solid #000}
.qv-rng .t{position:absolute;top:33px;font-size:10.5px;color:var(--dim);transform:translateX(-50%);white-space:nowrap}
.qv-kind{display:inline-block;font-size:10.5px;padding:0 4px;border:1px solid currentColor;border-radius:2px;line-height:14px}
.qv-bar{display:inline-block;height:9px;background:var(--cyan);vertical-align:middle}
.qv-tor{display:grid;grid-template-columns:minmax(120px,220px) 1fr;gap:2px 8px;font-size:12px;align-items:center}
.qv-tor .tr{position:relative;height:13px;background:#141414}
.qv-tor .tr i{position:absolute;top:1px;height:11px;background:var(--cyan)}
.qv-tor .tr b{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--yel)}
.qv-hist{display:flex;align-items:flex-end;gap:1px;height:130px;padding:4px 6px 0;position:relative}
.qv-hist i{flex:1;background:var(--cyan);min-height:1px}
.qv-hist .pm{position:absolute;top:0;bottom:0;width:2px;background:var(--yel)}
.qv-hist .cm{position:absolute;top:0;bottom:0;width:2px;background:var(--white)}
.qv-sel{display:flex;gap:4px;flex-wrap:wrap;align-items:center;padding:3px 0}
.qv-sel select{background:var(--org);color:#000;border:0;font:var(--fw) 12px var(--mono);height:20px}
.qv-ok{color:var(--up)}.qv-no{color:var(--dim)}
.qv-disc{color:var(--dim);font-size:11.5px;padding:6px 2px;line-height:1.45}
.qv-svg{width:100%;height:220px;display:block}
@media(max-width:700px){.qv-head .v{font-size:17px}.qv-tor{grid-template-columns:110px 1fr}.qv-mt th:nth-child(5),.qv-mt tr>td:nth-child(5):not([colspan]){display:none}.qv-mt td{white-space:normal!important}}`;
  document.head.appendChild(st);
})();

const qvP = (v, d = 1) => v == null || !isFinite(v) ? '—' : num(v * 100, d) + ' %';
const qvS = (v, d = 1) => v == null || !isFinite(v) ? '<span class="fl">—</span>' : `<span class="${v > 0 ? 'up' : v < 0 ? 'dn' : ''}">${v > 0 ? '+' : ''}${num(v * 100, d)} %</span>`;
const qvN = (v, d = 0) => v == null || !isFinite(v) ? '—' : num(v, d);
const qvF = v => v == null || !isFinite(v) ? '—' : num(v, Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 10 ? 1 : 2);
const qvD = d => d ? fmtD(+String(d).replace(/-/g, '').slice(0, 8)) : '—';
const qvM = (v) => v == null || !isFinite(v) ? '—' : num(v / 1e3, Math.abs(v) >= 1e5 ? 0 : 1) + ' Md';
const QV_KIND = { fait: ['Fait', 'up'], estimation: ['Estimation', 'cyan'], 'hypothèse': ['Hypothèse', 'am'] };
const QV_SUBS = [['s', 'Synthèse'], ['c', 'Scénarios'], ['h', 'Hypothèses et historique'], ['r', 'Risques et sensibilités'], ['m', 'Simulation et prévisions'],
  ['q', 'Qualité et facteurs'], ['v', 'Versions et événements'], ['b', 'Validation historique'], ['t', 'Toutes les sociétés']];
const QV_DISC = '<div class="qv-disc">QLAB est un outil d’analyse : les valeurs estimées dépendent d’hypothèses explicites et ne prédisent pas le cours futur. Elles ne garantissent aucune performance et ne constituent pas, à elles seules, une recommandation personnalisée d’investissement. Valeurs en francs CFA par action, sur la base du nombre d’actions actuel.</div>';

PAGES.QLAB = async (m, alive) => {
  const s = sec(ST.sec);
  const okV = !!(s && s.mkt === 'BRVM' && s.cls === 'Equity');
  const tabs = [['s', 'Statistiques'], ['v', 'Valorisation', okV ? '' : 'Réservé aux actions de la BRVM']];
  let tab = tabState('QLAB', 's'); if (tab === 'v' && !okV) tab = ST.tab.QLAB = 's';
  setTabs(tabs, tab, k => { if (k === 'v' && !okV) { toast('La valorisation QLAB est réservée aux actions de la BRVM.'); return; } ST.tab.QLAB = k; render(); });
  if (tab === 's') return QLAB_STATS(m, alive);
  return qvPage(m, alive, s);
};

async function qvPage(m, alive, s) {
  setTitle(`QLAB Valorisation · ${(s.short || s.n || s.id).toUpperCase()}`);
  m.innerHTML = '<div class="empty">Chargement de la valorisation…</div>';
  const [IX, C] = await Promise.all([getJSON('qlab/index.json').catch(() => null), getJSON(`qlab/${s.id}.json`).catch(() => null)]); if (!alive()) return;
  if (!IX) { m.innerHTML = pn('Valorisation QLAB', 'QLAB', '<div class="empty">Le moteur de valorisation n’a pas encore produit de résultats. Il est calculé chaque soir après la clôture.</div>'); return; }
  const sub = QV_SUBS.some(x => x[0] === QV.sub) ? QV.sub : (QV.sub = 's');
  const bar = subTabs(QV_SUBS, sub, 'data-qv');
  const bind = () => m.querySelectorAll('[data-qv]').forEach(b => b.onclick = () => { QV.sub = b.dataset.qv; qvPage(m, alive, s); });
  if (sub === 't') { m.innerHTML = bar + qvAll(IX, s) + QV_DISC; bind(); qvAllBind(m, IX, alive, s); return; }
  if (sub === 'b') { const B = await getJSON('qlab/backtest.json').catch(() => null); if (!alive()) return; m.innerHTML = bar + (C && C.cur ? qvHead(C, IX) : '') + qvBack(B, s) + QV_DISC; bind(); qvBackDraw(m, B, s); return; }
  if (!C || !C.cur) {
    const why = C && C.fail && C.fail.length ? C.fail[C.fail.length - 1].err.join(' ; ') : 'aucune estimation n’a encore été produite pour ce titre';
    m.innerHTML = bar + pn('Valorisation QLAB', 'QLAB', `<div class="empty">Pas d’estimation publiée pour ${esc(s.short || s.n)} : ${esc(why)}.<br>Le moteur ne publie une estimation que si les modèles applicables donnent un résultat cohérent ; sinon il le signale ici plutôt que d’afficher un chiffre peu fiable.</div>`) + QV_DISC;
    bind(); return;
  }
  const A = C.cur.a;
  let body = '';
  if (sub === 's') body = qvSyn(C, A, IX);
  else if (sub === 'c') body = qvScen(C, A);
  else if (sub === 'h') body = qvHyp(C, A);
  else if (sub === 'r') body = qvRisk(C, A);
  else if (sub === 'm') body = qvMC(C, A);
  else if (sub === 'q') body = qvQual(C, A);
  else if (sub === 'v') body = await qvVers(C, A, s, alive);
  if (!alive()) return;
  m.innerHTML = bar + qvHead(C, IX) + body + QV_DISC; bind();
  if (sub === 'c') { m.querySelectorAll('[data-qh]').forEach(b => b.onclick = () => { QV.h = +b.dataset.qh; qvPage(m, alive, s); }); }
  if (sub === 'v') { m.querySelectorAll('[data-qcmp]').forEach(el => el.onchange = () => { QV[el.dataset.qcmp] = el.value; qvPage(m, alive, s); }); }
}

/* en-tête commun : valeur, fourchette, cours, confiance, version, avertissements */
function qvHead(C, IX) {
  const A = C.cur.a, K = C.mkt || {}, st = C.status || { warn: [] }, pr = K.pr || {};
  const warn = [...(st.warn || []), ...(pr.warn || [])];
  const nx = IX.next_cycle ? qvD(IX.next_cycle) : '—';
  return `<div class="qv-head"><span><span class="l">Valeur estimée</span><span class="v">${qvF(K.v)}</span> FCFA</span>
    <span><span class="l">Fourchette 10-90 %</span>${qvF(K.p10)} – ${qvF(K.p90)}</span>
    <span><span class="l">Dernier cours</span>${qvF(K.price)} <span class="dm">(${qvD(K.pdate)})</span></span>
    <span><span class="l">Écart valeur / cours</span>${qvS(K.up, 0)}</span>
    <span><span class="l">Confiance</span>${A.syn.conf}/100 <span class="dm">(${esc(A.syn.conf_lbl)})</span></span>
    <span><span class="l">${esc(C.cur.type_n)}</span>${qvD(A.date)}</span><span><span class="l">Prochaine réévaluation complète</span>${nx}</span></div>
    ${warn.map(w => `<div class="qv-warn">${esc(w)}</div>`).join('')}
    ${A.syn.conf < 35 ? '<div class="qv-info">Confiance très faible : les modèles divergent fortement ou les données sont fragiles. La valeur indique un ordre de grandeur, pas une estimation précise ; voir le détail du score dans la synthèse.</div>' : ''}
    ${(K.k && Math.abs(K.k - 1) > 1e-6) ? `<div class="qv-info">Valeurs par action ajustées du fractionnement intervenu depuis l’évaluation (×${num(1 / K.k, 2)}).</div>` : ''}`;
}

function qvRange(A, K) {
  const ms = A.models.filter(x => x.ok && x.p50 > 0);
  const k = K.k || 1, vals = [A.syn.p10 * k, A.syn.p90 * k, K.price, ...ms.map(x => x.p50 * k)].filter(x => x > 0 && isFinite(x));
  let lo = Math.min(...vals), hi = Math.max(...vals); const pad = (hi - lo) * .06 || hi * .1; lo = Math.max(0, lo - pad); hi += pad;
  const X = v => ((v - lo) / (hi - lo) * 100).toFixed(2) + '%';
  const COL = { dcf: '#3fd3c0', ddm: '#ffa028', ri: '#4da7fd', mult_own: '#b69cff', mult_peer: '#ff7ab2' };
  return `<div class="qv-rng"><div class="ax"></div><div class="b1" style="left:${X(A.syn.p10 * k)};width:calc(${X(A.syn.p90 * k)} - ${X(A.syn.p10 * k)})"></div>
    <div class="b2" style="left:${X(A.syn.p25 * k)};width:calc(${X(A.syn.p75 * k)} - ${X(A.syn.p25 * k)})"></div><div class="c" style="left:${X(A.syn.v * k)}"></div>
    ${K.price ? `<div class="p" style="left:${X(K.price)}" title="Dernier cours"></div>` : ''}
    ${ms.map(x => `<div class="m" style="left:${X(x.p50 * k)};background:${COL[x.id]}" title="${esc(x.n)} : ${qvF(x.p50 * k)}"></div>`).join('')}
    <div class="t" style="left:${X(A.syn.p10 * k)}">${qvF(A.syn.p10 * k)}</div><div class="t" style="left:${X(A.syn.p90 * k)}">${qvF(A.syn.p90 * k)}</div></div>
    <div class="chips" style="padding:0 8px 4px;font-size:11px"><span><b style="color:var(--yel)">▼</b> cours</span><span><b class="wh">|</b> valeur centrale</span>
    <span class="dm">bandes : 25-75 % et 10-90 %</span>${ms.map(x => `<span><b style="color:${COL[x.id]}">●</b> ${esc(x.n.replace('Multiples prospectifs : ', 'Multiples : '))}</span>`).join('')}</div>`;
}

/* 11) Synthèse */
function qvSyn(C, A, IX) {
  const K = C.mkt || {}, k = K.k || 1, P = A.profile;
  const W = { a: 'pertinence', q: 'données', r: 'robustesse', o: 'hors échantillon', p: 'performance historique', coh: 'cohérence', red: 'redondance' };
  const rows = A.models.map(x => x.ok ? `<tr><td class="l wh">${esc(x.n)}</td><td><b>${qvF(x.v * k)}</b></td><td>${qvF(x.p10 * k)} – ${qvF(x.p90 * k)}</td><td><b class="am">${qvP(x.w, 0)}</b></td>
      <td class="l dm" style="font-size:11.5px;white-space:normal;min-width:200px">${Object.keys(W).map(c => `${W[c]} ${x.wd[c] == null ? '—' : num(x.wd[c], 2)}`).join(' · ')}</td></tr>
      <tr><td class="l dm" colspan="5" style="white-space:normal;font-size:11.5px;padding:0 6px 4px 14px">${esc([x.why, ...(x.txt || []), ...(x.notes || [])].join(' · '))}</td></tr>`
    : `<tr><td class="l qv-no">${esc(x.n)}</td><td colspan="4" class="l qv-no" style="white-space:normal">non appliqué : ${esc(x.why)}</td></tr>`).join('');
  const tbl = `<div class="tw"><table class="t qv-mt"><thead><tr><th class="l">Modèle</th><th>Valeur centrale</th><th>Fourchette 10-90 %</th><th>Poids</th><th class="l">Composantes du poids (produit, puis normalisation)</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  const conf = `<div class="kv2">${A.syn.conf_parts.map(p => `<span>${esc(p[0])}</span><b class="dn">${p[1]}</b>`).join('')}<span>Score de confiance</span><b>${A.syn.conf}/100 · ${esc(A.syn.conf_lbl)}</b></div>`;
  const liq = A.liq || {}, alt = A.alt;
  const right = `${pn('Profil de la société', 'QLAB', `<div class="lectb"><p><b>${esc(A.name)}</b> — ${esc(P.act)}.</p><p>Modèle économique retenu : <b>${esc(P.arch_n)}</b> ; ${esc(P.fw_txt)}.</p>
      ${P.notes.length ? `<p>${P.notes.map(esc).join(' · ')}</p>` : ''}<p><b>Moteurs</b> : ${P.drivers.map(esc).join(' ; ')}.</p></div>`)}
    ${A.rev.txt.length ? pn('Ce que le cours actuel suppose (DCF inversé)', 'QLAB', `<div class="lectb">${A.rev.txt.map(t => `<p>${esc(t)}</p>`).join('')}</div>`) : ''}
    ${alt ? pn('Au rendement exigé actuel du marché', 'QLAB', `<div class="kv2"><span>Rendement exigé implicite du marché aujourd’hui</span><b>${qvP(alt.ke_mkt)}</b><span>Coût des fonds propres correspondant pour ce titre</span><b>${qvP(alt.ke)}</b><span>Valeur centrale correspondante</span><b>${qvF(alt.v * k)}</b></div>`, { lect: 'Lecture alternative, hors synthèse : si l’on retenait le rendement que le marché exige aujourd’hui plutôt que sa médiane historique.' }) : ''}
    ${pn('Liquidité (distincte de l’incertitude sur la valeur)', 'QLAB', `<div class="kv2"><span>Séances sans échange (1 an)</span><b>${qvP(liq.zero, 0)}</b><span>Montant échangé moyen par séance (1 an)</span><b>${liq.adv1y ? num(liq.adv1y / 1e6, 1) + ' M FCFA' : '—'}</b>
      <span>Séances pour vendre 10 / 50 / 100 M FCFA</span><b>${['d10', 'd50', 'd100'].map(x => liq.d && liq.d[x] != null ? num(liq.d[x], 1) : '—').join(' / ')}</b><span>Prime d’illiquidité estimée</span><b>${qvP(liq.lp, 2)}</b>
      <span>Valeur centrale avec cette prime</span><b>${liq.v_adj ? qvF(liq.v_adj * k) : '—'}</b></div>`, { lect: 'Un cours stable n’est pas forcément un risque faible : le titre peut simplement être peu échangé. La prime d’illiquidité n’entre pas dans la valeur centrale ; elle indique ce qu’exigerait un investisseur qui veut être rémunéré pour la difficulté à vendre.' })}`;
  return `<div class="grid c2"><div>${pn('Synthèse des modèles', 'QLAB', qvRange(A, K) + tbl, { lect: `<b>Méthode</b> : chaque modèle applicable produit une distribution de valeurs ; le poids de chaque modèle est le produit de sa pertinence pour ce type d’entreprise, de la qualité des données, de sa robustesse (étroitesse de sa distribution), de la qualité hors échantillon de la prévision dont il dépend, de sa performance mesurée par la validation historique, de sa cohérence avec les résultats publiés et d’une pénalité de redondance. La valeur centrale est la <strong>médiane du mélange pondéré</strong> des distributions (jamais une moyenne simple) ; un désaccord entre modèles élargit donc la fourchette. ${A.syn.div_txt.length ? '<br><b>Écarts entre modèles</b> : ' + A.syn.div_txt.map(esc).join(' ; ') : ''}${(A.mexp || []).length ? '<br><b>Multiples</b> : ' + A.mexp.map(esc).join(' ') : ''}` })}
    ${pn('Niveau de confiance', 'QLAB', conf, { lect: 'Le score part de 100 et retire des points pour chaque source d’incertitude mesurée : données non vérifiées, historique court, désaccord entre modèles, largeur de la fourchette, ruptures comptables, pertes, activité cyclique, résultats variables, absence de validation hors échantillon, écart important avec le cours.' })}</div><div>${right}</div></div>`;
}

/* 12) Scénarios */
const QV_CONV = "Valeurs par action en francs CFA, base du nombre d’actions actuel ; date de référence : date d’évaluation. Dividendes : somme des dividendes ordinaires projetés sur la période, non réinvestis. Les scénarios portent sur la valeur estimée, les résultats et les dividendes : aucune projection du cours n’est faite, le marché pouvant rester durablement éloigné de la valeur estimée.";
function qvScen(C, A) {
  const SC = A.scen; const k = (C.mkt && C.mkt.k) || 1;
  if (!SC) return pn('Scénarios', 'QLAB', '<div class="empty">Scénarios indisponibles : aucun modèle intrinsèque (DCF, DDM ou résultat résiduel) n’est applicable.</div>');
  const h = [1, 3, 5, 10].includes(QV.h) ? QV.h : 1;
  const cols = [['bear', 'Baissier'], ['base', 'Central'], ['bull', 'Haussier']].filter(c => SC.rows[c[0]]);
  const R = c => SC.rows[c].h.find(x => x.h === h) || {};
  const fw = A.profile.fw;
  const line = (lbl, f) => `<tr><td class="l am">${lbl}</td>${cols.map(c => `<td>${f(R(c[0]), SC.rows[c[0]], c[0])}</td>`).join('')}</tr>`;
  const sel = `<div class="qv-sel">${[1, 3, 5, 10].map(x => `<button class="tb${x === h ? ' on' : ''}" data-qh="${x}">${x} an${x > 1 ? 's' : ''}</button>`).join('')}<span class="dm">horizon à partir du ${qvD(A.date)}</span></div>`;
  const tbl = `<div class="tw"><table class="t"><thead><tr><th class="l">À ${h} an${h > 1 ? 's' : ''}</th>${cols.map(c => `<th>${c[1]}</th>`).join('')}</tr></thead><tbody>
    <tr class="sec"><td class="l" colspan="4">Valeur</td></tr>
    ${line('Valeur estimée par action aujourd’hui', (r, S) => qvF(S.v0 * k))}
    ${line(`Valeur estimée par action dans ${h} an${h > 1 ? 's' : ''}`, (r) => `<b>${qvF(r.v * k)}</b>`)}
    ${line('Fourchette de la simulation (10-90 %)', (r, S, c) => c === 'base' && r.p10 ? `${qvF(r.p10 * k)} – ${qvF(r.p90 * k)}` : '')}
    <tr class="sec"><td class="l" colspan="4">Activité et résultats (année ${h})</td></tr>
    ${line('Croissance annuelle du chiffre d’affaires', r => qvP(r.g_rev))}
    ${fw === 'roe' ? line('Rentabilité des fonds propres', r => qvP(r.roe)) : line('Marge nette', r => qvP(r.nm))}
    ${line('Marge d’exploitation', r => qvP(r.om))}
    ${line('Bénéfice par action', r => qvF(r.eps * k))}
    ${line('Fonds propres par action', r => qvF(r.bvps * k))}
    ${line('Flux disponibles par action (DCF)', r => qvF(r.fcff * k))}
    <tr class="sec"><td class="l" colspan="4">Dividendes (séparément)</td></tr>
    ${line(`Dividende par action de l’année ${h}`, r => qvF(r.dps * k))}
    ${line('Dividendes cumulés sur la période', r => qvF(r.divs * k))}
    ${line('Dividendes annuels moyens rapportés au dernier cours', r => qvP(r.dy))}
  </tbody></table></div>`;
  const HY = { ke: 'Coût des fonds propres', glt: 'Croissance de long terme', pay0: 'Taux de distribution de départ', phi: 'Persistance de la rentabilité', roe0: 'Rentabilité des fonds propres de départ', roe_lt: 'Rentabilité à 10 ans',
    g_mid: 'Croissance du chiffre d’affaires (années 2 à 10)', m0: 'Marge nette de départ', m_lt: 'Marge nette normative', om0: 'Marge d’exploitation de départ', roic0: 'Rentabilité des capitaux investis' };
  const keys = Object.keys(HY).filter(x => cols.some(c => SC.rows[c[0]].hyp[x] != null));
  const hyp = `<div class="tw"><table class="t"><thead><tr><th class="l">Hypothèses</th>${cols.map(c => `<th>${c[1]}</th>`).join('')}</tr></thead><tbody>${keys.map(x => `<tr><td class="l am">${HY[x]}</td>${cols.map(c => `<td>${x === 'phi' ? num(SC.rows[c[0]].hyp[x], 2) : qvP(SC.rows[c[0]].hyp[x])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  const thr = (A.rev.thr || []).map(t => `${esc(t.n)} : ${t.k === 'ke' || t.k === 'g' || t.k === 'prof' ? qvP(t.v) : num(t.v, 2)}`);
  const risks = `<div class="lectb"><p><b>Baissier</b> — hypothèses d’exploitation (croissance, marges ou rentabilité, distribution) des simulations dont la valeur se situe entre les 15e et 25e centiles, le rendement exigé restant central. Événements qui le rendraient plus probable : ${A.profile.risks.map(esc).join(' ; ')}.</p>
    <p><b>Central</b> — hypothèses centrales. Seuils à partir desquels la conclusion s’inverse (valeur = cours) : ${thr.length ? thr.join(' ; ') : 'non calculables'}.</p>
    <p><b>Haussier</b> — hypothèses d’exploitation des simulations entre les 75e et 85e centiles ; il suppose que les moteurs de l’activité (${A.profile.drivers.slice(0, 3).map(esc).join(', ')}) restent favorables.</p>
    <p class="dm">L’incertitude sur le rendement exigé par le marché s’ajoute à celle des scénarios : elle apparaît dans la fourchette de la simulation du scénario central, qui s’élargit avec l’horizon.</p></div>`;
  return `<div class="grid c2"><div>${pn('Scénarios à 1, 3, 5 et 10 ans', 'QLAB', sel + tbl + qvScenSVG(SC, k), { lect: esc(QV_CONV) + ' Plus l’horizon est long, plus la fourchette s’élargit : les valeurs à 5 et 10 ans sont arrondies à deux chiffres significatifs.' })}</div>
    <div>${pn('Hypothèses des scénarios', 'QLAB', hyp)}${pn('Risques et événements susceptibles d’invalider les scénarios', 'QLAB', risks)}</div></div>`;
}
function qvScenSVG(SC, k) {
  const H = [0, 1, 3, 5, 10], C = { bear: '#ff433d', base: '#ffffff', bull: '#32c74c' };
  const ser = {}; for (const c of Object.keys(SC.rows)) ser[c] = H.map(h => h === 0 ? SC.rows[c].v0 * k : (SC.rows[c].h.find(x => x.h === h) || {}).v * k);
  const band = SC.rows.base ? SC.rows.base.h.map(x => [x.h, x.p10 * k, x.p90 * k]) : [];
  const all = [...Object.values(ser).flat(), ...band.flatMap(b => [b[1], b[2]])].filter(x => x > 0 && isFinite(x)); if (!all.length) return '';
  const lo = Math.min(...all) * .9, hi = Math.max(...all) * 1.05, W = 600, Hh = 200, pl = 52, pb = 18;
  const X = h => pl + h / 10 * (W - pl - 10), Y = v => 6 + (hi - v) / (hi - lo) * (Hh - pb - 6);
  const ticks = niceTicks(lo, hi, 4);
  const poly = band.length ? `<polygon points="${[...band.map(b => `${X(b[0])},${Y(b[2])}`), ...band.slice().reverse().map(b => `${X(b[0])},${Y(b[1])}`)].join(' ')}" fill="rgba(77,167,253,.15)"/>` : '';
  return `<svg class="qv-svg" viewBox="0 0 ${W} ${Hh}" preserveAspectRatio="none">${ticks.map(t => `<line x1="${pl}" x2="${W - 10}" y1="${Y(t)}" y2="${Y(t)}" stroke="#262626"/><text x="${pl - 4}" y="${Y(t) + 3}" fill="#a5a5a5" font-size="10" text-anchor="end">${num(t, 0)}</text>`).join('')}
    ${H.map(h => `<text x="${X(h)}" y="${Hh - 4}" fill="#a5a5a5" font-size="10" text-anchor="middle">${h === 0 ? 'auj.' : h + ' an' + (h > 1 ? 's' : '')}</text>`).join('')}${poly}
    ${Object.entries(ser).map(([c, v]) => `<polyline fill="none" stroke="${C[c]}" stroke-width="1.6" points="${H.map((h, i) => `${X(h)},${Y(v[i])}`).join(' ')}"/>`).join('')}</svg>
    <div class="chips" style="font-size:11px;padding:0 4px"><span style="color:#ff433d">— baissier</span><span>— central</span><span style="color:#32c74c">— haussier</span><span class="dm">bande : 10-90 % de la simulation (central)</span></div>`;
}

/* 13) Hypothèses et historique */
function qvHyp(C, A) {
  const fmtH = h => h.fmt === 'num' ? num(h.v, 2) : h.fmt === 'm' ? qvN(h.v, 0) + ' M FCFA' : qvP(h.v, 2);
  const hy = `<div class="tw"><table class="t"><thead><tr><th class="l">Hypothèse</th><th>Valeur</th><th class="l">Statut</th><th class="l">Justification</th></tr></thead><tbody>${A.hyp.map(h => { const kd = QV_KIND[h.kind] || [h.kind, 'dm'];
    return `<tr><td class="l am">${esc(h.n)}</td><td>${fmtH(h)}</td><td class="l"><span class="qv-kind ${kd[1]}">${kd[0]}</span></td><td class="l" style="white-space:normal;min-width:260px">${esc(h.why)}</td></tr>`; }).join('')}</tbody></table></div>`;
  const Hh = A.hist, ys = Hh.y.slice(-12), off = Hh.y.length - ys.length;
  const R = [['Chiffre d’affaires (PNB pour les banques)', 'rev', 'm'], ['Résultat d’exploitation', 'ebit', 'm'], ['EBITDA', 'ebitda', 'm'], ['Résultat net', 'ni', 'm'], ['Fonds propres', 'eq', 'm'],
    ['Flux de trésorerie d’exploitation', 'ocf', 'm'], ['Investissements', 'capex', 'm'], ['Dette nette', 'nd', 'm'], ['Dépôts de la clientèle', 'deposits', 'm'], ['Crédits à la clientèle', 'loans', 'm'], ['Coût du risque', 'cor', 'm'],
    ['Rentabilité des fonds propres', 'roe', 'p'], ['Marge nette', 'nm', 'p'], ['Marge d’exploitation', 'om', 'p'], ['Dividende ordinaire par action', 'dps', 'd'], ['Taux de distribution', 'pay', 'p']]
    .filter(r => Hh[r[1]] && Hh[r[1]].slice(off).some(v => v != null));
  const hist = `<div class="tw"><table class="t"><thead><tr><th class="l">Millions FCFA</th>${ys.map((y, i) => `<th title="${Hh.ver[off + i] ? 'comptes vérifiés dans les états financiers publiés' : 'non vérifié'}">${y}${Hh.ver[off + i] ? '' : '*'}</th>`).join('')}</tr></thead><tbody>
    ${R.map(r => `<tr><td class="l am">${r[0]}</td>${Hh[r[1]].slice(off).map(v => `<td>${v == null ? '<span class="fl">—</span>' : r[2] === 'p' ? qvP(v) : r[2] === 'd' ? num(v, 2) : qvN(v, 0)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  const Ra = A.ratios;
  const rat = `<div class="kv2"><span>PER (dernier exercice)</span><b>${qvF(Ra.pe)}</b><span>Cours / fonds propres</span><b>${qvF(Ra.pb)}</b><span>Rendement du dernier dividende</span><b>${qvP(Ra.dy)}</b>
    <span>Rentabilité des fonds propres (médiane 3 ans)</span><b>${qvP(Ra.roe3)}</b><span>Marge nette (médiane 3 ans)</span><b>${qvP(Ra.nm3)}</b><span>Croissance annuelle du chiffre d’affaires 5 / 10 ans</span><b>${qvP(Ra.cagr_rev5)} / ${qvP(Ra.cagr_rev10)}</b>
    <span>Croissance annuelle du résultat 5 ans</span><b>${qvP(Ra.cagr_ni5)}</b><span>Flux d’exploitation / résultat net (médiane)</span><b>${Ra.conv == null ? '—' : num(Ra.conv, 2)}</b><span>Taux de distribution (médiane 5 ans)</span><b>${qvP(Ra.pay5)}</b>
    <span>Exercices avec dividende sur 10 ans / baisses de plus de 10 %</span><b>${Ra.div10} / ${Ra.cuts}</b><span>Variabilité du résultat (5 ans)</span><b>${Ra.cv_ni == null ? '—' : num(Ra.cv_ni, 2)}</b>
    <span>Volatilité du cours (3 ans) / plus forte baisse (5 ans)</span><b>${qvP(Ra.vol3)} / ${qvP(Ra.mdd5)}</b><span>Bénéfice / fonds propres par action</span><b>${qvF(Ra.eps0)} / ${qvF(Ra.bvps0)}</b></div>`;
  return `${pn('Hypothèses utilisées', 'QLAB', hy, { lect: '<b>Fait</b> : donnée publiée. <b>Estimation</b> : grandeur mesurée sur les données. <b>Hypothèse</b> : choix de modélisation documenté. Aucune donnée manquante n’est complétée par un chiffre inventé : un modèle qui en a besoin est désactivé.' })}
    <div class="grid c2">${pn('Données historiques (exercice ' + A.fy + ' et antérieurs)', 'QLAB', hist, { lect: '* exercice non vérifié dans les états financiers publiés (données de secours). Les banques publient un produit net bancaire à la place du chiffre d’affaires.' })}${pn('Principaux ratios', 'QLAB', rat)}</div>`;
}

/* 14) Risques et sensibilités */
function qvRisk(C, A) {
  const k = (C.mkt && C.mkt.k) || 1, price = C.mkt && C.mkt.price, SE = A.sens;
  if (!SE) return pn('Sensibilités', 'QLAB', '<div class="empty">Sensibilités indisponibles : aucun modèle intrinsèque applicable.</div>');
  const cell = v => { if (v == null) return '<td class="fl">—</td>'; const r = price ? v * k / price - 1 : 0; return `<td style="background:${heatBg(r, .6)}">${qvF(v * k)}</td>`; };
  const g = SE.grid, xp = g.xlbl.includes('relatif') ? (x => (x > 0 ? '+' : '') + num(x * 100, 0) + ' %') : (x => (x > 0 ? '+' : '') + num(x * 100, 0) + ' pt');
  const grid = `<div class="tw"><table class="t hm"><thead><tr><th class="l">Coût des fonds propres \\ ${esc(g.xlbl)}</th>${g.x.map(x => `<th>${xp(x)}</th>`).join('')}</tr></thead><tbody>${g.ke.map((a, i) => `<tr><td class="l am">${a > 0 ? '+' : ''}${num(a * 100, 0)} pt</td>${g.v[i].map(cell).join('')}</tr>`).join('')}</tbody></table></div>`;
  const g2 = SE.grid2, grid2 = `<div class="tw"><table class="t hm"><thead><tr><th class="l">Croissance de long terme \\ rentabilité</th>${g2.x.map(x => `<th>${x > 0 ? '+' : ''}${num(x * 100, 0)} %</th>`).join('')}</tr></thead><tbody>${g2.glt.map((a, i) => `<tr><td class="l am">${a > 0 ? '+' : ''}${num(a * 100, 1)} pt</td>${g2.v[i].map(cell).join('')}</tr>`).join('')}</tbody></table></div>`;
  const T = SE.tornado, all = T.flatMap(t => [t.lo, t.hi]).concat(price ? [price / k] : []), lo = Math.min(...all), hi = Math.max(...all), X = v => (v - lo) / (hi - lo || 1) * 100;
  const torn = `<div class="qv-tor">${T.map(t => `<span>${esc(t.n)}</span><div class="tr"><i style="left:${X(t.lo)}%;width:${Math.max(.5, X(t.hi) - X(t.lo))}%"></i>${price ? `<b style="left:${X(price / k)}%"></b>` : ''}</div>`).join('')}</div>
    <div class="dm" style="font-size:11px;margin-top:3px">barres : valeur du modèle principal quand l’hypothèse passe de son 10e à son 90e centile, les autres restant centrales ; trait jaune : cours. Bornes : ${qvF(lo * k)} – ${qvF(hi * k)}</div>`;
  const glob = A.glob.length ? `<div class="qv-tor">${A.glob.map(r => `<span>${esc(r.n)}</span><div class="tr"><i style="left:${r.rho < 0 ? 50 + r.rho * 50 : 50}%;width:${Math.abs(r.rho) * 50}%;background:${r.rho < 0 ? 'var(--dn)' : 'var(--up)'}"></i><b style="left:50%;background:#666"></b></div>`).join('')}</div>` : '';
  const thr = (A.rev.thr || []).length ? `<div class="kv2">${A.rev.thr.map(t => `<span>${esc(t.n)}</span><b>${qvP(t.v)}</b>`).join('')}</div>` : '<div class="dm">Aucun seuil calculable dans les bornes testées.</div>';
  const reg = `<div class="tw"><table class="t"><thead><tr><th class="l">Régime économique</th><th class="l">Hypothèse pour ce type d’entreprise</th><th>Effet sur la valeur</th><th>Valeur</th></tr></thead><tbody>${A.reg.map(r => `<tr><td class="l am" title="${esc(r.desc)}">${esc(r.n)}</td>
    <td class="l dm" style="white-space:normal">${esc(r.desc)} : croissance ${r.hyp.dg > 0 ? '+' : ''}${num(r.hyp.dg, 1)} pt, rentabilité ${r.hyp.dprof > 0 ? '+' : ''}${num(r.hyp.dprof * 100, 0)} %, rendement exigé ${r.hyp.dke > 0 ? '+' : ''}${num(r.hyp.dke, 1)} pt, ${r.hyp.dur ? r.hyp.dur + ' ans' : 'durable'}${r.eff ? ' — ' + esc(r.eff) : ''}</td><td>${qvS(r.dv, 0)}</td><td>${qvF(r.v * k)}</td></tr>`).join('')}</tbody></table></div>`;
  return `<div class="grid c2"><div>${pn('Sensibilité croisée : coût des fonds propres × ' + esc(g.xlbl.split(' (')[0]), 'QLAB', grid, { lect: 'Valeur du modèle principal pour des variations simultanées de deux hypothèses. Vert : au-dessus du cours, rouge : en dessous.' })}
    ${pn('Sensibilité croisée : croissance de long terme × rentabilité', 'QLAB', grid2)}
    ${pn('Régimes économiques', 'QLAB', reg, { lect: 'Les régimes n’ont pas le même effet sur toutes les entreprises : les effets supposés dépendent du modèle économique (hypothèses de travail affichées, pas des probabilités).' })}</div>
    <div>${pn('Hypothèses les plus influentes (une à la fois)', 'QLAB', torn)}${pn('Influence globale (simulation, interactions comprises)', 'QLAB', glob, { lect: 'Corrélation de rang entre chaque hypothèse tirée et la valeur simulée : elle tient compte des variations simultanées de toutes les hypothèses.' })}
    ${pn('Seuils : où la conclusion change', 'QLAB', thr)}${pn('Risques propres au modèle économique', 'QLAB', `<div class="lectb"><p>${A.profile.risks.map(esc).join('<br>')}</p></div>`)}</div></div>`;
}

/* 15) Simulation et prévisions */
function qvMC(C, A) {
  const k = (C.mkt && C.mkt.k) || 1, price = C.mkt && C.mkt.price, M = A.mc;
  let hist = '<div class="empty">Simulation indisponible.</div>';
  if (M && M.bins && M.bins.c) { const b = M.bins, mx = Math.max(...b.c), n = b.c.length, X = v => (v / k - b.lo) / (b.step * n) * 100;
    hist = `<div class="qv-hist">${b.c.map(c => `<i style="height:${(c / mx * 100).toFixed(1)}%" title="${qvF((b.lo + 0) * k)}"></i>`).join('')}${price && X(price) >= 0 && X(price) <= 100 ? `<div class="pm" style="left:${X(price)}%" title="cours"></div>` : ''}<div class="cm" style="left:${X(A.syn.v * k)}%" title="valeur centrale"></div></div>
    <div style="display:flex;justify-content:space-between;font-size:10.5px;color:var(--dim);padding:0 6px"><span>${qvF(b.lo * k)}</span><span>${qvF((b.lo + b.step * n) * k)}</span></div>`; }
  const P = M ? `<div class="kv2"><span>Trajectoires simulées</span><b>${qvN(M.n)}</b><span>Modèle simulé (principal)</span><b>${esc((A.models.find(x => x.id === M.main) || {}).n || M.main)}</b>
    ${['0.1', '0.25', '0.5', '0.75', '0.9'].map(q => `<span>Centile ${num(+q * 100, 0)} de la synthèse</span><b>${qvF(M.p[q] * k)}</b>`).join('')}
    <span>Part des simulations au-dessus du cours</span><b>${qvP(M.share_above, 0)}</b></div>` : '';
  const prm = M ? `<div class="tw"><table class="t"><thead><tr><th class="l">Hypothèse tirée</th><th class="l">Loi</th><th class="l">Justification</th></tr></thead><tbody>${M.params.map(p => `<tr><td class="l am">${esc(p.n)}</td><td class="l">${esc(p.dist)}</td><td class="l dm" style="white-space:normal">${esc(p.why)}</td></tr>`).join('')}
    <tr><td class="l am">Dépendance</td><td class="l">corrélation ${num(M.corr.rho, 2)}</td><td class="l dm" style="white-space:normal">${esc(M.corr.why)} (${M.corr.n} observations)</td></tr></tbody></table></div>` : '';
  const fc = (F, lbl) => !F ? '' : pn(lbl, 'QLAB', `<div class="tw"><table class="t"><thead><tr><th class="l">Méthode</th><th>Exercices testés</th><th>Erreur / prévision naïve</th><th></th></tr></thead><tbody>${F.models.map(x => `<tr><td class="l">${esc(x.n)}</td><td>${x.k}</td><td>${x.ratio == null ? '—' : num(x.ratio * 100, 0) + ' %'}</td><td class="l">${x.id === F.best ? '<b class="qv-ok">retenue</b>' : ''}</td></tr>`).join('')}</tbody></table></div>
    <div class="kv2" style="margin-top:4px"><span>Prévision de l’exercice suivant (M FCFA)</span><b>${qvN(F.f, 0)}</b><span>Intervalle à 80 %</span><b>${qvN(F.lo, 0)} – ${qvN(F.hi, 0)}</b>
    <span>Couverture des intervalles passés</span><b>${F.cover ? num(F.cover[0] * 100, 0) + ' % (' + F.cover[1] + ' cas)' : 'non mesurable'}</b></div>`, { lect: esc(F.why) + '. Les méthodes sont comparées hors échantillon (origine glissante : chaque prévision n’utilise que les exercices antérieurs).' });
  return `<div class="grid c2"><div>${pn('Distribution des valeurs simulées (modèle principal)', 'QLAB', hist + P, { lect: 'La part des simulations au-dessus du cours est conditionnelle aux hypothèses retenues ; ce n’est pas une probabilité calibrée de hausse du cours.' })}${pn('Hypothèses tirées dans la simulation', 'QLAB', prm)}</div>
    <div>${fc(A.fc.ni, 'Prévisions statistiques du résultat net')}${fc(A.fc.rev, 'Prévisions statistiques du chiffre d’affaires')}
    ${A.fc.dps_ratio != null ? pn('Prévision du dividende utilisée par le DDM', 'QLAB', `<div class="kv2"><span>Erreur / dividende reconduit</span><b>${num(A.fc.dps_ratio * 100, 0)} % (${A.fc.dps_n} exercices)</b></div>`) : ''}</div></div>`;
}

/* 16) Qualité et facteurs */
function qvQual(C, A) {
  const F = C.fac || { scores: {}, raw: {}, def: [] }, raw = F.raw || {};
  const fmtR = (id, v) => v == null ? '—' : id === 'F6' ? num(v, 0) : id === 'F10' ? esc(raw.F10_txt || '') : ['F2', 'F4'].includes(id) ? num(v, 2) : id === 'F5' && !A.profile.arch_n.match(/Banque|bancaire|financier/) ? num(-v, 2) + ' ×' : id === 'F9' ? num(v * 100, 0) + ' %' : qvP(v);
  const tbl = `<div class="tw"><table class="t"><thead><tr><th class="l">Facteur</th><th class="l">Définition</th><th>Valeur</th><th class="l">Rang parmi les sociétés de la BRVM (0-100)</th></tr></thead><tbody>${F.def.map(d => { const s = F.scores[d.id];
    return `<tr><td class="l am">${d.id} ${esc(d.n)}</td><td class="l dm" style="white-space:normal">${esc(d.d)}</td><td>${d.id === 'F10' ? esc(raw.F10_txt || 'non notée') : fmtR(d.id, raw[d.id])}</td><td class="l">${s == null ? '<span class="fl">non mesurable</span>' : `<span class="qv-bar" style="width:${s}px;background:${s >= 60 ? 'var(--up)' : s <= 30 ? 'var(--dn)' : 'var(--amber)'}"></span> ${s}`}</td></tr>`; }).join('')}
    <tr><td class="l am">Gouvernance</td><td class="l dm" colspan="3" style="white-space:normal">${esc(F.gov || '')}</td></tr></tbody></table></div>`;
  const D = A.dq;
  const dq = `<div class="kv2"><span>Dernier exercice publié</span><b>${D.fy}</b><span>Exercices de résultat disponibles</span><b>${D.years}</b><span>Part des 5 derniers exercices vérifiés</span><b>${qvP(D.vshare, 0)}</b>
    <span>Dernier cours</span><b>${qvD(A.pdate)}</b></div><div class="lectb" style="margin-top:4px"><p><b>Exercices vérifiés</b> : ${D.verified.join(', ') || 'aucun'}.</p>
    ${D.missing.length ? `<p><b>Données manquantes</b> : ${D.missing.map(esc).join(' ; ')} (les modèles qui en dépendent sont désactivés ou moins pondérés).</p>` : ''}${D.warn.map(w => `<p class="am">${esc(w)}</p>`).join('')}</div>`;
  return `<div class="grid c2">${pn('Facteurs de qualité et de risque', 'QLAB', tbl, { lect: 'Chaque facteur est défini et mesuré sur les données publiées ; le rang compare la société aux autres sociétés de la BRVM (100 = la plus favorable). Les facteurs servent à l’interprétation et au niveau de confiance ; ils ne modifient pas la valeur.' })}${pn('Qualité des données', 'QLAB', dq)}</div>`;
}

/* 17) Versions et événements */
async function qvVers(C, A, s, alive) {
  const V = (C.vers || []).slice().reverse();
  const vt = `<div class="tw"><table class="t"><thead><tr><th class="l">Version</th><th class="l">Type</th><th>Date</th><th>Exercice</th><th>Cours</th><th>Valeur</th><th>Fourchette</th><th>Confiance</th><th class="l">Motif</th></tr></thead><tbody>${V.map(v => `<tr${v.id === C.cur.id ? ' class="cur"' : ''}><td class="l">${esc(v.id)}</td><td class="l">${esc(v.type_n)}</td><td>${qvD(v.date)}</td><td>${v.fy}</td><td>${qvF(v.price)}</td><td><b>${qvF(v.v)}</b></td><td>${qvF(v.p10)} – ${qvF(v.p90)}</td><td>${v.conf}</td><td class="l dm" style="white-space:normal">${esc(v.reason)}</td></tr>`).join('')}</tbody></table></div>`;
  let cmp = '<div class="dm" style="padding:6px">Une seule version pour l’instant : la comparaison sera disponible après la prochaine réévaluation.</div>';
  if (V.length >= 2) {
    const H = await getJSON(`qlab/hist/${s.id}.json`).catch(() => null); if (!alive()) return '';
    const L = (H && H.v) || []; const ids = L.map(r => r.id);
    const b = ids.includes(QV.cmpB) ? QV.cmpB : ids[ids.length - 1], a = ids.includes(QV.cmpA) && QV.cmpA !== b ? QV.cmpA : ids[Math.max(0, ids.indexOf(b) - 1)];
    const ra = L.find(r => r.id === a), rb = L.find(r => r.id === b);
    if (ra && rb) {
      const ka = ra.a.shares && rb.a.shares ? ra.a.shares / rb.a.shares : 1;
      const row = (l, fa, fb) => `<tr><td class="l am">${l}</td><td>${fa}</td><td>${fb}</td></tr>`;
      const hv = (r, key) => { const h = r.a.hyp.find(x => x.k === key); return h ? (h.fmt === 'num' ? num(h.v, 2) : h.fmt === 'm' ? qvN(h.v) : qvP(h.v)) : '—'; };
      const mv = (r, id, kk) => { const x = r.a.models.find(z => z.id === id && z.ok); return x ? qvF(x.v * kk) + ' <span class="dm">(' + qvP(x.w, 0) + ')</span>' : '—'; };
      const chg = rb.chg;
      cmp = `<div class="qv-sel">Comparer <select data-qcmp="cmpA">${ids.map(i => `<option${i === a ? ' selected' : ''}>${esc(i)}</option>`).join('')}</select> et <select data-qcmp="cmpB">${ids.map(i => `<option${i === b ? ' selected' : ''}>${esc(i)}</option>`).join('')}</select></div>
        <div class="tw"><table class="t"><thead><tr><th class="l"></th><th>${esc(a)}</th><th>${esc(b)}</th></tr></thead><tbody>
        ${row('Date / exercice', qvD(ra.a.date) + ' / ' + ra.a.fy, qvD(rb.a.date) + ' / ' + rb.a.fy)}${row('Valeur centrale (base actuelle)', qvF(ra.a.syn.v * ka), qvF(rb.a.syn.v))}
        ${row('Fourchette 10-90 %', qvF(ra.a.syn.p10 * ka) + ' – ' + qvF(ra.a.syn.p90 * ka), qvF(rb.a.syn.p10) + ' – ' + qvF(rb.a.syn.p90))}${row('Confiance', ra.a.syn.conf, rb.a.syn.conf)}
        ${row('Cours à la date', qvF(ra.a.price * ka), qvF(rb.a.price))}
        ${['dcf', 'ddm', 'ri', 'mult_own', 'mult_peer'].map(id => row(esc(((rb.a.models.find(z => z.id === id) || {}).n) || id), mv(ra, id, ka), mv(rb, id, 1))).join('')}
        ${['ke', 'glt', 'roe0', 'm0', 'g_mid', 'pay0', 'beta'].map(key => row(esc((rb.a.hyp.find(x => x.k === key) || ra.a.hyp.find(x => x.k === key) || { n: key }).n), hv(ra, key), hv(rb, key))).join('')}
        </tbody></table></div>${chg && rb.prev === ra.hash ? `<div class="lectb" style="padding:4px 2px"><p><b>Explication de la variation</b> : ${qvS(chg.dv)} au total${chg.d_data != null ? `, dont ${qvS(chg.d_data)} dû ${chg.method ? 'au changement de méthode' : 'aux informations nouvelles (comptes, dividendes, données)'} et ${qvS(chg.d_mkt)} aux paramètres de marché` : ''}.</p>${chg.lines.length ? `<p>${chg.lines.map(esc).join('<br>')}</p>` : ''}</div>` : ''}
        <div class="dm" style="font-size:11px">Empreinte de la version ${esc(b)} : ${esc((rb.hash || '').slice(0, 16))}… (chaînée à la précédente : ${rb.prev && ra && rb.prev === ra.hash ? 'oui' : rb.prev ? 'version précédente différente' : 'première version'})</div>`;
    }
  }
  const E = (C.events || []).slice().reverse();
  const ev = E.length ? `<div class="tw"><table class="t"><thead><tr><th>Détection</th><th class="l">Documents examinés</th><th>Niveau</th><th class="l">Décision</th><th class="l">Critères mesurés</th></tr></thead><tbody>${E.map(e => `<tr><td>${qvD(e.d_detect)}</td>
    <td class="l" style="white-space:normal;max-width:320px">${(e.titles || []).map(esc).join('<br>')}</td><td>${e.lvl === 2 ? '<b class="am">2</b>' : '1'}</td><td class="l" style="white-space:normal;max-width:300px">${esc(e.dec)}</td>
    <td class="l dm" style="white-space:normal">${(e.crit || []).map(c => `${c.hit ? '<b class="am">' : ''}${esc(c.n)} : ${esc(c.txt)}${c.thr != null ? ` (seuil ${num(Math.abs(c.thr) * 100, 0)} %)` : ''}${c.hit ? '</b>' : ''}`).join('<br>')}</td></tr>`).join('')}</tbody></table></div>`
    : '<div class="dm" style="padding:6px">Aucun document nouveau examiné depuis la version en vigueur.</div>';
  return `${pn('Historique des versions', 'QLAB', vt, { lect: 'Chaque version est conservée telle qu’elle a été publiée (données utilisées, hypothèses, résultats des modèles, synthèse), horodatée et chaînée à la précédente par une empreinte : aucune prévision passée n’est réécrite.' })}
    ${pn('Comparaison entre versions', 'QLAB', cmp)}
    ${pn('Événements examinés (actualisation exceptionnelle)', 'QLAB', ev, { lect: `<b>Niveau 1</b> : vérification — recalcul de contrôle avec les paramètres de marché de la version en vigueur ; la prévision officielle ne change pas. <b>Niveau 2</b> : réévaluation exceptionnelle complète, seulement si un seuil est franchi (valeur intrinsèque ≥ 10 %, bénéfice ≥ 15 %, nombre d’actions ≥ 5 %, dividende réduit de plus de moitié, dégradation de notation d’au moins deux crans). Les dossiers sont regroupés sur 30 jours, sauf urgence (perte, variation ≥ 25 %, opération sur le capital). Les variations du cours ne déclenchent jamais, à elles seules, une réévaluation.` })}`;
}

/* 18) Validation historique */
function qvBack(B, s) {
  if (!B) return pn('Validation historique', 'QLAB', '<div class="empty">Validation historique non encore calculée.</div>');
  const NM = { syn: 'Synthèse QLAB', ri: 'Résultat résiduel', ddm: 'Dividendes (DDM)', dcf: 'DCF', mult_own: 'Multiples historiques', mult_peer: 'Multiples des comparables' };
  const rows = Object.keys(NM).map(mk => { const a = (B.val.h1 || {})[mk], b = (B.val.h3 || {})[mk]; if (!a && !b) return '';
    const c = x => x ? `<td>${num(x.ic, 2)}</td><td>${num(x.ic_pos * 100, 0)} %</td><td>${qvS(x.spread, 0)}</td><td>${x.p1 ? `${x.p1[0]}-${x.p1[1]} : ${num(x.ic_p1, 2)} · ${x.p2[0]}-${x.p2[1]} : ${num(x.ic_p2, 2)}` : '—'}</td><td>${x.n}</td>` : '<td colspan="5" class="fl">non mesurable</td>';
    return `<tr><td class="l am">${NM[mk]}</td>${c(a)}${c(b)}<td>${B.perf && B.perf[mk] ? num(B.perf[mk].f, 2) : '—'}</td></tr>`; }).join('');
  const tbl = `<div class="tw"><table class="t"><thead><tr><th class="l" rowspan="2">Méthode</th><th colspan="5">1 an</th><th colspan="5">3 ans</th><th rowspan="2">Facteur de poids</th></tr>
    <tr><th>Corrélation de rang</th><th>Années positives</th><th>Écart tiers haut / bas</th><th>Sous-périodes</th><th>Obs.</th><th>Corrélation de rang</th><th>Années positives</th><th>Écart tiers haut / bas</th><th>Sous-périodes</th><th>Obs.</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  const F = B.fc || {}, G = B.gap || {};
  const kv = `<div class="kv2"><span>Évaluations point-in-time</span><b>${B.n} (${B.years ? B.years.join('-') : '—'})</b><span>Prévision du résultat : erreur / prévision naïve</span><b>${F.ratio != null ? num(F.ratio * 100, 0) + ' %' : '—'} (${F.n || 0} cas)</b>
    <span>Couverture des intervalles à 80 % (avant correction)</span><b>${F.cover80 != null ? num(F.cover80 * 100, 0) + ' %' : '—'}</b><span>Élargissement appliqué depuis</span><b>${F.scale80 ? '×' + num(F.scale80, 1) : '—'}</b>
    <span>Écart cours / valeur : persistance d’une année sur l’autre</span><b>${G.b != null ? num(G.b, 2) : '—'}</b><span>Demi-vie de l’écart</span><b>${G.half_life != null ? num(G.half_life, 1) + ' an(s)' : '—'}</b></div>
    ${F.methods ? `<div class="tw" style="margin-top:4px"><table class="t"><thead><tr><th class="l">Méthode de prévision (toutes sociétés)</th><th>Erreur / naïve</th><th>Cas</th></tr></thead><tbody>${Object.entries(F.methods).map(([k, v]) => `<tr><td class="l">${esc((QV_FC[k] || k))}</td><td>${num(v.ratio * 100, 0)} %</td><td>${v.n}</td></tr>`).join('')}</tbody></table></div>` : ''}`;
  const mine = (B.obs || []).filter(o => o.t === s.id);
  const my = mine.length ? `<div id="qvBt"></div><div class="tw"><table class="t"><thead><tr><th>Année</th><th>Date d’évaluation</th><th>Exercice</th><th>Cours</th><th>Valeur estimée</th><th>Valeur / cours</th><th>Rendement total 1 an</th><th>3 ans</th></tr></thead><tbody>${mine.map(o => `<tr><td>${o.y}</td><td>${qvD(o.d)}</td><td>${o.fy}</td><td>${qvF(o.p / (o.sf || 1))}</td><td>${qvF(o.v / (o.sf || 1))}</td><td>${qvS(o.v / o.p - 1, 0)}</td><td>${qvS(o.tr1)}</td><td>${qvS(o.tr3)}</td></tr>`).join('')}</tbody></table></div>`
    + '<div class="dm" style="font-size:11px">Cours et valeurs exprimés sur la base du nombre d’actions actuel (fractionnements pris en compte).</div>'
    : '<div class="dm" style="padding:6px">Aucune évaluation historique pour ce titre (historique de cours ou de comptes insuffisant).</div>';
  return `<div class="grid c2"><div>${pn('Pouvoir de classement de l’écart valeur / cours', 'QLAB', tbl, { lect: 'Pour chaque année, corrélation de rang entre l’écart valeur estimée / cours et le rendement total ultérieur (dividendes compris) relatif à la moyenne des titres évalués la même année. 0 = aucun pouvoir, 1 = classement parfait. L’écart tiers haut / bas compare le rendement relatif moyen du tiers des titres les plus « sous-évalués » et du tiers les plus « surévalués ». Le facteur de poids (borné entre 0,6 et 1,4) est utilisé dans la synthèse des versions suivantes.' })}
    ${B.wrule ? pn('Pondération des modèles selon leur performance', 'QLAB', `<div class="tw"><table class="t"><thead><tr><th class="l">Règle</th><th>Corrélation 1 an</th><th>Années positives</th><th>Corrélation 3 ans</th><th>Années positives</th><th></th></tr></thead><tbody>${B.wrule.table.map(r => `<tr${r.rule === B.wrule.chosen ? ' class="cur"' : ''}><td class="l">${esc(r.n)}</td><td>${num(r.ic1, 3)}</td><td>${num(r.pos1 * 100, 0)} %</td><td>${num(r.ic3, 3)}</td><td>${num(r.pos3 * 100, 0)} %</td><td class="l">${r.rule === B.wrule.chosen ? '<b class="qv-ok">retenue</b>' : ''}</td></tr>`).join('')}</tbody></table></div>`, { lect: esc(B.wrule.why) + '. Les facteurs de la règle retenue figurent dans la colonne « Facteur de poids » ci-dessus.' }) : ''}
    ${pn('Valeurs passées pour ce titre (point-in-time)', 'QLAB', my)}</div><div>${pn('Prévisions, calibration et convergence', 'QLAB', kv, { lect: 'Erreurs de prévision du résultat (comparées aux résultats effectivement publiés) et vitesse à laquelle l’écart entre cours et valeur estimée se réduit : deux choses différentes. Une erreur de valorisation n’est pas une erreur de prévision du cours.' })}
    ${pn('Limites de la validation', 'QLAB', `<div class="lectb">${(B.lim || []).map(l => `<p>${esc(l)}</p>`).join('')}</div>`)}</div></div>`;
}
const QV_FC = { naive: 'Naïve (dernier exercice reconduit)', moy3: 'Moyenne des 3 derniers exercices', derive: 'Tendance (croissance médiane récente)', roe: 'Retour de la rentabilité vers sa médiane', ar1: 'Autorégressif avec tendance' };
function qvBackDraw(m, B, s) {
  const host = m.querySelector('#qvBt'); if (!host || !B) return;
  const mine = (B.obs || []).filter(o => o.t === s.id); if (mine.length < 2) return;
  mine.forEach(o => { o.pc = o.p / (o.sf || 1); o.vc = o.v / (o.sf || 1); });
  const W = 600, Hh = 170, pl = 52, pb = 18, xs = mine.map(o => o.y), all = mine.flatMap(o => [o.pc, o.vc]).filter(x => x > 0);
  const lo = Math.min(...all) * .9, hi = Math.max(...all) * 1.05, x0 = Math.min(...xs), x1 = Math.max(...xs);
  const X = y => pl + (y - x0) / (x1 - x0 || 1) * (W - pl - 10), Y = v => 6 + (hi - v) / (hi - lo) * (Hh - pb - 6);
  host.innerHTML = `<svg class="qv-svg" style="height:170px" viewBox="0 0 ${W} ${Hh}" preserveAspectRatio="none">${niceTicks(lo, hi, 4).map(t => `<line x1="${pl}" x2="${W - 10}" y1="${Y(t)}" y2="${Y(t)}" stroke="#262626"/><text x="${pl - 4}" y="${Y(t) + 3}" fill="#a5a5a5" font-size="10" text-anchor="end">${num(t, 0)}</text>`).join('')}
    ${xs.map(y => `<text x="${X(y)}" y="${Hh - 4}" fill="#a5a5a5" font-size="10" text-anchor="middle">${y}</text>`).join('')}
    <polyline fill="none" stroke="#ffd200" stroke-width="1.5" points="${mine.map(o => `${X(o.y)},${Y(o.pc)}`).join(' ')}"/><polyline fill="none" stroke="#4da7fd" stroke-width="1.5" points="${mine.map(o => `${X(o.y)},${Y(o.vc)}`).join(' ')}"/></svg>
    <div class="chips" style="font-size:11px;padding:0 4px"><span style="color:#ffd200">— cours à la date d’évaluation</span><span style="color:#4da7fd">— valeur estimée avec les seules données de la date</span></div>`;
}

/* 19) Toutes les sociétés */
function qvAll(IX, s) {
  const cols = [['t', 'Titre', 'l'], ['n', 'Société', 'l'], ['arch', 'Modèle économique', 'l'], ['price', 'Cours'], ['v', 'Valeur'], ['p10', '10 %'], ['p90', '90 %'], ['up', 'Écart'], ['conf', 'Confiance'], ['fy', 'Exercice'], ['vdate', 'Évaluation']];
  const R = IX.rows.slice().sort((a, b) => { const x = a[QV.sort], y = b[QV.sort]; const c = typeof x === 'string' ? String(x).localeCompare(String(y)) : (x == null) - (y == null) || (x - y); return QV.desc ? -c : c; });
  const tbl = `<div class="tw"><table class="t"><thead><tr>${cols.map(c => `<th class="${c[2] || ''}${QV.sort === c[0] ? ' on' : ''}" data-qs="${c[0]}">${c[1]}${QV.sort === c[0] ? (QV.desc ? ' ▼' : ' ▲') : ''}</th>`).join('')}</tr></thead><tbody>
    ${R.map(r => `<tr data-qt="${esc(r.t)}"${r.t === s.id ? ' class="cur"' : ''} style="cursor:pointer"><td class="l tk">${esc(r.t)}</td><td class="l nm">${esc(r.n)}</td><td class="l dm">${esc(r.arch)}</td><td>${qvF(r.price)}${r.pr && r.pr !== 'fiable' ? ' <span class="am" title="cours à interpréter avec prudence">!</span>' : ''}</td>
      <td><b${r.conf < 35 ? ' class="dm"' : ''}>${qvF(r.v)}</b></td><td>${qvF(r.p10)}</td><td>${qvF(r.p90)}</td><td>${qvS(r.up, 0)}</td><td>${r.conf} <span class="dm">${esc(r.conf_lbl)}</span></td><td>${r.fy}</td><td>${qvD(r.vdate)}${r.ok ? '' : ' <span class="dn">!</span>'}</td></tr>`).join('')}</tbody></table></div>`;
  const M = IX.mkt || {};
  const kv = `<div class="kv2"><span>Rendement exigé médian des actions de la BRVM depuis 2010</span><b>${qvP(M.ke_lr)}</b><span>Rendement exigé implicite aujourd’hui</span><b>${qvP(M.ke_now)}</b>
    <span>Prime de risque du marché retenue</span><b>${qvP(M.erp, 2)}</b><span>Rendement du dividende agrégé</span><b>${qvP(M.dy, 2)}</b><span>Bêta moyen des actions (a priori)</span><b>${M.beta_prior ? num(M.beta_prior[0], 2) : '—'}</b>
    <div class="h">Taux sans risque et croissance de long terme par pays</div>${Object.keys(M.rf || {}).map(c => `<span>${esc(c)}</span><b>${qvP(M.rf[c], 2)} · ${qvP((M.glt || {})[c])}</b>`).join('')}
    <div class="h">Cycle</div><span>Cycle semestriel en cours</span><b>${qvD(IX.cycle_start)}</b><span>Prochaine réévaluation complète</span><b>${qvD(IX.next_cycle)}</b><span>Dernier calcul</span><b>${esc((IX.ts || '').replace('T', ' ').slice(0, 16))} UTC</b><span>Moteur</span><b>${esc(IX.engine)}</b></div>`;
  const none = (IX.none || []).length ? pn('Sociétés sans estimation publiée', 'QLAB', `<div class="lectb">${IX.none.map(x => `<p><b>${esc(x.t)}</b> ${esc(x.n)} : ${esc((x.why || []).join(' ; '))}</p>`).join('')}</div>`) : '';
  const lect = M.ke_now && M.ke_lr && M.ke_now < M.ke_lr - .01 ? `Le marché valorise aujourd’hui les actions de la BRVM à un rendement exigé implicite de <strong>${qvP(M.ke_now)}</strong>, contre <strong>${qvP(M.ke_lr)}</strong> en médiane depuis 2010 : avec un rendement exigé « normal », une majorité de titres ressort au-dessus de sa valeur estimée. La lecture « au rendement exigé actuel du marché » est donnée pour chaque titre dans la synthèse.` : '';
  return `<div class="grid c2">${pn('Valorisation QLAB de toutes les sociétés', 'QLAB', tbl, { lect: 'Cliquer sur une ligne ouvre la valorisation du titre. ! : cours ancien, titre suspendu ou peu échangé ; ! rouge : réévaluation semestrielle non réalisée.' })}<div>${pn('Paramètres de marché', 'QLAB', kv, { lect })}${none}</div></div>`;
}
function qvAllBind(m, IX, alive, s) {
  m.querySelectorAll('[data-qs]').forEach(th => th.onclick = () => { const k = th.dataset.qs; if (QV.sort === k) QV.desc = !QV.desc; else { QV.sort = k; QV.desc = !['t', 'n', 'arch'].includes(k); } qvPage(m, alive, s); });
  m.querySelectorAll('[data-qt]').forEach(tr => tr.onclick = () => { QV.sub = 's'; ST.tab.QLAB = 'v'; go('QLAB', tr.dataset.qt); });
}

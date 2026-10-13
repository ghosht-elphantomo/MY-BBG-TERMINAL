/* ================= FQT — PORT : portefeuille personnel (positions, risque, performance, dividendes) =================
   Les positions sont saisies par l'utilisateur et enregistrées dans ce navigateur seulement (localStorage) ;
   tous les calculs partent des cours relevés et des dividendes publiés. */
'use strict';
const PORT_K = 'fqt_port_v1';
const portLoad = () => { try { const o = JSON.parse(localStorage.getItem(PORT_K) || 'null'); if (o && Array.isArray(o.pos)) return o; } catch (e) { /* stockage indisponible */ } return { base: 'XOF', pos: [] }; };
const portSave = P => { try { localStorage.setItem(PORT_K, JSON.stringify(P)); } catch (e) { /* stockage indisponible */ } };
const PORT_ST = { P: null };
const portP = () => PORT_ST.P || (PORT_ST.P = portLoad());

/* série quotidienne de la valeur du portefeuille (composition actuelle) et des indices de référence, convertis dans la devise de base */
async function portSeries(P, days = 400) {
  const ids = [...new Set(P.pos.map(p => p.id).concat(['BRVMC', 'QQQ']))].filter(id => Q.by[id]);
  const S = Object.fromEntries(await Promise.all(ids.map(async id => [id, await series(id).catch(() => null)])));
  const t0 = new Date(Date.now() - days * 864e5), i0 = t0.getUTCFullYear() * 10000 + (t0.getUTCMonth() + 1) * 100 + t0.getUTCDate();
  const xs = [...new Set(Object.values(S).filter(Boolean).flatMap(s => s.x.filter(d => d >= i0)))].sort((a, b) => a - b);
  const ff = s => { const out = []; let j = 0, lv = null; while (j < s.x.length && s.x[j] < xs[0]) { lv = s.c[j]; j++; } for (const d of xs) { while (j < s.x.length && s.x[j] <= d) { lv = s.c[j]; j++; } out.push(lv); } return out; };
  const C = {}; for (const id of ids) { if (!S[id]) continue; const f = await fxFactor(Q.by[id].ccy, P.base, xs).catch(() => null); C[id] = fxApply(ff(S[id]), f); }
  return { xs, C };
}
const rets = a => { const r = []; for (let i = 1; i < a.length; i++) r.push(a[i] != null && a[i - 1] ? a[i] / a[i - 1] - 1 : 0); return r; };
const covar = (a, b) => { const n = Math.min(a.length, b.length); if (n < 3) return null; const ma = U.mean(a.slice(-n)), mb = U.mean(b.slice(-n)); let s = 0; for (let i = 0; i < n; i++) s += (a[a.length - n + i] - ma) * (b[b.length - n + i] - mb); return s / (n - 1); };

PAGES.PORT = async (m, alive) => {
  setTitle('Portfolio & Risk Analytics'); const P = portP();
  const tab = tabState('PORT', 'p'); setTabs([['p', 'Positions'], ['r', 'Risque'], ['h', 'Performance'], ['d', 'Dividendes']], tab, k => { ST.tab.PORT = k; render(); });
  setActs([{ n: 91, l: 'Exporter (CSV)', run: () => { const csv = 'titre;quantite;prix_de_revient\n' + P.pos.map(p => `${p.id};${p.q};${p.c ?? ''}`).join('\n'); const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'portefeuille.csv'; a.click(); } },
    { n: 92, l: 'Importer (coller)', run: () => { const b = $('ptImp'); if (b) b.hidden = !b.hidden; } }, { n: 93, l: 'Vider le portefeuille', run: () => { if (confirm('Supprimer toutes les positions de ce navigateur ?')) { P.pos = []; portSave(P); render(); } } }]);
  const W = await WMKT(); if (!alive()) return; const UF = W && W.fx ? fxUsd(W) : { USD: { now: 1, d: 1 } };
  const conv = (v, ccy, k = 'now') => { if (v == null) return null; if (ccy === P.base) return v; if (ccy === 'XOF' && P.base === 'EUR') return v / XOF_EUR; if (ccy === 'EUR' && P.base === 'XOF') return v * XOF_EUR; const a = UF[ccy], b = UF[P.base]; return a && b && a[k] && b[k] ? v * a[k] / b[k] : null; };
  const rows = P.pos.map(p => { const s = Q.by[p.id]; if (!s) return { p, s: null }; const v = conv(p.q * s.last, s.ccy), v0 = s.prev ? conv(p.q * s.prev, s.ccy, 'd') : null, cost = p.c ? conv(p.q * p.c, s.ccy) : null;
    return { p, s, v, dj: v != null && v0 != null ? v - v0 : null, cost, pl: v != null && cost != null ? v - cost : null, inc: s.dps && s.mkt === 'BRVM' ? conv(p.q * s.dps, s.ccy) : s.yld ? conv(p.q * s.last * s.yld, s.ccy) : null }; });
  const ok = rows.filter(r => r.v != null), tot = ok.reduce((a, r) => a + r.v, 0), dj = ok.reduce((a, r) => a + (r.dj || 0), 0), cst = ok.filter(r => r.cost != null), pl = cst.reduce((a, r) => a + r.pl, 0), cb = cst.reduce((a, r) => a + r.cost, 0);
  const inc = ok.reduce((a, r) => a + (r.inc || 0), 0), cur = P.base, dec = cur === 'XOF' ? 0 : 2, mny = v => v == null ? '—' : num(v, dec), mnyS = v => v == null ? '—' : `<span class="${cls(v)}">${v > 0 ? '+' : ''}${num(v, dec)}</span>`;
  const head = `<div class="tools ttb"><span class="tlab">Devise de base</span><select class="ofld" id="ptB">${['XOF', 'USD', 'EUR'].map(c => `<option ${c === cur ? 'selected' : ''}>${c}</option>`).join('')}</select>
      <span class="tlab">Titre</span><input class="ofld" id="ptT" placeholder="SNTS, AAPL, QQQ…" autocomplete="off" style="width:150px"><span class="tlab">Quantité</span><input class="ofld" id="ptQ" style="width:90px"><span class="tlab">Prix de revient unitaire</span><input class="ofld" id="ptC" placeholder="facultatif" style="width:100px">
      <button class="tb on" id="ptA">Ajouter / mettre à jour</button><span class="gsp"></span><span class="dm">${P.pos.length} positions · enregistrées dans ce navigateur</span></div>
    <div id="ptImp" class="tools" hidden><textarea class="ofld" id="ptX" rows="4" style="width:420px;height:70px" placeholder="Une position par ligne : TITRE;QUANTITÉ;PRIX_DE_REVIENT&#10;SNTS;100;28000&#10;AAPL;10"></textarea><button class="tb" id="ptXo">Importer</button><span class="dm">Les titres déjà présents sont mis à jour.</span></div>`;
  const kv = `<div class="kv2"><span>Valeur du portefeuille</span><b class="wh">${mny(tot)} ${cur}</b><span>Résultat du jour</span><b>${mnyS(dj)} ${tot ? `(${pc(dj / (tot - dj))})` : ''}</b><span>Plus ou moins-value latente</span><b>${cst.length ? `${mnyS(pl)} (${pc(cb ? pl / cb : null)})` : '<span class="dm">indiquez les prix de revient</span>'}</b>
      <span>Revenu annuel de dividendes</span><b>${inc ? `${mny(inc)} ${cur}` : '—'}</b><span>Rendement du portefeuille</span><b>${tot && inc ? num(inc / tot * 100, 2) + ' %' : '—'}</b><span>Positions</span><b>${ok.length}${rows.length > ok.length ? ` <span class="dm">(${rows.length - ok.length} sans cours ou sans change)</span>` : ''}</b></div>`;
  const bind = () => {
    $('ptB').onchange = e => { P.base = e.target.value; portSave(P); render(); };
    const T = $('ptT'); T.oninput = () => { const L = searchSecs(T.value).slice(0, 10); if (!L.length) { ddClose(); return; } ddOpen(T, L.map(s => ({ code: s.id, l: esc(s.short || s.n), run: () => { T.value = s.id; $('ptQ').focus(); } }))); };
    const add = () => { const id = (Q.by[T.value.trim().toUpperCase()] || searchSecs(T.value)[0] || {}).id, q = parseFloat(String($('ptQ').value).replace(/\s/g, '').replace(',', '.')), c = parseFloat(String($('ptC').value).replace(/\s/g, '').replace(',', '.'));
      if (!id || !isFinite(q) || q <= 0) { T.focus(); return; } const ex = P.pos.find(x => x.id === id); if (ex) { ex.q = q; ex.c = isFinite(c) ? c : ex.c; } else P.pos.push({ id, q, c: isFinite(c) ? c : null }); portSave(P); render(); };
    $('ptA').onclick = add; [$('ptQ'), $('ptC')].forEach(x => x.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); add(); } });
    $('ptXo').onclick = () => { for (const ln of $('ptX').value.split(/\n/)) { const [t, q, c] = ln.split(/[;,\t]/).map(x => (x || '').trim()); const s = Q.by[(t || '').toUpperCase()] || (t ? searchSecs(t)[0] : null), qq = parseFloat(String(q || '').replace(',', '.')), cc = parseFloat(String(c || '').replace(',', '.'));
      if (!s || !(qq > 0)) continue; const ex = P.pos.find(x => x.id === s.id); if (ex) { ex.q = qq; if (isFinite(cc)) ex.c = cc; } else P.pos.push({ id: s.id, q: qq, c: isFinite(cc) ? cc : null }); } portSave(P); render(); };
    m.querySelectorAll('[data-pdel]').forEach(b => b.onclick = e => { e.stopPropagation(); P.pos = P.pos.filter(x => x.id !== b.dataset.pdel); portSave(P); render(); });
    m.querySelectorAll('[data-ped]').forEach(b => b.onclick = e => { e.stopPropagation(); const p = P.pos.find(x => x.id === b.dataset.ped); if (!p) return; T.value = p.id; $('ptQ').value = p.q; $('ptC').value = p.c ?? ''; $('ptQ').focus(); });
  };
  if (!P.pos.length) { m.innerHTML = head + pn('Portefeuille', 'PORT', `<div class="empty">Aucune position. Saisissez un titre, une quantité et, si vous le souhaitez, votre prix de revient unitaire (dans la devise du titre), puis « Ajouter ». Vous pouvez aussi coller une liste avec 92) Importer.</div>`, { lect: 'Les positions restent dans ce navigateur : elles ne sont envoyées nulle part. Les valeurs, le risque et les dividendes sont calculés à partir des cours relevés toutes les 15 minutes.' }); bind(); return; }
  const grp = k => { const o = {}; for (const r of ok) { const g = k(r); o[g] = (o[g] || 0) + r.v; } return Object.entries(o).sort((a, b) => b[1] - a[1]); };
  const alloc = (title, L) => pn(title, 'PORT', `<table class="t wcr"><tbody>${L.map(([g, v]) => `<tr><td class="l am">${esc(g)}</td><td class="wh">${num(v / tot * 100, 1)} %</td><td class="wcb" style="width:45%"><i class="p" style="left:0;width:${(v / tot * 100).toFixed(1)}%"></i></td></tr>`).join('')}</tbody></table>`, { np: true });
  if (tab === 'p') {
    const L = rows.slice().sort((a, b) => (b.v || 0) - (a.v || 0));
    m.innerHTML = head + `<div class="grid side">${pn(`Positions · valeurs en ${cur}`, 'PORT', `<div class="tw"><table class="t"><thead><tr><th class="l">Titre</th><th class="l">Nom</th><th>Quantité</th><th>Prix de revient</th><th>Cours</th><th>Var. jour</th><th>Valeur (${cur})</th><th>Poids</th><th>Résultat jour</th><th>+/− latente</th><th>%</th><th>Rdt div.</th><th></th></tr></thead><tbody>
        ${L.map((r, i) => { const s = r.s; if (!s) return `<tr><td class="l"><span class="rn">${i + 1})</span>${esc(r.p.id)}</td><td class="l dm" colspan="11">titre introuvable dans la base</td><td><span class="pdx" data-pdel="${esc(r.p.id)}">✕</span></td></tr>`;
          return `<tr data-sec="${s.id}" data-to="DES" style="cursor:pointer"><td class="l"><span class="rn">${i + 1})</span><b class="wh">${s.id}</b></td><td class="l am">${esc(s.short || s.n)}</td><td>${num(r.p.q, r.p.q % 1 ? 2 : 0)}</td><td>${r.p.c ? px(s, r.p.c) : '<span class="dm">—</span>'}</td><td class="wh">${px(s, s.last)} <span class="dm">${s.ccy}</span></td><td>${pc(s.pct)}</td>
            <td class="wh">${mny(r.v)}</td><td>${r.v != null && tot ? num(r.v / tot * 100, 1) + ' %' : '—'}</td><td>${mnyS(r.dj)}</td><td>${r.pl != null ? mnyS(r.pl) : '—'}</td><td>${r.pl != null && r.cost ? pc(r.pl / r.cost) : '—'}</td><td>${s.yld ? num(s.yld * 100, 2) + ' %' : '—'}</td>
            <td class="l"><span class="pdx" data-ped="${s.id}" title="modifier">✎</span> <span class="pdx" data-pdel="${s.id}" title="supprimer">✕</span></td></tr>`; }).join('')}
        <tr class="sep2"><td class="l wh" colspan="6">Total</td><td class="wh">${mny(tot)}</td><td>100 %</td><td>${mnyS(dj)}</td><td>${cst.length ? mnyS(pl) : '—'}</td><td>${cb ? pc(pl / cb) : '—'}</td><td>${tot && inc ? num(inc / tot * 100, 2) + ' %' : '—'}</td><td></td></tr></tbody></table></div>`,
        { np: true, lect: `Valeurs converties en ${cur} au cours de change du dernier relevé (franc CFA : parité fixe avec l’euro). Prix de revient dans la devise du titre ; la plus-value latente inclut donc l’effet de change. Rendement du dividende : dernier dividende publié ÷ cours (BRVM, net) ou rendement indicatif (US). Clic sur une ligne : fiche du titre.` })}
      <div>${pn('Synthèse', 'PORT', kv)}${alloc('Répartition par secteur', grp(r => r.s.grp || 'Autres'))}${alloc('Répartition par marché et devise', grp(r => `${r.s.mkt === 'BRVM' ? 'BRVM' : r.s.mkt === 'US' ? 'États-Unis' : r.s.mkt || 'Autre'} · ${r.s.ccy}`))}</div></div>`;
    bind(); return;
  }
  m.innerHTML = head + `<div class="empty" id="ptW">Calcul sur les cours quotidiens du dernier an…</div>`; bind();
  const D = await portSeries(P); if (!alive()) return;
  const live = ok.filter(r => D.C[r.p.id]), n = D.xs.length;
  const V = D.xs.map((_, t) => { let s = 0; for (const r of live) { const c = D.C[r.p.id][t]; if (c == null) return null; s += r.p.q * c; } return s; });
  const k0 = V.findIndex(v => v != null), Vx = V.slice(k0), X = D.xs.slice(k0), rp = rets(Vx).slice(-252);
  const RB = D.C.BRVMC ? rets(D.C.BRVMC.slice(k0)).slice(-252) : null, RQ = D.C.QQQ ? rets(D.C.QQQ.slice(k0)).slice(-252) : null;
  if (tab === 'r') {
    const sd = U.std(rp), srt = rp.slice().sort((a, b) => a - b), q5 = U.q(srt, .05), tail = srt.filter(x => x <= q5), cvar = tail.length ? U.mean(tail) : null, Vn = Vx[Vx.length - 1];
    let pk = -Infinity, mdd = 0; for (const v of Vx) { if (v == null) continue; pk = Math.max(pk, v); mdd = Math.min(mdd, v / pk - 1); }
    const beta = R => R && U.std(R) ? covar(rp, R) / (U.std(R) ** 2) : null, corr = R => R && U.std(R) && sd ? covar(rp, R) / (U.std(R) * sd) : null;
    const A = live.map(r => ({ r, x: rets(D.C[r.p.id].slice(k0)).slice(-252), w: r.v / live.reduce((a, z) => a + z.v, 0) }));
    const Sg = A.map(a => A.map(b => covar(a.x, b.x) || 0)), vp = A.reduce((s, a, i) => s + A.reduce((t, b, j) => t + a.w * b.w * Sg[i][j], 0), 0);
    const rc = A.map((a, i) => ({ a, c: vp > 0 ? a.w * A.reduce((t, b, j) => t + b.w * Sg[i][j], 0) / vp : null, vol: Math.sqrt(Sg[i][i] * 252) }));
    const wavgVol = A.reduce((s, a) => s + a.w * Math.sqrt(Sg[A.indexOf(a)][A.indexOf(a)]), 0), dr = Math.sqrt(vp) ? wavgVol / Math.sqrt(vp) : null;
    const cm = A.length <= 14 ? `<table class="t"><thead><tr><th class="l"></th>${A.map(a => `<th>${a.r.s.id}</th>`).join('')}</tr></thead><tbody>${A.map((a, i) => `<tr><td class="l am">${a.r.s.id}</td>${A.map((b, j) => { const c = Sg[i][j] / Math.sqrt(Sg[i][i] * Sg[j][j] || 1); return `<td style="background:${i === j ? '#141414' : c > 0 ? `rgba(255,67,61,${Math.min(.75, Math.abs(c)).toFixed(2)})` : `rgba(50,120,255,${Math.min(.75, Math.abs(c)).toFixed(2)})`}">${i === j ? '—' : num(c, 2)}</td>`; }).join('')}</tr>`).join('')}</tbody></table>` : '<div class="dm" style="padding:6px">Matrice affichée jusqu’à 14 positions.</div>';
    m.innerHTML = head + `<div class="grid c3">${pn('Risque du portefeuille (1 an, quotidien)', 'PORT', `<div class="kv2"><span>Volatilité annualisée</span><b class="wh">${num(sd * Math.sqrt(252) * 100, 1)} %</b><span>VaR 95 % sur 1 jour (historique)</span><b class="dn">${num(-q5 * 100, 2)} % · ${mny(-q5 * Vn)} ${cur}</b><span>VaR 95 % sur 10 jours (√10)</span><b class="dn">${mny(-q5 * Math.sqrt(10) * Vn)} ${cur}</b><span>Perte moyenne au-delà de la VaR (CVaR)</span><b class="dn">${cvar != null ? num(-cvar * 100, 2) + ' %' : '—'}</b>
          <span>Baisse maximale sur la période</span><b class="dn">${num(mdd * 100, 1)} %</b><span>Bêta contre BRVM Composite</span><b>${beta(RB) != null ? num(beta(RB), 2) : '—'}</b><span>Bêta contre QQQ (Nasdaq-100)</span><b>${beta(RQ) != null ? num(beta(RQ), 2) : '—'}</b><span>Corrélation BRVM / QQQ</span><b>${corr(RB) != null ? num(corr(RB), 2) : '—'} / ${corr(RQ) != null ? num(corr(RQ), 2) : '—'}</b><span>Ratio de diversification</span><b>${dr ? num(dr, 2) : '—'}</b><span>Observations</span><b>${rp.length} séances</b></div>`, { lect: `Calculé sur la composition actuelle et les cours quotidiens convertis en ${cur}. VaR historique : 5e centile des variations quotidiennes. Ratio de diversification : volatilité moyenne pondérée des titres ÷ volatilité du portefeuille (1 = aucune diversification).` })}
        ${pn('Contribution au risque', 'PORT', `<table class="t wcr"><thead><tr><th class="l">Titre</th><th>Poids</th><th>Volatilité</th><th>Part du risque</th><th class="c"></th></tr></thead><tbody>${rc.sort((a, b) => (b.c || 0) - (a.c || 0)).map(x => `<tr><td class="l"><b class="wh">${x.a.r.s.id}</b></td><td>${num(x.a.w * 100, 1)} %</td><td>${num(x.vol * 100, 1)} %</td><td class="${x.c > x.a.w * 1.25 ? 'dn' : 'wh'}">${x.c != null ? num(x.c * 100, 1) + ' %' : '—'}</td><td class="wcb" style="width:30%"><i class="${x.c >= 0 ? 'p' : 'n'}" style="left:0;right:auto;width:${Math.min(100, Math.abs(x.c || 0) * 100).toFixed(1)}%"></i></td></tr>`).join('')}</tbody></table>`, { np: true, lect: 'Part du risque : contribution de chaque titre à la variance du portefeuille. En rouge : titre qui pèse nettement plus dans le risque que dans le capital.' })}
        ${pn('Corrélations entre positions', 'PORT', `<div class="tw">${cm}</div>`, { np: true, lect: 'Rouge : les titres évoluent ensemble ; bleu : en sens contraire. Variations quotidiennes sur un an, dans la devise de base.' })}</div>`;
    bind(); return;
  }
  if (tab === 'h') {
    const norm = a => { const b = a.slice(k0); const f = b.find(v => v != null); return b.map(v => v != null && f ? v / f * 100 : null); };
    const perf = (a, days) => { const b = a.slice(k0), t = new Date(Date.now() - days * 864e5), ti = t.getUTCFullYear() * 10000 + (t.getUTCMonth() + 1) * 100 + t.getUTCDate(); let j = X.findIndex(d => d >= ti); if (j < 0) return null; const e = b[b.length - 1]; return b[j] && e ? e / b[j] - 1 : null; };
    const ytd = a => { const b = a.slice(k0), y = Math.floor(X[X.length - 1] / 10000); let j = X.findIndex(d => Math.floor(d / 10000) === y); if (j <= 0) return null; return b[j - 1] ? b[b.length - 1] / b[j - 1] - 1 : null; };
    const PER = [['1 sem.', 7], ['1 mois', 30], ['3 mois', 91], ['6 mois', 182], ['1 an', 365]], L = [['Portefeuille', V], ['BRVM Composite', D.C.BRVMC], ['QQQ', D.C.QQQ]].filter(x => x[1]);
    m.innerHTML = head + `${pn(`Performance de la composition actuelle (base 100, en ${cur})`, 'PORT', cvb('ptG', 330), { np: true })}
      ${pn('Rendements par période', 'PORT', `<table class="t"><thead><tr><th class="l"></th>${PER.map(p => `<th>${p[0]}</th>`).join('')}<th>Depuis janv.</th></tr></thead><tbody>${L.map(([l, a]) => `<tr><td class="l am">${l}</td>${PER.map(p => `<td>${pc(perf(a, p[1]))}</td>`).join('')}<td>${pc(ytd(a))}</td></tr>`).join('')}</tbody></table>`, { np: true, lect: `Simulation : valeur qu’auraient eue les quantités actuelles sur la période, dividendes non compris, en ${cur}. Ce n’est pas la performance réelle de vos achats successifs.` })}`;
    new TSChart($('ptG'), { panes: [{ h: 1, fmt: v => num(v, 0) }], grid: 'dot', xticks: bbgTicks }).set({ x: X, series: [{ y: norm(V), color: '#f9a33a', w: 2, label: 'Portefeuille', fmt: v => num(v, 1) }].concat(D.C.BRVMC ? [{ y: norm(D.C.BRVMC), color: '#5fd0ea', w: 1.3, label: 'BRVM Composite', fmt: v => num(v, 1) }] : [], D.C.QQQ ? [{ y: norm(D.C.QQQ), color: '#e6e6e6', w: 1.3, label: 'QQQ', fmt: v => num(v, 1) }] : []) }, [0, X.length - 1]);
    bind(); return;
  }
  /* dividendes */
  const DV = await getJSON('dividends.json').catch(() => []); if (!alive()) return; const today = new Date().toISOString().slice(0, 10);
  const up = (Array.isArray(DV) ? DV : []).filter(x => P.pos.some(p => p.id === x.t) && x.dps && ((x.det && x.det >= today) || (x.pay && x.pay >= today))).sort((a, b) => String(a.dex || a.pay).localeCompare(String(b.dex || b.pay)));
  m.innerHTML = head + `<div class="grid c2b">${pn(`Revenu annuel de dividendes estimé · ${mny(inc)} ${cur}`, 'PORT', `<table class="t"><thead><tr><th class="l">Titre</th><th>Quantité</th><th>Dernier dividende / titre</th><th>Exercice</th><th>Revenu (${cur})</th><th>Rendement</th><th>Part du revenu</th></tr></thead><tbody>${ok.slice().sort((a, b) => (b.inc || 0) - (a.inc || 0)).map(r => `<tr><td class="l"><b class="wh">${r.s.id}</b> <span class="am">${esc(r.s.short || r.s.n)}</span></td><td>${num(r.p.q, 0)}</td><td>${r.s.mkt === 'BRVM' && r.s.dps ? px(r.s, r.s.dps) + ' ' + r.s.ccy : r.s.yld ? 'rendement ' + num(r.s.yld * 100, 2) + ' %' : '—'}</td><td class="dm">${r.s.dps_ex || '—'}</td><td class="wh">${r.inc ? mny(r.inc) : '—'}</td><td>${r.s.yld ? num(r.s.yld * 100, 2) + ' %' : '—'}</td><td>${r.inc && inc ? num(r.inc / inc * 100, 1) + ' %' : '—'}</td></tr>`).join('')}</tbody></table>`, { np: true, lect: 'Estimation à dividende inchangé : dernier dividende net publié (BRVM) ou rendement indicatif (US) × quantité détenue. Le dividende futur peut être différent.' })}
    ${pn('Prochains détachements et paiements de vos titres', 'DIVC', up.length ? `<table class="t"><thead><tr><th class="l">Titre</th><th>Dividende</th><th>Détachement</th><th>Paiement</th><th>Montant pour vous</th></tr></thead><tbody>${up.map(x => { const p = P.pos.find(q => q.id === x.t), s = Q.by[x.t]; return `<tr><td class="l wh">${esc(x.t)}</td><td>${num(x.dps, 2)}</td><td>${x.det ? fds(x.det) : '—'}</td><td>${x.pay ? fds(x.pay) : '—'}</td><td class="wh">${s ? mny(conv(p.q * x.dps, s.ccy)) + ' ' + cur : '—'}</td></tr>`; }).join('')}</tbody></table>` : '<div class="empty">Aucun détachement annoncé pour vos titres.</div>', { np: true })}</div>`;
  bind();
};

/* ------------------------------------------------------------------ TECH : analyse technique (tendance, oscillateurs, volatilité, niveaux) —
   indicateurs calculés sur les cours quotidiens publiés ; signaux descriptifs, pas une recommandation */
PAGES.TECH = async (m, alive) => {
  const s = sec(ST.sec); setTitle('Technical Analysis'); const S = await series(s.id).catch(() => null); if (!alive()) return;
  if (!S || S.c.length < 60 || s.f !== 'D') { m.innerHTML = pn('Analyse technique', 'TECH', '<div class="empty">Historique quotidien insuffisant pour ce titre.</div>'); return; }
  const c = S.c, h = S.h, l = S.l, n = c.length, L = n - 1, last = c[L], P = v => px(s, v);
  const sm = k => U.sma(c, k), M20 = sm(20), M50 = sm(50), M100 = sm(100), M200 = sm(200), R = U.rsi(c, 14);
  const e12 = U.ema(c, 12), e26 = U.ema(c, 26), macd = c.map((_, i) => e12[i] - e26[i]), sig = U.ema(macd.map(v => isFinite(v) ? v : NaN), 9, 26), hist = macd.map((v, i) => v - sig[i]);
  const sd20 = (() => { const o = new Float64Array(n).fill(NaN); for (let i = 19; i < n; i++) { let a = 0, b = 0; for (let j = i - 19; j <= i; j++) { a += c[j]; b += c[j] * c[j]; } const mm = a / 20; o[i] = Math.sqrt(Math.max(0, b / 20 - mm * mm)); } return o; })();
  const bu = M20.map((v, i) => v + 2 * sd20[i]), bl = M20.map((v, i) => v - 2 * sd20[i]), pB = (last - bl[L]) / (bu[L] - bl[L]);
  const tr = c.map((v, i) => i ? Math.max(h[i] - l[i], Math.abs(h[i] - c[i - 1]), Math.abs(l[i] - c[i - 1])) : h[i] - l[i]), atr = U.mean(tr.slice(-14));
  const hh14 = Math.max(...h.slice(-14)), ll14 = Math.min(...l.slice(-14)), stK = hh14 > ll14 ? (last - ll14) / (hh14 - ll14) * 100 : null;
  const kS = []; for (let i = L - 2; i <= L; i++) { const H = Math.max(...h.slice(i - 13, i + 1)), Lo = Math.min(...l.slice(i - 13, i + 1)); kS.push(H > Lo ? (c[i] - Lo) / (H - Lo) * 100 : null); } const stD = kS.every(v => v != null) ? U.mean(kS) : null;
  const roc = k => n > k && c[L - k] ? last / c[L - k] - 1 : null;
  const lr = c.slice(-61).map((v, i, a) => i ? Math.log(v / a[i - 1]) : 0).slice(1), vol20 = U.std(lr.slice(-20)) * Math.sqrt(252), vol60 = U.std(lr) * Math.sqrt(252);
  const cross = (a, b) => { for (let i = L; i > Math.max(1, L - 750); i--) if (isFinite(a[i]) && isFinite(b[i]) && isFinite(a[i - 1]) && isFinite(b[i - 1]) && Math.sign(a[i] - b[i]) !== Math.sign(a[i - 1] - b[i - 1])) return { i, up: a[i] > b[i] }; return null; };
  const gx = cross(M50, M200), mx = cross(macd, sig);
  const k52 = Math.max(0, n - 252), hi52 = Math.max(...h.slice(k52)), lo52 = Math.min(...l.slice(k52)), hi20 = Math.max(...h.slice(-20)), lo20 = Math.min(...l.slice(-20));
  /* pivots classiques sur la dernière séance close */
  /* pivots hebdomadaires : plus haut, plus bas et clôture des 5 dernières séances (plus parlants que la seule veille sur les titres peu échangés) */
  const hW = Math.max(...h.slice(-5)), lW = Math.min(...l.slice(-5)), PP = (hW + lW + last) / 3, R1 = 2 * PP - lW, S1 = 2 * PP - hW, R2 = PP + (hW - lW), S2 = PP - (hW - lW);
  const sigs = [['Cours au-dessus de la MM 200', last > M200[L]], ['MM 50 au-dessus de la MM 200', M50[L] > M200[L]], ['Cours au-dessus de la MM 50', last > M50[L]], ['MACD au-dessus de son signal', macd[L] > sig[L]], ['RSI au-dessus de 50', R[L] > 50], ['Rendement 3 mois positif', roc(63) > 0], ['Rendement 12 mois positif', roc(252) > 0]].filter(x => x[1] != null && (typeof x[1] === 'boolean'));
  const nUp = sigs.filter(x => x[1]).length;
  const row = (a, b, c2 = '') => `<tr><td class="l am">${a}</td><td class="wh">${b}</td><td class="l">${c2}</td></tr>`, yn = (v, a, b) => v ? `<span class="up">${a}</span>` : `<span class="dn">${b}</span>`, dd = i => fd(S.x[i]);
  const ecart = v => isFinite(v) ? pc(last / v - 1) : '—';
  m.innerHTML = `<div class="grid c4 tch">${pn('1) Tendance', 'TECH', `<table class="t"><tbody>${row('Cours', P(last) + ' ' + esc(s.ccy), fd(S.x[L]))}${[['MM 20', M20], ['MM 50', M50], ['MM 100', M100], ['MM 200', M200]].map(([a, A]) => row(a, isFinite(A[L]) ? P(A[L]) : '—', isFinite(A[L]) ? `${ecart(A[L])} ${yn(last > A[L], '▲', '▼')}` : '')).join('')}
        ${row('Croisement MM 50 / MM 200', gx ? (gx.up ? '<span class="up">haussier</span>' : '<span class="dn">baissier</span>') : '—', gx ? 'le ' + dd(gx.i) : 'aucun sur 3 ans')}</tbody></table>`, { np: true })}
    ${pn('2) Oscillateurs', 'TECH', `<table class="t"><tbody>${row('RSI 14', num(R[L], 1), R[L] > 70 ? '<span class="dn">surachat (> 70)</span>' : R[L] < 30 ? '<span class="up">survente (< 30)</span>' : 'zone neutre')}${row('MACD (12, 26)', num(macd[L], 3), `signal ${num(sig[L], 3)}`)}${row('Histogramme MACD', `<span class="${cls(hist[L])}">${num(hist[L], 3)}</span>`, mx ? `${mx.up ? '<span class="up">▲</span>' : '<span class="dn">▼</span>'} ${dd(mx.i).slice(0, 5)}` : '')}
        ${row('Stochastique %K / %D (14, 3)', stK != null ? `${num(stK, 1)} / ${stD != null ? num(stD, 1) : '—'}` : '—', stK > 80 ? 'zone haute' : stK < 20 ? 'zone basse' : '')}${row('Williams %R (14)', stK != null ? num(stK - 100, 1) : '—', '')}
        ${[['1 mois', 21], ['3 mois', 63], ['6 mois', 126], ['12 mois', 252]].map(([a, d]) => row('Variation ' + a, pc(roc(d)), '')).join('')}</tbody></table>`, { np: true })}
    ${pn('3) Volatilité', 'TECH', `<table class="t"><tbody>${row('ATR 14 séances', P(atr), num(atr / last * 100, 2) + ' %')}${row('Bandes de Bollinger (20, 2)', `${P(bl[L])} – ${P(bu[L])}`, `l. ${num((bu[L] - bl[L]) / M20[L] * 100, 1)} %`)}${row('Position dans les bandes (%B)', num(pB * 100, 0) + ' %', pB > 1 ? 'au-dessus de la bande haute' : pB < 0 ? 'sous la bande basse' : '')}
        ${row('Volatilité 20 séances (ann.)', num(vol20 * 100, 1) + ' %', '')}${row('Volatilité 60 séances (ann.)', num(vol60 * 100, 1) + ' %', '')}${row('Position sur 52 semaines', num((last - lo52) / (hi52 - lo52) * 100, 0) + ' %', '')}</tbody></table>`, { np: true })}
    ${pn('4) Niveaux', 'TECH', `<table class="t"><tbody>${row('Résistance 2 (R2)', P(R2), ecart(R2))}${row('Résistance 1 (R1)', P(R1), ecart(R1))}${row('Pivot', P(PP), ecart(PP))}${row('Support 1 (S1)', P(S1), ecart(S1))}${row('Support 2 (S2)', P(S2), ecart(S2))}${row('Plus haut / bas 20 séances', `${P(hi20)} / ${P(lo20)}`, '')}${row('Plus haut / bas 52 semaines', `${P(hi52)} / ${P(lo52)}`, '')}</tbody></table>`, { np: true, lect: `Pivots hebdomadaires : plus haut, plus bas et dernier cours des 5 séances jusqu’au ${fd(S.x[L])}.` })}</div>
    <div class="grid side">${pn(`${esc(ykey(s))} · cours, MM 50 / MM 200, Bollinger ; RSI ; MACD (1 an)`, 'TECH', cvb('teG', 420), { np: true })}
      ${pn(`Synthèse : ${nUp} ${nUp > 1 ? 'signaux haussiers' : 'signal haussier'} sur ${sigs.length}`, 'TECH', `<table class="t"><tbody>${sigs.map(([a, v]) => `<tr><td class="l am">${a}</td><td>${v ? '<span class="up">oui</span>' : '<span class="dn">non</span>'}</td></tr>`).join('')}</tbody></table><div class="tsc"><i style="width:${(nUp / sigs.length * 100).toFixed(0)}%"></i></div>`, { np: true, lect: 'Lecture descriptive de la tendance à partir des cours publiés : ce n’est pas une recommandation d’achat ou de vente. Sur les titres peu échangés, plus haut et plus bas égalent souvent la clôture : ATR et stochastique sont alors moins parlants.' })}</div>`;
  const k0 = Math.max(0, n - 260), sl = a => Array.from(a).slice(k0).map(v => isFinite(v) ? v : null);
  new TSChart($('teG'), { panes: [{ h: 2.2 }, { h: .8, fixed: [0, 100], refs: [{ v: 70, color: CL.dn }, { v: 30, color: CL.up }], title: 'RSI 14' }, { h: .9, title: 'MACD' }], grid: 'dot', xticks: bbgTicks })
    .set({ x: S.x.slice(k0), series: [{ y: sl(c), color: '#ffffff', w: 1.4, label: s.id, fmt: v => P(v) }, { y: sl(M50), color: '#f9a33a', w: 1.1, label: 'MM 50', fmt: v => P(v) }, { y: sl(M200), color: '#ff3d4d', w: 1.1, label: 'MM 200', fmt: v => P(v) },
      { y: sl(bu), color: 'rgba(95,208,234,.55)', w: 1, label: 'Bollinger haute', fmt: v => P(v) }, { y: sl(bl), color: 'rgba(95,208,234,.55)', w: 1, label: 'Bollinger basse', fmt: v => P(v) },
      { pane: 1, y: sl(R), color: '#b69cff', w: 1.2, label: 'RSI', fmt: v => num(v, 1) }, { pane: 2, type: 'bar', y: sl(hist), colorFn: v => v >= 0 ? CL.up : CL.dn, label: 'Histogramme', fmt: v => num(v, 3) }, { pane: 2, y: sl(macd), color: '#5fd0ea', w: 1.1, label: 'MACD', fmt: v => num(v, 3) }, { pane: 2, y: sl(sig), color: '#f9a33a', w: 1, label: 'Signal', fmt: v => num(v, 3) }] }, [0, n - 1 - k0]);
};

/* ------------------------------------------------------------------ EA : écran « Earnings Analysis » — publications de résultats à venir
   (date, moment, consensus du trimestre) et publiées (BPA réel contre consensus, surprise, réaction du cours) ; actions US suivies */
PAGES.EA = async (m, alive) => {
  setTitle('Earnings Analysis'); const E = await getJSON('ee.json').catch(() => null); if (!alive()) return;
  if (!E) { m.innerHTML = pn('Résultats', 'EA', '<div class="empty">Estimations en attente du relevé du soir.</div>'); return; }
  const tab = tabState('EA', 'u'); setTabs([['u', 'À venir'], ['p', 'Publiés (60 jours)']], tab, k => { ST.tab.EA = k; render(); });
  const us = t => { const x = String(t || '').match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/); return x ? `${x[3]}-${x[1].padStart(2, '0')}-${x[2].padStart(2, '0')}` : null; };
  const today = new Date().toISOString().slice(0, 10), wd = d => new Date(d + 'T12:00:00Z').toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: '2-digit', timeZone: 'UTC' });
  const st = ST.ea = ST.ea || { q: '' };
  if (tab === 'u') {
    const L = Object.entries(E).map(([id, x]) => { const d = us(x.ed), s = Q.by[id]; if (!d || d < today || !s) return null; const q0 = (x.qr || [])[0] || {}, sur = (x.sur || []).slice().sort((a, b) => (us(b.d) || '').localeCompare(us(a.d) || ''))[0];
      return { id, s, d, when: /after market/i.test(x.ed) ? 'après clôture' : /before market/i.test(x.ed) ? 'avant ouverture' : '—', est: /estimated|algorithm/i.test(x.ed), q: q0.fiscalEnd, eps: q0.consensusEPSForecast, hi: q0.highEPSForecast, lo: q0.lowEPSForecast, nb: q0.noOfEstimates, last: sur }; }).filter(Boolean)
      .filter(r => !st.q || (r.id + ' ' + r.s.n).toLowerCase().includes(st.q.toLowerCase())).sort((a, b) => a.d.localeCompare(b.d) || (b.s.mcap || 0) - (a.s.mcap || 0));
    let cur = '', k = 0; const rows = L.map(r => { const hd = r.d !== cur ? `<tr class="grp"><td class="l" colspan="11">${wd(r.d)}${r.d === today ? ' · aujourd’hui' : ''}</td></tr>` : ''; cur = r.d;
      return hd + `<tr data-sec="${r.id}" data-to="EE" style="cursor:pointer"><td class="l"><span class="rn">${++k})</span><b class="wh">${r.id}</b></td><td class="l am">${esc(r.s.short || r.s.n)}</td><td class="l">${r.when}${r.est ? ' <i class="qd" title="date estimée d’après l’historique de publication">e</i>' : ''}</td><td class="l dm">${esc(r.q || '')}</td><td class="wh">${r.eps != null ? num(r.eps, 2) : '—'}</td><td class="dm">${r.lo != null ? num(r.lo, 2) + ' – ' + num(r.hi, 2) : '—'}</td><td>${r.nb ?? '—'}</td><td>${r.last ? `<span class="${cls(r.last.pct)}">${r.last.pct > 0 ? '+' : ''}${num(r.last.pct, 1)} %</span>` : '—'}</td><td class="wh">${px(r.s, r.s.last)}</td><td>${pc(r.s.pct)}</td><td>${big(r.s.mcap)}</td></tr>`; }).join('');
    m.innerHTML = `<div class="tools ttb"><span class="tnar"><input id="eaQ" class="ofld" value="${esc(st.q)}" placeholder="&lt;Filtrer&gt;"></span><span class="dm">${L.length} publications à venir · actions US suivies</span><span class="gsp"></span><span class="dm">e = date estimée</span></div>
      ${pn('Publications de résultats à venir', 'EA', `<div class="tw" style="max-height:calc(100vh - 250px - var(--nwh, 90px))"><table class="t"><thead><tr><th class="l">Titre</th><th class="l">Société</th><th class="l">Moment</th><th class="l">Trimestre</th><th>BPA consensus</th><th>Fourchette</th><th>Analystes</th><th>Dernière surprise</th><th>Cours</th><th>Var. jour</th><th>Capi. ($)</th></tr></thead><tbody>${rows || '<tr><td class="l dm" colspan="11">Aucune publication annoncée.</td></tr>'}</tbody></table></div>`,
        { np: true, lect: 'Dates et consensus du bénéfice par action (BPA) publiés pour le trimestre en cours ; « Dernière surprise » = BPA publié au trimestre précédent contre le consensus d’alors. Clic : estimations du titre (EE). Aucun consensus public pour la BRVM.' })}`;
  } else {
    const t60 = new Date(Date.now() - 60 * 864e5).toISOString().slice(0, 10);
    const L = Object.entries(E).flatMap(([id, x]) => (x.sur || []).map(su => ({ id, s: Q.by[id], d: us(su.d), q: su.q, eps: su.eps, cons: su.cons, pct: su.pct }))).filter(r => r.s && r.d && r.d >= t60 && r.d <= today).sort((a, b) => b.d.localeCompare(a.d));
    m.innerHTML = `<div class="empty">Calcul des réactions de cours…</div>`;
    const react = await Promise.all(L.map(async r => { const S = await series(r.id).catch(() => null); if (!S) return null; const di = +r.d.replace(/-/g, ''); let i = S.x.findIndex(x => x >= di); if (i < 1) return null; const j = Math.min(S.x.length - 1, i + 1); return j > i - 1 ? S.c[j] / S.c[i - 1] - 1 : null; })); if (!alive()) return;
    const beat = L.filter(r => r.pct > 0).length, avg = L.length ? U.mean(L.map(r => r.pct || 0)) : null;
    m.innerHTML = `<div class="tools ttb"><span class="tlab">Publications</span><b class="wh">${L.length}</b><span class="tlab">Au-dessus du consensus</span><b class="up">${beat}</b><span class="dm">(${L.length ? num(beat / L.length * 100, 0) : '—'} %)</span><span class="tlab">Surprise moyenne</span><b class="${cls(avg)}">${avg != null ? num(avg, 1) + ' %' : '—'}</b></div>
      ${pn('Résultats publiés depuis 60 jours', 'EA', `<div class="tw" style="max-height:calc(100vh - 250px - var(--nwh, 90px))"><table class="t"><thead><tr><th class="l">Date</th><th class="l">Titre</th><th class="l">Société</th><th class="l">Trimestre</th><th>BPA publié</th><th>Consensus</th><th>Surprise</th><th class="c"></th><th>Réaction (2 séances)</th></tr></thead><tbody>${L.map((r, i) => `<tr data-sec="${r.id}" data-to="SURP" style="cursor:pointer"><td class="l dm">${fds(r.d)}</td><td class="l"><span class="rn">${i + 1})</span><b class="wh">${r.id}</b></td><td class="l am">${esc(r.s.short || r.s.n)}</td><td class="l dm">${esc(r.q)}</td><td class="wh">${num(r.eps, 2)}</td><td>${num(r.cons, 2)}</td><td><span class="${cls(r.pct)}">${r.pct > 0 ? '+' : ''}${num(r.pct, 1)} %</span></td><td class="wcb" style="width:16%;min-width:90px;position:relative"><span class="z" style="position:absolute;left:50%;top:2px;bottom:2px;border-left:1px solid #5a5a5a"></span><i style="position:absolute;top:4px;bottom:4px;${r.pct >= 0 ? 'left:50%;background:#32c74c' : 'right:50%;background:#ff433d'};width:${Math.min(50, Math.abs(r.pct) / 20 * 50).toFixed(1)}%"></i></td><td>${react[i] != null ? pc(react[i]) : '—'}</td></tr>`).join('') || '<tr><td class="l dm" colspan="9">Aucune publication sur la période.</td></tr>'}</tbody></table></div>`,
        { np: true, lect: 'Surprise = (BPA publié − consensus) ÷ |consensus|. Réaction : variation du cours entre la clôture de la veille de la publication et celle du lendemain (couvre une publication avant l’ouverture comme après la clôture). Barre : surprise (échelle ±20 %).' })}`;
  }
  const q = $('eaQ'); if (q) q.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); st.q = q.value.trim(); render(); } };
};

/* ------------------------------------------------------------------ Alertes personnelles (onglet de ALRT) : seuils de cours, de variation,
   de RSI, de moyenne mobile, de plus haut / bas 52 semaines, de rendement ; vérifiées à chaque relevé, enregistrées dans ce navigateur */
const MA_K = 'fqt_alerts_v1';
const maLoad = () => { try { const a = JSON.parse(localStorage.getItem(MA_K) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } };
const maSave = A => { try { localStorage.setItem(MA_K, JSON.stringify(A)); } catch (e) { /* stockage indisponible */ } };
const MA_T = {
  pxu: ['Cours ≥', s => s.last, (v, t) => v >= t, true], pxd: ['Cours ≤', s => s.last, (v, t) => v <= t, true],
  up: ['Hausse du jour ≥ (%)', s => s.pct != null ? s.pct * 100 : null, (v, t) => v >= t, true], dn: ['Baisse du jour ≥ (%)', s => s.pct != null ? -s.pct * 100 : null, (v, t) => v >= t, true],
  rsiu: ['RSI 14 ≥', s => s.rsi, (v, t) => v >= t, true], rsid: ['RSI 14 ≤', s => s.rsi, (v, t) => v <= t, true],
  mau: ['Cours au-dessus de la MM 200', s => s.sma200 ? (s.last / s.sma200 - 1) * 100 : null, v => v > 0, false], mad: ['Cours sous la MM 200', s => s.sma200 ? (s.last / s.sma200 - 1) * 100 : null, v => v < 0, false],
  hi: ['Nouveau plus haut 52 semaines', s => s.hi52 ? (s.last / s.hi52 - 1) * 100 : null, v => v >= -1e-9, false], lo: ['Nouveau plus bas 52 semaines', s => s.lo52 ? (s.last / s.lo52 - 1) * 100 : null, v => v <= 1e-9, false],
  yld: ['Rendement du dividende ≥ (%)', s => s.yld != null ? s.yld * 100 : null, (v, t) => v >= t, true],
};
function maCheck(notify = true) {
  if (!Q.sum || !Q.by) return; const A = maLoad(); let ch = false, fired = [];
  for (const a of A) { const s = Q.by[a.id], T = MA_T[a.k]; if (!s || !T || a.hit) continue; const v = T[1](s); if (v == null || !isFinite(v)) continue; if (T[2](v, a.v)) { a.hit = Date.now(); a.hv = v; ch = true; fired.push(a); } }
  if (ch) maSave(A);
  if (notify && fired.length && typeof Notification !== 'undefined' && Notification.permission === 'granted') for (const a of fired) { try { new Notification(`Alerte ${a.id}`, { body: `${MA_T[a.k][0]}${MA_T[a.k][3] ? ' ' + num(a.v, 2) : ''} · ${px(Q.by[a.id], Q.by[a.id].last)}` }); } catch (e) { /* notifications refusées */ } }
  const n = A.filter(a => a.hit && !a.seen).length, b = document.getElementById('alB'); if (b) { b.hidden = !n; b.textContent = `🔔 ${n}`; b.title = `${n} alerte(s) déclenchée(s)`; }
}
setInterval(() => maCheck(true), 60000); setTimeout(() => maCheck(false), 4000);
document.addEventListener('click', e => { if (e.target && e.target.id === 'alB') { ST.tab.ALRT = 'mine'; go('ALRT'); } });
const ALRT_OLD = PAGES.ALRT;
PAGES.ALRT = async (m, alive) => {
  const tab = tabState('ALRT', 'sys'); setTabs([['sys', 'Alertes fondamentales'], ['mine', 'Mes alertes']], tab, k => { ST.tab.ALRT = k; render(); });
  if (tab !== 'mine') return ALRT_OLD(m, alive);
  setTitle('Alert Monitor · Mes alertes'); maCheck(false); const A = maLoad(); A.forEach(a => { if (a.hit) a.seen = true; }); maSave(A); maCheck(false);
  const st = ST.ma = ST.ma || { k: 'pxu' };
  m.innerHTML = `<div class="tools ttb"><span class="tlab">Titre</span><input class="ofld" id="maT" placeholder="SNTS, AAPL…" autocomplete="off" style="width:140px"><span class="tlab">Condition</span><select class="ofld" id="maK">${Object.entries(MA_T).map(([k, t]) => `<option value="${k}" ${st.k === k ? 'selected' : ''}>${t[0]}</option>`).join('')}</select>
      <span class="tlab">Seuil</span><input class="ofld" id="maV" style="width:90px" ${MA_T[st.k][3] ? '' : 'disabled placeholder="—"'}><button class="tb on" id="maA">Ajouter l’alerte</button><span class="gsp"></span>
      ${typeof Notification !== 'undefined' && Notification.permission !== 'granted' ? '<button class="tb" id="maN">Activer les notifications du navigateur</button>' : '<span class="dm">notifications du navigateur actives</span>'}</div>
    ${pn(`Mes alertes · ${A.length}`, 'ALRT', A.length ? `<table class="t"><thead><tr><th class="l">Titre</th><th class="l">Nom</th><th class="l">Condition</th><th>Seuil</th><th>Valeur actuelle</th><th>Cours</th><th class="l">État</th><th></th></tr></thead><tbody>${A.map((a, i) => { const s = Q.by[a.id], T = MA_T[a.k]; const v = s && T ? T[1](s) : null;
        return `<tr data-sec="${esc(a.id)}" data-to="GP" style="cursor:pointer"><td class="l"><span class="rn">${i + 1})</span><b class="wh">${esc(a.id)}</b></td><td class="l am">${esc(s ? s.short || s.n : '—')}</td><td class="l">${T ? T[0] : '—'}</td><td>${T && T[3] ? num(a.v, 2) : '—'}</td><td>${v != null ? num(v, 2) + (['up', 'dn', 'mau', 'mad', 'hi', 'lo', 'yld'].includes(a.k) ? ' %' : '') : '—'}</td><td class="wh">${s ? px(s, s.last) : '—'}</td>
          <td class="l">${a.hit ? `<span class="dn">déclenchée</span> <span class="dm">${new Date(a.hit).toLocaleString('fr-FR', { timeZone: 'Africa/Abidjan', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>` : '<span class="up">armée</span>'}</td>
          <td class="l">${a.hit ? `<span class="pdx" data-mre="${i}" title="réarmer">↻</span>` : ''} <span class="pdx" data-mdel="${i}" title="supprimer">✕</span></td></tr>`; }).join('')}</tbody></table>` : '<div class="empty">Aucune alerte. Choisissez un titre, une condition et un seuil.</div>',
      { np: true, lect: 'Les alertes sont vérifiées à chaque relevé (toutes les 15 minutes) tant que le terminal est ouvert dans ce navigateur ; une alerte déclenchée allume la cloche en haut à droite et, si vous l’avez permis, envoie une notification. ↻ pour la réarmer. Clic sur une ligne : graphique du titre.' })}`;
  const T = $('maT'); T.oninput = () => { const L = searchSecs(T.value).slice(0, 10); if (!L.length) { ddClose(); return; } ddOpen(T, L.map(s => ({ code: s.id, l: esc(s.short || s.n), run: () => { T.value = s.id; $('maV').focus(); } }))); };
  $('maK').onchange = e => { st.k = e.target.value; render(); };
  const add = () => { const s = Q.by[T.value.trim().toUpperCase()] || searchSecs(T.value)[0], v = parseFloat(String($('maV').value).replace(/\s/g, '').replace(',', '.')); if (!s || (MA_T[st.k][3] && !isFinite(v))) { T.focus(); return; }
    const B = maLoad(); B.push({ id: s.id, k: st.k, v: MA_T[st.k][3] ? v : null, t: Date.now() }); maSave(B); maCheck(false); render(); };
  $('maA').onclick = add; $('maV').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); add(); } };
  const nb = $('maN'); if (nb) nb.onclick = () => Notification.requestPermission().then(() => render());
  m.querySelectorAll('[data-mdel]').forEach(b => b.onclick = e => { e.stopPropagation(); const B = maLoad(); B.splice(+b.dataset.mdel, 1); maSave(B); maCheck(false); render(); });
  m.querySelectorAll('[data-mre]').forEach(b => b.onclick = e => { e.stopPropagation(); const B = maLoad(), a = B[+b.dataset.mre]; if (a) { a.hit = null; a.seen = false; a.hv = null; } maSave(B); render(); });
};

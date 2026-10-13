/* ================= FQT — ECO (calendrier économique façon Bloomberg) et ECST (statistiques économiques mondiales) ================= */

/* ---------- drapeaux simplifiés en SVG (aucune ressource externe) ---------- */
const FLAG_N = { US: 'États-Unis', EU: 'Zone euro', GB: 'Royaume-Uni', JP: 'Japon', CN: 'Chine', DE: 'Allemagne', FR: 'France', IT: 'Italie', ES: 'Espagne', CA: 'Canada', AU: 'Australie', CH: 'Suisse', IN: 'Inde', BR: 'Brésil',
  ZA: 'Afrique du Sud', NG: 'Nigeria', GH: 'Ghana', CI: 'Côte d’Ivoire', SN: 'Sénégal', KE: 'Kenya', MA: 'Maroc', EG: 'Égypte' };
function flagSVG(c, w = 22, h = 14) {
  const v3 = (a, b, d) => `<rect width="7.34" height="14" fill="${a}"/><rect x="7.33" width="7.34" height="14" fill="${b}"/><rect x="14.66" width="7.34" height="14" fill="${d}"/>`;
  const h3 = (a, b, d) => `<rect width="22" height="4.67" fill="${a}"/><rect y="4.66" width="22" height="4.68" fill="${b}"/><rect y="9.33" width="22" height="4.67" fill="${d}"/>`;
  const star = (cx, cy, r, col) => { let p = ''; for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr = k % 2 ? r * .42 : r; p += `${(cx + rr * Math.cos(a)).toFixed(2)},${(cy + rr * Math.sin(a)).toFixed(2)} `; } return `<polygon points="${p}" fill="${col}"/>`; };
  const uj = (W, H) => `<rect width="${W}" height="${H}" fill="#012169"/><path d="M0 0L${W} ${H}M${W} 0L0 ${H}" stroke="#fff" stroke-width="${H / 4.7}"/><path d="M0 0L${W} ${H}M${W} 0L0 ${H}" stroke="#c8102e" stroke-width="${H / 14}"/><path d="M${W / 2} 0V${H}M0 ${H / 2}H${W}" stroke="#fff" stroke-width="${H / 3.2}"/><path d="M${W / 2} 0V${H}M0 ${H / 2}H${W}" stroke="#c8102e" stroke-width="${H / 5.6}"/>`;
  let b = '';
  switch (c) {
    case 'US': b = '<rect width="22" height="14" fill="#fff"/>' + [0, 2, 4, 6, 8, 10, 12].map(k => `<rect y="${k * 14 / 13}" width="22" height="${14 / 13}" fill="#b22234"/>`).join('') + '<rect width="9.5" height="7.54" fill="#3c3b6e"/>' + [[2, 1.6], [4.7, 1.6], [7.4, 1.6], [3.3, 3.8], [6, 3.8], [2, 6], [4.7, 6], [7.4, 6]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r=".55" fill="#fff"/>`).join(''); break;
    case 'EU': b = '<rect width="22" height="14" fill="#003399"/>' + Array.from({ length: 12 }, (_, k) => { const a = k * Math.PI / 6; return `<circle cx="${(11 + 4.3 * Math.cos(a)).toFixed(2)}" cy="${(7 + 4.3 * Math.sin(a)).toFixed(2)}" r=".7" fill="#ffcc00"/>`; }).join(''); break;
    case 'GB': b = uj(22, 14); break;
    case 'JP': b = '<rect width="22" height="14" fill="#fff"/><circle cx="11" cy="7" r="4.2" fill="#bc002d"/>'; break;
    case 'CN': b = '<rect width="22" height="14" fill="#de2910"/>' + star(4.2, 4, 2.6, '#ffde00') + star(8.2, 1.6, .8, '#ffde00') + star(9.6, 3.4, .8, '#ffde00') + star(9.6, 5.8, .8, '#ffde00') + star(8.2, 7.4, .8, '#ffde00'); break;
    case 'DE': b = h3('#000', '#dd0000', '#ffce00'); break;
    case 'FR': b = v3('#0055a4', '#fff', '#ef4135'); break;
    case 'IT': b = v3('#009246', '#fff', '#ce2b37'); break;
    case 'ES': b = '<rect width="22" height="14" fill="#aa151b"/><rect y="3.5" width="22" height="7" fill="#f1bf00"/>'; break;
    case 'CA': b = '<rect width="22" height="14" fill="#fff"/><rect width="5.5" height="14" fill="#d52b1e"/><rect x="16.5" width="5.5" height="14" fill="#d52b1e"/>' + star(11, 6.6, 3.4, '#d52b1e') + '<rect x="10.6" y="8.5" width=".8" height="3" fill="#d52b1e"/>'; break;
    case 'AU': b = '<rect width="22" height="14" fill="#00008b"/>' + `<g>${uj(11, 7)}</g>` + star(5.5, 10.6, 1.5, '#fff') + star(17, 3, .9, '#fff') + star(14.5, 6.5, .9, '#fff') + star(19.5, 6, .9, '#fff') + star(17, 11.3, .9, '#fff'); break;
    case 'CH': b = '<rect width="22" height="14" fill="#da291c"/><rect x="9.6" y="2.6" width="2.8" height="8.8" fill="#fff"/><rect x="6.6" y="5.6" width="8.8" height="2.8" fill="#fff"/>'; break;
    case 'IN': b = h3('#ff9933', '#fff', '#138808') + '<circle cx="11" cy="7" r="1.8" fill="none" stroke="#000080" stroke-width=".6"/>'; break;
    case 'BR': b = '<rect width="22" height="14" fill="#009c3b"/><polygon points="11,1.4 20.4,7 11,12.6 1.6,7" fill="#ffdf00"/><circle cx="11" cy="7" r="3.1" fill="#002776"/>'; break;
    case 'ZA': b = '<rect width="22" height="7" fill="#de3831"/><rect y="7" width="22" height="7" fill="#002395"/><path d="M0 0L9 7L0 14M9 7H22" stroke="#fff" stroke-width="4.6" fill="none"/><path d="M0 0L9 7L0 14M9 7H22" stroke="#007a4d" stroke-width="2.8" fill="none"/><polygon points="0,1.6 6.6,7 0,12.4" fill="#ffb612"/><polygon points="0,2.9 5,7 0,11.1" fill="#000"/>'; break;
    case 'NG': b = v3('#008751', '#fff', '#008751'); break;
    case 'GH': b = h3('#ce1126', '#fcd116', '#006b3f') + star(11, 7, 2.2, '#000'); break;
    case 'CI': b = v3('#f77f00', '#fff', '#009e60'); break;
    case 'SN': b = v3('#00853f', '#fdef42', '#e31b23') + star(11, 7, 2.2, '#00853f'); break;
    case 'KE': b = '<rect width="22" height="4.2" fill="#000"/><rect y="4.2" width="22" height="5.6" fill="#fff"/><rect y="5" width="22" height="4" fill="#bb0000"/><rect y="9.8" width="22" height="4.2" fill="#006600"/><ellipse cx="11" cy="7" rx="2" ry="4" fill="#bb0000" stroke="#000" stroke-width=".5"/>'; break;
    case 'MA': b = '<rect width="22" height="14" fill="#c1272d"/><polygon points="11,3.2 12.3,7.8 8.4,5 13.6,5 9.7,7.8" fill="none" stroke="#006233" stroke-width=".7"/>'; break;
    case 'EG': b = h3('#ce1126', '#fff', '#000') + '<rect x="10" y="5.6" width="2" height="2.8" fill="#c09300"/>'; break;
    default: b = '<rect width="22" height="14" fill="#444"/>';
  }
  return `<svg class="flg" width="${w}" height="${h}" viewBox="0 0 22 14" aria-label="${esc(FLAG_N[c] || c)}"><title>${esc(FLAG_N[c] || c)}</title>${b}</svg>`;
}
/* pertinence : 4 barres croissantes (haute = 4, moyenne = 3, faible = 1) */
const relBars = i => { const lit = i >= 1 ? 4 : i === 0 ? 3 : 1; return `<svg class="rel" width="14" height="12" viewBox="0 0 14 12" aria-label="importance">${[0, 1, 2, 3].map(k => `<rect x="${k * 3.5}" y="${9 - k * 2.6}" width="2.4" height="${3 + k * 2.6}" fill="${k < lit ? (lit === 4 ? '#f9a33a' : '#e6e6e6') : '#3a3a3a'}"/>`).join('')}</svg>`; };

/* ---------- ECO : calendrier économique ---------- */
const ECO_REG = [['MAJ', 'Principales économies', ['US', 'EU', 'GB', 'JP', 'CN']], ['ALL', 'Monde (22 pays et zones)', null], ['US', 'États-Unis', ['US']], ['EZ', 'Zone euro', ['EU', 'DE', 'FR', 'IT', 'ES']],
  ['EUR', 'Europe', ['EU', 'DE', 'FR', 'IT', 'ES', 'GB', 'CH']], ['AM', 'Amériques', ['US', 'CA', 'BR']], ['AS', 'Asie-Pacifique', ['JP', 'CN', 'IN', 'AU']], ['AF', 'Afrique', ['ZA', 'NG', 'GH', 'CI', 'SN', 'KE', 'MA', 'EG']], ['UEMOA', 'UEMOA (Côte d’Ivoire, Sénégal)', ['CI', 'SN']]];
const ECO_CAT = { mny: 'Politique monétaire', prce: 'Prix', bsnss: 'Activité / enquêtes', gov: 'État / banque centrale', bnd: 'Adjudications', hse: 'Logement', enrg: 'Énergie', cnsm: 'Consommation', trd: 'Commerce extérieur', lbr: 'Emploi', mrkt: 'Marchés', gdp: 'PIB' };
/* publications US reliées à une série FRED de ECWB / ECST (historique long dans le panneau de détail) */
const ECO_FRED = [[/^Non Farm Payrolls$/i, 'PAYEMS'], [/^Unemployment Rate$/i, 'UNRATE'], [/^Initial Jobless Claims$/i, 'ICSA'], [/^(Core )?Inflation Rate (YoY|MoM)$|^CPI$/i, 'CPIAUCSL'], [/^Core Inflation Rate/i, 'CPILFESL'],
  [/^Core PCE Price Index/i, 'PCEPILFE'], [/^PPI (MoM|YoY)$/i, 'PPIACO'], [/^Retail Sales (MoM|YoY)$/i, 'RSAFS'], [/^Industrial Production (MoM|YoY)$/i, 'INDPRO'], [/^Housing Starts$/i, 'HOUST'], [/Michigan Consumer Sentiment/i, 'UMCSENT'],
  [/^JOLTs Job Openings$/i, 'JTSJOL'], [/^GDP Growth Rate/i, 'GDPC1'], [/^Fed Interest Rate Decision$/i, 'DFF'], [/^MBA 30-Year Mortgage Rate$|^30-Year Mortgage Rate/i, 'MORTGAGE30US'], [/^S&P\/Case-Shiller/i, 'CSUSHPINSA']];
function ecoVal(r, v) { if (v == null || v === '') return '<span class="dm">—</span>'; if (typeof v !== 'number') return esc(String(v));
  const dd = Math.min(3, Math.max(...[r.a, r.f, r.pr].filter(x => typeof x === 'number').map(x => { const s = String(x); return s.includes('.') ? s.split('.')[1].length : 0; })));
  const sc = { K: ' k', M: ' M', B: ' Md', T: ' T' }[r.sc] || '', u = r.u || ''; const cur = /^[$€£¥]$|^[A-Z]{3}$/.test(u) ? u : '';
  return num(v, dd) + (u === '%' ? '%' : '') + sc + (cur ? (sc ? '' : ' ') + cur : '') + (u && u !== '%' && !cur ? ' ' + esc(u) : ''); }
const ecoDT = d => { const t = new Date(d + ':00Z'); return { day: t.toLocaleDateString('fr-FR', { timeZone: 'Africa/Abidjan', day: '2-digit', month: '2-digit' }), hm: t.toLocaleTimeString('fr-FR', { timeZone: 'Africa/Abidjan', hour: '2-digit', minute: '2-digit' }), wd: t.toLocaleDateString('fr-FR', { timeZone: 'Africa/Abidjan', weekday: 'long', day: 'numeric', month: 'long' }), ms: t.getTime(), key: d.slice(0, 10) }; };
const ymd = t => new Date(t).toISOString().slice(0, 10);
const monday = t => { const d = new Date(t); const k = (d.getUTCDay() + 6) % 7; d.setUTCDate(d.getUTCDate() - k); d.setUTCHours(0, 0, 0, 0); return d.getTime(); };

PAGES.ECO = async (m, alive) => {
  setTitle('Economic Calendars'); const C = await getJSON('calendar.json').catch(() => null); if (!alive()) return;
  if (!C || !C.rows || !C.rows.length) { m.innerHTML = pn('Calendrier économique', 'ECO', '<div class="empty">Calendrier en attente du prochain relevé (toutes les 15 minutes).</div>'); return; }
  const now = Date.now(), wk = monday(now), DAY = 864e5;
  const st = ST.eco2 = ST.eco2 || { reg: 'MAJ', imp: -1, view: 'A', d0: ymd(wk), d1: ymd(wk + 6 * DAY), q: '', sel: null };
  const R = ECO_REG.find(r => r[0] === st.reg) || ECO_REG[0], cset = R[2] ? new Set(R[2]) : null, q = st.q.trim().toLowerCase();
  const rows = C.rows.map(r => Object.assign({ T: ecoDT(r.d) }, r)).filter(r => (!cset || cset.has(r.c)) && r.i >= st.imp && r.T.key >= st.d0 && r.T.key <= st.d1 && (!q || (r.t + ' ' + (FLAG_N[r.c] || '') + ' ' + r.c + ' ' + (r.ind || '')).toLowerCase().includes(q)));
  const regMenu = () => [{ h: 'Calendriers' }].concat(ECO_REG.map(([k, l, cs]) => ({ l: (st.reg === k ? '● ' : '○ ') + l + (cs ? ` <span class="dm">${cs.join(' ')}</span>` : ''), run: () => { st.reg = k; render(); } })));
  const impMenu = () => [{ h: 'Importance minimale' }].concat([[-1, 'Toutes les publications'], [0, 'Moyenne et haute'], [1, 'Haute seulement']].map(([k, l]) => ({ l: (st.imp === k ? '● ' : '○ ') + l, run: () => { st.imp = k; render(); } })));
  const per = (a, b) => { st.d0 = ymd(a); st.d1 = ymd(b); render(); };
  setActs([{ n: 1, l: 'Calendriers', menu: regMenu }, { n: 2, l: 'Importance', menu: impMenu },
    { n: 3, l: 'Période', menu: () => [{ h: 'Période' }, { l: 'Aujourd’hui', run: () => per(now, now) }, { l: 'Cette semaine', run: () => per(wk, wk + 6 * DAY) }, { l: 'Semaine dernière', run: () => per(wk - 7 * DAY, wk - DAY) }, { l: 'Semaine prochaine', run: () => per(wk + 7 * DAY, wk + 13 * DAY) },
      { l: 'Toute la fenêtre disponible', run: () => { st.d0 = C.from; st.d1 = C.to; render(); } }] }]);
  const nextI = rows.findIndex(r => r.T.ms >= now - 5 * 60e3);
  const sel = st.sel != null ? C.rows.find(r => r.d + r.c + r.t === st.sel) : null;
  const tbl = rows.length ? `<table class="t eco"><thead><tr><th></th><th class="l">Date</th><th class="l">Heure</th><th class="l" colspan="2">Pays</th><th>R</th><th class="l">Événement</th><th class="l">Période</th><th title="Prévision du consensus publiée avant le chiffre">Prév.</th><th>Réel</th><th>Préc.</th></tr></thead><tbody>${rows.map((r, k) => {
      const fut = r.T.ms > now, id = r.d + r.c + r.t;
      return `<tr class="${fut ? 'fut' : ''}${k === nextI ? ' nx' : ''}${st.sel === id ? ' hl' : ''}" data-ev="${esc(id)}" data-n="${k + 1}"><td class="no">${k + 1})</td><td class="l am">${r.T.day}</td><td class="l am">${r.T.hm}</td><td class="fl">${flagSVG(r.c)}</td><td class="l cc">${r.c}</td><td>${relBars(r.i)}</td><td class="l ev">${esc(r.t)}</td><td class="l am">${esc(r.p || '')}</td><td>${ecoVal(r, r.f)}</td><td class="wh b">${ecoVal(r, r.a)}</td><td>${ecoVal(r, r.pr)}</td></tr>`; }).join('')}</tbody></table>`
    : '<div class="empty">Aucune publication pour ces critères.</div>';
  /* vue hebdomadaire : une colonne par jour */
  const week = () => { const a = Date.parse(st.d0 + 'T00:00:00Z'), b = Date.parse(st.d1 + 'T00:00:00Z'), days = []; for (let t = a; t <= b && days.length < 14; t += DAY) days.push(ymd(t));
    const by = {}; rows.forEach(r => (by[r.T.key] = by[r.T.key] || []).push(r)); const show = days.filter((d, i) => by[d] || new Date(d).getUTCDay() % 6);
    return `<div class="ecw" style="grid-template-columns:repeat(${show.length},minmax(0,1fr))">${show.map(d => `<div class="ecd${d === ymd(now) ? ' td' : ''}"><div class="ecdh">${new Date(d + 'T12:00:00Z').toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: '2-digit' })}</div>${(by[d] || []).map(r => `<div class="ecx${r.T.ms > now ? ' fut' : ''}" data-ev="${esc(r.d + r.c + r.t)}" title="${esc(r.t)}"><span class="am">${r.T.hm}</span>${flagSVG(r.c, 16, 10)}${relBars(r.i)}<span class="t">${esc(r.t)}</span>${r.a != null ? `<span class="wh">${ecoVal(r, r.a)}</span>` : r.f != null ? `<span class="dm">${ecoVal(r, r.f)}</span>` : ''}</div>`).join('') || '<div class="dm" style="padding:4px">—</div>'}</div>`).join('')}</div>`; };
  const tools = `<input class="ofld" id="ecQ" placeholder="Saisir un pays ou un événement" value="${esc(st.q)}" style="width:230px"><button class="tb" id="ecBr" data-n="6"><em>6)</em> Parcourir ▾</button><span class="eclk" id="ecClk"></span>
    <span class="gsp"></span><input class="ofld dt" id="ecD0" value="${fds(st.d0)}"><span class="cal">▦</span><span class="dm">–</span><input class="ofld dt" id="ecD1" value="${fds(st.d1)}"><span class="cal">▦</span>
    <span class="tlab">Vue</span><label class="erad"><input type="radio" name="ecv" value="A" ${st.view === 'A' ? 'checked' : ''}><i></i>Agenda</label><label class="erad"><input type="radio" name="ecv" value="W" ${st.view === 'W' ? 'checked' : ''}><i></i>Hebdomadaire</label>`;
  const tools2 = `<select class="ofld" id="ecReg">${ECO_REG.map(([k, l]) => `<option value="${k}" ${st.reg === k ? 'selected' : ''}>${l}</option>`).join('')}</select><select class="ofld dk" id="ecImp">${[[-1, 'Toutes importances'], [0, 'Moyenne et haute'], [1, 'Haute seulement']].map(([k, l]) => `<option value="${k}" ${st.imp === k ? 'selected' : ''}>${l}</option>`).join('')}</select>
    ${[['Aujourd’hui', 0, 0], ['Semaine dernière', -7, -1], ['Cette semaine', 0, 6], ['Semaine prochaine', 7, 13]].map(([l, a, b], i) => `<button class="tb alt" data-per="${i}">${l}</button>`).join('')}<span class="gsp"></span><span class="dm">${rows.length} publication${rows.length > 1 ? 's' : ''} · heure GMT (Abidjan) · relevé ${new Date(C.ts * 1000).toLocaleString('fr-FR', { timeZone: 'Africa/Abidjan', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>`;
  m.innerHTML = `<div class="tools ecot">${tools}</div><div class="tools ecot2">${tools2}</div>
    <div class="grid ${sel ? 'side' : ''}"><div class="pn"><div class="tw" id="ecTw" style="max-height:calc(100vh - 262px - var(--nwh, 90px))">${st.view === 'W' ? week() : tbl}</div>
      <div class="lect">Prév. = prévision du consensus publiée avant le chiffre · Réel = chiffre publié · Préc. = chiffre de la période précédente. Fond gris = à venir ; ligne orange = prochaine publication. R = importance pour les marchés. Calendrier : TradingView.</div></div>
      ${sel ? `<div class="grid" style="align-content:start" id="ecDet"></div>` : ''}</div>`;
  const clk = () => { const e = $('ecClk'); if (!e || !alive()) return false; e.textContent = new Date().toLocaleTimeString('fr-FR', { timeZone: 'Africa/Abidjan' }) + ' GMT'; return true; }; clk(); const iv = setInterval(() => { if (!clk()) clearInterval(iv); }, 1000);
  $('ecQ').oninput = e => { clearTimeout(ST._ecq); ST._ecq = setTimeout(() => { st.q = e.target.value; render(); setTimeout(() => { const i = $('ecQ'); if (i) { i.focus(); i.setSelectionRange(i.value.length, i.value.length); } }, 0); }, 350); };
  $('ecBr').onclick = e => ddOpen(e.currentTarget, [{ h: 'Pays et zones' }].concat(Object.keys(FLAG_N).map(c => ({ code: c, l: `${flagSVG(c, 16, 10)} ${esc(FLAG_N[c])}`, run: () => { st.q = FLAG_N[c]; st.reg = 'ALL'; render(); } }))));
  $('ecReg').onchange = e => { st.reg = e.target.value; render(); }; $('ecImp').onchange = e => { st.imp = +e.target.value; render(); };
  m.querySelectorAll('[data-per]').forEach(b => b.onclick = () => { const [, a, z] = [['', 0, 0], ['', -7, -1], ['', 0, 6], ['', 7, 13]][+b.dataset.per]; const base = +b.dataset.per === 0 ? Date.parse(ymd(now) + 'T00:00:00Z') : wk; per(base + a * DAY, base + z * DAY); });
  const dIn = () => { const a = parseDMY($('ecD0').value), b = parseDMY($('ecD1').value); if (!a || !b || b < a) { toast('Dates au format jj/mm/aaaa.'); return; } st.d0 = i2s(a); st.d1 = i2s(b); render(); };
  ['ecD0', 'ecD1'].forEach(id => { $(id).onchange = dIn; $(id).onkeydown = e => { if (e.key === 'Enter') dIn(); }; });
  m.querySelectorAll('input[name="ecv"]').forEach(r => r.onchange = () => { st.view = r.value; render(); });
  m.querySelectorAll('[data-ev]').forEach(tr => tr.onclick = () => { st.sel = st.sel === tr.dataset.ev ? null : tr.dataset.ev; render(); });
  /* place la prochaine publication en haut de la liste (comme le terminal) */
  const tw = $('ecTw'), nx = tw && tw.querySelector('tr.nx'); if (nx && st.view === 'A' && !sel) tw.scrollTop = Math.max(0, nx.offsetTop - 26 * 4);
  else if (sel && tw) { const h = tw.querySelector('tr.hl'); if (h) tw.scrollTop = Math.max(0, h.offsetTop - 26 * 4); }
  if (!sel) return;
  /* panneau de détail : la publication, ses occurrences dans la fenêtre et, pour les États-Unis, la série FRED liée */
  const T = ecoDT(sel.d), same = C.rows.filter(r => r.c === sel.c && r.t === sel.t).sort((a, b) => b.d.localeCompare(a.d)), fred = sel.c === 'US' ? (ECO_FRED.find(([rx]) => rx.test(sel.t)) || [])[1] : null;
  const surpr = typeof sel.a === 'number' && typeof sel.f === 'number' ? sel.a - sel.f : null;
  $('ecDet').innerHTML = pn(`${flagSVG(sel.c)} ${esc(sel.t)}`, 'ECO', `<div class="kv2"><span>Pays / zone</span><b>${esc(FLAG_N[sel.c] || sel.c)}</b><span>Publication</span><b>${T.wd}, ${T.hm} GMT</b><span>Période</span><b>${esc(sel.p || '—')}</b><span>Catégorie</span><b>${esc(ECO_CAT[sel.cat] || sel.cat || '—')}</b>
      <span>Importance</span><b>${['Faible', 'Moyenne', 'Haute'][sel.i + 1]} ${relBars(sel.i)}</b><span>Prévision (consensus)</span><b>${ecoVal(sel, sel.f)}</b><span>Réel</span><b class="wh">${ecoVal(sel, sel.a)}</b><span>Précédent</span><b>${ecoVal(sel, sel.pr)}</b>
      ${surpr != null ? `<span>Écart au consensus</span><b class="${cls(surpr)}">${surpr > 0 ? '+' : ''}${ecoVal(sel, surpr)}</b>` : ''}${sel.src ? `<span>Organisme</span><b>${esc(sel.src)}</b>` : ''}${sel.ind ? `<span>Indicateur</span><b>${esc(sel.ind)}</b>` : ''}</div>`,
    { tools: `<button class="tb" id="ecX">Fermer ✕</button>${fred ? `<button class="tb" data-fn="ECST">Série ${fred} dans ECST</button>` : ''}` })
    + (same.length > 1 ? pn('Autres dates dans la fenêtre', 'ECO', `<table class="t"><thead><tr><th class="l">Date</th><th class="l">Période</th><th>Prév.</th><th>Réel</th><th>Préc.</th></tr></thead><tbody>${same.map(r => { const t = ecoDT(r.d); return `<tr${r === sel ? ' class="hl"' : ''}><td class="l">${t.day} ${t.hm}</td><td class="l am">${esc(r.p || '')}</td><td>${ecoVal(r, r.f)}</td><td class="wh">${ecoVal(r, r.a)}</td><td>${ecoVal(r, r.pr)}</td></tr>`; }).join('')}</tbody></table>`, { np: true }) : '')
    + (fred ? pn(`Historique de la série ${fred} (FRED)`, 'ECST', cvb('ecF', 220), { lect: 'Niveau de la série publiée par la Réserve fédérale de St. Louis ; zones grises = récessions.' }) : '');
  $('ecX').onclick = () => { st.sel = null; render(); };
  if (fred) { const E = await getJSON('eco.json').catch(() => null); if (!alive() || !E || !E.s[fred]) { const e = $('ecF'); if (e) e.innerHTML = '<div class="empty">Série indisponible.</div>'; return; } ST.ecst = Object.assign(ST.ecst || {}, { geo: 'US', sel: 'F:' + fred });
    const [d, v] = E.s[fred]; const ch = new TSChart($('ecF'), { panes: [{ h: 1 }] }); ch.set({ x: d, series: [{ y: v, color: CL.amber, label: fred, fmt: y => num(y, 2) }] }, [Math.max(0, d.findIndex(z => z >= d[d.length - 1] - 100000)), d.length - 1]); }
};

/* ---------- ECST : statistiques économiques mondiales (arbre des concepts, comme le terminal) ---------- */
const ECST_US = [['Comptes nationaux (PIB)', ['GDPC1']], ['Prix', ['CPIAUCSL', 'CPILFESL', 'PCEPILFE', 'PPIACO', 'T10YIE', 'T5YIFR']], ['Marché du travail', ['UNRATE', 'PAYEMS', 'ICSA', 'JTSJOL', 'SAHMREALTIME']],
  ['Commerce de détail', ['RSAFS']], ['Secteur industriel', ['INDPRO']], ['Logement et immobilier', ['HOUST', 'CSUSHPINSA', 'MORTGAGE30US']], ['Enquêtes et indicateurs de cycle', ['UMCSENT', 'USREC', 'RECPROUSM156N']],
  ['Marché monétaire', ['DFEDTARU', 'DFEDTARL', 'IORB', 'DPCREDIT', 'DPRIME', 'SOFR', 'OBFR', 'DTB4WK', 'DTB3', 'DTB6', 'DTB1YR', 'DCPF3M', 'DCPN3M', 'ECBDFR', 'ECBMRRFR']], ['Secteur monétaire', ['DFF', 'WALCL', 'WTREGEN', 'RRPONTSYD', 'NETLIQ', 'M2SL']], ['Taux du Trésor', ['DGS1MO', 'DGS3MO', 'DGS6MO', 'DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS7', 'DGS10', 'DGS20', 'DGS30', 'DFII10', 'T10Y2Y', 'T10Y3M']],
  ['Crédit', ['BAMLH0A0HYM2', 'BAMLC0A0CM', 'BAMLH0A3HYC', 'BAA10Y', 'AAA10Y', 'HYIG']], ['Conditions financières et volatilité', ['STLFSI4', 'NFCI', 'VIXCLS', 'VXNCLS', 'OVXCLS', 'GVZCLS']], ['Change', ['DTWEXBGS', 'DEXUSEU']], ['Marchés', ['SP500', 'NASDAQCOM', 'DCOILWTICO']]];
const ECST_WB = [['Comptes nationaux', ['NY.GDP.MKTP.KD.ZG', 'NY.GDP.MKTP.CD', 'NY.GDP.PCAP.CD', 'NY.GDP.PCAP.PP.CD', 'NE.GDI.TOTL.ZS']], ['Prix', ['FP.CPI.TOTL.ZG']],
  ['Population et conditions de vie', ['SP.POP.TOTL', 'SP.POP.GROW', 'SP.URB.TOTL.IN.ZS', 'SP.DYN.LE00.IN', 'SI.POV.DDAY', 'SL.UEM.TOTL.ZS']], ['Finances publiques', ['GC.DOD.TOTL.GD.ZS', 'GC.REV.XGRT.GD.ZS']],
  ['Commerce extérieur et balance des paiements', ['BN.CAB.XOKA.GD.ZS', 'NE.EXP.GNFS.ZS', 'NE.IMP.GNFS.ZS', 'BX.KLT.DINV.WD.GD.ZS', 'BX.TRF.PWKR.DT.GD.ZS']], ['Monnaie et crédit', ['FM.LBL.BMNY.ZG', 'FS.AST.PRVT.GD.ZS', 'FR.INR.LEND']],
  ['Structure de l’économie', ['NV.AGR.TOTL.ZS', 'NV.IND.TOTL.ZS', 'NV.SRV.TOTL.ZS']], ['Numérique et énergie', ['IT.CEL.SETS.P2', 'IT.NET.USER.ZS', 'EG.ELC.ACCS.ZS']]];
const ECST_GEO = [['US', 'États-Unis', 'US'], ['UEMOA', 'UEMOA (Union)', 'CI'], ['CIV', 'Côte d’Ivoire', 'CI', 'Côte d\'Ivoire'], ['SEN', 'Sénégal', 'SN', 'Sénégal'], ['BEN', 'Bénin', null, 'Bénin'], ['BFA', 'Burkina Faso', null, 'Burkina'],
  ['MLI', 'Mali', null, 'Mali'], ['NER', 'Niger', null, 'Niger'], ['TGO', 'Togo', null, 'Togo'], ['GNB', 'Guinée-Bissau', null, 'Guinée-Bissau'], ['SSF', 'Afrique subsaharienne', null], ['WLD', 'Monde', null]];
const ICO_CH = '<svg width="12" height="10" viewBox="0 0 12 10" style="vertical-align:-1px"><rect x=".5" y=".5" width="11" height="9" fill="none" stroke="#aaa"/><path d="M2 7.5L4.5 4.5L6.5 6L10 2" stroke="#fff" fill="none"/></svg>';
const ECST_WBN = { 'NY.GDP.MKTP.KD.ZG': 'Croissance du PIB réel', 'FP.CPI.TOTL.ZG': 'Inflation (prix à la consommation)' };
/* construit l'arbre (nœud -> lignes) pour une zone ; chaque ligne : { k, n, code, u, mode, pts:[[période, valeur]...] (du plus récent au plus ancien), x, y (historique) } */
async function ecstTree(geo) {
  const G = ECST_GEO.find(g => g[0] === geo) || ECST_GEO[0], out = [];
  if (geo === 'US') { const E = await getJSON('eco.json').catch(() => null); if (!E) return out; const M = Object.fromEntries(E.meta.map(x => [x.id, x]));
    const fq = { D: 'Quotidien', W: 'Hebdomadaire', M: 'Mensuel', Q: 'Trimestriel' };
    for (const [g, ids] of ECST_US) { const rows = ids.filter(id => M[id] && E.s[id]).map(id => { const [d, v] = E.s[id], n = d.length, mt = M[id]; const pts = []; for (let i = n - 1; i >= 0 && pts.length < 6; i--) if (v[i] != null) pts.push([d[i], v[i]]);
        const ya = (() => { const t = d[n - 1] - 10000; let k = -1; for (let i = n - 1; i >= 0; i--) if (d[i] <= t) { k = i; break; } return k >= 0 ? v[k] : null; })();
        return { k: 'F:' + id, n: mt.n, code: id, u: mt.u, f: fq[mt.f] || mt.f, mode: 'L', pts, ya, x: d, y: v, src: 'FRED' }; }); if (rows.length) out.push([g, rows]); }
    return out; }
  if (geo === 'UEMOA' || G[3]) { const B = await getJSON('bceao.json').catch(() => null);
    if (B) { const nm = geo === 'UEMOA' ? 'UEMOA' : G[3], per = o => Object.entries(o || {}).filter(([k]) => /^\d{4}(-\d{2})?$/.test(k)).sort((a, b) => b[0].localeCompare(a[0]));
      const pr = []; const inf = B.infl && (B.infl[nm] || (geo === 'UEMOA' ? B.infl.Union : null)); if (inf) pr.push({ k: 'B:infl', n: 'Inflation sur 1 an (glissement)', code: 'BCEAO', u: '%', f: 'Mensuel / annuel', mode: 'P', pts: per(inf), src: 'BCEAO' });
      if (B.money && B.money.rows) { const mk = geo === 'UEMOA' ? 'Union' : nm; for (const [a, o] of Object.entries(B.money.rows)) if (o[mk] != null) pr.push({ k: 'B:m:' + a, n: a, code: 'BCEAO', u: 'Md FCFA', f: 'Mensuel', mode: 'P', pts: [[B.money.asof, o[mk]]], src: 'BCEAO' }); }
      if (pr.length) out.push(['Prix et monnaie (BCEAO)', pr]);
      if (geo === 'UEMOA') { const pol = (B.policy || []).slice().reverse(); out.push(['Politique monétaire (BCEAO)', [{ k: 'B:pret', n: 'Taux directeur (guichet de prêt marginal)', code: 'BCEAO', u: '%', f: 'Décisions', mode: 'P', pts: pol.map(p => [p.d, p.pret]), src: 'BCEAO' },
          { k: 'B:min', n: 'Taux minimum de soumission (appels d’offres)', code: 'BCEAO', u: '%', f: 'Décisions', mode: 'P', pts: pol.map(p => [p.d, p.min]), src: 'BCEAO' },
          { k: 'B:mm', n: 'Taux moyen du marché monétaire', code: 'BCEAO', u: '%', f: 'Mensuel', mode: 'P', pts: (B.mm || []).slice().reverse().map(x => [x.m, x.t]), src: 'BCEAO' }]]);
        if (B.act) out.push(['Activité économique (BCEAO, glissement annuel)', Object.entries(B.act).map(([a, o]) => ({ k: 'B:a:' + a, n: a, code: 'BCEAO', u: '%', f: 'Mensuel / annuel', mode: 'P', pts: per(o), src: 'BCEAO' }))]);
        if (B.credit) { const lab = k => k.replace(/^credits\.vol\./, 'Crédits · ').replace(/^credits\.taux\./, 'Crédits, taux · ').replace(/^credits\.duree\./, 'Crédits · ').replace(/^depots\.vol\./, 'Dépôts · ').replace(/^depots\.taux\./, 'Dépôts, taux · ').replace(/^marge\.taux\./, '');
          out.push(['Conditions de banque (BCEAO)', Object.entries(B.credit).map(([a, o]) => ({ k: 'B:c:' + a, n: lab(a), code: 'BCEAO', u: /taux|marge/.test(a) ? '%' : /duree/.test(a) ? 'mois' : 'Md FCFA', f: 'Mensuel / annuel', mode: 'P', pts: per(o), src: 'BCEAO' }))]); } } } }
  if (geo !== 'US' && geo !== 'UEMOA') { const W = await getJSON('uemoa.json').catch(() => null);
    if (W && W.ind) for (const [g, codes] of ECST_WB) { const rows = codes.filter(c => W.ind[c] && W.ind[c].v && W.ind[c].v[geo]).map(c => { const o = W.ind[c].v[geo], ys = Object.keys(o).sort();
        return { k: 'W:' + c, n: W.ind[c].n, code: c, u: W.ind[c].u, f: 'Annuel', mode: 'P', pts: ys.slice().reverse().map(y => [y, o[y]]), x: ys.map(y => +y * 10000 + 1231), y: ys.map(y => o[y]), src: 'Banque mondiale' }; }); if (rows.length) out.push([g + ' (Banque mondiale)', rows]); } }
  /* séries BCEAO mêlant moyennes annuelles (AAAA) et glissements mensuels (AAAA-MM) : deux lignes distinctes, jamais sur le même axe */
  for (const node of out) { const rows = []; for (const r of node[1]) { if (r.mode !== 'P' || r.src !== 'BCEAO') { rows.push(r); continue; } const an = r.pts.filter(p => /^\d{4}$/.test(p[0])), mo = r.pts.filter(p => !/^\d{4}$/.test(p[0]));
      if (an.length && mo.length) { rows.push(Object.assign({}, r, { k: r.k + ':m', n: r.n + ' · mensuel', f: 'Mensuel', pts: mo }), Object.assign({}, r, { k: r.k + ':a', n: r.n + ' · annuel', f: 'Annuel', pts: an })); } else rows.push(r); } node[1] = rows; }
  return out;
}
const ecstFmt = (v, u) => v == null || !isFinite(v) ? '—' : Math.abs(v) >= 1e9 && /\$|hab/.test(u || '') ? big(v) : num(v, Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 100 ? 1 : 2);
const ecstPer = p => typeof p === 'number' ? fd(p) : /^\d{4}-\d{2}-\d{2}$/.test(p) ? fds(p) : /^\d{4}-\d{2}$/.test(p) ? MOIS_AX[+p.slice(5) - 1] + ' ' + p.slice(0, 4) : p;

PAGES.ECST = async (m, alive) => {
  setTitle('World Economic Statistics'); const st = ST.ecst = ST.ecst || { geo: 'US', open: {}, sel: null, q: '', tr: 'V' };
  const T = await ecstTree(st.geo); if (!alive()) return; const G = ECST_GEO.find(g => g[0] === st.geo) || ECST_GEO[0];
  const q = st.q.trim().toLowerCase(), all = T.flatMap(([g, rows]) => rows.map(r => Object.assign({ g }, r)));
  if (!st.sel || !all.find(r => r.k === st.sel)) st.sel = all.length ? all[0].k : null; const S = all.find(r => r.k === st.sel);
  if (!Object.keys(st.open).length || st.openGeo !== st.geo) { st.open = {}; st.openGeo = st.geo; T.slice(0, 3).forEach(([g]) => st.open[g] = 1); if (S) st.open[S.g] = 1; }
  const vis = T.map(([g, rows]) => [g, rows.filter(r => !q || (r.n + ' ' + r.code).toLowerCase().includes(q))]).filter(([, rows]) => rows.length);
  /* transformation (comme « Transformation : Value ») : valeur, variation sur la période, variation sur 1 an */
  const trf = (r, i) => { const v = r.pts[i] && r.pts[i][1]; if (st.tr === 'V' || v == null) return v; if (st.tr === 'P') { const p = r.pts[i + 1] && r.pts[i + 1][1]; return p ? (['%', 'pts'].includes(r.u) ? v - p : v / p - 1) : null; }
    if (r.mode === 'L' && i === 0 && r.ya != null) return ['%', 'pts'].includes(r.u) ? v - r.ya : v / r.ya - 1; return null; };
  const fmtT = (r, v) => v == null ? '—' : st.tr === 'V' ? ecstFmt(v, r.u) : ['%', 'pts'].includes(r.u) ? sgn(v, 2, ' pt', 1) : pc(v, 1);
  const cols = 4;
  const tree = `<div class="ectr">${ECST_GEO.map(([k, l, fl]) => `<div class="ecg${k === st.geo ? ' on' : ''}" data-geo="${k}">${fl ? flagSVG(fl, 16, 10) : '<span class="nf"></span>'} ${esc(l)}</div>`).join('')}</div>`;
  const nodes = vis.map(([g, rows]) => `<div class="ecn"><div class="ecnh" data-node="${esc(g)}"><b>${st.open[g] || q ? '⊟' : '⊞'}</b> ${esc(g)} <span class="dm">(${rows.length})</span></div>${st.open[g] || q ? rows.map(r => {
      const vals = Array.from({ length: cols }, (_, i) => trf(r, i));
      return `<div class="ecr${r.k === st.sel ? ' on' : ''}" data-k="${esc(r.k)}"><span class="nm">${esc(r.n)}</span><span class="tk">${ICO_CH} ${esc(r.code)}</span><span class="u dm">${esc(r.u || '')}</span>${vals.map((v, i) => `<span class="v${i ? '' : ' wh'}">${r.pts[i] ? fmtT(r, v) : ''}<small>${r.pts[i] ? ecstPer(r.pts[i][0]) : ''}</small></span>`).join('')}</div>`; }).join('') : ''}</div>`).join('');
  m.innerHTML = `<div class="grid ecst"><div class="pn ecl"><div class="tools"><span class="tlab">Zone</span><select class="ofld" id="esG">${ECST_GEO.map(([k, l]) => `<option value="${k}" ${k === st.geo ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select></div>
      <div class="tools"><input class="ofld" id="esQ" placeholder="Chercher un concept dans l’arbre" value="${esc(st.q)}" style="width:100%;text-transform:none"></div>${tree}
      <div class="ectn"><div class="ectnh">Concepts · ${esc(G[1])}</div>${T.map(([g, rows]) => `<div class="ecti${st.open[g] ? ' on' : ''}" data-solo="${esc(g)}"><b>${st.open[g] ? '⊟' : '⊞'}</b> ${esc(g.replace(/ \((BCEAO|Banque mondiale)[^)]*\)$/, ''))} <span class="dm">${rows.length}</span></div>`).join('')}</div></div>
    <div class="grid" style="align-content:start;min-width:0"><div class="pn"><div class="tools"><span class="tlab">Source</span><span class="wh">${esc([...new Set(all.map(r => r.src))].join(' · ') || '—')}</span><span class="tlab">Transformation</span><select class="ofld" id="esT"><option value="V" ${st.tr === 'V' ? 'selected' : ''}>Valeur</option><option value="P" ${st.tr === 'P' ? 'selected' : ''}>Variation sur la période</option><option value="Y" ${st.tr === 'Y' ? 'selected' : ''}>Variation sur 1 an</option></select>
        <span class="gsp"></span><button class="tb alt" id="esOpen">Tout ouvrir</button><button class="tb alt" id="esClose">Tout fermer</button></div>
      <div class="ech"><span>${esc(G[1])} · concept</span><span>Code</span><span>Unité</span>${Array.from({ length: cols }, (_, i) => `<span>${i ? 'Période −' + i : 'Dernier'}</span>`).join('')}</div>
      <div class="tw" style="max-height:calc(100vh - 500px - var(--nwh, 90px));min-height:240px">${nodes || '<div class="empty">Aucune donnée pour cette zone.</div>'}</div></div>
      ${S ? pn(`${esc(S.n)} <span class="dm">${esc(S.code)}</span>`, 'ECST', cvb('esC', 190), { sel: esc(S.src) + ' · ' + esc(S.f || ''), lect: `Unité : ${esc(S.u || '—')}. Dernière valeur ${ecstFmt(S.pts[0] && S.pts[0][1], S.u)} (${S.pts[0] ? ecstPer(S.pts[0][0]) : '—'}).` }) : ''}</div></div>`;
  $('esG').onchange = e => { st.geo = e.target.value; st.sel = null; render(); }; m.querySelectorAll('[data-geo]').forEach(d => d.onclick = () => { st.geo = d.dataset.geo; st.sel = null; render(); });
  $('esT').onchange = e => { st.tr = e.target.value; render(); };
  $('esQ').oninput = e => { clearTimeout(ST._esq); ST._esq = setTimeout(() => { st.q = e.target.value; render(); setTimeout(() => { const i = $('esQ'); if (i) { i.focus(); i.setSelectionRange(i.value.length, i.value.length); } }, 0); }, 300); };
  m.querySelectorAll('[data-node]').forEach(d => d.onclick = () => { st.open[d.dataset.node] = !st.open[d.dataset.node]; render(); });
  m.querySelectorAll('[data-solo]').forEach(d => d.onclick = () => { const g = d.dataset.solo; if (st.open[g] && Object.values(st.open).filter(Boolean).length === 1) { st.open[g] = 0; } else { st.open = { [g]: 1 }; const r = (T.find(t => t[0] === g) || [0, []])[1][0]; if (r) st.sel = r.k; } render(); });
  m.querySelectorAll('.ecr').forEach(d => d.onclick = () => { st.sel = d.dataset.k; render(); });
  $('esOpen').onclick = () => { T.forEach(([g]) => st.open[g] = 1); render(); }; $('esClose').onclick = () => { st.open = { _: 1 }; render(); };
  if (!S) return;
  if (S.x && S.mode === 'L') { const ch = new TSChart($('esC'), { panes: [{ h: 1 }] }); ch.set({ x: S.x, series: [{ y: S.y, color: CL.amber, label: S.code, fmt: y => num(y, 2) }] }, [Math.max(0, S.x.findIndex(z => z >= S.x[S.x.length - 1] - 150000)), S.x.length - 1]); }
  else { const P = S.pts.slice(0, 30).reverse(); barChart($('esC'), { labels: P.map(p => String(ecstPer(p[0])).replace(/^(\d{4})-.*/, '$1')), values: P.map(p => p[1]), fmt: v => ecstFmt(v, S.u), labelsOnBars: P.length <= 14, pos: '#3d7cc9', neg: '#ff3d4d', padB: 22 }); }
};

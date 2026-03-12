// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  PROFILER ENGINE (v3 — job-aware)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function pfDot(a,b){return DIMS.reduce((s,d)=>s+(a[d]||0)*(b[d]||0),0)}
function pfMag(v){return Math.sqrt(DIMS.reduce((s,d)=>s+(v[d]||0)**2,0))}
function pfCos(a,b){const ma=pfMag(a),mb=pfMag(b);return(ma&&mb)?pfDot(a,b)/(ma*mb):0}

function shuffle(a){const r=[...a];for(let i=r.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[r[i],r[j]]=[r[j],r[i]]}return r}
function pfInit(){pfShuffled=[];pfCur=0;pfAnswers=[];pfResult=null;pfJob=null;renderPfIntro()}
function buildQuestions(jobId){
  const job=JOB_GROUPS.flatMap(g=>g.jobs).find(j=>j.id===jobId);
  if(!job)return shuffle(Q_BASE);
  const descs=Q_DESC[job.scenario];
  return shuffle(Q_BASE.map((q,i)=>{const d=descs?.[i];return{...q,a:{...q.a,desc:d?.a||''},b:{...q.b,desc:d?.b||''}}}));
}

function renderPfIntro(){
  let jobsHtml='';
  JOB_GROUPS.forEach((g,gi)=>{
    const oc=gi===0?' open':'';
    jobsHtml+=`<div class="pf-job-group"><div class="pf-job-group-label${oc}" style="border-color:${g.color}25" onclick="toggleJobGroup(this)"><span style="background:${g.color};width:3px;height:14px;border-radius:2px;display:inline-block;flex-shrink:0"></span><span style="color:${g.color}">${g.groupLabel}</span><span class="jg-arrow">▼</span></div><div class="pf-job-grid${oc}">`;
    g.jobs.forEach(j=>{jobsHtml+=`<button class="pf-job-chip" data-jid="${j.id}" onclick="pfSelectJob('${j.id}')"><span class="pf-job-chip-i">${j.icon}</span><span class="pf-job-chip-t">${j.label}</span></button>`});
    jobsHtml+=`</div></div>`;
  });
  document.getElementById('pfWrap').innerHTML=`<button class="back" onclick="go('s-landing')">← 처음으로</button><div class="pf-intro fadein"><div class="mono pf-badge">Career Values Profiler <span style="opacity:.4">v3</span></div><h1 class="pf-h">당신의 커리어 가치관을<br><span>발견</span>합니다</h1><p class="pf-p">12개의 구체적 시나리오에서 트레이드오프를 선택하세요.<br>각 선택이 6개 가치 차원에 미치는 복합 효과를 분석합니다.</p><div class="pf-dims">${DIMS.map(d=>`<span class="pf-dim" style="border-color:${DIM_META[d].color}30;color:${DIM_META[d].color}">${DIM_META[d].icon} ${DIM_META[d].label}</span>`).join('')}</div><div class="pf-job-section"><div class="pf-job-label">먼저, 현재 직무를 선택해주세요</div>${jobsHtml}<div class="pf-job-notice" id="pfJobNotice"></div></div><button class="pf-start" id="pfStartBtn" onclick="pfStart()" disabled style="opacity:.4;cursor:not-allowed">직무를 선택하면 시작할 수 있습니다</button><p class="mono" style="margin-top:20px;font-size:11px;color:rgba(255,255,255,.18)">약 3~5분 · 12문항 · 직무 맞춤 시나리오</p></div>`;
}
function toggleJobGroup(el){el.classList.toggle('open');el.nextElementSibling.classList.toggle('open')}
function pfSelectJob(jobId){
  pfJob=JOB_GROUPS.flatMap(g=>g.jobs).find(j=>j.id===jobId);
  document.querySelectorAll('.pf-job-chip').forEach(c=>c.classList.toggle('on',c.dataset.jid===jobId));
  document.querySelectorAll('.pf-job-chip.on').forEach(c=>{const g=c.closest('.pf-job-grid'),l=g?.previousElementSibling;if(g&&!g.classList.contains('open')){g.classList.add('open');l?.classList.add('open')}});
  const n=document.getElementById('pfJobNotice');
  if(pfJob&&!pfJob.custom){n.innerHTML=`현재 <strong>${pfJob.label}</strong>은 범용 시나리오가 적용됩니다. 곧 직무별 맞춤 시나리오가 추가됩니다.`;n.classList.add('show')}else{n.classList.remove('show')}
  const btn=document.getElementById('pfStartBtn');btn.disabled=false;btn.style.opacity='1';btn.style.cursor='pointer';btn.textContent='시작하기';
}
function pfStart(){if(!pfJob)return;pfCur=0;pfAnswers=[];pfShuffled=buildQuestions(pfJob.id);renderPfQ()}

function renderPfQ(){
  if(pfCur>=pfShuffled.length){pfFinish();return}
  const q=pfShuffled[pfCur];
  const bars=pfShuffled.map((_,i)=>`<div class="pf-bar" style="background:${i<pfCur?'#E8B931':i===pfCur?'rgba(232,185,49,.4)':'rgba(255,255,255,.05)'}"></div>`).join('');
  function fxTags(fx){return DIMS.filter(d=>Math.abs(fx[d])>=.3).sort((a,b)=>Math.abs(fx[b])-Math.abs(fx[a])).map(d=>{const v=fx[d],pos=v>0;return`<span class="opt-fx-tag" style="background:${pos?DIM_META[d].color+'15':'rgba(255,255,255,.03)'};color:${pos?DIM_META[d].color:'rgba(255,255,255,.25)'};border-color:${pos?DIM_META[d].color+'30':'rgba(255,255,255,.06)'}">${pos?'↑':'↓'} ${DIM_META[d].label}</span>`}).join('')}
  document.getElementById('pfWrap').innerHTML=`<div class="pf-q fadein"><div style="display:flex;justify-content:space-between;margin-bottom:12px"><span class="mono" style="font-size:12px;color:rgba(255,255,255,.3)">${String(pfCur+1).padStart(2,'0')} / ${pfShuffled.length}</span><span class="mono" style="font-size:12px;color:rgba(255,255,255,.18)">${q.label}</span></div><div class="pf-progress">${bars}</div><p class="pf-prompt">두 회사에서 동시에 오퍼를 받았습니다. 어디를 선택하시겠습니까?</p><div class="opt-card" id="pfOptA" onclick="pfSelect('a')"><div style="display:flex;align-items:center;gap:10px;margin-bottom:8px"><span class="mono opt-tag" style="color:#E8B931;background:rgba(232,185,49,.15)">A</span><span class="opt-title">${q.a.title}</span></div><p class="opt-desc">${q.a.desc}</p><div class="opt-fx">${fxTags(q.a.fx)}</div></div><div class="opt-card" id="pfOptB" onclick="pfSelect('b')"><div style="display:flex;align-items:center;gap:10px;margin-bottom:8px"><span class="mono opt-tag" style="color:#7B68C8;background:rgba(123,104,200,.15)">B</span><span class="opt-title">${q.b.title}</span></div><p class="opt-desc">${q.b.desc}</p><div class="opt-fx">${fxTags(q.b.fx)}</div></div></div>`;
}
let pfLock=false;
function pfSelect(side){if(pfLock)return;pfLock=true;const q=pfShuffled[pfCur];document.getElementById(side==='a'?'pfOptA':'pfOptB').classList.add('sel-'+side);document.getElementById(side==='a'?'pfOptB':'pfOptA').classList.add('dim');setTimeout(()=>{pfAnswers.push({fx:side==='a'?q.a.fx:q.b.fx});pfCur++;pfLock=false;renderPfQ()},500)}

function pfFinish(){
  const scores={};DIMS.forEach(d=>scores[d]=0);pfAnswers.forEach(a=>DIMS.forEach(d=>scores[d]+=(a.fx[d]||0)));
  let best=null,bestSim=-Infinity;PROFILES.forEach(p=>{const s=pfCos(scores,p.vec);if(s>bestSim){bestSim=s;best=p}});
  pfResult={scores,profile:best,similarity:bestSim,job:pfJob};
  const allSim=PROFILES.map(p=>({p,s:pfCos(scores,p.vec)})).sort((a,b)=>b.s-a.s);
  const vals=DIMS.map(d=>scores[d]),mn=Math.min(...vals);const shifted={};DIMS.forEach(d=>shifted[d]=scores[d]-mn);const mx=Math.max(...DIMS.map(d=>shifted[d]),.01);const norm={};DIMS.forEach(d=>norm[d]=shifted[d]/mx);
  const sz=280,cx=sz/2,cy=sz/2,r=sz*.34,as=Math.PI*2/DIMS.length;const pt=(i,v)=>({x:cx+r*v*Math.cos(as*i-Math.PI/2),y:cy+r*v*Math.sin(as*i-Math.PI/2)});
  let svg=`<svg width="${sz}" height="${sz}" viewBox="0 0 ${sz} ${sz}"><defs><linearGradient id="rg2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#E8B931" stop-opacity=".3"/><stop offset="50%" stop-color="#7B68C8" stop-opacity=".2"/><stop offset="100%" stop-color="#4A9B8E" stop-opacity=".3"/></linearGradient></defs>`;
  [.2,.4,.6,.8,1].forEach(lv=>{svg+=`<path d="${DIMS.map((_,i)=>{const p=pt(i,lv);return`${i?'L':'M'} ${p.x} ${p.y}`}).join(' ')} Z" fill="none" stroke="rgba(255,255,255,.06)"/>`});
  DIMS.forEach((_,i)=>{const p=pt(i,1);svg+=`<line x1="${cx}" y1="${cy}" x2="${p.x}" y2="${p.y}" stroke="rgba(255,255,255,.06)"/>`});
  svg+=`<path d="${DIMS.map((d,i)=>{const p=pt(i,norm[d]);return`${i?'L':'M'} ${p.x} ${p.y}`}).join(' ')} Z" fill="url(#rg2)" stroke="rgba(232,185,49,.7)" stroke-width="2"/>`;
  DIMS.forEach((d,i)=>{const p=pt(i,norm[d]);svg+=`<circle cx="${p.x}" cy="${p.y}" r="5" fill="${DIM_META[d].color}" stroke="#0d0d1a" stroke-width="2"/>`});
  DIMS.forEach((d,i)=>{const p=pt(i,1.22);svg+=`<text x="${p.x}" y="${p.y}" text-anchor="middle" dominant-baseline="middle" fill="${DIM_META[d].color}" font-size="11" font-weight="600">${DIM_META[d].icon} ${DIM_META[d].label}</text>`});svg+=`</svg>`;
  const sorted=[...DIMS].sort((a,b)=>scores[b]-scores[a]);
  const barsH=sorted.map(d=>`<div style="display:flex;align-items:center;gap:12px"><span style="width:72px;font-size:13px;color:${DIM_META[d].color};font-weight:600;text-align:right">${DIM_META[d].icon} ${DIM_META[d].label}</span><div style="flex:1;height:26px;background:rgba(255,255,255,.03);border-radius:4px;overflow:hidden;position:relative"><div style="height:100%;width:${norm[d]*100}%;background:linear-gradient(90deg,${DIM_META[d].color}33,${DIM_META[d].color}99);border-radius:4px"></div><span class="mono" style="position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:11px;color:rgba(255,255,255,.45)">${scores[d]>=0?'+':''}${scores[d].toFixed(2)}</span></div></div>`).join('');
  const simH=allSim.map(({p,s})=>`<div style="display:flex;align-items:center;gap:10px;font-size:12px;color:rgba(255,255,255,.4)"><span class="mono" style="width:90px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p.type}</span><div style="flex:1;height:6px;background:rgba(255,255,255,.04);border-radius:3px;overflow:hidden"><div style="height:100%;width:${Math.max(0,((s+1)/2)*100)}%;background:linear-gradient(90deg,rgba(232,185,49,.3),rgba(232,185,49,.8));border-radius:3px"></div></div><span class="mono" style="width:40px">${(s*100).toFixed(0)}%</span></div>`).join('');
  const scenarioKey=pfJob?.scenario||'tech';const jobFit=best.jobFit?.[scenarioKey]||best.jobFit?.tech;const jobLabel=pfJob?.label||'기술';
  document.getElementById('pfWrap').innerHTML=`<div class="pf-result"><div class="slideup" style="text-align:center;margin-bottom:36px"><div class="mono" style="font-size:11px;letter-spacing:4px;color:rgba(232,185,49,.6);text-transform:uppercase;margin-bottom:16px">Your Career DNA</div><h2 style="font-size:28px;font-weight:700;color:#f0ede6;margin-bottom:6px">${best.type}</h2><span class="mono" style="font-size:11px;color:rgba(255,255,255,.25)">cosine similarity: ${(bestSim*100).toFixed(1)}% · ${jobLabel} 직군</span></div><div class="slideup" style="display:flex;justify-content:center;margin-bottom:28px">${svg}</div><div class="slideup" style="display:flex;flex-direction:column;gap:10px;margin-bottom:28px">${barsH}</div><div class="pf-res-box slideup"><h3 class="mono pf-res-label" style="color:rgba(232,185,49,.7)">분석</h3><p style="font-size:14px;line-height:1.8;color:rgba(255,255,255,.55)">${best.desc}</p></div><div class="pf-res-box slideup"><h3 class="mono pf-res-label" style="color:rgba(123,104,200,.7)">${jobLabel} 직군에서의 적합 경로</h3><p style="font-size:14px;line-height:1.8;color:rgba(255,255,255,.55)">${jobFit.fit}</p></div><div class="pf-res-box slideup"><h3 class="mono pf-res-label" style="color:rgba(212,100,78,.7)">${jobLabel} 직군 주의점</h3><p style="font-size:14px;line-height:1.8;color:rgba(255,255,255,.55)">${jobFit.caution}</p></div><div class="pf-res-box slideup"><h3 class="mono pf-res-label" style="color:rgba(255,255,255,.35)">전체 프로필 유사도</h3><div style="display:flex;flex-direction:column;gap:8px">${simH}</div></div><button class="pf-to-compare" onclick="pfToCompare()">이 가치관으로 회사 비교하기<span class="sub">${best.type} · ${jobLabel} → 추천 기준: ${PRIORITIES.find(p=>p.key===best.mapPri)?.label||''}</span></button><div style="text-align:center;margin-top:1rem"><button class="back" onclick="pfInit()" style="margin:0">다시 측정하기</button></div></div>`;
}
function pfToCompare(){
  if(pfResult?.profile?.mapPri)curPri=pfResult.profile.mapPri;
  if(pfResult?.scores){
    const dimToPri={compensation:'salary',security:'stability',growth:'growth',autonomy:'wlb',flexibility:'wlb',impact:'brand'};
    const sorted=[...DIMS].sort((a,b)=>pfResult.scores[a]-pfResult.scores[b]);
    for(const d of sorted){const pk=dimToPri[d];if(pk&&pk!==curPri&&PRIORITIES.some(p=>p.key===pk)){curSacrifice=pk;break}}
  }
  go('s-input');
  const a=document.getElementById('priAuto');
  if(pfResult){
    const sacLabel=curSacrifice?PRIORITIES.find(p=>p.key===curSacrifice)?.label:'';
    a.innerHTML=`🎯 <strong>${pfResult.profile.type}</strong> (${pfResult.job?.label||''} 직군) 가치관 분석 결과, 최우선: <strong>${PRIORITIES.find(p=>p.key===curPri)?.label}</strong>${sacLabel?`, 포기 가능: <strong>${sacLabel}</strong>`:''} — 다른 기준을 선택해도 됩니다.`;
    a.classList.add('show');
  }
}

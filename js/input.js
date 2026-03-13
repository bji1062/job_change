// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  INPUT — 우선순위, 검색, 복지, 근무방식, 연봉, calc
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ━━ WORK STYLE ━━
function setWS(s,field,val){
  wsState[s][field]=val;
  const containerId={ot:'otBtns',wage:'wageBtns',remote:'remoteBtns',flex:'flexBtns'}[field]+s.toUpperCase();
  document.querySelectorAll(`#${containerId} .ws-btn`).forEach(b=>b.classList.toggle('on',b.dataset.v===val));
  const w=wsState[s];
  const warn=document.getElementById('wsWarn'+s.toUpperCase());
  warn.classList.toggle('show',w.wage==='inclusive'&&(w.ot==='mid'||w.ot==='high'));
  renderOTCalc(s);
  calc();
}

function renderOTCalc(s){
  const el=document.getElementById('otCalc'+s.toUpperCase());
  el.classList.remove('show');
}

function applyWSPreset(s,type){
  const preset=WORK_PRESETS[type];
  if(!preset)return;
  const label=TYPE_LABELS[type]||type;
  Object.entries(preset).forEach(([field,val])=>setWS(s,field,val));
  const pr=document.getElementById('wsPr'+s.toUpperCase());
  pr.innerHTML=`💡 <strong>${label} 평균</strong> 근무방식을 자동으로 채웠습니다. 실제와 다르면 수정하세요.`;
  pr.classList.add('show');
}

function getWSHours(s){return OT_HRS[wsState[s].ot]||0}
function getOTPay(s){
  const w=wsState[s];
  if(w.wage!=='separate'||w.ot==='low')return 0;
  const salRange=s==='a'?getSalRange():getOfferRange();
  if(!salRange.mid)return 0;
  const hourlyBase=salRange.mid*10000/12/209;
  const extraHrs=OT_HRS[w.ot]-40;
  return Math.round(extraHrs*hourlyBase*1.5*4.33*12/10000);
}

// ━━ PRIORITY ━━
function initPri(){
  document.getElementById('priGrid').innerHTML=PRIORITIES.map(p=>`<button class="pri-c${p.key===curPri?' on':''}" data-k="${p.key}" onclick="setPri('${p.key}')"><span class="pri-c-i">${p.icon}</span><span class="pri-c-t">${p.label}</span></button>`).join('');
  renderPriPreview(curPri);
  document.getElementById('priSacSection').style.display='block';
  renderSacGrid();
  updateSelSummary();
}
function setPri(k){
  curPri=k;
  if(curSacrifice===k)curSacrifice=null;
  document.querySelectorAll('#priGrid .pri-c').forEach(c=>c.classList.toggle('on',c.dataset.k===k));
  renderPriPreview(k);
  document.getElementById('priSacSection').style.display='block';
  renderSacGrid();
  updateSelSummary();
}
function renderSacGrid(){
  const grid=document.getElementById('sacGrid');
  grid.innerHTML=PRIORITIES.filter(p=>p.key!==curPri).map(p=>`<button class="pri-c${p.key===curSacrifice?' sac-on':''}" data-k="${p.key}" onclick="setSacrifice('${p.key}')"><span class="pri-c-i">${p.icon}</span><span class="pri-c-t">${p.label}</span></button>`).join('');
}
function setSacrifice(k){
  if(k===curPri)return;
  curSacrifice=k;
  document.querySelectorAll('#sacGrid .pri-c').forEach(c=>c.classList.toggle('sac-on',c.dataset.k===k));
  const pv=PRI_PREVIEW[k],pri=PRIORITIES.find(p=>p.key===k);
  if(pv&&pri){
    const el=document.getElementById('sacPreview'),inner=document.getElementById('sacPvInner');
    inner.innerHTML=`<div style="display:flex;align-items:center;gap:8px;font-size:.82rem"><span style="font-size:1.1rem">${pri.icon}</span><span><strong style="color:var(--red)">${pv.title}</strong>을 포기 가능으로 선택했습니다. 리포트에서 포기 비용을 정량화합니다.</span></div>`;
    el.classList.remove('open');
    requestAnimationFrame(()=>requestAnimationFrame(()=>el.classList.add('open')));
  }
  updateSelSummary();
}
function updateSelSummary(){
  const el=document.getElementById('priSelSummary');
  const priObj=PRIORITIES.find(p=>p.key===curPri);
  const sacObj=curSacrifice?PRIORITIES.find(p=>p.key===curSacrifice):null;
  if(priObj&&sacObj){
    document.getElementById('selPriVal').textContent=priObj.icon+' '+priObj.label;
    document.getElementById('selSacVal').textContent=sacObj.icon+' '+sacObj.label;
    el.style.display='flex';
  } else {
    el.style.display='none';
  }
}
function renderPriPreview(k){const pv=PRI_PREVIEW[k],pri=PRIORITIES.find(p=>p.key===k);if(!pv||!pri)return;const el=document.getElementById('priPreview'),inner=document.getElementById('priPvInner');inner.innerHTML=`<div class="pri-pv-head"><span class="pri-pv-icon">${pri.icon}</span><div class="pri-pv-title"><span>${pv.title}</span>을 최우선으로<br>비교하겠습니다.</div></div><div class="pri-pv-checks">${pv.checks.map(c=>`<div class="pri-pv-check"><span class="pri-pv-check-icon">✓</span><span>${c}</span></div>`).join('')}</div><div class="pri-pv-tip"><span class="pri-pv-tip-icon">📌</span><span>${pv.tip}</span></div>`;el.classList.remove('open');requestAnimationFrame(()=>requestAnimationFrame(()=>el.classList.add('open')))}

// ━━ SEARCH ━━
function doSearch(s){const q=document.getElementById(s==='a'?'sA':'sB').value.trim().toLowerCase();const el=document.getElementById(s==='a'?'rA':'rB');if(q.length<1){el.classList.remove('open');return}const m=DB.filter(c=>c.name.toLowerCase().includes(q)||c.aliases.some(a=>a.toLowerCase().includes(q)));if(m.length){el.innerHTML=m.map(c=>`<div class="si" onclick="selComp('${s}','${c.id}')"><div class="si-logo">${c.logo}</div><div class="si-info"><div class="si-name">${c.name}</div><div class="si-meta">${c.industry}</div></div><span class="si-badge">DB</span></div>`).join('')}else{el.innerHTML=`<div class="sr-empty">검색 결과 없음<span style="display:block;font-size:.72rem;color:var(--t4);margin-top:4px">기업 유형을 선택하면 평균 복지를 채워드려요</span></div>`}el.classList.add('open')}
function selComp(s,id){const c=DB.find(x=>x.id===id);if(!c)return;matched[s]=c;document.getElementById(s==='a'?'sA':'sB').value=c.name;document.getElementById(s==='a'?'rA':'rB').classList.remove('open');document.getElementById(s==='a'?'tA':'tB').value=c.type;document.getElementById(s==='a'?'mA':'mB').classList.add('show');document.getElementById(s==='a'?'pA':'pB').classList.remove('show');benS[s]=c.benefits.map(b=>({...b,checked:b.val>0}));renderBen(s);
  const ws=c.workStyle||{};const type=c.type;
  const preset=WORK_PRESETS[type]||{};
  setWS(s,'ot',preset.ot||'mid');
  setWS(s,'wage',preset.wage||'inclusive');
  setWS(s,'remote',ws.remote&&ws.unlimitedPTO?'free':ws.remote?'hybrid':preset.remote||'none');
  setWS(s,'flex',ws.flex?'flexible':preset.flex||'none');
  const pr=document.getElementById('wsPr'+s.toUpperCase());
  pr.innerHTML=`✓ <strong>${c.name}</strong> DB 근무방식 + ${TYPE_LABELS[type]} 평균 추정 적용`;pr.classList.add('show');
  calc()}
function clearM(s){matched[s]=null;document.getElementById(s==='a'?'mA':'mB').classList.remove('show');document.getElementById(s==='a'?'pA':'pB').classList.remove('show');document.getElementById(s==='a'?'sA':'sB').value='';benS[s]=[];renderBen(s);wsState[s]={ot:null,wage:null,remote:null,flex:null};['ot','wage','remote','flex'].forEach(f=>{const cid={ot:'otBtns',wage:'wageBtns',remote:'remoteBtns',flex:'flexBtns'}[f]+s.toUpperCase();document.querySelectorAll(`#${cid} .ws-btn`).forEach(b=>b.classList.remove('on'))});document.getElementById('wsWarn'+s.toUpperCase()).classList.remove('show');document.getElementById('otCalc'+s.toUpperCase()).classList.remove('show');document.getElementById('wsPr'+s.toUpperCase()).classList.remove('show');calc()}
function onTypeChange(s){if(matched[s])return;const type=document.getElementById(s==='a'?'tA':'tB').value;const preset=BEN_PRESETS[type];const label=TYPE_LABELS[type]||type;if(!preset||!preset.length){benS[s]=[];document.getElementById(s==='a'?'pA':'pB').classList.remove('show');renderBen(s)}else{benS[s]=preset.map(b=>({...b}));const pb=document.getElementById(s==='a'?'pA':'pB');pb.innerHTML=`💡 <strong>${label} 평균 복지</strong>를 자동으로 채웠습니다. 아는 항목만 수정해주세요.`;pb.classList.add('show');document.getElementById(s==='a'?'mA':'mB').classList.remove('show');renderBen(s)}applyWSPreset(s,type);calc()}

// ━━ BENEFITS ━━
function renderBen(s){const list=benS[s];if(!list?.length){document.getElementById(s==='a'?'blA':'blB').innerHTML='';document.getElementById(s==='a'?'bcA':'bcB').textContent='';return}const grouped={};list.forEach((b,i)=>{if(!grouped[b.cat])grouped[b.cat]=[];grouped[b.cat].push({...b,idx:i})});let h='';for(const[cat,items]of Object.entries(grouped)){h+=`<div class="bg"><div class="bg-label">${CAT_LABELS[cat]||cat}</div>`;items.forEach(b=>{h+=`<div class="bi"><input type="checkbox" class="bi-ck" ${b.checked?'checked':''} onchange="togBen('${s}',${b.idx},this.checked)"><span class="bi-n">${b.name}${b.note?`<span class="bi-note">${b.note}</span>`:''}</span><span class="bi-badge ${b.badge==='auto'?'b-auto':'b-est'}">${b.badge==='auto'?'DB':'추정'}</span><input type="number" class="bi-v" value="${b.val}" onchange="setBenV('${s}',${b.idx},this.value)"><span class="bi-u">만</span></div>`});h+='</div>'}const isPreset=!matched[s]&&list.length>0;if(isPreset){const type=document.getElementById(s==='a'?'tA':'tB').value;h+=`<div class="ben-note-preset">모든 금액은 <strong>${TYPE_LABELS[type]||type} 평균 추정치</strong>입니다. 실제 금액을 아는 항목만 수정하세요. 체크 해제 항목은 합산 제외.</div>`}document.getElementById(s==='a'?'blA':'blB').innerHTML=h;const ac=list.filter(b=>b.checked&&b.val>0).length;document.getElementById(s==='a'?'bcA':'bcB').textContent=isPreset?`(${ac}/${list.length}개 · 평균 추정)`:`(${ac}개 항목)`}
function togBen(s,i,c){benS[s][i].checked=c;calc()}
function setBenV(s,i,v){benS[s][i].val=Number(v)||0;calc()}
function getBenTotal(s){let t=0;(benS[s]||[]).forEach(b=>{if(b.checked)t+=b.val});return{ben:t,net:t}}

// ━━ Salary helpers ━━
function getSalRange(){const v=document.getElementById('salA').value;if(!v)return{min:0,max:0,mid:0};const[lo,hi]=v.split('-').map(Number);return{min:lo,max:hi,mid:Math.round((lo+hi)/2)}}
function getOfferRange(){const base=getSalRange();if(!base.min||selectedRate===null)return{min:0,max:0,mid:0};const mult=1+selectedRate/100;return{min:Math.round(base.min*mult),max:Math.round(base.max*mult),mid:Math.round(base.mid*mult)}}
function setRate(r){selectedRate=r;document.querySelectorAll('.rate-chip').forEach(c=>c.classList.toggle('on',Number(c.dataset.rate)===r));updateRateResult();calc()}
function updateRateResult(){const el=document.getElementById('rateResult');const base=getSalRange();if(!base.min){el.innerHTML=`<span class="rate-result-placeholder">현직 연봉을 먼저 선택하면 예상 연봉이 계산됩니다.</span>`;return}if(selectedRate===null){el.innerHTML=`<span class="rate-result-placeholder">인상율을 선택해주세요.</span>`;return}const offer=getOfferRange();const rateLabel=selectedRate===0?'동결':'+'+selectedRate+'%';el.innerHTML=`<div class="rate-result-calc"><span class="rate-result-range">${offer.min.toLocaleString()} ~ ${offer.max.toLocaleString()}만원</span><span class="rate-result-detail">현직 ${base.min.toLocaleString()}~${base.max.toLocaleString()} × ${rateLabel}</span></div>`}
function fR(range){if(!range||!range.min)return'—';const f=v=>v>=10000?(v/10000).toFixed(1)+'억':v.toLocaleString()+'만';return range.min===range.max?f(range.min):`${f(range.min)} ~ ${f(range.max)}`}
function calc(){const salA=getSalRange(),salB=getOfferRange();const bA=getBenTotal('a'),bB=getBenTotal('b');
  if(salA.min){const tAmin=salA.min+bA.net,tAmax=salA.max+bA.net;document.getElementById('tcbA').textContent=`${salA.min.toLocaleString()}~${salA.max.toLocaleString()}`;document.getElementById('tcnA').textContent=`복지 ${bA.net>=0?'+':''}${bA.net.toLocaleString()}만`;document.getElementById('tctA').textContent=`${tAmin.toLocaleString()}~${tAmax.toLocaleString()}만`}else{document.getElementById('tcbA').textContent='—';document.getElementById('tcnA').textContent='복지 0만';document.getElementById('tctA').textContent='—'}
  if(salB.min){const tBmin=salB.min+bB.net,tBmax=salB.max+bB.net;document.getElementById('tcbB').textContent=`${salB.min.toLocaleString()}~${salB.max.toLocaleString()}`;document.getElementById('tcnB').textContent=`복지 ${bB.net>=0?'+':''}${bB.net.toLocaleString()}만`;document.getElementById('tctB').textContent=`${tBmin.toLocaleString()}~${tBmax.toLocaleString()}만`}else{document.getElementById('tcbB').textContent='—';document.getElementById('tcnB').textContent='복지 0만';document.getElementById('tctB').textContent='—'}
  const el=document.getElementById('diffV');if(salA.min&&salB.min){const dMin=(salB.min+bB.net)-(salA.min+bA.net),dMax=(salB.max+bB.net)-(salA.max+bA.net);const dStr=dMin===dMax?`${dMin>0?'+':''}${dMin.toLocaleString()}만원`:`${dMin>0?'+':''}${dMin.toLocaleString()} ~ ${dMax>0?'+':''}${dMax.toLocaleString()}만원`;if(dMin===0&&dMax===0){el.textContent='동일';el.style.color='var(--t2)'}else if(dMin>0){el.textContent=`이직처 ${dStr}`;el.style.color='var(--green)'}else if(dMax<0){el.textContent=`현직 +${Math.abs(dMax).toLocaleString()}${dMin!==dMax?' ~ +'+Math.abs(dMin).toLocaleString():''}만원`;el.style.color='var(--red)'}else{el.textContent=dStr;el.style.color='var(--t2)'}}else{el.textContent='—';el.style.color='var(--t2)'}
  updateRateResult()}

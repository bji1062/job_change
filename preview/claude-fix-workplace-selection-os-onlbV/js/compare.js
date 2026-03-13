// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  COMPARE ENGINE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function fW(v){return Math.abs(v)>=10000?(v/10000).toFixed(1)+'억원':Math.round(v).toLocaleString()+'만원'}
function getBenByCat(s,cat){let t=0;(benS[s]||[]).forEach(b=>{if(b.checked&&b.cat===cat)t+=b.val});return t}

function compare(){
  const salA=getSalRange(),salB=getOfferRange();
  if(!salA.min||!salB.min){alert('현직 연봉과 이직 인상율을 모두 선택해주세요.');return}
  // [FIX] 기업 유형 미선택 검증
  const typeAVal=document.getElementById('tA').value, typeBVal=document.getElementById('tB').value;
  if(!typeAVal||!typeBVal){alert('기업 유형을 모두 선택해주세요.');return}

  const bA=getBenTotal('a'),bB=getBenTotal('b');
  const effA={min:salA.min+bA.net,max:salA.max+bA.net,mid:salA.mid+bA.net};
  const effB={min:salB.min+bB.net,max:salB.max+bB.net,mid:salB.mid+bB.net};
  const comA=Number(document.getElementById('comA').value)||0,comB=Number(document.getElementById('comB').value)||0;
  const hrsA=getWSHours('a'),hrsB=getWSHours('b');
  const otPayA=getOTPay('a'),otPayB=getOTPay('b');
  const wA=wsState.a,wB=wsState.b;
  const nA=matched.a?matched.a.name:'현직',nB=matched.b?matched.b.name:'이직처';
  const wsA=matched.a?.workStyle||{},wsB=matched.b?.workStyle||{};
  const pri=PRIORITIES.find(p=>p.key===curPri);
  const effDiffMid=effB.mid-effA.mid,salDiffMid=salB.mid-salA.mid;
  const effDiffMin=effB.min-effA.min,effDiffMax=effB.max-effA.max;
  const diffRange=effDiffMin===effDiffMax?`${effDiffMin>0?'+':''}${fW(effDiffMin)}`:`${effDiffMin>0?'+':''}${fW(effDiffMin)} ~ ${effDiffMax>0?'+':''}${fW(effDiffMax)}`;

  let html=`<div class="rp-div"><span>${pri.icon} ${pri.label} 기준 비교 리포트</span></div>`;

  if(curSacrifice){
    const sacObj=PRIORITIES.find(p=>p.key===curSacrifice);
    html+=`<div style="display:flex;gap:.75rem;margin-bottom:1rem"><div style="flex:1;padding:.65rem .85rem;background:var(--purple-d);border:1px solid rgba(139,108,246,.2);border-radius:8px;text-align:center"><div style="font-size:.58rem;font-weight:700;color:var(--purple);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.2rem">최우선</div><div style="font-size:.82rem;font-weight:700;color:var(--t1)">${pri.icon} ${pri.label}</div></div><div style="flex:1;padding:.65rem .85rem;background:var(--red-d);border:1px solid rgba(239,80,80,.2);border-radius:8px;text-align:center"><div style="font-size:.58rem;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.2rem">포기 가능</div><div style="font-size:.82rem;font-weight:700;color:var(--t1)">${sacObj.icon} ${sacObj.label}</div></div></div>`;
  }

  if(pfResult){html+=`<div class="callout gold" style="margin-bottom:1rem"><span class="callout-icon">🎯</span><span><strong>${pfResult.profile.type}</strong> 가치관이 반영된 리포트입니다. 상위 가치: ${DIMS.filter(d=>pfResult.scores[d]>0).sort((a,b)=>pfResult.scores[b]-pfResult.scores[a]).slice(0,3).map(d=>`<strong style="color:${DIM_META[d].color}">${DIM_META[d].label}</strong>`).join(', ')}</span></div>`}

  // Verdict card helper
  function vdCard(icon,title,p1Label,p1Winner,p1Details,p2Label,p2Winner,p2Details,chooseText){
    let h=`<div class="vd-wrap"><div class="vd-header"><span class="vd-header-icon">${icon}</span><div class="vd-header-title"><span>${title}</span> 분석</div></div>`;
    h+=`<div class="vd-header-sub">선택하신 최우선 기준으로 두 가지 관점에서 비교합니다</div>`;
    h+=`<div class="vd-persp"><div class="vp p1"><div class="vp-label"><div class="vp-dot"></div>${p1Label}</div><div class="vp-winner">${p1Winner}</div><div class="vp-details">${p1Details}</div></div>`;
    h+=`<div class="vp p2"><div class="vp-label"><div class="vp-dot"></div>${p2Label}</div><div class="vp-winner">${p2Winner}</div><div class="vp-details">${p2Details}</div></div></div>`;
    if(chooseText)h+=`<div class="vd-choose"><span class="ch-icon">📌</span><span>${chooseText}</span></div>`;
    h+=`</div>`;return h;
  }

  // Build verdict based on priority
  let vdHtml='';
  if(curPri==='salary'){
    const totalA=effA.mid+otPayA, totalB=effB.mid+otPayB;
    const totalDiff=totalB-totalA;
    const hvA_=hrsA>0?Math.round(totalA*10000/(hrsA*52)):0;
    const hvB_=hrsB>0?Math.round(totalB*10000/(hrsB*52)):0;
    const totalWin=totalDiff>0?nB:totalDiff<0?nA:'동일';
    const hvWin_=hvA_&&hvB_?(hvA_>hvB_?nA:hvB_>hvA_?nB:'동일'):'';
    const p1W=totalWin==='동일'?'동일':`<span class="${totalWin===nA?'n-a':'n-b'}">${totalWin}</span> 유리`;
    const p1D=`총 보상(연봉+복지+야근수당) 기준<br>${totalDiff===0?'차이 없음':`차이 <strong>${totalDiff>0?'+':''}${fW(totalDiff)}</strong>`}${otPayA||otPayB?`<br><span style="font-size:.68rem;color:var(--t4)">야근수당 포함</span>`:''}`;
    let p2W='—',p2D='근무시간 미입력';
    if(hvA_&&hvB_){const hvDiff_=hvB_-hvA_;const pct_=Math.round(Math.abs(hvDiff_)/Math.min(hvA_,hvB_)*100);p2W=hvWin_==='동일'?`거의 동일 <span style="font-size:.72rem;color:var(--t4)">${pct_}%</span>`:`<span class="${hvWin_===nA?'n-a':'n-b'}">${hvWin_}</span> 유리`;p2D=`시간당 <strong>${hvDiff_>0?'+':''}${hvDiff_.toLocaleString()}원 (${pct_}%)</strong><br>"많이 벌어도 많이 일하면<br>시간당은 다를 수 있습니다"`}
    let choose=`<strong>"총액"</strong>이 중요하면 ${totalWin}`;
    if(hvWin_&&hvWin_!==totalWin&&hvWin_!=='동일')choose+=`, <strong>"시간 효율"</strong>이면 ${hvWin_}`;
    vdHtml=vdCard(pri.icon,pri.label,'총액',p1W,p1D,'시간당 가치',p2W,p2D,choose);
  }
  else if(curPri==='wlb'){
    const hA_=OT_HRS[wA.ot]||0, hB_=OT_HRS[wB.ot]||0;
    const fewer=hA_&&hB_?(hA_<hB_?nA:hB_<hA_?nB:'동일'):'미입력';
    const diff_=Math.abs(hA_-hB_), annDiff=diff_*52;
    const autoA=(REMOTE_SAVE[wA.remote]||0)+(wA.flex!=='none'?50:0)+(wsA.unlimitedPTO?80:0);
    const autoB=(REMOTE_SAVE[wB.remote]||0)+(wB.flex!=='none'?50:0)+(wsB.unlimitedPTO?80:0);
    const autoWin=autoA>autoB?nA:autoB>autoA?nB:'동일';
    const p1W=fewer==='미입력'?'야근 빈도 미입력':fewer==='동일'?'동일':`<span class="${fewer===nA?'n-a':'n-b'}">${fewer}</span> 유리`;
    const p1D=hA_&&hB_&&hA_!==hB_?`주당 <strong>${diff_}시간</strong> 덜 일함<br>연간 <strong>${annDiff}시간(≈${Math.round(annDiff/8)}근무일)</strong> 차이`:(hA_&&hB_?'근무시간 동일':'야근 빈도를 선택하면 비교할 수 있습니다');
    const dB=[],dA=[];
    if((REMOTE_SAVE[wB.remote]||0)>(REMOTE_SAVE[wA.remote]||0))dB.push(`재택 ${REMOTE_LABELS[wB.remote]}`);
    else if((REMOTE_SAVE[wA.remote]||0)>(REMOTE_SAVE[wB.remote]||0))dA.push(`재택 ${REMOTE_LABELS[wA.remote]}`);
    if(wB.flex!=='none'&&(wA.flex==='none'||wB.flex==='flexible'))dB.push(FLEX_LABELS[wB.flex]);
    else if(wA.flex!=='none'&&(wB.flex==='none'||wA.flex==='flexible'))dA.push(FLEX_LABELS[wA.flex]);
    if(wsB.unlimitedPTO)dB.push('자율 휴가');if(wsA.unlimitedPTO)dA.push('자율 휴가');
    const p2W=autoWin==='동일'?'동일':`<span class="${autoWin===nA?'n-a':'n-b'}">${autoWin}</span> 유리`;
    let p2D='';
    if(autoWin===nB&&dB.length)p2D=dB.map(d=>`<strong>${d}</strong>`).join(' + ');
    else if(autoWin===nA&&dA.length)p2D=dA.map(d=>`<strong>${d}</strong>`).join(' + ');
    else p2D='자율성 조건 비슷';
    p2D+=`<br>"야근이 많아도 시간을<br>스스로 조절할 수 있는가"`;
    let choose='';
    if(fewer!=='동일'&&fewer!=='미입력'&&autoWin!=='동일'&&fewer!==autoWin)choose=`<strong>"적게 일하기"</strong>가 중요하면 ${fewer}, <strong>"시간 자율성"</strong>이면 ${autoWin}`;
    else if(fewer!=='동일'&&fewer!=='미입력')choose=`${fewer}이 근무시간과 시간 자율성 모두 유리합니다`;
    vdHtml=vdCard(pri.icon,pri.label,'적게 일하기',p1W,p1D,'시간 자율성',p2W,p2D,choose);
  }
  else if(curPri==='benefits'){
    const benWin=bA.ben===bB.ben?'동일':bA.ben>bB.ben?nA:nB;
    const totalA=effA.mid+otPayA,totalB=effB.mid+otPayB,td=totalB-totalA;
    const p1W=benWin==='동일'?'동일':`<span class="${benWin===nA?'n-a':'n-b'}">${benWin}</span> 유리`;
    const p2W=td===0?'동일':`<span class="${td>0?'n-b':'n-a'}">${td>0?nB:nA}</span> 유리`;
    vdHtml=vdCard(pri.icon,pri.label,'복지 항목',p1W,`복리후생 합산<br><strong>${bA.ben.toLocaleString()}만 vs ${bB.ben.toLocaleString()}만</strong>`,'총 보상 포함',p2W,`연봉+복지+야근수당 합산<br>차이 <strong>${td>0?'+':''}${fW(td)}</strong>${Math.abs(td)<1200?'<br>"1,200만 이하면 복지 만족도 우선"':''}`,null);
  }
  else if(curPri==='brand'){
    vdHtml=vdCard(pri.icon,pri.label,'지금의 브랜드','정성적 판단',`"이 회사 다녀요"라고 말할 때<br>주변의 <strong>인식과 신뢰도</strong>`,'3년 후 이력서','정성적 판단',`다음 이직에서의<br><strong>연봉 협상력</strong>으로 전환`,`브랜드는 정량화 어렵지만, <strong>3년 후 이력서에 더 빛날 이름</strong>을 선택하세요`);
  }
  html+=vdHtml;

  // Salary comparison (always show)
  const effWin=effDiffMid>0?'b':effDiffMid<0?'a':'eq';
  html+=`<div class="cmp"><div class="cmp-head">💰 보상 비교</div><div class="cmp-body"><div class="vs-row"><div class="vs-card a-s${effWin==='a'?' win':''}"><div class="vs-side">${nA}</div><div class="vs-big">${fR(effA)}</div><div class="vs-detail">연봉 <strong>${fR(salA)}</strong> + 복지 <strong>${bA.net>=0?'+':''}${bA.net.toLocaleString()}만</strong></div></div><div class="vs-card b-s${effWin==='b'?' win':''}"><div class="vs-side">${nB}</div><div class="vs-big">${fR(effB)}</div><div class="vs-detail">연봉 <strong>${fR(salB)}</strong> + 복지 <strong>${bB.net>=0?'+':''}${bB.net.toLocaleString()}만</strong></div></div></div>`;
  if(salDiffMid>0&&effDiffMid<salDiffMid&&bA.ben>bB.ben)html+=`<div class="callout warn"><span class="callout-icon">⚠️</span><span>${nA}의 복지가 <strong>${fW(bA.ben-bB.ben)}</strong> 더 많아, 연봉이 올라도 실질 보상 차이는 줄어듭니다.${Math.abs(effDiffMid)<1200?' 이 정도 차이라면 복지 만족도가 더 중요할 수 있습니다.':''}</span></div>`;
  // Overtime detail breakdown
  if(otPayA>0||otPayB>0){
    function otDetail(s,name){
      const w=wsState[s],sal=s==='a'?salA:salB,otp=s==='a'?otPayA:otPayB;
      if(w.wage==='inclusive'){return`<div class="ot-detail-side"><div class="ot-detail-name">${name} <span class="ot-wage-tag inc">포괄임금</span></div><div class="ot-detail-warn">⚠️ 야근수당이 연봉에 포함<br>추가 수당 없음</div><div class="ot-detail-sum">연간 추가: <strong>0원</strong></div></div>`}
      if(w.wage==='separate'&&w.ot!=='low'&&sal.mid){
        const monthSal=sal.mid*10000/12,hb=Math.round(monthSal/209),ex=OT_HRS[w.ot]-40,wk=Math.round(ex*hb*1.5),mo=Math.round(wk*4.33);
        return`<div class="ot-detail-side"><div class="ot-detail-name">${name} <span class="ot-wage-tag sep">비포괄</span></div><div class="ot-detail-row"><span>통상시급 (연봉÷12÷209h)</span><span class="v">${hb.toLocaleString()}원</span></div><div class="ot-detail-row"><span>주당 연장근로 (${ex}h × 1.5배)</span><span class="v">+${wk.toLocaleString()}원</span></div><div class="ot-detail-row"><span>월 추가 수당 (×4.33주)</span><span class="v">+${mo.toLocaleString()}원</span></div><div class="ot-detail-sum">연간 추가: <strong class="green">+약 ${otp.toLocaleString()}만원</strong></div></div>`}
      return''}
    const dA=otDetail('a',nA),dB=otDetail('b',nB);
    if(dA||dB){
      let otMsg='';
      if(otPayA>0&&otPayB>0){const d=otPayB-otPayA;otMsg=d===0?'양쪽 모두 비포괄임금제로 야근수당이 보전됩니다.':`양쪽 모두 야근수당이 보전되며, <strong>${d>0?nB:nA}</strong>이 연 약 <strong>${fW(Math.abs(d))}</strong> 더 받습니다.`}
      else if(otPayB>0)otMsg=`<strong>${nB}</strong>는 비포괄임금제로 야근수당 연 약 <strong>${fW(otPayB)}</strong>이 추가 보전됩니다.`;
      else if(otPayA>0)otMsg=`<strong>${nA}</strong>는 비포괄임금제로 야근수당 연 약 <strong>${fW(otPayA)}</strong>이 추가 보전됩니다.`;
      html+=`<div class="ot-detail-box"><div class="ot-detail-head">💵 야근수당 상세</div><div class="ot-detail-grid">${dA}${dB}</div>${otMsg?`<div class="ot-detail-verdict"><span class="icon">⚡</span><span>${otMsg}</span></div>`:''}</div>`;
    }
  }
  html+=`</div></div>`;

  // [FIX] 시간당 실질 가치 — 양쪽 모두 입력된 경우만 비교 표시
  if(hrsA>0&&hrsB>0){
    const annHrsA=hrsA*52, annHrsB=hrsB*52;
    const effAmidOT=effA.mid+otPayA, effBmidOT=effB.mid+otPayB;
    const hvA=Math.round(effAmidOT*10000/annHrsA);
    const hvB=Math.round(effBmidOT*10000/annHrsB);
    const hvDiff=hvB-hvA;
    const hvWin=hvDiff>0?nB:hvDiff<0?nA:'동일';
    const otTagA=otPayA>0?` <span style="font-size:.58rem;color:var(--green)">+야근수당 ${otPayA}만</span>`:'';
    const otTagB=otPayB>0?` <span style="font-size:.58rem;color:var(--green)">+야근수당 ${otPayB}만</span>`:'';
    html+=`<div class="cmp"><div class="cmp-head">⏱ 시간당 실질 가치</div><div class="cmp-body">`;
    const incA=wA.wage==='inclusive'&&wA.ot!=='low',incB=wB.wage==='inclusive'&&wB.ot!=='low';
    if(incA&&incB)html+=`<div class="callout warn" style="margin-bottom:.65rem"><span class="callout-icon">🚨</span><span><strong>${nA}, ${nB} 모두 포괄임금제</strong>입니다. 연장근로 수당이 연봉에 포함된 방식으로, 야근이 늘수록 시간당 실질 가치가 낮아집니다.</span></div>`;
    else{
      if(incA)html+=`<div class="callout warn" style="margin-bottom:.65rem"><span class="callout-icon">🚨</span><span><strong>${nA}은 포괄임금제</strong>입니다. 연장근로 수당이 연봉에 포함된 방식으로, 야근이 늘수록 시간당 실질 가치가 낮아집니다.</span></div>`;
      if(incB)html+=`<div class="callout warn" style="margin-bottom:.65rem"><span class="callout-icon">🚨</span><span><strong>${nB}은 포괄임금제</strong>입니다. 연장근로 수당이 연봉에 포함된 방식으로, 야근이 늘수록 시간당 실질 가치가 낮아집니다.</span></div>`;
    }
    html+=`<div class="hourly-result"><div class="hourly-grid">`;
    html+=`<div class="hval"><div class="hval-num a">${hvA.toLocaleString()}원</div><div class="hval-label">${nA} / 시간${otTagA}</div></div>`;
    html+=`<div class="hval"><div class="hval-num b">${hvB.toLocaleString()}원</div><div class="hval-label">${nB} / 시간${otTagB}</div></div>`;
    const pct=Math.round(Math.abs(hvDiff)/Math.min(hvA,hvB)*100);
    html+=`<div class="hval"><div class="hval-num diff">${hvDiff>0?'+':''}${hvDiff.toLocaleString()}원</div><div class="hval-label">${hvWin} +${pct}%</div></div>`;
    html+=`</div>`;
    const annDiffHrs=Math.abs(annHrsA-annHrsB);const annDiffDays=Math.round(annDiffHrs/8);
    const salMore=effBmidOT>effAmidOT?nB:nA;const salDiffAbs=Math.abs(effBmidOT-effAmidOT);
    const pctHV=pct;const moreHrsName=annHrsA>annHrsB?nA:nB;const lessHrsName=moreHrsName===nA?nB:nA;
    const benDiff=bA.ben-bB.ben;const otDiff=otPayB-otPayA;
    const bothInclusive=wA.wage==='inclusive'&&wB.wage==='inclusive';const bothSeparate=wA.wage==='separate'&&wB.wage==='separate';const sameHrs=annDiffHrs<53;
    let msg='';
    if(sameHrs&&pctHV<5){msg=`근무시간이 비슷하고 시간당 가치도 거의 동일합니다 (차이 ${pctHV}%). <strong>근무 환경과 복지 항목</strong>으로 비교하세요.`}
    else if(sameHrs&&pctHV>=5){msg=`근무시간은 비슷하지만, <strong>${hvWin}</strong>이 시간당 <strong>${pctHV}% (${Math.abs(hvDiff).toLocaleString()}원)</strong> 높습니다. ${Math.abs(benDiff)>100?`${benDiff>0?nA:nB}의 복지가 연 ${fW(Math.abs(benDiff))} 더 많아 차이를 만듭니다.`:'연봉 차이가 그대로 시간당 가치에 반영됩니다.'}`}
    else if(annDiffHrs>100&&pctHV<10){
      if(otDiff>0&&benDiff>0){msg=`${moreHrsName}이 야근수당으로 연 <strong>${fW(Math.abs(otDiff))}</strong> 더 벌지만, ${lessHrsName}의 복지가 연 <strong>${fW(Math.abs(benDiff))}</strong> 더 많아 실질 격차는 <strong>${fW(salDiffAbs)}</strong>으로 줄어듭니다. <strong>${annDiffHrs.toLocaleString()}시간(≈${annDiffDays}근무일)</strong> 더 일한 결과, 시간당 차이는 겨우 <strong>${Math.abs(hvDiff).toLocaleString()}원(${pctHV}%)</strong>.`}
      else if(otDiff<0&&benDiff<0){msg=`${lessHrsName}이 야근수당으로 연 <strong>${fW(Math.abs(otDiff))}</strong> 더 벌지만, ${moreHrsName}의 복지가 연 <strong>${fW(Math.abs(benDiff))}</strong> 더 많아 격차가 줄어듭니다. 시간당으로는 <strong>${Math.abs(hvDiff).toLocaleString()}원(${pctHV}%)</strong> 차이.`}
      else if(bothInclusive){msg=`두 회사 모두 <strong>포괄임금제</strong>라 야근을 많이 해도 추가 수당이 없습니다. ${moreHrsName}이 연 <strong>${annDiffHrs.toLocaleString()}시간</strong> 더 일하지만 시간당 가치는 <strong>${Math.abs(hvDiff).toLocaleString()}원(${pctHV}%)</strong> 차이. 포괄임금 아래서 야근이 늘수록 시간당 가치가 희석됩니다.`}
      else if(bothSeparate){msg=`두 회사 모두 <strong>비포괄임금제</strong>라 야근수당이 보전됩니다. 그래도 ${moreHrsName}이 <strong>${annDiffHrs.toLocaleString()}시간</strong> 더 일해서 시간당 차이는 <strong>${Math.abs(hvDiff).toLocaleString()}원(${pctHV}%)</strong>에 불과합니다.`}
      else{msg=`${salMore}이 연 <strong>${fW(salDiffAbs)}</strong> 더 벌지만, <strong>${annDiffHrs.toLocaleString()}시간(≈${annDiffDays}근무일)</strong> 더 일합니다. 시간당 차이는 <strong>${Math.abs(hvDiff).toLocaleString()}원(${pctHV}%)</strong>.`}
    }else if(pctHV>=10){
      const hvWinName=hvDiff>0?nB:nA;
      if(hvWinName===moreHrsName){msg=`<strong>${hvWinName}</strong>이 더 일하면서도 시간당 가치가 <strong>${pctHV}%</strong> 높습니다. 보상이 근무시간 이상으로 크다는 의미입니다.`}
      else if(hvWinName===lessHrsName){msg=`<strong>${hvWinName}</strong>이 덜 일하면서 시간당 가치도 <strong>${pctHV}%</strong> 높습니다.${annDiffHrs>100?` ${moreHrsName}은 연 ${annDiffHrs.toLocaleString()}시간 더 일하고도 시간당으로는 뒤처집니다.`:''}`}
      else{msg=`<strong>${hvWinName}</strong>이 시간당 <strong>${pctHV}% (${Math.abs(hvDiff).toLocaleString()}원)</strong> 높습니다.`}
    }else{msg=`시간당 실질 가치 차이는 <strong>${Math.abs(hvDiff).toLocaleString()}원(${pctHV}%)</strong>입니다.${annDiffHrs>0?` ${moreHrsName}이 연 ${annDiffHrs.toLocaleString()}시간 더 일합니다.`:''} ${Math.abs(benDiff)>100?`복지 차이(연 ${fW(Math.abs(benDiff))})도 함께 고려하세요.`:'근무 환경과 성장 기회를 비교하세요.'}`}
    html+=`<div class="hourly-verdict"><span class="icon">⚡</span><span>${msg}</span></div>`;
    let noteItems=[];if(effA.mid||effB.mid)noteItems.push('연봉');if(bA.ben||bB.ben)noteItems.push('복지');if(otPayA||otPayB)noteItems.push('야근수당');
    const noteFormula=noteItems.length?noteItems.join('+'):'연봉+복지';
    let noteExtra='';
    if(wA.wage==='inclusive'||wB.wage==='inclusive'){const who=[wA.wage==='inclusive'?nA:'',wB.wage==='inclusive'?nB:''].filter(Boolean).join(', ');noteExtra=` · ${who}은 포괄임금(야근수당 미포함)`}
    html+=`</div><div class="hourly-note">계산식: (${noteFormula}) ÷ (주당근무시간×52주)${noteExtra}</div></div></div>`;
  }

  // [FIX] WLB 비교 — 야근 선택 시에도 통근/리프레시 정보 포함
  if(curPri==='wlb'){
    html+=`<div class="cmp"><div class="cmp-head">⚖️ 근무방식 비교</div><div class="cmp-body">`;
    const tA_=Math.round(comA*2*240/60),tB_=Math.round(comB*2*240/60),tw=tA_<tB_?'a':tB_<tA_?'b':'eq';
    if(comA||comB){
      html+=`<div class="vs-row"><div class="vs-card a-s${tw==='a'?' win':''}"><div class="vs-side">${nA} 통근</div><div class="vs-big">편도 ${comA}분</div><div class="vs-detail">연간 <strong>${tA_}시간</strong></div></div><div class="vs-card b-s${tw==='b'?' win':''}"><div class="vs-side">${nB} 통근</div><div class="vs-big">편도 ${comB}분</div><div class="vs-detail">연간 <strong>${tB_}시간</strong></div></div></div>`;
      const timeDiff=Math.abs(tA_-tB_);if(timeDiff>0)html+=`<div class="callout info"><span class="callout-icon">💡</span><span>연간 <strong>${timeDiff}시간</strong> 차이 = 약 <strong>${Math.round(timeDiff/8)}일</strong> 근무일에 해당합니다.</span></div>`;
    }
    if(wsB.remote||wsB.flex)html+=`<div class="callout good"><span class="callout-icon">✅</span><span><strong>${nB}</strong>은 ${wsB.remote?'원격근무':''}${wsB.flex?' 유연출퇴근':''} 가능.${wsB.unlimitedPTO?' <strong>자율 휴가제</strong> 운영.':''}</span></div>`;
    if(wsA.remote||wsA.flex)html+=`<div class="callout good"><span class="callout-icon">✅</span><span><strong>${nA}</strong>은 ${wsA.remote?'원격근무':''}${wsA.flex?' 유연출퇴근':''} 가능.</span></div>`;
    const rlA=wsA.refreshLeave,rlB=wsB.refreshLeave;if(rlA||rlB)html+=`<div class="callout info"><span class="callout-icon">🏖️</span><span><strong>리프레시 휴가:</strong> ${nA} — ${rlA||'없음'} | ${nB} — ${rlB||'없음'}</span></div>`;
    if(wA.ot||wB.ot){
      const remSaveA=REMOTE_SAVE[wA.remote]||0,remSaveB=REMOTE_SAVE[wB.remote]||0;
      const rc=(vA,vB,lowerBetter)=>{if(vA===vB)return['v-neu','v-neu'];return lowerBetter?(vA<vB?['v-good','v-bad']:['v-bad','v-good']):(vA>vB?['v-good','v-bad']:['v-bad','v-good'])};
      const otC=rc(OT_HRS[wA.ot]||40,OT_HRS[wB.ot]||40,true);
      const wgA_=wA.wage==='separate'?1:0,wgB_=wB.wage==='separate'?1:0;const wgC=rc(wgA_,wgB_,false);
      const rmA_=REMOTE_SAVE[wA.remote]||0,rmB_=REMOTE_SAVE[wB.remote]||0;const rmC=rc(rmA_,rmB_,false);
      const fxA_=wA.flex==='flexible'?2:wA.flex!=='none'?1:0,fxB_=wB.flex==='flexible'?2:wB.flex!=='none'?1:0;const fxC=rc(fxA_,fxB_,false);
      const cmC=rc(comA,comB,true);
      html+=`<div class="wlb-card"><div class="wlb-title">⚖️ 근무방식 상세 비교</div>`;
      html+=`<div class="wlb-legend"><div class="wlb-legend-item"><div class="wlb-legend-dot" style="background:var(--green)"></div>상대적 유리</div><div class="wlb-legend-item"><div class="wlb-legend-dot" style="background:var(--amber)"></div>중립 / 동일</div><div class="wlb-legend-item"><div class="wlb-legend-dot" style="background:var(--red)"></div>상대적 불리</div></div>`;
      html+=`<div class="wlb-compare"><div class="wlb-col"><div class="wlb-col-label"><div class="dot" style="background:var(--blue)"></div>${nA}</div>`;
      html+=`<div class="wlb-item"><span class="k">야근</span><span class="v ${otC[0]}">${OT_LABELS[wA.ot]||'—'} (주 ${OT_HRS[wA.ot]||'?'}h)</span></div>`;
      html+=`<div class="wlb-item"><span class="k">임금유형</span><span class="v ${wgC[0]}">${WAGE_LABELS[wA.wage]||'—'}</span></div>`;
      html+=`<div class="wlb-item"><span class="k">재택</span><span class="v ${rmC[0]}">${REMOTE_LABELS[wA.remote]||'—'}</span></div>`;
      html+=`<div class="wlb-item"><span class="k">유연근무</span><span class="v ${fxC[0]}">${FLEX_LABELS[wA.flex]||'—'}</span></div>`;
      html+=`<div class="wlb-item"><span class="k">통근</span><span class="v ${cmC[0]}">${comA}분</span></div>`;
      html+=`</div><div class="wlb-divider"></div><div class="wlb-col" style="padding-left:.75rem"><div class="wlb-col-label"><div class="dot" style="background:var(--amber)"></div>${nB}</div>`;
      html+=`<div class="wlb-item"><span class="k">야근</span><span class="v ${otC[1]}">${OT_LABELS[wB.ot]||'—'} (주 ${OT_HRS[wB.ot]||'?'}h)</span></div>`;
      html+=`<div class="wlb-item"><span class="k">임금유형</span><span class="v ${wgC[1]}">${WAGE_LABELS[wB.wage]||'—'}</span></div>`;
      html+=`<div class="wlb-item"><span class="k">재택</span><span class="v ${rmC[1]}">${REMOTE_LABELS[wB.remote]||'—'}</span></div>`;
      html+=`<div class="wlb-item"><span class="k">유연근무</span><span class="v ${fxC[1]}">${FLEX_LABELS[wB.flex]||'—'}</span></div>`;
      html+=`<div class="wlb-item"><span class="k">통근</span><span class="v ${cmC[1]}">${comB}분</span></div>`;
      html+=`</div></div></div>`;
      const hvA2=hrsA>0?Math.round((effA.mid+otPayA)*10000/(hrsA*52)):0;
      const hvB2=hrsB>0?Math.round((effB.mid+otPayB)*10000/(hrsB*52)):0;
      html+=`<table class="wlb-summary"><thead><tr><th>항목</th><th>${nA}</th><th>${nB}</th><th>우위</th></tr></thead><tbody>`;
      if(hvA2&&hvB2){const w_=hvA2>hvB2?nA:hvB2>hvA2?nB:'동일';html+=`<tr><td>시간당 가치</td><td class="td-a">${hvA2.toLocaleString()}원</td><td class="td-b">${hvB2.toLocaleString()}원</td><td class="td-win">${w_} ▲</td></tr>`}
      {const oA=OT_HRS[wA.ot]||40,oB=OT_HRS[wB.ot]||40,w_=oA<oB?nA:oB<oA?nB:'동일';html+=`<tr><td>야근 부담</td><td class="td-a">${OT_LABELS[wA.ot]||'—'}</td><td class="td-b">${OT_LABELS[wB.ot]||'—'}</td><td class="${w_===nA?'td-win':w_===nB?'td-win':''}" style="color:${w_===nA?'var(--blue)':w_===nB?'var(--amber)':'var(--t3)'};font-weight:700">${w_} ▲</td></tr>`}
      {html+=`<tr><td>재택 절감비용</td><td class="td-a">연 ${remSaveA}만</td><td class="td-b">연 ${remSaveB}만</td><td class="td-win">${remSaveA>remSaveB?nA:remSaveB>remSaveA?nB:'동일'} ▲</td></tr>`}
      {const wA_=wA.wage==='separate',wB_=wB.wage==='separate';html+=`<tr><td>임금 유형</td><td class="td-a" ${!wA_?'style="color:var(--red)"':''}>${wA_?'비포괄 ✓':'포괄 ⚠'}</td><td class="td-b" ${!wB_?'style="color:var(--red)"':''}>${wB_?'비포괄 ✓':'포괄 ⚠'}</td><td class="td-win">${wA_&&!wB_?nA:wB_&&!wA_?nB:'동일'} ▲</td></tr>`}
      {const fA=wA.flex!=='none',fB=wB.flex!=='none';html+=`<tr><td>유연근무</td><td class="td-a">${FLEX_LABELS[wA.flex]||'—'}</td><td class="td-b">${FLEX_LABELS[wB.flex]||'—'}</td><td class="td-win">${fA&&!fB?nA:fB&&!fA?nB:wA.flex==='flexible'&&wB.flex!=='flexible'?nA:wB.flex==='flexible'&&wA.flex!=='flexible'?nB:'동일'} ▲</td></tr>`}
      html+=`</tbody></table>`;
    }
    html+=`</div></div>`;
  }

  if(curPri==='benefits'){const listA=benS.a||[],listB=benS.b||[];if(listA.length||listB.length){const allKeys=new Set();listA.forEach(b=>allKeys.add(b.key));listB.forEach(b=>allKeys.add(b.key));let rows='';allKeys.forEach(k=>{const a=listA.find(b=>b.key===k),b_=listB.find(b=>b.key===k);const vA=a?.checked?a.val:0,vB=b_?.checked?b_.val:0;const nm=a?.name||b_?.name||k;const df=vB-vA;rows+=`<tr><td class="td-name">${nm}</td><td class="td-a">${vA?vA.toLocaleString()+'만':'—'}</td><td class="td-b">${vB?vB.toLocaleString()+'만':'—'}</td><td class="td-diff ${df>0?'pos':df<0?'neg':'eq'}">${df!==0?(df>0?'+':'')+df.toLocaleString()+'만':'—'}</td></tr>`});const totA=listA.reduce((s,b)=>s+(b.checked?b.val:0),0),totB=listB.reduce((s,b)=>s+(b.checked?b.val:0),0),totD=totB-totA;html+=`<div class="cmp"><div class="cmp-head">🎁 복리후생 항목별 비교</div><div class="cmp-body"><table class="ben-compare"><thead><tr><th>항목</th><th>${nA}</th><th>${nB}</th><th>차이</th></tr></thead><tbody>${rows}<tr style="border-top:2px solid var(--border)"><td style="font-weight:700;color:var(--t1)">합계</td><td class="td-a" style="font-weight:700">${totA.toLocaleString()}만</td><td class="td-b" style="font-weight:700">${totB.toLocaleString()}만</td><td class="td-diff ${totD>0?'pos':totD<0?'neg':'eq'}" style="font-weight:700">${totD===0?'동일':(totD>0?'+':'')+totD.toLocaleString()+'만'}</td></tr></tbody></table></div></div>`}}
  if(curPri==='brand'){html+=`<div class="cmp"><div class="cmp-head">🏢 브랜드 가치</div><div class="cmp-body"><div class="callout info"><span class="callout-icon">💡</span><span>회사 브랜드는 <strong>"다음 이직"의 연봉 협상력</strong>으로 전환됩니다. 3년 후 이력서에 더 빛날 이름을 선택하세요.</span></div></div></div>`}

  // Qualitative benefits
  const qualA=(benS.a||[]).filter(b=>b.qual),qualB=(benS.b||[]).filter(b=>b.qual);
  if(qualA.length||qualB.length){html+=`<div class="cmp"><div class="cmp-head">📋 금전 환산 어려운 혜택</div><div class="cmp-body">`;qualA.forEach(b=>{html+=`<div class="qual-item"><span class="qual-side qs-a">${nA}</span><span>${b.qualText||b.name}</span></div>`});qualB.forEach(b=>{html+=`<div class="qual-item"><span class="qual-side qs-b">${nB}</span><span>${b.qualText||b.name}</span></div>`});html+=`</div></div>`}

  // [FIX] 3년 투영 — 변수 섀도잉 수정 (barWA/barWB)
  const grA=GROWTH_RATES[typeAVal]||0.04,grB=GROWTH_RATES[typeBVal]||0.04;
  const projA=[salA.mid],projB=[salB.mid];
  let cumDiff=0;
  for(let y=1;y<=3;y++){projA.push(Math.round(projA[y-1]*(1+grA)));projB.push(Math.round(projB[y-1]*(1+grB)));cumDiff+=(projB[y]-projA[y])}
  const maxVal=Math.max(...projA,...projB);
  html+=`<div class="cmp"><div class="cmp-head">📈 3년 후 기대 연봉</div><div class="cmp-body">`;
  html+=`<div class="proj-legend"><div class="proj-legend-item"><div class="proj-legend-dot" style="background:var(--blue)"></div>${nA} (${TYPE_LABELS[typeAVal]||typeAVal})</div><div class="proj-legend-item"><div class="proj-legend-dot" style="background:var(--amber)"></div>${nB} (${TYPE_LABELS[typeBVal]||typeBVal})</div></div>`;
  html+=`<div class="proj-bars">`;
  const labels=['현재','1년차','2년차','3년차'];
  for(let y=0;y<=3;y++){
    const barWA=Math.max(20,projA[y]/maxVal*100),barWB=Math.max(20,projB[y]/maxVal*100);
    const fV=v=>v>=10000?(v/10000).toFixed(1)+'억':v.toLocaleString()+'만';
    html+=`<div class="proj-row"><div class="proj-row-label">${labels[y]}</div><div class="proj-bar-wrap"><div class="proj-bar a" style="width:${barWA}%"><span class="proj-bar-val">${fV(projA[y])}</span></div><div class="proj-bar b" style="width:${barWB}%"><span class="proj-bar-val">${fV(projB[y])}</span></div></div></div>`;
  }
  html+=`</div>`;
  const totalDiff3yr=cumDiff;
  const grAp=Math.round(grA*100),grBp=Math.round(grB*100);
  html+=`<div class="proj-summary"><strong>3년 누적 차이 ${totalDiff3yr>0?'+':''}${fW(totalDiff3yr)}</strong> — ${nB}이 연평균 ${grBp}%↑ (${GROWTH_LABELS[typeBVal]||''}) vs ${nA} ${grAp}%↑ (${GROWTH_LABELS[typeAVal]||''}).${typeBVal==='startup'?' 스타트업 성장률이 실현되지 않으면 격차는 줄어듭니다.':''}</div>`;
  html+=`<div class="proj-note"><span>⚠️</span> 고용노동부 업종별 임금 데이터 기반 추정 · 개인 성과에 따라 실제와 다를 수 있음</div>`;
  html+=`</div></div>`;

  // Bottom line
  let blText='';
  if(curPri==='salary'){
    const totA=effA.mid+otPayA,totB=effB.mid+otPayB,td=totB-totA;
    const hvA_=hrsA>0?Math.round(totA*10000/(hrsA*52)):0,hvB_=hrsB>0?Math.round(totB*10000/(hrsB*52)):0;
    const hvWin_=hvA_&&hvB_?(hvA_>hvB_?nA:hvB_>hvA_?nB:'동일'):'';
    const totalWin=td>0?nB:td<0?nA:'동일';
    if(totalWin!=='동일'&&hvWin_&&hvWin_!==totalWin){blText=`총액은 <span class="${totalWin===nA?'hl-a':'hl-b'}">${totalWin}</span>이 ${Math.abs(td)>0?fW(Math.abs(td)):''} 유리하지만, 시간당 가치는 <span class="${hvWin_===nA?'hl-a':'hl-b'}">${hvWin_}</span>이 높습니다. 당신에게 중요한 건 "총액"인가요, "시간 효율"인가요?`}
    else{blText=td>0?`총 보상 기준 <span class="hl-b">${nB}</span>이 ${fW(Math.abs(td))} 유리합니다.`:td<0?`<span class="hl-a">${nA}</span>이 총 보상 기준 유리합니다.`:'총 보상이 동일합니다.'}
  }
  else if(curPri==='wlb'){
    const hA_=OT_HRS[wA.ot]||0,hB_=OT_HRS[wB.ot]||0;
    const fewer=hA_&&hB_?(hA_<hB_?nA:hB_<hA_?nB:'동일'):'미입력';
    const autoA=(REMOTE_SAVE[wA.remote]||0)+(wA.flex!=='none'?50:0)+(wsA.unlimitedPTO?80:0);
    const autoB=(REMOTE_SAVE[wB.remote]||0)+(wB.flex!=='none'?50:0)+(wsB.unlimitedPTO?80:0);
    const autoWin=autoA>autoB?nA:autoB>autoA?nB:'동일';
    if(fewer!=='동일'&&fewer!=='미입력'&&autoWin!=='동일'&&fewer!==autoWin){blText=`"적게 일하기"는 <span class="${fewer===nA?'hl-a':'hl-b'}">${fewer}</span>, "시간 자율성"은 <span class="${autoWin===nA?'hl-a':'hl-b'}">${autoWin}</span>이 유리합니다. 당신에게 워라밸이란 "근무시간 자체"인가요, "시간의 자유"인가요?`}
    else if(fewer!=='동일'&&fewer!=='미입력'){const diff_=Math.abs(hA_-hB_),annD=diff_*52;blText=`<span class="${fewer===nA?'hl-a':'hl-b'}">${fewer}</span>이 주당 <strong>${diff_}시간</strong> 덜 일합니다 (연 ${annD}시간 ≈ ${Math.round(annD/8)}근무일).`}
    else{blText='야근 빈도를 선택하면 더 정확한 비교가 가능합니다. 재택/유연근무 조건으로 비교하세요.'}
  }
  else if(curPri==='benefits'){if(bA.ben===bB.ben)blText='복리후생 합산이 동일합니다. 개별 항목의 질적 차이를 비교해보세요.';else{const bw=bA.ben>bB.ben?nA:nB;const td=Math.abs((effA.mid+otPayA)-(effB.mid+otPayB));blText=td<1200?`총 보상 차이가 크지 않아(${fW(td)}), 복지가 풍부한 <span class="${bA.ben>bB.ben?'hl-a':'hl-b'}">${bw}</span>이 일상 만족도에서 유리합니다.`:`복지는 <span class="${bA.ben>bB.ben?'hl-a':'hl-b'}">${bw}</span>이 연 ${fW(Math.abs(bA.ben-bB.ben))} 더 풍부합니다.`}}
  else if(curPri==='brand')blText=`브랜드 가치는 "지금의 자부심"과 "3년 후 이력서" 두 가지로 나뉩니다. 당신에게 더 중요한 건 어느 쪽인가요?`;
  html+=`<div class="bottom-line"><div class="bl-label">결론</div><div class="bl-text">${blText.replace(/\. /g,'.<br>')}</div></div>`;

  // [FIX] Sacrifice cost — WLB 미입력 시 안내 메시지 표시
  if(curSacrifice){
    const sacPri=PRIORITIES.find(p=>p.key===curSacrifice);
    html+=`<div class="sac-card"><div class="sac-head">✕ ${sacPri.icon} ${sacPri.label} — 포기해도 괜찮을까?</div><div class="sac-body">`;
    const totalA=effA.mid+otPayA, totalB=effB.mid+otPayB;
    if(curSacrifice==='salary'){const td=Math.abs(totalB-totalA);const monthly=Math.round(td/12);const better=totalB>totalA?nB:nA;html+=`<div class="sac-cost-box"><div class="sac-cost-label">${better}을 선택하면 받는 추가 보상</div><div class="sac-cost-val">연 ${fW(td)}</div><div class="sac-cost-detail">월 ${monthly.toLocaleString()}만원 · 일 ${Math.round(td*10000/365).toLocaleString()}원</div></div><div class="sac-question">이 금액을 포기할 수 있나요?</div>`}
    else if(curSacrifice==='wlb'){
      const hA_=OT_HRS[wA.ot]||0, hB_=OT_HRS[wB.ot]||0;
      if(!hA_||!hB_){html+=`<div class="sac-cost-box"><div class="sac-cost-label">근무방식 미입력</div><div class="sac-cost-val">—</div><div class="sac-cost-detail">야근 빈도를 선택하면 포기 비용을 계산합니다</div></div>`}
      else{const diff_=Math.abs(hA_-hB_),annD=diff_*52,annDays=Math.round(annD/8);const more_=hA_>hB_?nA:nB;html+=`<div class="sac-cost-box"><div class="sac-cost-label">${more_}은 매주 더 일합니다</div><div class="sac-cost-val">주 +${diff_}시간</div><div class="sac-cost-detail">연간 ${annD.toLocaleString()}시간 = 약 ${annDays}근무일</div></div><div class="sac-question">이만큼의 추가 근무를 감수할 수 있나요?</div>`}
    }
    else if(curSacrifice==='benefits'){const diff_=Math.abs(bA.ben-bB.ben),better_=bA.ben>bB.ben?nA:nB;html+=`<div class="sac-cost-box"><div class="sac-cost-label">${better_}의 복지가 더 풍부합니다</div><div class="sac-cost-val">연 ${fW(diff_)}</div><div class="sac-cost-detail">복리후생 항목 합산 차이</div></div><div class="sac-question">이 복지 차이를 포기할 수 있나요?</div>`}
    else if(curSacrifice==='brand'){html+=`<div class="sac-cost-box"><div class="sac-cost-label">회사 브랜드는 "다음 이직"에서 연봉 협상력</div><div class="sac-cost-val" style="font-size:1.1rem">3년 후 이력서 가치</div><div class="sac-cost-detail">정량화 어렵지만, 브랜드 차이가 다음 연봉 1,000만+ 차이를 만들 수 있음</div></div><div class="sac-question">이력서 가치를 포기할 수 있나요?</div>`}
    html+=`</div></div>`;
  }

  // Remaining criteria summary
  const restKeys=PRIORITIES.filter(p=>p.key!==curPri&&p.key!==curSacrifice).map(p=>p.key);
  if(restKeys.length>0){
    html+=`<div class="rest-summary"><div class="rest-head">📊 나머지 기준 요약</div>`;
    const totalA=effA.mid+otPayA, totalB=effB.mid+otPayB;
    restKeys.forEach(k=>{
      const pri=PRIORITIES.find(p=>p.key===k);
      let val='',winCls='rest-tie';
      if(k==='salary'){const d=totalB-totalA;val=d===0?'동일':d>0?`${nB} +${fW(d)}`:`${nA} +${fW(Math.abs(d))}`;winCls=d!==0?'rest-win':'rest-tie'}
      else if(k==='wlb'){const hA_=OT_HRS[wA.ot]||0,hB_=OT_HRS[wB.ot]||0;if(hA_&&hB_){val=hA_===hB_?`동일 (주 ${hA_}h)`:hA_<hB_?`${nA} 유리 (주 ${hA_}h vs ${hB_}h)`:`${nB} 유리 (주 ${hB_}h vs ${hA_}h)`;winCls=hA_!==hB_?'rest-win':'rest-tie'}else{val=`통근 ${comA}분 vs ${comB}분`}}
      else if(k==='benefits'){val=bA.ben===bB.ben?'동일':bA.ben>bB.ben?`${nA} +${fW(bA.ben-bB.ben)}`:`${nB} +${fW(bB.ben-bA.ben)}`;winCls=bA.ben!==bB.ben?'rest-win':'rest-tie'}
      else if(k==='brand'){val='정량 비교 어려움';winCls='rest-tie'}
      html+=`<div class="rest-item"><span class="rest-icon">${pri.icon}</span><span class="rest-label">${pri.label}</span><span class="rest-val ${winCls}">${val}</span></div>`;
    });
    html+=`</div>`;
  }

  if(!pfResult){html+=`<div class="rp-profiler-cta"><p>내가 선택한 기준이 정말 맞을까?<br><strong>커리어 가치관 테스트</strong>로 검증해보세요.</p><button class="rp-profiler-btn" onclick="go('s-profiler')">🎯 가치관 테스트 하기</button></div>`}
  html+=`<div class="disclaimer">복리후생 금액은 공개 채용 정보 기반 추정치이며 실제와 다를 수 있습니다.</div>`;
  document.getElementById('report').innerHTML=html;
  document.getElementById('report').classList.add('visible');
  document.getElementById('report').scrollIntoView({behavior:'smooth',block:'start'});
}

// ━━ APP (navigation + init) ━━

function go(id){document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));document.getElementById(id).classList.add('active');if(id==='s-profiler')pfInit();if(id==='s-input'){initPri();calc()}}

document.addEventListener('click',e=>{['a','b'].forEach(s=>{const w=document.getElementById(s==='a'?'sA':'sB').parentElement;if(!w.contains(e.target))document.getElementById(s==='a'?'rA':'rB').classList.remove('open')})});

// ━━ INIT ━━
initPri();calc();

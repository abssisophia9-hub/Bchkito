"""HTTP handlers + HTML for the Bchkito Care prototype."""

from __future__ import annotations

# Split large HTML into module constants for the server script.

CAREGIVER_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Bchkito Care — لوحة العائلة</title>
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Syne:wght@600;700;800&display=swap" rel="stylesheet"/>
<style>
:root{--sea:#0b3d4a;--foam:#eef7f5;--saff:#e2a008;--ink:#102a32;--muted:#5a7a82;--danger:#b42318;--ok:#0f7a4c;--line:rgba(11,61,74,.12)}
*{box-sizing:border-box}body{margin:0;font-family:Amiri,serif;background:linear-gradient(160deg,#f2faf8,#d7ebe6);color:var(--ink)}
header{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.25rem;border-bottom:1px solid var(--line);background:rgba(255,255,255,.7);backdrop-filter:blur(8px);position:sticky;top:0;z-index:5}
.brand{font-family:Syne,sans-serif;font-weight:800;font-size:1.6rem;color:var(--sea);margin:0}
nav a{margin-inline-start:1rem;color:var(--sea);text-decoration:none;font-family:Syne,sans-serif;font-size:.85rem}
main{max-width:1100px;margin:0 auto;padding:1.25rem}
.grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:rgba(255,255,255,.78);border:1px solid var(--line);border-radius:1rem;padding:1rem}
.card h2{font-family:Syne,sans-serif;font-size:1rem;margin:0 0 .75rem;color:var(--sea)}
.stat{font-size:2rem;font-family:Syne,sans-serif;font-weight:800}
.muted{color:var(--muted);font-size:.95rem}
table{width:100%;border-collapse:collapse;font-size:1rem}
td,th{padding:.45rem .3rem;border-bottom:1px solid var(--line);text-align:right}
.badge{display:inline-block;padding:.15rem .55rem;border-radius:999px;font-family:Syne,sans-serif;font-size:.7rem}
.badge.taken{background:#d8f3e7;color:var(--ok)}.badge.missed{background:#fde8e6;color:var(--danger)}
.badge.pending,.badge.reminded{background:#fff4d6;color:#8a6a00}.badge.skipped{background:#eee;color:#555}
.badge.critical{background:#fde8e6;color:var(--danger)}.badge.warning{background:#fff4d6;color:#8a6a00}
button,.btn{font-family:Syne,sans-serif;border:none;background:var(--sea);color:var(--foam);border-radius:.7rem;padding:.55rem .9rem;cursor:pointer}
button.ghost{background:transparent;color:var(--sea);border:1px solid var(--line)}
button.danger{background:var(--danger)}
input,select,textarea{width:100%;padding:.5rem .65rem;border:1px solid var(--line);border-radius:.6rem;font-family:Amiri,serif;font-size:1.05rem;margin:.25rem 0 .6rem;background:#fff}
.row{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}
.alert{padding:.75rem;border-radius:.8rem;background:#fff;border:1px solid var(--line);margin-bottom:.5rem}
.alert.critical{border-color:var(--danger);background:#fff5f4}
.outbox{font-size:.9rem;white-space:pre-wrap;background:#0b3d4a;color:#eef7f5;padding:.75rem;border-radius:.8rem;margin-bottom:.5rem}
</style>
</head>
<body>
<header>
  <h1 class="brand">Bchkito Care</h1>
  <nav>
    <a href="/">لوحة العائلة</a>
    <a href="/elder">محاكي القلادة</a>
  </nav>
</header>
<main>
  <div class="grid" style="margin-bottom:1rem">
    <div class="card"><h2>الجدة</h2><div class="stat" id="elderName">—</div><div class="muted" id="elderMeta"></div></div>
    <div class="card"><h2>التزام اليوم</h2><div class="stat" id="compliance">—</div><div class="muted" id="complianceDetail"></div></div>
    <div class="card"><h2>القلادة</h2><div class="stat" id="battery">—</div><div class="muted" id="online"></div></div>
  </div>

  <div class="grid">
    <div class="card" style="grid-column: span 1">
      <h2>تنبيهات العائلة</h2>
      <div id="alerts"></div>
    </div>
    <div class="card">
      <h2>واتساب (صندوق الإرسال)</h2>
      <div id="outbox"></div>
    </div>
  </div>

  <div class="card" style="margin-top:1rem">
    <div class="row" style="justify-content:space-between">
      <h2 style="margin:0">جرعات اليوم</h2>
      <div class="row">
        <button type="button" id="btnDue">محاكاة: حان وقت الدوا</button>
        <button type="button" class="ghost" id="btnRefresh">تحديث</button>
      </div>
    </div>
    <table><thead><tr><th>الدوا</th><th>الوقت</th><th>الحالة</th><th>إجراء</th></tr></thead><tbody id="doses"></tbody></table>
  </div>

  <div class="grid" style="margin-top:1rem">
    <div class="card">
      <h2>إضافة / تعديل دواء</h2>
      <input id="medName" placeholder="الاسم (ميتفورمين / إنسولين)"/>
      <input id="medDose" placeholder="الجرعة الظاهرة للعائلة"/>
      <select id="medRoute"><option value="oral">فموي</option><option value="insulin">إنسولين</option><option value="other">آخر</option></select>
      <input id="medTimes" placeholder="الأوقات HH:MM مفصولة بفاصلة — مثال 09:00,21:00"/>
      <button type="button" id="btnAddMed">حفظ الدواء</button>
    </div>
    <div class="card">
      <h2>تسجيل سكر الدم</h2>
      <input id="gluVal" type="number" placeholder="mg/dL"/>
      <input id="gluNote" placeholder="ملاحظة"/>
      <button type="button" id="btnGlu">حفظ</button>
      <div id="gluList" class="muted" style="margin-top:.75rem"></div>
    </div>
    <div class="card">
      <h2>موعد طبيب</h2>
      <input id="aptTitle" placeholder="العنوان"/>
      <input id="aptWhen" type="datetime-local"/>
      <input id="aptLoc" placeholder="المكان"/>
      <button type="button" id="btnApt">إضافة</button>
      <div id="aptList" class="muted" style="margin-top:.75rem"></div>
    </div>
  </div>
</main>
<script>
async function api(path, opts){
  const res = await fetch(path, Object.assign({headers:{'Content-Type':'application/json'}}, opts||{}));
  const data = await res.json();
  if(!res.ok) throw new Error(data.error||'error');
  return data;
}
function badge(status){return `<span class="badge ${status}">${status}</span>`}
async function refresh(){
  const s = await api('/api/care/state');
  const c = await api('/api/care/compliance');
  document.getElementById('elderName').textContent = s.elder.name;
  document.getElementById('elderMeta').textContent = `${s.elder.city} · مقدّم الرعاية: ${s.elder.caregiver_name}`;
  document.getElementById('battery').textContent = s.elder.pendant_battery + '%';
  document.getElementById('online').textContent = s.elder.pendant_online ? 'متصلة' : 'غير متصلة';
  const taken = c.counts.taken||0, total=c.total||0;
  document.getElementById('compliance').textContent = `${taken}/${total}`;
  document.getElementById('complianceDetail').textContent = `missed ${c.counts.missed||0} · pending ${c.counts.pending||0} · reminded ${c.counts.reminded||0}`;

  document.getElementById('alerts').innerHTML = (s.alerts||[]).slice(0,8).map(a=>`
    <div class="alert ${a.severity}">
      <div><span class="badge ${a.severity}">${a.type}</span> ${a.message_darija||a.message}</div>
      <div class="muted">${a.created_at}${a.acked_at?' · تمّت المعالجة':''}</div>
      ${a.acked_at?'':`<button class="ghost" data-ack="${a.id}">تمّت الاتصال بها</button>`}
    </div>`).join('') || '<div class="muted">لا تنبيهات</div>';

  document.getElementById('outbox').innerHTML = (s.whatsapp_outbox||[]).slice(0,5).map(m=>`
    <div class="outbox">${m.body}\n\n→ ${m.to||'?'}\n${m.delivered?'✓ delivered':(m.note||'stub')}</div>`).join('') || '<div class="muted">فارغ — ستظهر تنبيهات واتساب هنا</div>';

  const today = new Date().toISOString().slice(0,10);
  const doses = (s.doses||[]).filter(d=>(d.scheduled_at||'').startsWith(today) || true).slice(0,12);
  document.getElementById('doses').innerHTML = doses.map(d=>`<tr>
    <td>${d.medication_name}</td>
    <td>${(d.scheduled_at||'').slice(11,16)}</td>
    <td>${badge(d.status)}</td>
    <td class="row">
      <button class="ghost" data-mark="${d.id}" data-st="taken">أخذت</button>
      <button class="ghost" data-mark="${d.id}" data-st="missed">فوتت</button>
      <button class="ghost" data-mark="${d.id}" data-st="skipped">تخطت</button>
    </td></tr>`).join('');

  document.getElementById('gluList').innerHTML = (s.glucose||[]).slice(0,5).map(g=>`<div>${g.value_mg_dl??'—'} · ${g.note||''}</div>`).join('')||'لا سجلات';
  document.getElementById('aptList').innerHTML = (s.appointments||[]).map(a=>`<div>${a.title} — ${(a.at||'').slice(0,16)} · ${a.location||''}</div>`).join('')||'لا مواعيد';
}
document.getElementById('btnRefresh').onclick = refresh;
document.getElementById('btnDue').onclick = async()=>{ await api('/api/care/demo/due',{method:'POST',body:'{}'}); await refresh(); };
document.getElementById('btnAddMed').onclick = async()=>{
  const times = document.getElementById('medTimes').value.split(',').map(s=>s.trim()).filter(Boolean);
  await api('/api/care/medications',{method:'POST',body:JSON.stringify({
    name:document.getElementById('medName').value,
    dose_label:document.getElementById('medDose').value,
    route:document.getElementById('medRoute').value,
    times
  })});
  await refresh();
};
document.getElementById('btnGlu').onclick = async()=>{
  const v = document.getElementById('gluVal').value;
  await api('/api/care/glucose',{method:'POST',body:JSON.stringify({
    value_mg_dl: v?Number(v):null,
    note:document.getElementById('gluNote').value
  })});
  await refresh();
};
document.getElementById('btnApt').onclick = async()=>{
  const when = document.getElementById('aptWhen').value;
  await api('/api/care/appointments',{method:'POST',body:JSON.stringify({
    title:document.getElementById('aptTitle').value,
    at: when? new Date(when).toISOString(): new Date().toISOString(),
    location:document.getElementById('aptLoc').value
  })});
  await refresh();
};
document.body.addEventListener('click', async(e)=>{
  const ack = e.target.closest('[data-ack]');
  if(ack){ await api('/api/care/alerts/'+ack.dataset.ack+'/ack',{method:'POST',body:'{}'}); return refresh(); }
  const mark = e.target.closest('[data-mark]');
  if(mark){ await api('/api/care/doses/'+mark.dataset.mark,{method:'POST',body:JSON.stringify({status:mark.dataset.st})}); return refresh(); }
});
refresh(); setInterval(refresh, 4000);
</script>
</body></html>
"""

ELDER_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Bchkito — القلادة</title>
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Syne:wght@700;800&display=swap" rel="stylesheet"/>
<style>
:root{--sea:#0b3d4a;--foam:#eef7f5;--saff:#e2a008;--ink:#102a32;--muted:#5a7a82}
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:Amiri,serif;background:radial-gradient(ellipse at 30% 0%,rgba(226,160,8,.2),transparent 50%),linear-gradient(165deg,#f3faf8,#cfe4df);color:var(--ink)}
header{padding:1rem 1.25rem;display:flex;justify-content:space-between;align-items:center}
.brand{font-family:Syne,sans-serif;font-weight:800;font-size:1.8rem;color:var(--sea);margin:0}
a{color:var(--sea);font-family:Syne,sans-serif;font-size:.85rem;text-decoration:none}
main{max-width:560px;margin:0 auto;padding:0 1rem 3rem}
.pendant{margin:1rem auto;width:min(280px,70vw);aspect-ratio:1;border-radius:50%;background:radial-gradient(circle at 50% 40%,#1a6b7c,#0b3d4a 60%,#062830);box-shadow:0 28px 50px rgba(6,40,48,.35);display:grid;place-items:center;position:relative;transition:transform .2s}
.pendant.talking{animation:pulse 1s ease infinite}
.pendant::before{content:"";position:absolute;top:-36px;width:8px;height:40px;background:#5a7a82;border-radius:4px}
.face{text-align:center;color:var(--foam)}
.eyes{display:flex;gap:2rem;justify-content:center;margin-bottom:.6rem}
.eye{width:22px;height:22px;background:var(--foam);border-radius:50%}
.mouth{width:40px;height:8px;margin:0 auto;background:var(--saff);border-radius:999px}
.sos{display:block;width:100%;margin:1rem 0;padding:1.1rem;font-size:1.4rem;font-family:Syne,sans-serif;font-weight:800;border:none;border-radius:1rem;background:#b42318;color:#fff;cursor:pointer}
.chips{display:flex;flex-wrap:wrap;gap:.45rem;margin:1rem 0}
.chips button{font-family:Amiri,serif;font-size:1.05rem;border:1px solid rgba(11,61,74,.12);background:rgba(255,255,255,.7);border-radius:999px;padding:.4rem .85rem;cursor:pointer;color:var(--sea)}
.panel{background:rgba(255,255,255,.75);border:1px solid rgba(11,61,74,.12);border-radius:1.1rem;padding:1rem}
textarea{width:100%;min-height:70px;border-radius:.8rem;border:1px solid rgba(11,61,74,.12);padding:.75rem;font-family:Amiri,serif;font-size:1.2rem}
.send{margin-top:.5rem;width:100%;padding:.75rem;border:none;border-radius:.8rem;background:var(--sea);color:var(--foam);font-family:Syne,sans-serif;font-weight:700;cursor:pointer}
.bubble{margin-top:.9rem;background:var(--sea);color:var(--foam);padding:1rem;border-radius:1rem;font-size:1.3rem;line-height:1.5;min-height:4rem}
.meta{font-family:Syne,sans-serif;font-size:.75rem;color:var(--muted);margin-top:.5rem}
@keyframes pulse{50%{transform:scale(1.03)}}
.hint{color:var(--muted);margin-top:1rem}
</style>
</head>
<body>
<header>
  <h1 class="brand">Bchkito</h1>
  <a href="/">لوحة العائلة</a>
</header>
<main>
  <div class="pendant" id="pendant"><div class="face"><div class="eyes"><span class="eye"></span><span class="eye"></span></div><div class="mouth"></div></div></div>
  <button class="sos" id="sos" type="button">🆘 نجدة — عيّطي لبنتي</button>
  <div class="chips">
    <button data-q="وقت الدوا">وقت الدوا</button>
    <button data-q="خذيت الدوا">خذيت الدوا</button>
    <button data-q="ماخذيتش">ماخذيتش</button>
    <button data-q="نلعبو">نلعبو</button>
    <button data-q="قسيت السكر 140">السكر 140</button>
    <button data-q="كيفاش الجو فإفران">الجو</button>
    <button data-q="صباح الخير">صباح الخير</button>
  </div>
  <div class="panel">
    <textarea id="input" placeholder="هضر بالدارجة… (الجدة ماكتبش عادة — هاد غير للمحاكاة)"></textarea>
    <button class="send" id="send" type="button">قولي لبشكيتو</button>
    <div class="bubble" id="reply">بشكيتو غادي يهضر هنا.</div>
    <div class="meta" id="meta">intent: —</div>
  </div>
  <p class="hint">محاكاة القلادة: تذكير الدوا، تأكيد، نجدة، وألعاب الذاكرة. العائلة كتسير كلشي من اللوحة.</p>
</main>
<script>
const reply=document.getElementById('reply'), meta=document.getElementById('meta'), pendant=document.getElementById('pendant');
async function talk(text){
  const q=(text||'').trim(); if(!q) return;
  pendant.classList.add('talking'); reply.textContent='…';
  try{
    const res=await fetch('/api/turn',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:q})});
    const data=await res.json();
    if(!res.ok) throw new Error(data.error||'fail');
    reply.textContent=data.reply;
    meta.textContent=`intent: ${data.intent} · ${data.latency_s}s`;
  }catch(e){ reply.textContent='خطأ: '+e.message; }
  finally{ pendant.classList.remove('talking'); }
}
document.getElementById('send').onclick=()=>talk(document.getElementById('input').value);
document.getElementById('sos').onclick=async()=>{
  await fetch('/api/care/sos',{method:'POST',body:'{}'});
  talk('عيطي لبنتي ما بخير');
};
document.querySelector('.chips').onclick=e=>{
  const b=e.target.closest('button[data-q]'); if(!b) return;
  document.getElementById('input').value=b.dataset.q; talk(b.dataset.q);
};
</script>
</body></html>
"""

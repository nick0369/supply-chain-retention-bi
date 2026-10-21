const data=window.OPERATIONS;
const $=id=>document.getElementById(id);
const number=value=>new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(value);
const compact=value=>new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2}).format(value);
const pct=value=>`${(value*100).toFixed(1)}%`;
const sum=(rows,key)=>rows.reduce((a,r)=>a+r[key],0);
const ratio=(a,b)=>b?a/b:0;
const esc=value=>String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
if(!data)throw Error('Run operations-bi build before opening dashboard');
for(const [id,key] of [['market','market'],['mode','shipping_mode']]){
 for(const value of [...new Set(data.delivery.map(r=>r[key]))].sort()){
  const option=document.createElement('option');option.value=value;option.textContent=value;$(id).append(option);
 }
}
function selected(){return data.delivery.filter(r=>($('market').value==='all'||r.market===$('market').value)&&($('mode').value==='all'||r.shipping_mode===$('mode').value));}
function render(){
 const rows=selected(),orders=sum(rows,'completed_orders'),late=sum(rows,'late_orders');
 const cards=[['Completed orders',number(orders),'Distinct orders · COMPLETE/CLOSED'],['Late-delivery rate',pct(ratio(late,orders)),`${number(late)} observed late orders`],['Net sales',compact(sum(rows,'net_sales')),'Dataset monetary units · not INR/USD'],['Recorded profit',compact(sum(rows,'recorded_profit')),'Source-field sum · unaudited']];
 $('cards').innerHTML=cards.map(([label,value,note])=>`<div class="card"><small>${label}</small><strong>${value}</strong><span>${note}</span></div>`).join('');
 const modes=[...new Set(rows.map(r=>r.shipping_mode))];
 $('deliveryBars').innerHTML=modes.map(mode=>{const group=rows.filter(r=>r.shipping_mode===mode),rate=ratio(sum(group,'late_orders'),sum(group,'completed_orders'));return `<div class="bar-row"><div class="bar-title"><span>${esc(mode)}</span><strong>${pct(rate)} · ${number(sum(group,'completed_orders'))} orders</strong></div><div class="track"><div class="fill" style="width:${rate*100}%"></div></div></div>`;}).join('');
 $('deliveryRows').innerHTML=rows.map(r=>`<tr><td>${esc(r.market)}</td><td>${esc(r.shipping_mode)}</td><td>${number(r.completed_orders)}</td><td>${number(r.late_orders)}</td><td>${pct(r.late_rate)}</td><td>${compact(r.net_sales)}</td></tr>`).join('');
 const cost=Math.max(0,Math.min(1000000,Number($('cost').value)||0));
 $('preventValue').textContent=`${$('prevent').value}%`;
 $('savings').textContent=`${compact(late*Number($('prevent').value)/100*cost)} units`;
}
const maximum=Math.max(...data.monthly.map(r=>r.net_sales));
$('monthlyChart').innerHTML=data.monthly.map(r=>`<div class="history-row"><span>${r.month}</span><div class="history-bars"><div class="bill" style="width:${100*r.net_sales/maximum}%"></div></div><span class="history-value">${compact(r.net_sales)}</span></div>`).join('');
$('window').textContent=`Snapshot ${data.report.window.as_of} · observed through ${data.report.window.observed_through}`;
$('retentionCards').innerHTML=data.retention.map(r=>`<div class="card"><small>${r.segment}</small><strong>${number(r.customers)}</strong><span>${r.future_inactive_rate===null?'Future outcome unobserved':pct(r.future_inactive_rate)+' inactive next 90d'}</span></div>`).join('');
const cohorts=[...new Set(data.cohorts.map(r=>r.cohort))].sort();
$('cohortRows').innerHTML=cohorts.map(cohort=>{const rows=data.cohorts.filter(r=>r.cohort===cohort);return `<tr><td>${cohort}</td><td>${number(rows[0].size)}</td>`+rows.map(r=>`<td style="background:${r.retention===null?'#f4f7f8':`rgba(39,135,131,${0.05+r.retention*0.45})`}">${r.retention===null?'—':pct(r.retention)}</td>`).join('')+'</tr>';}).join('');
$('checks').innerHTML=data.report.checks.map(r=>`<span class="check">${r.passed?'✓':'✕'} ${r.name.replaceAll('_',' ')}</span>`).join('');
$('warnings').textContent=(data.report.quality_warnings||[]).join(' ');
$('build').textContent=`${number(data.report.line_count)} lines → ${number(data.report.orders)} orders · ${data.report.database_dialect} · ${data.report.ingestion.status} · ${data.report.built_at_utc} · SHA-256 ${data.report.source_sha256}`;
['market','mode','prevent','cost'].forEach(id=>$(id).addEventListener('input',render));
$('reset').onclick=()=>{$('market').value='all';$('mode').value='all';render();};
$('export').onclick=()=>{const rows=selected(),fields=['market','shipping_mode','completed_orders','late_orders','late_rate','net_sales','recorded_profit'];const csv=[fields.join(','),...rows.map(r=>fields.map(f=>JSON.stringify(r[f])).join(','))].join('\n');const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));link.download='delivery-performance.csv';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);};
render();

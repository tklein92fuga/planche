import {startMotion} from './motion.js?v=motion-1';
import {types,statuses,initial,key,today,importRows} from './data.js?v=motion-1';
import {createCatalog} from './catalog-ui.js?v=motion-1';
import {createPaths} from './paths-ui.js?v=motion-1';
import {workStatus,updateWorkStatus} from './progress-state.js';
const storage='planche.v1',main=document.querySelector('#main'),modal=document.querySelector('#modal');
const read=()=>{try{return JSON.parse(localStorage.getItem(storage))||initial();}catch{return initial();}};
let state=read(),toastTimer,importBusy=false;
const pages={accueil:['◈','Vue d’ensemble'],decouvrir:['✺','Découvrir'],parcours:['▦','Parcours']};
const page=()=>({catalogue:'decouvrir',decouverte:'decouvrir'}[location.hash.slice(1)]|| (Object.hasOwn(pages,location.hash.slice(1))?location.hash.slice(1):'accueil'));
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
const opts=(values,selected)=>Object.entries(values).map(([k,v])=>`<option value="${esc(k)}" ${k===selected?'selected':''}>${esc(v)}</option>`).join('');
const typeNames=Object.fromEntries(Object.entries(types).map(([k,v])=>[k,v.label]));
const completed=()=>state.items.filter(i=>i.status==='done');
const xp=()=>completed().length*25+state.items.filter(i=>i.rating>0).length*10+state.items.filter(i=>String(i.review||'').trim()).length*15;
const level=()=>Math.floor(xp()/100)+1;
const bar=(n,max)=>`<div class="track"><i style="width:${max?Math.min(100,Math.round(n/max*100)):0}%"></i></div>`;
const byId=id=>state.items.find(i=>i.id===id);
function notify(message){const toast=document.querySelector('#toast');toast.textContent=message;toast.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.classList.remove('visible'),3600);}
function save(){try{localStorage.setItem(storage,JSON.stringify(state));render();if(page()==='decouvrir')pathsUI.sync();return true;}catch{state=read();render();notify('Sauvegarde impossible. Vérifie l’espace disponible.');return false;}}
function setStatus(work,status){state.items=updateWorkStatus(state.items,work,status,{resolved:pathsUI.resolved(),date:today(),id:crypto.randomUUID()});const saved=save();if(saved)document.dispatchEvent(new CustomEvent('planche:status',{detail:{id:work.id,status}}));if(saved)notify(status==='done'?'Œuvre terminée · progression mise à jour.':status==='doing'?'Œuvre en cours · progression mise à jour.':'Œuvre remise à découvrir.');return saved;}
const statusOf=work=>workStatus(state.items,work,pathsUI.resolved());
function render(){
 const current=page();
 if(location.hash&& !Object.hasOwn(pages,location.hash.slice(1))&&!['#catalogue','#decouverte'].includes(location.hash))history.replaceState(null,'','#accueil');
 document.querySelector('#nav').innerHTML=Object.entries(pages).map(([k,[icon,label]])=>`<a href="#${k}" ${current===k?'aria-current="page"':''}><span>${icon}</span>${label}</a>`).join('');
 document.querySelector('#side').innerHTML=`<section class="level"><span class="stat-icon">✦</span><b>Niveau ${level()}</b><small>${xp()%100} / 100 XP</small>${bar(xp()%100,100)}</section>${state.demo?'<button class="ghost demo" data-act="demo">Retirer la démo</button>':''}`;
 if(current==='decouvrir'){main.innerHTML=catalogUI.mount();catalogUI.load();}
 else{main.innerHTML=pathsUI.mount(current);pathsUI.load();}
}
function show(title,body){modal.innerHTML=`<div class="section-line modal-head"><h2 id="modal-title">${title}</h2><button class="ghost" data-act="close" aria-label="Fermer">×</button></div>${body}`;modal.setAttribute('aria-labelledby','modal-title');if(!modal.open)modal.showModal();}
const field=(label,name,value='',type='text',attrs='')=>`<label>${label}<input name="${name}" type="${type}" value="${esc(value)}" ${attrs}></label>`;
const select=(label,name,values,value)=>`<label>${label}<select name="${name}">${opts(values,value)}</select></label>`;
const actions=label=>`<div class="form-actions"><button class="dark" type="submit">${label}</button></div>`;
function cover(i){
  const ident=i.catalogId||i.id;
  const steam=i.evidence?.some(e=>e.source==='Metacritic')?null:String(ident).match(/^steam:(\d+)$/)||String(i.image||'').match(/steam\/apps\/(\d+)/);
  const fallback=/^https?:\/\//i.test(i.image||'')?i.image:'';
  const image=steam?'https://cdn.cloudflare.steamstatic.com/steam/apps/'+steam[1]+'/library_600x900.jpg':
    fallback||((i.type==='film'||i.type==='tv'||i.type==='game')&&/^(imdb:|steam:|awards:)/.test(ident)?'/api/catalog/art?id='+encodeURIComponent(ident):'');
  const lookup=!/^(imdb:|steam:|books:|awards:)/.test(ident)?'/api/catalog/art?'+new URLSearchParams({title:i.title,type:i.type,year:i.year||''}):'';
  return `<div class="cover" style="--tint:${types[i.type].color}"><em>${esc(i.title)}</em>${image?`<img src="${esc(image)}" data-fallback="${esc(fallback)}" data-lookup="${esc(lookup)}" alt="" loading="lazy" referrerpolicy="no-referrer">`:''}<span class="tag ${i.status}">${statuses[i.status]||''}</span></div>`;
}
main.addEventListener('error',e=>{
  const img=e.target;
  if(img.tagName!=='IMG')return;
  if(img.dataset.fallback&&img.src!==img.dataset.fallback){img.classList.add('cover-fallback');img.src=img.dataset.fallback;img.dataset.fallback='';}
  else if(img.dataset.lookup){img.src=img.dataset.lookup;img.dataset.lookup='';}
  else img.hidden=true;
},true);

function importDialog(){
  show('Importer une liste',`<form data-form="import"><p class="muted">Formats .xlsx et .csv, jusqu’à 8 Mo. La première ligne doit contenir une colonne « Titre ». Pour une liste mixte, ajoute une colonne « Type ».</p><label class="drop">Choisir un fichier<input name="file" type="file" accept=".csv,.xlsx" required></label>${select('Format si la colonne Type est vide','type',typeNames,'film')}<label class="check"><input type="checkbox" name="enrich" checked> Rechercher les métadonnées et les visuels disponibles</label><a href="exemple.csv" download>Télécharger un CSV d’exemple ↓</a>${actions('Importer')}<p class="form-message" role="status"></p></form>`);
}
function tell(form, message){form.querySelector('.form-message').textContent=message;}
async function api(path, body){
  const response=await fetch('/api/'+path,{method:'POST',body});
  const payload=await response.json();
  if(!response.ok)throw Error(payload.error||'Le service est indisponible.');
  return payload;
}
async function importFile(form,data){
  const file=data.file, extension=file.name.split('.').pop().toLowerCase();
  if(!['csv','xlsx'].includes(extension))throw Error('Choisis un fichier .csv ou .xlsx.');
  tell(form,'Lecture du fichier…');
  const rows=await api(extension,file);
  const name=(data.name||'').trim()||file.name.replace(/\.[^.]+$/,'');
  const existing=state.collections.find(c=>key(c.name)===key(name));
  const collection=existing||{id:crypto.randomUUID(),name};
  const items=importRows(rows,data.type,collection.id);
  if(!items.length)throw Error('Aucune ligne avec un titre.');
  const seen=new Map();
  const add = i=>{
    const sig=[i.type,key(i.title)].join('|');
    const year=String(i.year||'');
    const years=seen.get(sig)||new Set();
    if(years.has(year)||years.has('')||(!year&&years.size))return false;
    years.add(year);
    seen.set(sig,years);
    return true;
  };
  state.items.filter(i=>i.collection===collection.id).forEach(add);
  const fresh=items.filter(add);
  if(!fresh.length)throw Error('Toutes ces œuvres sont déjà présentes dans cette collection.');
  if(!existing)state.collections.push(collection);
  state.items.push(...fresh);
  if(!save())throw Error('Impossible de sauvegarder cet import.');
  let enriched=0;
  if(data.enrich){
    for(let index=0;index<fresh.length;index+=4){
      tell(form,`${fresh.length} œuvres sauvegardées. Enrichissement ${index} / ${fresh.length}…`);
      const batch=fresh.slice(index,index+4);
      const found=await api('enrich',JSON.stringify(batch.map(({type,title,year})=>({type,title,year})))).catch(()=>[]);
      found.forEach((metadata,n)=>{
        if(!metadata.source)return;
        const item=byId(batch[n].id);
        if(!item)return;
        for(const [k,v] of Object.entries(metadata))if(v&&!item[k])item[k]=v;
        enriched++;
      });
      save();
    }
  }
  location.hash='accueil';render();
  modal.close();
  notify(`${fresh.length} ajoutée(s) · ${enriched} correspondance(s) · ${items.length-fresh.length} doublon(s)`);
}

document.addEventListener('click',event=>{
 const button=event.target.closest('[data-act]');if(!button)return;
 if(button.dataset.act==='import')importDialog();
 if(button.dataset.act==='close'&&!importBusy)modal.close();
 if(button.dataset.act==='demo'&&confirm('Retirer les données de démonstration ?')){state.items=state.items.filter(i=>!i.id.startsWith('demo-'));state.demo=false;save();}
});
document.addEventListener('submit',async event=>{
 const form=event.target;if(form.dataset.form!=='import')return;event.preventDefault();if(importBusy)return;
 importBusy=true;const buttons=modal.querySelectorAll('button');buttons.forEach(b=>b.disabled=true);
 try{await importFile(form,Object.fromEntries(new FormData(form)));}catch(error){tell(form,error.message);}finally{importBusy=false;buttons.forEach(b=>b.disabled=false);}
});
modal.addEventListener('cancel',event=>{if(importBusy)event.preventDefault();});
window.addEventListener('hashchange',()=>{render();main.focus({preventScroll:true});window.scrollTo(0,0);});
window.addEventListener('storage',event=>{if((event.key===storage||event.key==='planche.trophies.v1')&&!importBusy){state=read();render();}});
const catalogUI=createCatalog({types,esc,opts,cover,show,notify,library:()=>state.items,setStatus,statusOf});
const pathsUI=createPaths({esc,library:()=>state.items,level,xp,notify,setStatus,open:item=>catalogUI.open(item)});
startMotion();
render();
if(page()==='decouvrir')pathsUI.sync();

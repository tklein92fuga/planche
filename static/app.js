import {types,statuses,initial,key,today,importRows} from './data.js';
import {createCatalog} from './catalog-ui.js';
import {createPaths} from './paths-ui.js';
const storage = 'planche.v1';
const main = document.querySelector('#main');
const modal = document.querySelector('#modal');
const read = ()=>{try{return JSON.parse(localStorage.getItem(storage)) || initial();}catch{return initial();}};
let state = read();
let filter = {type:'all',status:'all',query:'',collection:'all'};
let toastTimer;
let importBusy = false;
const pages = {accueil:['◈','Vue d’ensemble'],bibliotheque:['▦','Bibliothèque'],decouvrir:['✺','Découvrir'],parcours:['▦','Parcours'],profil:['♜','Profil & trophées'],collections:['▱','Collections'],objectifs:['◎','Objectifs & badges'],recommandations:['✧','Pour moi']};
const page = ()=>{
  const route=location.hash.slice(1);
  const current={catalogue:'decouvrir',decouverte:'decouvrir'}[route]||route;
  return Object.hasOwn(pages,current)?current:'accueil';
};
const esc = value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
const opts = (values, selected)=>Object.entries(values).map(([k,v])=>`<option value="${esc(k)}" ${k===selected?'selected':''}>${esc(v)}</option>`).join('');
const typeNames = Object.fromEntries(Object.entries(types).map(([k,v])=>[k,v.label]));
const progress = (n,max)=>max?Math.round(n/max*100):0;
const collections = ()=>Object.fromEntries(state.collections.map(c=>[c.id,c.name]));
const byId = id=>state.items.find(i=>i.id===id);
const completed = ()=>state.items.filter(i=>i.status==='done');
const xp = ()=>completed().length*25+state.items.filter(i=>i.rating>0).length*10+state.items.filter(i=>i.review.trim()).length*15;
const level = ()=>Math.floor(xp()/100)+1;
const bar = (n,max)=>`<div class="track"><i style="width:${Math.min(100,progress(n,max))}%"></i></div>`;
const mediaLength = i=>i.length?(i.type==='film'?`${esc(i.length)}${/^\d+$/.test(i.length)?' min':''}`:i.type==='book'?`${esc(i.length)}${/^\d+$/.test(i.length)?' p.':''}`:esc(i.length)):'';
function save(){
  try {localStorage.setItem(storage,JSON.stringify(state)); render(); if(!['parcours','profil'].includes(page()))pathsUI.sync(); return true;}
  catch {state=read(); render(); notify('Sauvegarde impossible. Vérifie l’espace disponible dans le navigateur.');return false;}
}
function notify(message){
  const toast=document.querySelector('#toast');
  toast.textContent=message;
  toast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>toast.classList.remove('visible'),3600);
}
function cover(i){
  const ident=i.catalogId||i.id;
  const steam=String(ident).match(/^steam:(\d+)$/)||String(i.image||'').match(/steam\/apps\/(\d+)/);
  const fallback=/^https?:\/\//i.test(i.image||'')?i.image:'';
  const image=steam?'https://cdn.cloudflare.steamstatic.com/steam/apps/'+steam[1]+'/library_600x900.jpg':
    fallback||((i.type==='film'||i.type==='game')&&/^(imdb:|steam:|awards:)/.test(ident)?'/api/catalog/art?id='+encodeURIComponent(ident):'');
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

function card(i, reason=''){
  return `<article class="work"><button class="work-open" data-act="edit" data-id="${i.id}">${cover(i)}<span class="work-title">${esc(i.title)}</span><span class="muted">${types[i.type].label}${i.year?' · '+esc(i.year):''}${i.genre?' · '+esc(i.genre):''}</span></button>${reason?`<p class="reason">${esc(reason)}</p>`:''}</article>`;
}
const empty = message=>`<div class="empty">${message}</div>`;
function title(kicker,heading,description,action=''){
  return `<div class="page-title"><div><p class="eyebrow">${kicker}</p><h1>${heading}</h1><p class="muted">${description}</p></div>${action}</div>`;
}
function goalsMarkup(){
  if(!state.goals.length)return empty('Aucun objectif pour le moment.');
  return state.goals.map(g=>{
    const count=completed().filter(i=>(g.type==='all'||i.type===g.type)&&i.completed>=g.start&&(!g.end||i.completed<=g.end)).length;
    return `<article class="panel goal"><div class="section-line"><div><span class="eyebrow">${count>=g.target?'OBJECTIF ATTEINT':'OBJECTIF PERSONNEL'}</span><h3>${esc(g.title)}</h3></div><button class="ghost" data-act="goal" data-id="${g.id}" aria-label="Modifier l’objectif">•••</button></div><p class="muted">${g.type==='all'?'Tous les formats':types[g.type].plural} · depuis le ${esc(g.start)}${g.end?' · jusqu’au '+esc(g.end):''}</p><div class="section-line goal-count"><b>${count} / ${g.target}</b><span>${Math.min(100,progress(count,g.target))} %</span></div>${bar(count,g.target)}</article>`;
  }).join('');
}
function dashboard(){
  const done=completed(), percent=progress(done.length,state.items.length);
  const hours=Math.round(done.filter(i=>i.type==='film').reduce((total,i)=>total+(/^\d+(?:[.,]\d+)?(?:\s*min)?$/i.test(i.length)?parseFloat(String(i.length).replace(',','.')):0),0));
  const days=Array.from({length:7},(_,i)=>today(i-6));
  const counts=days.map(d=>done.filter(i=>i.completed===d).length);
  const recent=[...state.items].sort((a,b)=>Number(b.status==='doing')-Number(a.status==='doing')).slice(0,4);
  return `<section class="hero"><div class="hero-text"><p class="eyebrow"><span class="pulse"></span> LE JOURNAL DE TES DÉCOUVERTES</p><h1>Culture<br><em>en cours.</em></h1><p>Films, livres et jeux. Fais de ta liste d’envies une collection qui avance.</p><a class="dark" href="#bibliotheque">Ma bibliothèque &nbsp; ↗</a></div><div class="hero-art" aria-hidden="true"></div></section>
  <section class="stat-grid" aria-label="Statistiques"><article class="panel stat"><div><span>Œuvres terminées</span><b>${done.length}<small> / ${state.items.length}</small></b></div><div class="ring" style="--pct:${percent}%" aria-label="${percent} % terminé"><span>${percent}%</span></div></article><article class="panel stat"><div><span>Temps de cinéma</span><b>${Math.floor(hours/60)}<small> h </small>${hours%60}<small> min</small></b></div><i class="stat-icon peach">◉</i></article><article class="panel stat"><div><span>Progression</span><b>Niv. ${level()}</b></div><i class="stat-icon lime">✦</i></article></section>
  <div class="dashboard-grid"><section class="panel activity"><div class="section-line"><h2>Activité</h2><span class="chip">7 derniers jours</span></div><div class="chart" aria-label="Œuvres terminées par jour">${days.map((d,i)=>`<div class="chart-column"><span>${counts[i]}</span><i style="height:${Math.max(3,counts[i]/Math.max(1,...counts)*58)}px"></i><small>${new Date(d+'T12:00').toLocaleDateString('fr',{weekday:'short'})}</small></div>`).join('')}</div></section><section class="panel mix"><h2>Par format</h2>${Object.entries(types).map(([k,t])=>{
    const total=state.items.filter(i=>i.type===k).length,n=done.filter(i=>i.type===k).length;
    return `<div><div class="section-line"><span>${t.icon} &nbsp; ${t.plural}</span><b>${n} / ${total}</b></div>${bar(n,total)}</div>`;
  }).join('')}</section></div>
  <section class="shelf"><div class="section-line"><h2>Sur l’étagère</h2><a href="#bibliotheque">Tout voir ↗</a></div>${recent.length?`<div class="works">${recent.map(i=>card(i)).join('')}</div>`:empty('Importe une liste ou ajoute ta première œuvre.')}</section>`;
}
function library(){
  return title('TES ŒUVRES','Bibliothèque<span>.</span>','Retrouve tes listes et reprends là où tu en étais.', '<button class="dark" data-act="edit">+ Ajouter une œuvre</button>')+
  `<section class="library"><div class="filter-bar"><input type="search" id="search" placeholder="Rechercher un titre, un genre…" aria-label="Rechercher" value="${esc(filter.query)}"><select id="filter-status" aria-label="Statut">${opts({all:'Tous les statuts',...statuses},filter.status)}</select><select id="filter-collection" aria-label="Collection">${opts({all:'Toutes les collections',...collections()},filter.collection)}</select></div><div class="tabs">${Object.entries({all:'Tout',...Object.fromEntries(Object.entries(types).map(([k,v])=>[k,v.plural]))}).map(([k,v])=>`<button data-act="type" data-id="${k}" aria-pressed="${filter.type===k}">${v}</button>`).join('')}</div><div id="results"></div></section>`;
}
function results(){
  const matched=state.items.filter(i=>(filter.type==='all'||filter.type===i.type)&&(filter.status==='all'||filter.status===i.status)&&(filter.collection==='all'||filter.collection===i.collection)&&key([i.title,i.creator,i.genre].join(' ')).includes(key(filter.query)));
  document.querySelector('#results').innerHTML=`<p class="muted count">${matched.length} œuvre${matched.length===1?'':'s'}</p>`+(matched.length?`<div class="works">${matched.map(i=>card(i)).join('')}</div>`:empty('Aucune œuvre ne correspond à ces filtres.'));
}
function recommendation(){
  const fav=state.items.filter(i=>i.rating>=4);
  const genres=i=>String(i.genre||'').split(/[,;/]/).map(key).filter(Boolean);
  const ranked=state.items.filter(i=>i.status!=='done').map(i=>{
    const related=fav.filter(f=>f.id!==i.id&&genres(i).some(g=>genres(f).includes(g)));
    return {i,score:related.length*3+(i.status==='doing'?2:0)+fav.filter(f=>f.type===i.type&&f.id!==i.id).length*.25,
      reason:related.length?`Dans le même genre que ${related[0].title}, que tu as bien noté.`:i.status==='doing'?'À reprendre dans tes œuvres en cours.':'Une œuvre à découvrir dans ta bibliothèque.'};
  }).sort((a,b)=>b.score-a.score);
  return title('LA SUITE DU PROGRAMME','Pour moi<span>.</span>','Des suggestions parmi les œuvres de ta bibliothèque, selon tes notes et ta progression.')+
    (ranked.length?`<div class="works">${ranked.slice(0,8).map(r=>card(r.i,r.reason)).join('')}</div>`:empty('Ajoute une œuvre à découvrir pour recevoir une suggestion.'));
}
function render(){
  const current=page();
  document.querySelector('#nav').innerHTML=Object.entries(pages).map(([k,[icon,label]])=>`<a href="#${k}" ${current===k?'aria-current="page"':''}><span>${icon}</span>${label}</a>`).join('');
  document.querySelector('#side').innerHTML=`<section class="level"><span class="stat-icon">✦</span><b>Niveau ${level()}</b><small>${xp()%100} / 100 XP</small>${bar(xp()%100,100)}</section>${state.demo?'<button class="ghost demo" data-act="demo">Retirer la démo</button>':''}`;
  if(current==='parcours'||current==='profil'){main.innerHTML=pathsUI.mount(current);pathsUI.load();}
  if(current==='decouvrir'){main.innerHTML=catalogUI.mount();catalogUI.load();}
  if(current==='accueil')main.innerHTML=dashboard();
  if(current==='bibliotheque'){main.innerHTML=library();results();}
  if(current==='collections')main.innerHTML=title('TES LISTES','Collections<span>.</span>','Regroupe tes œuvres comme tu le souhaites.','<button class="dark" data-act="collection">+ Nouvelle collection</button>')+
    (state.collections.length?`<div class="collection-grid">${state.collections.map(c=>{
      const items=state.items.filter(i=>i.collection===c.id), n=items.filter(i=>i.status==='done').length;
      return `<article class="panel collection"><div class="section-line"><i class="stat-icon lime">▱</i><button class="ghost" data-act="collection" data-id="${c.id}" aria-label="Modifier ${esc(c.name)}">•••</button></div><h2>${esc(c.name)}</h2><p class="muted">${n} sur ${items.length} terminées</p>${bar(n,items.length)}<button data-act="view-collection" data-id="${c.id}">Ouvrir ↗</button></article>`;
    }).join('')}</div>`:empty('Crée une collection ou importe une liste.'));
  if(current==='objectifs'){
    const badges=[['✦','Premier pas',completed().length>=1,'Terminer une œuvre'],['◈','Curiosité',Object.keys(types).every(t=>completed().some(i=>i.type===t)),'Terminer une œuvre de chaque format'],['✎','La critique',state.items.some(i=>i.review.trim()),'Écrire une critique'],['✺','Dix au compteur',completed().length>=10,'Terminer dix œuvres']];
    main.innerHTML=title('TON PARCOURS','Objectifs & badges<span>.</span>','25 XP par œuvre terminée, 10 XP par note, 15 XP par critique.','<button class="dark" data-act="goal">+ Nouvel objectif</button>')+
    `<div class="collection-grid">${goalsMarkup()}</div><section class="shelf"><h2>Badges</h2><div class="badge-grid">${badges.map(([icon,name,earned,rule])=>`<article class="panel badge ${earned?'earned':''}"><i>${icon}</i><h3>${name}</h3><p>${rule}</p><small>${earned?'Débloqué':'À débloquer'}</small></article>`).join('')}</div></section>`;
  }
  if(current==='recommandations')main.innerHTML=recommendation();
}
function show(title,body){
  modal.innerHTML=`<div class="section-line modal-head"><h2 id="modal-title">${title}</h2><button class="ghost" data-act="close" aria-label="Fermer">×</button></div>${body}`;
  modal.setAttribute('aria-labelledby','modal-title');
  if(!modal.open)modal.showModal();
}
const field=(label,name,value='',type='text',attrs='')=>`<label>${label}<input name="${name}" type="${type}" value="${esc(value)}" ${attrs}></label>`;
const select=(label,name,values,value)=>`<label>${label}<select name="${name}">${opts(values,value)}</select></label>`;
const actions=(saveLabel,remove=false)=>`<div class="form-actions">${remove?'<button type="button" class="danger" data-act="remove">Supprimer</button>':''}<button class="dark" type="submit">${saveLabel}</button></div>`;
function edit(id){
  const i=byId(id)||{};
  show(id?'Fiche de l’œuvre':'Ajouter une œuvre',`<form data-form="item" data-id="${id||''}">${field('Titre','title',i.title,'text','required maxlength="200"')}<div class="form-grid">${select('Format','type',typeNames,i.type)}${select('Statut','status',statuses,i.status)}${select('Collection','collection',{'':'Sans collection',...collections()},i.collection)}${field('Année','year',i.year,'number','min="1" max="9999"')}${field('Auteur, cinéaste ou studio','creator',i.creator)}${field('Genre','genre',i.genre)}${field('Durée (min) ou pages','length',i.length)}${select('Note sur 5','rating',{0:'Sans note',1:'1 ★',2:'2 ★',3:'3 ★',4:'4 ★',5:'5 ★'},String(i.rating||0))}</div><label>Critique<textarea name="review" rows="3">${esc(i.review)}</textarea></label>${field('Adresse du visuel','image',i.image,'url')}<div class="section-line"><button type="button" data-act="lookup">✧ Chercher les métadonnées</button>${i.source?`<small class="muted">Source : ${esc(i.source)}</small>`:''}</div>${actions('Enregistrer',Boolean(id))}<p class="form-message" role="status"></p></form>`);
}
function collectionDialog(id){
  const c=state.collections.find(c=>c.id===id);
  show(c?'Modifier la collection':'Nouvelle collection',`<form data-form="collection" data-id="${id||''}">${field('Nom','name',c?.name,'text','required maxlength="100"')}${actions('Enregistrer',Boolean(c))}</form>`);
}
function goalDialog(id){
  const g=state.goals.find(g=>g.id===id);
  show(g?'Modifier l’objectif':'Nouvel objectif',`<form data-form="goal" data-id="${id||''}">${field('Nom de l’objectif','title',g?.title,'text','required maxlength="100"')}<div class="form-grid">${select('Format','type',{all:'Tous les formats',...typeNames},g?.type)}${field('Nombre à terminer','target',g?.target||3,'number','required min="1" max="10000"')}${field('Date de début','start',g?.start||today().slice(0,7)+'-01','date','required')}${field('Échéance facultative','end',g?.end,'date')}</div>${actions('Enregistrer',Boolean(g))}<p class="form-message" role="status"></p></form>`);
}
function importDialog(){
  show('Importer une liste',`<form data-form="import"><p class="muted">Formats .xlsx et .csv, jusqu’à 8 Mo. La première ligne doit contenir une colonne « Titre ». Pour une liste mixte, ajoute une colonne « Type ».</p><label class="drop">Choisir un fichier<input name="file" type="file" accept=".csv,.xlsx" required></label>${field('Nom de la collection (facultatif)','name','','text','maxlength="100"')}${select('Format si la colonne Type est vide','type',typeNames,'film')}<label class="check"><input type="checkbox" name="enrich" checked> Rechercher les métadonnées et les visuels disponibles</label><a href="exemple.csv" download>Télécharger un CSV d’exemple ↓</a>${actions('Importer')}<p class="form-message" role="status"></p></form>`);
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
  const name=data.name.trim()||file.name.replace(/\.[^.]+$/,'');
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
  filter={type:'all',status:'all',query:'',collection:collection.id};
  location.hash='bibliotheque';render();
  modal.close();
  notify(`${fresh.length} ajoutée(s) · ${enriched} correspondance(s) · ${items.length-fresh.length} doublon(s)`);
}
document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-act]');
  if(!button)return;
  const {act,id}=button.dataset;
  if(act==='edit')edit(id);
  if(act==='collection')collectionDialog(id);
  if(act==='goal')goalDialog(id);
  if(act==='import')importDialog();
  if(act==='close'&&!importBusy)modal.close();
  if(act==='view-collection'){filter={type:'all',status:'all',query:'',collection:id};location.hash='bibliotheque';}
  if(act==='type'){
    filter.type=id;
    document.querySelectorAll('[data-act="type"]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    results();
  }
  if(act==='demo'&&confirm('Retirer les œuvres, collections et objectifs d’exemple ?')){
    state.items=state.items.filter(i=>!i.id.startsWith('demo-'));
    const used=new Set(state.items.map(i=>i.collection));
    state.collections=state.collections.filter(c=>!['cinema','imaginaire'].includes(c.id)||used.has(c.id));
    state.goals=state.goals.filter(g=>g.id!=='g1');
    if(!state.collections.some(c=>c.id===filter.collection))filter.collection='all';
    state.demo=false;save();
  }
  if(act==='remove'){
    const form=button.closest('form'), {id,form:kind}=form.dataset;
    if(!confirm('Supprimer cet élément ?'))return;
    if(kind==='item')state.items=state.items.filter(i=>i.id!==id);
    if(kind==='goal')state.goals=state.goals.filter(g=>g.id!==id);
    if(kind==='collection'){
      state.collections=state.collections.filter(c=>c.id!==id);
      state.items.forEach(i=>{if(i.collection===id)i.collection='';});
      if(filter.collection===id)filter.collection='all';
    }
    if(save())modal.close();
  }
  if(act==='lookup'){
    const form=button.closest('form');
    const {title,type,year}=Object.fromEntries(new FormData(form));
    if(!title.trim()){tell(form,'Indique d’abord le titre.');return;}
    button.disabled=true;
    tell(form,'Recherche en cours…');
    try{
      const [found]=await api('enrich',JSON.stringify([{title:title.trim(),type,year}]));
      if(!found.source){tell(form,'Aucune correspondance trouvée pour ce titre.');return;}
      for(const [k,v] of Object.entries(found))if(v&&form.elements[k]&&!form.elements[k].value)form.elements[k].value=v;
      form.dataset.source=found.source;
      tell(form,'Métadonnées récupérées via '+found.source+'.');
    }catch{tell(form,'Recherche indisponible. Tu peux remplir les champs manuellement.');}
    finally{button.disabled=false;}
  }
});
document.addEventListener('submit',async event=>{
  const form=event.target, kind=form.dataset.form, id=form.dataset.id;
  if(!kind)return;
  event.preventDefault();
  const data=Object.fromEntries(new FormData(form));
  if(kind==='import'){
    if(importBusy)return;
    importBusy=true;
    const buttons=modal.querySelectorAll('button');
    buttons.forEach(b=>b.disabled=true);
    try{await importFile(form,data);}catch(error){tell(form,error.message);}
    finally{importBusy=false;buttons.forEach(b=>b.disabled=false);}
    return;
  }
  for(const k in data)if(typeof data[k]==='string')data[k]=data[k].trim();
  if(kind==='item'){
    if(!data.title){tell(form,'Indique un titre.');return;}
    const old=byId(id);
    const item={...old,...data,id:id||crypto.randomUUID(),rating:Number(data.rating),
      completed:data.status==='done'?old?.completed||today():'',
      source:form.dataset.source||old?.source||''};
    state.items=old?state.items.map(i=>i.id===id?item:i):[item,...state.items];
  }
  if(kind==='collection'){
    if(!data.name){form.elements.name.setCustomValidity('Indique un nom.');form.elements.name.reportValidity();return;}
    const c={id:id||crypto.randomUUID(),name:data.name};
    state.collections=id?state.collections.map(x=>x.id===id?c:x):[...state.collections,c];
  }
  if(kind==='goal'){
    if(!data.title||data.end&&data.end<data.start){tell(form,'Indique un nom et une échéance égale ou postérieure au début.');return;}
    const goal={...data,id:id||crypto.randomUUID(),target:Number(data.target)};
    state.goals=id?state.goals.map(g=>g.id===id?goal:g):[...state.goals,goal];
  }
  if(save()){modal.close();notify('Enregistré.');}
});
modal.addEventListener('cancel',event=>{if(importBusy)event.preventDefault();});
document.addEventListener('input',e=>{
  if(e.target.id==='search'){filter.query=e.target.value;results();}
  if(e.target.validity?.customError)e.target.setCustomValidity('');
});
document.addEventListener('change',e=>{
  if(e.target.id==='filter-status'){filter.status=e.target.value;results();}
  if(e.target.id==='filter-collection'){filter.collection=e.target.value;results();}
});
window.addEventListener('hashchange',()=>{render();main.focus({preventScroll:true});window.scrollTo(0,0);});
window.addEventListener('storage',event=>{if(event.key===storage&&!importBusy){state=read();render();}});
const catalogUI=createCatalog({
  types,esc,opts,cover,show,notify,
  library:()=>state.items,
  add:{
    collections,
    item:(item,collection)=>{
      state.items.unshift({
        id:crypto.randomUUID(),catalogId:item.id,type:item.type,title:item.title,year:item.year,
        genre:item.genre||'',creator:item.creator||'',image:item.image||'',length:item.length||'',
        collection,status:'todo',rating:0,review:'',completed:'',
        evidence:item.evidence,edition:item.edition,source:item.evidence.map(e=>e.source).join(', ')
      });
      return save();
    }
  }
});
const pathsUI=createPaths({
  esc,library:()=>state.items,level,xp,notify,
  open:(item,existing)=>existing?edit(existing.id):catalogUI.open(item)
});
render();
if(!['parcours','profil'].includes(page()))pathsUI.sync();

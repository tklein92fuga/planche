import {mediaNames} from './media-ui.js';
export function createPaths({esc,library,open,level,xp,notify}) {
  let courseQuery='',courseFacet='all',unitPage=1,lookup=new Map(),loadRevision=0,media='all',allGroups=[],groups=[],resolved={},tracked=new Map(),mode='parcours',selected='',page=1,query='',family='',request=0,filter='all',tier='all',items=new Map();
  const facetNames={editorial:'Sélections thématiques',genre:'Genres et types',decade:'Décennies',franchise:'Sagas et univers',country:'Pays de production',developer:'Studios et développeurs',publisher:'Éditeurs',platform:'Plateformes',author:'Auteurs'};
  const active=()=>['#parcours','#profil'].includes(location.hash);
  const done=g=>g.members.filter(id=>tracked.get(id)?.status==='done').length;
  const percent=g=>g.total?Math.floor(done(g)/g.total*100):0;
  const medal=g=>ledger()[g.id]?.tier||(g.kind==='meta'?'platinum':g.total>=50?'gold':g.total>=15?'silver':'bronze');
  const names={bronze:'Bronze',silver:'Argent',gold:'Or',platinum:'Platine'};
  const trophy=g=>`<span class="trophy-icon ${medal(g)}" aria-label="${names[medal(g)]}"><svg viewBox="0 0 64 64" aria-hidden="true"><path d="M19 9h26v15c0 12-7 17-13 17S19 36 19 24Z"/><path d="M19 14H9v6c0 10 7 14 14 14M45 14h10v6c0 10-7 14-14 14M32 41v12M22 56h20"/><path d="m32 15 2 5 6 1-4 4 1 6-5-3-5 3 1-6-4-4 6-1Z" class="trophy-star"/></svg></span>`;
  function ledger(){try{return JSON.parse(localStorage.getItem('planche.trophies.v1'))||{};}catch{return {};}}
  function earn(){
    const awards=ledger(),newOnes=[];
    for(const g of allGroups.filter(g=>g.kind!=='group')){
      if(g.ready&&g.total>=3&&done(g)===g.total&&!awards[g.id]){
        awards[g.id]={date:new Date().toISOString(),title:g.title,tier:medal(g),revision:g.revision,total:g.total};newOnes.push(g.title);
      }
    }
    if(newOnes.length){
      try{localStorage.setItem('planche.trophies.v1',JSON.stringify(awards));notify(`Trophée débloqué · ${newOnes[0]}${newOnes.length>1?` et ${newOnes.length-1} autre(s)`:''}`);}
      catch{notify('Impossible de sauvegarder les trophées. Vérifie l’espace disponible.');}
    }
  }
  function mount(current='parcours'){
    mode=current;
    return `<div class="journeys"><div id="journey-view" aria-live="polite">Chargement des parcours…</div></div>`;
  }
  const heading=(g)=>`<div class="path-heading"><p class="eyebrow">${esc(g.family||'TES PARCOURS CULTURELS')}</p><h1>${esc(g.title)}</h1><p>${done(g)} / ${g.total} œuvres · ${percent(g)} %</p></div>`;
  const meter=g=>`<div class="track"><i style="width:${percent(g)}%"></i></div>`;
  const counts=g=>`<span>${done(g)} / ${g.total} terminées</span>`;
  function tile(i){
    items.set(i.id,i);
    const status=tracked.get(i.id)?.status||'todo';
    return `<button class="mastery-tile ${status}" data-path-work="${esc(i.id)}" aria-label="${esc(i.title)} · ${mediaNames[i.type]} · ${status==='done'?'Terminé':status==='doing'?'En cours':'À découvrir'}" title="${esc(i.title)}">${status==='done'?'<span class="tile-complete" aria-hidden="true">✓</span>':''}</button>`;
  }
  function row(g){
    const award=ledger()[g.id];
    return `<section class="journey-row ${award?'awarded':''}"><button class="journey-title" data-path-list="${esc(g.id)}"><span>${g.kind==='meta'?'MÉTA-LISTE':g.kind==='group'?'SECTION':'SOUS-LISTE'}</span><strong>${esc(g.title)}</strong><small>${g.total?`${done(g)} / ${g.total} œuvres`:'Sélection à compléter'}</small></button><div class="journey-progress">${g.total?`<div class="mastery-tiles">${g.items.slice(0,16).map(tile).join('')}</div>${meter(g)}`:'<p class="muted">Les œuvres de cette liste seront ajoutées après sélection.</p>'}</div><div class="journey-reward ${award?'earned':'locked'}">${g.kind==='group'?'<small>Ouvrir</small>':`${trophy(g)}<small>${award?'Débloqué':names[medal(g)]}</small>`}</div></section>`;
  }
  function mediaNav(){return `<nav class="media-navbar" aria-label="Filtrer les parcours par format">${[['all','Tout'],['film','Films'],['game','Jeux vidéo'],['book','Livres']].map(([id,label])=>`<button data-path-media="${id}" aria-label="${label}" aria-pressed="${media===id}">${label}</button>`).join('')}</nav>${media!=='all'?'<p class="path-data-note">Les trophées demandent la liste complète, tous formats confondus.</p>':''}`;}
  function controls(){
    const families=[...new Set(groups.filter(g=>g.kind==='meta').map(g=>g.family))];
    return `<div class="filter-bar"><input type="search" id="journey-search" value="${esc(query)}" placeholder="Rechercher une liste…" aria-label="Rechercher une liste"><select id="journey-family" aria-label="Famille"><option value="">Toutes les familles</option>${families.map(f=>`<option ${f===family?'selected':''}>${esc(f)}</option>`).join('')}</select></div>`;
  }
  const sublistCount=n=>n+' sous-liste'+(n>1?'s':'');
  function descendants(g){
    return (g.children||[]).flatMap(id=>{const child=lookup.get(id);return !child?[]:child.kind==='group'?descendants(child):[child];});
  }
  function courseFor(g){return g.kind==='meta'?g:groups.find(c=>c.id===g.meta);}
  function courseUnits(course){return descendants(course).filter(g=>(courseFacet==='all'||(g.facet||'editorial')===courseFacet)&&g.title.toLocaleLowerCase('fr').includes(courseQuery.toLocaleLowerCase('fr')));}
  function courseNavigation(course){
    if(!course)return '';
    return `<nav class="path-navigation" aria-label="Sous-listes de ${esc(course.title)}"><button class="path-overview" data-path-list="">Toutes les méta-listes</button><button class="path-course-title ${selected===course.id?'selected':''}" data-path-list="${esc(course.id)}"><strong>${esc(course.title)}</strong><span>${sublistCount(descendants(course).length)}</span></button>${courseUnits(course).slice((unitPage-1)*40,unitPage*40).map((child,index)=>`<button class="path-nav-item ${selected===child.id?'selected':''}" data-path-list="${esc(child.id)}"><span>${esc(facetNames[child.facet||'editorial'])}</span><strong>${esc(child.title)}</strong><span>${done(child)} / ${child.total} terminées</span></button>`).join('')}</nav>`;
  }
  function metaCard(g){
    const count=descendants(g).length;
    return `<button class="meta-index-card" data-path-list="${esc(g.id)}"><span class="eyebrow">${esc(g.family)}</span><strong>${esc(g.title)}</strong><span>${count?sublistCount(count):'Sous-listes à venir'}</span><span class="meta-card-progress">${percent(g)} % · ${done(g)} / ${g.total} œuvres</span>${meter(g)}</button>`;
  }
  function match(g){return (!family||family===g.family)&&g.title.toLocaleLowerCase('fr').includes(query.toLocaleLowerCase('fr'));}
  async function draw(){
    if(!active())return;
    const version=++request;
    const target=document.querySelector('#journey-view');if(!target)return;
    if(mode==='profil'){target.innerHTML=profile();return;}
    let content='';
    const g=groups.find(g=>g.id===selected);
    const course=g?courseFor(g):null;
    if(!g){
      const visible=groups.filter(g=>g.kind==='meta'&&(!family||family===g.family)&&(!query||g.title.toLocaleLowerCase('fr').includes(query.toLocaleLowerCase('fr'))||descendants(g).some(c=>c.title.toLocaleLowerCase('fr').includes(query.toLocaleLowerCase('fr')))));
      content=`<div class="path-heading"><p class="eyebrow">TES PARCOURS CULTURELS</p><h1>Choisis une méta-liste.</h1><p>Ouvre un univers pour découvrir ses sous-listes et suivre ta progression.</p><a href="#profil">Mon profil et mes trophées</a></div>${controls()}<div class="meta-index">${visible.map(metaCard).join('')||'<p>Aucune méta-liste pour cette recherche.</p>'}</div>`;
    }else if(g.kind==='meta'||g.kind==='group'){
      const allUnits=descendants(g),units=courseUnits(g);
      const pages=Math.max(1,Math.ceil(units.length/40));unitPage=Math.min(unitPage,pages);
      const categories=[...new Set(allUnits.map(g=>g.facet||'editorial'))];
      content=`${heading(g)}${meter(g)}<p class="course-description">${sublistCount(units.length)} à compléter. Une case représente une œuvre.</p><div class="mastery-legend"><span>Terminé</span><span>En cours</span><span>À découvrir</span></div><div class="filter-bar course-filters"><input id="course-search" type="search" aria-label="Rechercher une sous-liste" value="${esc(courseQuery)}" placeholder="Rechercher une sous-liste…"><select id="course-facet" aria-label="Critère des sous-listes"><option value="all">Tous les critères</option>${categories.map(f=>`<option value="${f}" ${courseFacet===f?'selected':''}>${esc(facetNames[f])}</option>`).join('')}</select></div><p class="muted">${units.length} sous-liste(s) · page ${unitPage} / ${pages}</p><div class="course-units">${units.length?units.slice((unitPage-1)*40,unitPage*40).map(row).join(''):'<div class="empty">Les sous-listes de cette méta-liste seront proposées dès qu’au moins trois œuvres pourront être regroupées autour d’un sujet.</div>'}</div>${pages>1?`<div class="catalog-pagination"><button data-unit-page="-1" ${unitPage<=1?'disabled':''}>Précédente</button><span>${unitPage} / ${pages}</span><button data-unit-page="1" ${unitPage>=pages?'disabled':''}>Suivante</button></div>`:''}`;
    }else{
      target.innerHTML=`${mediaNav()}<div class="path-layout">${courseNavigation(course)}<div class="path-content">Chargement…</div></div>`;
      try{
        const response=await fetch('/api/paths/detail?'+new URLSearchParams({id:g.id,page,type:media}));
        if(!response.ok)throw Error('Impossible de charger cette liste.');
        const detail=await response.json();if(version!==request||!active())return;
        const pages=Math.max(1,Math.ceil(detail.total/60));
        content=`<button class="ghost" data-path-list="${esc(course?.id||'')}">Retour à ${esc(course?.title||'toutes les méta-listes')}</button>${heading(g)}${meter(g)}<div class="mastery-legend"><span>Terminé</span><span>En cours</span><span>À découvrir</span></div>${detail.total?`<div class="mastery-tiles">${detail.items.map(tile).join('')}</div><div class="path-work-list">${detail.items.map(i=>`<button class="path-work-row" data-path-work="${esc(i.id)}">${tileLabel(i)}<span><strong>${esc(i.title)}</strong><small>${esc(i.year)} · ${mediaNames[i.type]}</small></span></button>`).join('')}</div><div class="catalog-pagination"><button data-path-page="-1" ${page<=1?'disabled':''}>Précédente</button><span>${page} / ${pages}</span><button data-path-page="1" ${page>=pages?'disabled':''}>Suivante</button></div>`:'<div class="empty">Aucune œuvre pour ce format.</div>'}`;
      }catch(e){content=`<p>${esc(e.message)}</p>`;}
    }
    if(version===request&&active())target.innerHTML=`${mediaNav()}${g?`<div class="path-layout">${courseNavigation(course)}<div class="path-content">${content}</div></div>`:`<div class="path-content">${content}</div>`}`;
  }

  function tileLabel(i){const status=tracked.get(i.id)?.status||'todo';return `<span class="mastery-tile ${status}">${status==='done'?'<span class="tile-complete" aria-hidden="true">✓</span>':''}</span>`;}
  function profile(){
    const awards=ledger(),entries=Object.entries(awards).filter(([id])=>groups.some(g=>g.id===id&&g.kind!=='group')).sort((a,b)=>b[1].date.localeCompare(a[1].date));
    const available=groups.filter(g=>g.kind!=='group');
    const filtered=available.filter(g=>match(g)&&(tier==='all'||medal(g)===tier)&&(filter==='all'||filter==='earned'&&awards[g.id]||filter==='locked'&&!awards[g.id]));
    const ongoing=available.filter(g=>g.kind==='sublist'&&g.total>0&&!awards[g.id]).sort((a,b)=>percent(b)-percent(a)).slice(0,5);
    const unique=new Set(library().filter(i=>i.status==='done').map(i=>i.catalogId||resolved[i.id]||i.id));
    return `<section class="profile-banner"><div class="profile-avatar">Q</div><div><p class="eyebrow">CARNET PERSONNEL</p><h1>Mon profil culturel.</h1><p>Niveau ${level()} · ${xp()} XP</p></div><div class="profile-stats"><div><b>${unique.size}</b><span>Œuvres terminées</span></div><div><b>${entries.length}</b><span>Trophées obtenus</span></div><div><b>${available.filter(g=>g.ready).length}</b><span>Listes disponibles</span></div></div></section><div class="profile-metals">${Object.entries(names).map(([k,n])=>`<div>${trophy({kind:k==='platinum'?'meta':'sublist',total:k==='gold'?50:k==='silver'?15:1})}<b>${entries.filter(([,a])=>a.tier===k).length}</b><span>${n}</span></div>`).join('')}</div><div class="profile-layout"><section><div class="section-line"><h2>Tous les trophées</h2><span>${entries.length} / ${available.length}</span></div>${controls()}<div class="trophy-filters"><select id="trophy-filter" aria-label="Statut des trophées">${[['all','Tous les trophées'],['earned','Débloqués'],['locked','À débloquer']].map(([k,n])=>`<option value="${k}" ${filter===k?'selected':''}>${n}</option>`).join('')}</select><select id="trophy-tier" aria-label="Métal">${[['all','Tous les métaux'],...Object.entries(names)].map(([k,n])=>`<option value="${k}" ${tier===k?'selected':''}>${n}</option>`).join('')}</select></div><p class="muted">Bronze · 3–14 œuvres. Argent · 15–49. Or · 50 et plus. Platine · méta-liste complète. Un trophée acquis reste dans ta collection.</p><div class="trophy-list">${filtered.map(g=>{const a=awards[g.id];return `<button class="trophy-row ${a?'earned':'locked'}" data-profile-path="${esc(g.id)}">${trophy(g)}<span><strong>${esc(g.title)}</strong><small>${esc(g.breadcrumb.join(' / ')||g.family)}</small>${meter(g)}<small>${a?`Obtenu le ${new Date(a.date).toLocaleDateString('fr-FR')}`:g.total?`${done(g)} / ${g.total} œuvres · ${percent(g)} %`:'Sélection à compléter'}</small></span><b>${a?'✓':names[medal(g)]}</b></button>`;}).join('')||'<div class="empty">Aucun trophée pour ces filtres.</div>'}</div></section><aside class="trophy-cabinet"><h2>Ma vitrine</h2>${entries.length?entries.slice(0,6).map(([id,a])=>`<button class="cabinet-item" data-profile-path="${esc(id)}">${trophy(groups.find(g=>g.id===id)||{kind:'sublist',total:a.total})}<span><strong>${esc(a.title)}</strong><small>${names[a.tier]} · ${new Date(a.date).toLocaleDateString('fr-FR')}</small></span></button>`).join(''):'<div class="cabinet-empty">♜<h3>Ton premier trophée t’attend.</h3><p>Termine toutes les œuvres d’une sous-liste pour le débloquer.</p></div>'}<h2>Prochains trophées</h2>${ongoing.map(g=>`<button class="cabinet-item" data-profile-path="${esc(g.id)}">${trophy(g)}<span><strong>${esc(g.title)}</strong><small>${done(g)} / ${g.total} œuvres</small>${meter(g)}</span></button>`).join('')}</aside></div>`;
  }
  async function load(background=false){
    const version=++loadRevision;request++;
    try{
      const [response,matches]=await Promise.all([fetch('/api/paths'),fetch('/api/catalog/resolve',{method:'POST',body:JSON.stringify(library().map(({id,catalogId,type,title,year})=>({id,catalogId,type,title,year})))}).then(r=>{if(!r.ok)throw Error('Impossible de lire la progression.');return r.json();})]);
      if(!response.ok)throw Error('Redémarre le serveur pour activer les nouveaux parcours.');
      const data=await response.json();if(version!==loadRevision||(!background&&!active()))return;
      allGroups=data.groups;
      const projection=mode==='parcours'&&media!=='all'?await fetch('/api/paths?'+new URLSearchParams({type:media})).then(r=>{if(!r.ok)throw Error('Impossible de filtrer les parcours.');return r.json();}):data;
      if(version!==loadRevision||(!background&&!active()))return;
      groups=projection.groups;lookup=new Map(groups.map(g=>[g.id,g]));if(selected&&!groups.some(g=>g.id===selected)){const previous=allGroups.find(g=>g.id===selected);selected=groups.some(g=>g.id===previous?.meta)?previous.meta:'';}
      resolved=matches;tracked=new Map();items=new Map();
      for(const g of allGroups)for(const i of g.items)items.set(i.id,i);
      const rank={todo:0,doing:1,done:2};
      for(const item of library()){const id=item.catalogId||resolved[item.id];if(id&&(!tracked.has(id)||rank[item.status]>rank[tracked.get(id).status]))tracked.set(id,item);}
      earn();if(!background)await draw();
    }catch(e){const target=document.querySelector('#journey-view');if(target&&active()&&version===loadRevision)target.textContent=e.message;}
  }
  document.addEventListener('click',e=>{
    const format=e.target.closest('[data-path-media]');if(format){media=format.dataset.pathMedia;page=1;unitPage=1;return load();}
    const unitPaging=e.target.closest('[data-unit-page]');if(unitPaging){unitPage+=Number(unitPaging.dataset.unitPage);return draw();}
    const path=e.target.closest('[data-path-list]');if(path){courseQuery='';courseFacet='all';unitPage=1;selected=path.dataset.pathList;page=1;query='';return draw();}
    const profilePath=e.target.closest('[data-profile-path]');if(profilePath){selected=profilePath.dataset.profilePath;page=1;query='';location.hash='#parcours';}
    const paging=e.target.closest('[data-path-page]');if(paging){page+=Number(paging.dataset.pathPage);draw();}
    const work=e.target.closest('[data-path-work]');if(work){const item=items.get(work.dataset.pathWork);if(item)open(item,tracked.get(item.id));}
  });
  document.addEventListener('change',e=>{
    if(e.target.id==='course-facet'){courseFacet=e.target.value;unitPage=1;draw();}
    if(e.target.id==='journey-family'){family=e.target.value;draw();}
    if(e.target.id==='trophy-filter'){filter=e.target.value;draw();}
    if(e.target.id==='trophy-tier'){tier=e.target.value;draw();}
  });
  document.addEventListener('input',e=>{
    if(e.target.id==='course-search'){courseQuery=e.target.value;unitPage=1;const position=e.target.selectionStart;draw().then(()=>{const input=document.querySelector('#course-search');if(input){input.focus();input.setSelectionRange(position,position);}});}
    if(e.target.id==='journey-search'){query=e.target.value;const start=e.target.selectionStart;draw().then(()=>{const input=document.querySelector('#journey-search');if(input){input.focus();input.setSelectionRange(start,start);}});}
  });
  return {mount,load,sync:()=>load(true)};
}

export function createPaths({esc,library,open,level,xp}) {
  let groups=[],category='Genres',selected='',resolved={},page=1,request=0,tracked=new Map();
  const categories=['Genres','Pays','Récompenses'];
  const active=()=>location.hash==='#parcours';
  const progress=group=>group.members.filter(id=>tracked.get(id)?.status==='done').length;
  const stateFor=item=>tracked.get(item.id)||library().find(i=>i.type===item.type && i.title===item.title && String(i.year||'')===String(item.year||''));
  const icon=name=>`<img src="icons/${name}.svg" alt="">`;
  function mount(){
    return `<div class="path-page"><div class="path-topbar"><div><h1>Mes parcours culturels</h1><p>Une œuvre, une case. Avance dans les univers qui te plaisent.</p></div><div class="path-level"><b>Niveau ${level()}</b><span>${xp()%100} / 100 XP</span></div></div><div class="path-layout"><nav id="path-navigation" class="path-navigation" aria-label="Listes thématiques"></nav><div id="path-content" class="path-content" aria-live="polite">Chargement des listes…</div></div></div>`;
  }
  function nav(){
    const filtered=groups.filter(g=>g.category===category);
    document.querySelector('#path-navigation').innerHTML=`<div class="path-category-tabs">${categories.map(c=>`<button data-path-category="${c}" aria-pressed="${c===category}">${c}</button>`).join('')}</div><button class="path-overview ${!selected?'selected':''}" data-path-list="">Vue d’ensemble</button>${filtered.map(g=>`<button class="path-nav-item ${g.id===selected?'selected':''}" data-path-list="${esc(g.id)}"><strong>${esc(g.title)}</strong><span>${esc(g.subtitle)} · ${g.total} œuvres</span></button>`).join('')}`;
  }
  function tiles(group){
    return `<div class="mastery-tiles">${group.items.map(i=>{
      const item=stateFor(i),status=item?.status||'todo';
      return `<button class="mastery-tile ${status}" data-path-work="${esc(i.id)}" title="${esc(i.title)} · ${status==='done'?'Terminé':status==='doing'?'En cours':'À découvrir'}" aria-label="${esc(i.title)} · ${status==='done'?'Terminé':status==='doing'?'En cours':'À découvrir'}">${status==='done'?icon('crown'):status==='doing'?icon('play'):''}</button>`;
    }).join('')}</div>`;
  }
  function legend(){
    return `<div class="mastery-legend"><span><i class="mastery-tile done">${icon('crown')}</i>Terminé</span><span><i class="mastery-tile doing">${icon('play')}</i>En cours</span><span><i class="mastery-tile todo"></i>À découvrir</span></div>`;
  }
  function preview(group){
    const own=[...tracked.entries()].filter(([id])=>group.members.includes(id)).map(([id,i])=>({...i,id}));
    const items=[...own,...group.items.filter(i=>!own.some(o=>o.id===i.id))].slice(0,16);
    return {...group,items};
  }
  function overview(){
    const filtered=groups.filter(g=>g.category===category);
    const unique=new Set(filtered.flatMap(g=>g.members));
    const done=new Set(library().filter(i=>i.status==='done').map(i=>i.catalogId||resolved[i.id]).filter(id=>unique.has(id)));
    const percent=unique.size?Math.round(done.size/unique.size*100):0;
    return `<div class="path-heading"><p class="eyebrow">MES PARCOURS / ${esc(category.toUpperCase())}</p><h2>${esc(category)}</h2><p>Progression · <b>${percent} %</b> · ${done.size} / ${unique.size} œuvres</p></div>${legend()}${category==='Pays'?'<p class="path-data-note">Les pays d’origine sont affichés lorsqu’ils sont référencés dans les données. Une coproduction peut figurer dans plusieurs listes.</p>':''}${category==='Récompenses'?'<p class="path-data-note">Chaque liste rassemble les prix ou nominations effectivement documentés dans la base.</p>':''}<div class="mastery-groups">${filtered.map(g=>`<section class="mastery-row"><div class="mastery-row-title"><button data-path-list="${esc(g.id)}">${esc(g.title)}</button><span>${g.category==='Genres'?esc(g.subtitle)+' · ':''}${progress(g)} / ${g.total} terminées</span></div><div>${tiles(preview(g))}${g.total>16?`<button class="path-see-all" data-path-list="${esc(g.id)}">Voir les ${g.total} œuvres</button>`:''}</div></section>`).join('')||'<div class="empty">Aucune liste disponible pour cette catégorie pour le moment.</div>'}</div>`;
  }
  async function draw(){
    if(!active())return;
    tracked=new Map();
    const rank={todo:0,doing:1,done:2};
    for(const item of library()){
      const id=item.catalogId||resolved[item.id];
      if(id&&(!tracked.has(id)||rank[item.status]>rank[tracked.get(id).status]))tracked.set(id,item);
    }
    nav();
    if(!selected){document.querySelector('#path-content').innerHTML=overview();return;}
    const version=++request;
    try{
      const response=await fetch('/api/paths/detail?'+new URLSearchParams({id:selected,page}));
      if(!response.ok)throw Error('Impossible de charger cette liste.');
      const g=await response.json();
      if(!active()||version!==request||g.id!==selected)return;
      const local=groups.find(group=>group.id===g.id);
      if(local)local.items=g.items;
      const done=progress(g),pages=Math.max(1,Math.ceil(g.total/g.pageSize));
      document.querySelector('#path-content').innerHTML=`<div class="path-heading"><button class="ghost" data-path-list="">Toutes les listes</button><h2>${esc(g.title)}</h2><p>${esc(g.subtitle)} · ${done} / ${g.total} terminées · ${g.total?Math.round(done/g.total*100):0} %</p></div>${legend()}<section class="path-unit"><div class="section-line"><h3>${esc(g.title)}</h3><span>Page ${g.page} / ${pages}</span></div>${tiles(g)}<div class="path-work-list">${g.items.map(i=>{
        const item=stateFor(i),status=item?.status||'todo';
        return `<button data-path-work="${esc(i.id)}" class="path-work-row"><span class="mastery-tile ${status}">${status==='done'?icon('crown'):icon('play')}</span><span><strong>${esc(i.title)}</strong><small>${esc(i.year)} · ${status==='done'?'Terminé':status==='doing'?'En cours':'À découvrir'}</small></span></button>`;
      }).join('')}</div><div class="catalog-pagination"><button data-path-page="-1" ${page<=1?'disabled':''}>Précédente</button><span>${page} / ${pages}</span><button data-path-page="1" ${page>=pages?'disabled':''}>Suivante</button></div></section>`;
    }catch(error){if(active()&&version===request)document.querySelector('#path-content').textContent=error.message;}
  }
  async function load(){
    try{
      const version=++request;
      const [response,matches]=await Promise.all([
        fetch('/api/paths'),
        fetch('/api/catalog/resolve',{method:'POST',body:JSON.stringify(library().map(({id,catalogId,type,title,year})=>({id,catalogId,type,title,year})))}).then(r=>r.ok?r.json():{})
      ]);
      if(!response.ok)throw Error('Redémarre le serveur pour activer les parcours.');
      const data=await response.json();
      if(!active()||version!==request)return;
      groups=data.groups;resolved=matches;
      await draw();
    }catch(error){if(active())document.querySelector('#path-content').textContent=error.message;}
  }
  document.addEventListener('click',event=>{
    const categoryButton=event.target.closest('[data-path-category]');
    if(categoryButton){category=categoryButton.dataset.pathCategory;selected='';page=1;request++;draw();}
    const list=event.target.closest('[data-path-list]');
    if(list){selected=list.dataset.pathList;page=1;request++;draw();}
    const paging=event.target.closest('[data-path-page]');
    if(paging){page+=Number(paging.dataset.pathPage);draw();}
    const work=event.target.closest('[data-path-work]');
    if(work){
      const id=work.dataset.pathWork;
      const existing=tracked.get(id);
      const item=groups.flatMap(g=>g.items).find(i=>i.id===id)||(existing?{...existing,id}:null);
      if(item)open(item,stateFor(item));
    }
  });
  return {mount,load};
}

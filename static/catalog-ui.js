export function createCatalog({types, esc, opts, cover, show, library, add, notify}) {
  let filter = {q:'',type:'all',criterion:'all',sort:'votes',page:1};
  let lastItems = [];
  let revision = 0;
  let timer;
  let debounce;
  let status;
  const active = () => location.hash === '#catalogue';
  const safeLink = url => /^https:\/\//.test(url || '') ? esc(url) : '#';
  const sourceNames = {imdb:'Films · IMDb',books:'Livres · Open Library',steam:'Jeux · Steam',awards:'Prix & nominations'};
  const formatCount = n => Number(n || 0).toLocaleString('fr-FR');
  async function get(path) {
    const response = await fetch(path);
    if (!response.ok) throw Error(response.status === 404 ? 'Redémarre le serveur Python pour activer le catalogue.' : 'Impossible de charger le catalogue.');
    return response.json();
  }
  function evidence(item) {
    return item.evidence.map(e => `<li><a href="${safeLink(e.url)}" target="_blank" rel="noopener noreferrer">${esc(e.source)}</a> · ${e.kind === 'award' ? esc((e.nomination ? 'Nomination · ' : 'Prix · ') + e.label) : `${esc(e.value)}/${esc(e.scale)} · ${formatCount(e.votes)} avis${e.label ? ' · '+esc(e.label) : ''}`}<small>Vérifié le ${esc(e.checked.slice(0,10))}</small></li>`).join('');
  }
  function exists(item) {
    return library().some(i => i.catalogId === item.id || i.type === item.type && String(i.title).toLocaleLowerCase() === item.title.toLocaleLowerCase() && (!i.year || !item.year || String(i.year) === item.year));
  }
  function mount() {
    clearTimeout(timer);
    return `<div class="page-title"><div><p class="eyebrow">EXPLORER LES ŒUVRES</p><h1>Catalogue<span>.</span></h1><p class="muted">Des œuvres sélectionnées sur leurs notes, prix ou nominations. Ajoute celles qui t’intéressent à ta bibliothèque.</p></div><button class="dark" data-cat="refresh">Actualiser les sources</button></div>
      <details class="panel catalog-rules"><summary>Critères et couverture des sources</summary><div id="catalog-status" role="status">Chargement des sources…</div><p>Les scores des lecteurs concernent l’œuvre, toutes éditions confondues. Une édition française identifiée est obligatoire pour chaque livre. Steam utilise les avis affichés en anglais sur le magasin français. La couverture dépend des catalogues accessibles.</p><p>Metacritic et les jeux exclusifs aux consoles ne disposent pas encore de source connectée. Les prix et nominations sont limités aux distinctions recensées dans la source Wikidata.</p></details>
      <section class="library"><div class="filter-bar"><input id="catalog-search" type="search" aria-label="Rechercher dans le catalogue" placeholder="Titre, auteur, genre…" value="${esc(filter.q)}"><select id="catalog-type" aria-label="Format du catalogue">${opts({all:'Tous les formats',...Object.fromEntries(Object.entries(types).map(([k,t])=>[k,t.plural]))},filter.type)}</select><select id="catalog-criterion" aria-label="Critère de sélection">${opts({all:'Tous les critères',award:'Prix et nominations'},filter.criterion)}</select><select id="catalog-sort" aria-label="Trier le catalogue">${opts({votes:'Nombre d’avis',score:'Note',year:'Plus récents',title:'Titre A–Z'},filter.sort)}</select></div><div id="catalog-results" aria-live="polite"></div></section>`;
  }
  async function load() {
    const request = ++revision;
    try {
      const data = await get('/api/catalog?' + new URLSearchParams(filter));
      if (!active() || request !== revision) return;
      lastItems = data.items;
      const pages = Math.max(1,Math.ceil(data.total/24));
      if (filter.page > pages) {filter.page = pages;load();return;}
      document.querySelector('#catalog-results').innerHTML = `<p class="muted count">${formatCount(data.total)} œuvre(s) · page ${filter.page} / ${pages}</p>` +
        (data.items.length ? `<div class="works catalog-works">${data.items.map(i => `<article class="work"><button class="work-open" data-cat="detail" data-id="${esc(i.id)}">${cover({...i,status:'todo'})}<span class="work-title">${esc(i.title)}</span><span class="muted">${types[i.type].label} · ${esc(i.year || 'Année inconnue')}</span></button><p class="catalog-proof">${i.evidence.some(e=>e.kind==='award') ? '✦ Prix / nomination' : i.evidence[0] ? `${esc(i.evidence[0].source)} · ${esc(i.evidence[0].value)}/${i.evidence[0].scale}` : ''}</p><button data-cat="detail" data-id="${esc(i.id)}">${exists(i) ? 'Dans ma bibliothèque' : '+ Ajouter'}</button></article>`).join('')}</div>` :
        '<div class="empty">Aucune œuvre pour ces filtres. Consulte les sources ou lance une actualisation.</div>') +
        `<div class="catalog-pagination"><button data-cat="previous" ${filter.page<=1?'disabled':''}>Précédente</button><span>${filter.page} / ${pages}</span><button data-cat="next" ${filter.page>=pages?'disabled':''}>Suivante</button></div>`;
    } catch (error) {
      if (active() && request===revision) document.querySelector('#catalog-results').textContent=error.message;
    }
  }
  async function poll() {
    clearTimeout(timer);
    if (!active()) return;
    try {
      const next = await get('/api/catalog/status');
      if (!active()) return;
      const changed = !status || next.total!==status.total || next.running!==status.running;
      status=next;
      document.querySelector('#catalog-status').innerHTML = `<p><b>${formatCount(status.total)} œuvres</b> · ${formatCount(status.counts.film)} films · ${formatCount(status.counts.book)} livres · ${formatCount(status.counts.game)} jeux</p><ul>${Object.entries(status.rules).map(([k,rule])=>{
        const s=status.sources.find(s=>s.id===k);
        return `<li><b>${sourceNames[k]}</b> · ${esc(rule)}<small>${s ? esc(s.message) + ' · ' + esc(s.updated.slice(0,10)) : 'Collecte à lancer'}${s?.status==='error'||s?.status==='interrupted'?' · À réessayer':''}</small></li>`;
      }).join('')}</ul>`;
      document.querySelector('[data-cat="refresh"]').disabled=status.running;
      if(changed)load();
      if(status.running)timer=setTimeout(poll,4000);
    } catch(error) {
      if(active())document.querySelector('#catalog-status').textContent=error.message;
    }
  }
  document.addEventListener('input',event=>{
    if(event.target.id!=='catalog-search')return;
    filter.q=event.target.value;filter.page=1;
    clearTimeout(debounce);debounce=setTimeout(load,250);
  });
  document.addEventListener('change',event=>{
    const name={'catalog-type':'type','catalog-criterion':'criterion','catalog-sort':'sort'}[event.target.id];
    if(name){filter[name]=event.target.value;filter.page=1;load();}
  });
  document.addEventListener('click',async event=>{
    const button=event.target.closest('[data-cat]');
    if(!button)return;
    const action=button.dataset.cat;
    if(action==='previous'||action==='next'){filter.page+=action==='next'?1:-1;load();}
    if(action==='refresh'){
      button.disabled=true;
      try {
        const response=await fetch('/api/catalog/update',{method:'POST'});
        if(!response.ok)throw Error('Actualisation indisponible. Redémarre le serveur puis réessaie.');
        await response.json();notify('Collecte lancée. La progression est disponible dans les sources.');poll();
      } catch(error){notify(error.message);button.disabled=false;}
    }
    if(action==='detail'){
      const item=lastItems.find(i=>i.id===button.dataset.id);
      if(!item)return;
      show(esc(item.title),`<p class="muted">${types[item.type].label} · ${esc(item.year)}${item.creator?' · '+esc(item.creator):''}</p><p>${esc(item.genre)}</p><ul class="catalog-evidence">${evidence(item)}</ul>${item.edition?`<p>Édition française · <a href="${safeLink(item.edition.url)}" target="_blank" rel="noopener noreferrer">${esc(item.edition.title)}</a></p>`:''}${exists(item)?'<p>Cette œuvre figure déjà dans ta bibliothèque.</p>':`<form id="catalog-add" data-id="${esc(item.id)}"><label>Collection<select name="collection">${opts({'':'Sans collection',...add.collections()},'')}</select></label><button class="dark" type="submit">Ajouter à ma bibliothèque</button></form>`}`);
    }
  });
  document.addEventListener('submit',event=>{
    if(event.target.id!=='catalog-add')return;
    event.preventDefault();
    const item=lastItems.find(i=>i.id===event.target.dataset.id);
    if(!item||exists(item))return;
    if(add.item(item,new FormData(event.target).get('collection'))) {
      document.querySelector('#modal').close();
      notify('Œuvre ajoutée à ta bibliothèque.');
      load();
    }
  });
  return {mount,load(){load();poll();}};
}

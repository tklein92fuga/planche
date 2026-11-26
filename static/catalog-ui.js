import {sourceLink} from './media-ui.js?v=live-2';
export function createCatalog({types, esc, opts, cover, show, library, setStatus, statusOf, notify}) {
  const defaults={q:'',type:'all',criterion:'all',sort:'votes',year_min:'',year_max:'',min_score:'',genre:'',page:1};
  let filter={...defaults};
  let lastItems = [];
  let selectedItem;
  let revision = 0;
  let timer;
  let debounce;
  let status;
  const active = () => ['#decouvrir','#catalogue','#decouverte'].includes(location.hash);
  const safeLink = url => /^https:\/\//.test(url || '') ? esc(url) : '#';
  const sourceNames = {imdb:'Films · IMDb','imdb-tv':'Séries TV · IMDb',books:'Livres · éditions françaises',goodreads:'Livres · Goodreads',metacritic:'Jeux · Metacritic',awards:'Prix & nominations'};
  const sourceAnchor=item=>{const link=sourceLink(item);return link?`<a class="work-source-link" href="${esc(link.url)}" target="_blank" rel="noopener noreferrer" aria-label="Voir ${link.label} : ${esc(item.title)}">${link.label} ↗</a>`:'';};
  const formatCount = n => Number(n || 0).toLocaleString('fr-FR');
  async function get(path) {
    const response = await fetch(path);
    if (!response.ok) throw Error(response.status === 404 ? 'Redémarre le serveur Python pour activer le catalogue.' : 'Impossible de charger le catalogue.');
    return response.json();
  }
  function evidence(item) {
    return item.evidence.map(e => `<li><a href="${safeLink(e.url)}" target="_blank" rel="noopener noreferrer">${esc(e.source)}</a> · ${e.kind === 'award' ? esc((e.nomination ? 'Nomination · ' : 'Prix · ') + e.label+(e.year?' · '+e.year:'')) : `${esc(e.value)}/${esc(e.scale)} · ${formatCount(e.votes)} avis${e.label ? ' · '+esc(e.label+(e.year?' · '+e.year:'')) : ''}`}<small>Vérifié le ${esc(e.checked.slice(0,10))}</small></li>`).join('');
  }
  const statusButtons=item=>`<div class="work-status-actions" role="group" aria-label="État de ${esc(item.title)}">${[['done','Terminé'],['doing','En cours']].map(([value,label])=>`<button data-cat="${value}" data-id="${esc(item.id)}" aria-pressed="${statusOf(item)===value}">${label}</button>`).join('')}</div>`;
  function mount() {
    clearTimeout(timer);
    return `<div class="page-title"><div><p class="eyebrow">EXPLORER LES ŒUVRES</p><h1>Découvrir<span>.</span></h1><p class="muted">Explore le catalogue et coche tes découvertes pour avancer dans tous tes parcours.</p></div></div>
      <details class="panel catalog-rules"><summary>Critères et couverture des sources</summary><div id="catalog-status" role="status">Chargement des sources…</div><p>Les livres rapprochés utilisent les notes Goodreads, avec leur source et leur date. Les autres conservent leur référence Open Library. Les scores des lecteurs concernent l’œuvre, toutes éditions confondues. Une édition française identifiée est obligatoire pour chaque livre. Les jeux sont sélectionnés avec un Metascore d’au moins 70/100 et au moins 10 critiques professionnelles. La couverture dépend des catalogues accessibles.</p><p>Rapprochement initial des livres: <a href="https://github.com/zygmuntz/goodbooks-10k" target="_blank" rel="noopener noreferrer">goodbooks-10k</a>, relevé Goodreads de 2017 sous CC BY-SA 4.0. Les notes historiques sont signalées.</p><p>Les séries et mini-séries utilisent la note IMDb globale (au moins 7/10 et 1 000 votes), sans ajouter les épisodes individuels. La collecte Metacritic couvre les jeux PC et consoles accessibles dans son classement public. Le Metascore concerne la version de référence affichée par Metacritic. Les prix et nominations sont limités aux distinctions recensées dans la source Wikidata.</p></details>
      <section class="library"><div class="filter-bar"><input id="catalog-search" type="search" aria-label="Rechercher dans le catalogue" placeholder="Titre, auteur, genre…" value="${esc(filter.q)}"><select id="catalog-type" aria-label="Format du catalogue">${opts({all:'Tous les formats',...Object.fromEntries(Object.entries(types).map(([k,t])=>[k,t.plural]))},filter.type)}</select><select id="catalog-criterion" aria-label="Critère de sélection">${opts({all:'Tous les critères',award:'Prix et nominations'},filter.criterion)}</select><select id="catalog-sort" aria-label="Trier le catalogue">${opts({votes:'Nombre d’avis',score:'Note',year:'Plus récents',title:'Titre A–Z'},filter.sort)}</select></div><div class="catalog-extra-filters"><label>Genre<input id="catalog-genre" type="search" placeholder="Drama, RPG…" value="${esc(filter.genre)}"></label><label>Depuis<input id="catalog-year-min" type="number" min="1" max="9999" placeholder="Année" value="${esc(filter.year_min)}"></label><label>Jusqu’à<input id="catalog-year-max" type="number" min="1" max="9999" placeholder="Année" value="${esc(filter.year_max)}"></label><label>Score minimal / 100<select id="catalog-score">${opts({'':'Tous les scores',70:'70 / 100',80:'80 / 100',90:'90 / 100'},filter.min_score)}</select></label><button data-cat="reset" class="ghost">Réinitialiser</button></div><p class="muted catalog-filter-help">Les notes sont ramenées sur 100 pour le filtre. Pour les jeux, le score est le Metascore des critiques professionnelles. Les œuvres sans score restent visibles avec « Tous les scores ».</p><div id="catalog-results" aria-live="polite"></div></section>`;
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
        (data.items.length ? `<div class="works catalog-works">${data.items.map(i => `<article class="work"><button class="work-open" data-cat="detail" data-id="${esc(i.id)}">${cover({...i,status:statusOf(i)})}<span class="work-title">${esc(i.title)}</span><span class="muted">${types[i.type].label} · ${esc(i.year || 'Année inconnue')}${i.type==='tv'&&i.endYear&&String(i.endYear)!==String(i.year)?'–'+esc(i.endYear):''}</span></button><p class="catalog-proof">${i.evidence.some(e=>e.kind==='award') ? '✦ Prix / nomination' : i.evidence[0] ? `${esc(i.evidence[0].source)} · ${esc(i.evidence[0].value)}/${i.evidence[0].scale}` : ''}</p>${sourceAnchor(i)}${statusButtons(i)}</article>`).join('')}</div>` :
        '<div class="empty">Aucune œuvre pour ces filtres. Essaie un autre filtre.</div>') +
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
      document.querySelector('#catalog-status').innerHTML = `<p><b>${formatCount(status.total)} œuvres</b> · ${formatCount(status.counts.film)} films · ${formatCount(status.counts.tv)} séries TV · ${formatCount(status.counts.book)} livres · ${formatCount(status.counts.game)} jeux</p><ul>${Object.entries(status.rules).map(([k,rule])=>{
        const s=status.sources.find(s=>s.id===k);
        return `<li><b>${sourceNames[k]}</b> · ${esc(rule)}<small>${s ? esc(s.message) + ' · ' + esc(s.updated.slice(0,10)) : 'Collecte à lancer'}${s?.status==='error'||s?.status==='interrupted'?' · À réessayer':''}</small></li>`;
      }).join('')}</ul>`;
      if(changed)load();
      if(status.running)timer=setTimeout(poll,4000);
    } catch(error) {
      if(active())document.querySelector('#catalog-status').textContent=error.message;
    }
  }
  document.addEventListener('input',event=>{
    const name={'catalog-search':'q','catalog-genre':'genre','catalog-year-min':'year_min','catalog-year-max':'year_max'}[event.target.id];
    if(!name)return;
    filter[name]=event.target.value;filter.page=1;
    clearTimeout(debounce);debounce=setTimeout(load,250);
  });
  document.addEventListener('change',event=>{
    const name={'catalog-type':'type','catalog-criterion':'criterion','catalog-sort':'sort','catalog-score':'min_score'}[event.target.id];
    if(name){filter[name]=event.target.value;filter.page=1;load();}
  });
  document.addEventListener('click',async event=>{
    const button=event.target.closest('[data-cat]');
    if(!button)return;
    const action=button.dataset.cat;
    if(action==='reset'){
      clearTimeout(debounce);
      filter={...defaults};
      document.querySelector('#main').innerHTML=mount();
      load();poll();
    }
    if(action==='previous'||action==='next'){filter.page+=action==='next'?1:-1;load();}
    if(['done','doing','todo'].includes(action)){
      const item=lastItems.find(i=>i.id===button.dataset.id)||(selectedItem?.id===button.dataset.id?selectedItem:null);
      if(item)setStatus(item,action);
    }
    if(action==='detail'){
      const item=lastItems.find(i=>i.id===button.dataset.id);
      if(item)openItem(item);
    }
  });
  function openItem(item){
    selectedItem=item;
    show(esc(item.title),`<p class="muted">${types[item.type].label} · ${esc(item.year)}${item.type==='tv'&&item.endYear&&String(item.endYear)!==String(item.year)?'–'+esc(item.endYear):''}${item.creator?' · '+esc(item.creator):''}</p><p>${esc(item.genre)}</p>${sourceAnchor(item)}<ul class="catalog-evidence">${evidence(item)}</ul>${item.edition?`<p>Édition française · <a href="${safeLink(item.edition.url)}" target="_blank" rel="noopener noreferrer">${esc(item.edition.title)}</a></p>`:''}${statusButtons(item)}<button class="ghost" data-cat="todo" data-id="${esc(item.id)}">Remettre à découvrir</button>`);
  }
  function updateStatus(item){
    const status=statusOf(item);
    for(const button of document.querySelectorAll('[data-cat="done"],[data-cat="doing"]'))if(button.dataset.id===item.id)button.setAttribute('aria-pressed',String(button.dataset.cat===status));
  }
  return {mount,open:openItem,updateStatus,load(){load();poll();}};
}

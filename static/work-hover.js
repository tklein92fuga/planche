import {sourceLink} from './media-ui.js?v=source-links-1';
const mediaNames={film:'Film',tv:'Série TV',game:'Jeu vidéo',book:'Livre'};
export function createWorkHover({esc,lookup,onStatus}){
  let trigger=null,item=null,box=null,showTimer,hideTimer,generation=0,touch=false,skipFocus=false;
  const cache=new Map();
  const safe=url=>/^https:\/\//.test(url||'')?esc(url):'#';
  function hide(){clearTimeout(showTimer);clearTimeout(hideTimer);generation++;if(trigger){trigger.removeAttribute('aria-controls');trigger.removeAttribute('aria-description');trigger.setAttribute('aria-expanded','false');}box?.remove();box=null;trigger=null;item=null;}
  function position(){if(!box||!trigger)return;const r=trigger.getBoundingClientRect(),b=box.getBoundingClientRect();box.style.left=Math.max(12,Math.min(innerWidth-b.width-12,r.right+12))+ 'px';box.style.top=Math.max(12,Math.min(innerHeight-b.height-12,r.top-12))+'px';}
  function render(result,loading=false){
    if(!box||!item)return;
    const link=sourceLink(item);
    const proof=item.evidence?.find(e=>e.kind==='rating');
    const art=/^https:\/\//.test(result?.image||'')?result.image:/^https:\/\//.test(item.image||'')?item.image:(item.type==='film'||item.type==='tv')?'/api/catalog/art?id='+encodeURIComponent(item.id):'';
    const status={done:'Terminé',doing:'En cours',todo:'À découvrir'}[item.status]||'À découvrir';
    box.innerHTML=`<div class="work-hover-head"><span>FICHE D’ŒUVRE</span><button data-hover-close aria-label="Fermer la fiche">Fermer</button></div><div class="work-hover-summary">${art?`<img src="${esc(art)}" alt="" loading="lazy" referrerpolicy="no-referrer">`:''}<div><p class="work-hover-type">${mediaNames[item.type]} · ${esc(item.year||'Date non renseignée')}${item.type==='tv'&&item.endYear&&String(item.endYear)!==String(item.year)?'–'+esc(item.endYear):''}</p><h2 id="work-hover-title">${esc(item.title)}</h2>${item.creator?`<p>${esc(item.creator)}</p>`:''}<p class="work-hover-genres">${esc(item.genre||'')}</p>${item.length?`<p>${esc(item.length)} ${(item.type==='film'||item.type==='tv')?(item.type==='tv'?'min · durée indicative IMDb':'min'):item.type==='book'?'pages':''}</p>`:''}${proof?`<p class="work-hover-rating">${esc(proof.value)} / ${esc(proof.scale)} <span>${esc(proof.source)}</span>${proof.label?`<small>${esc(proof.label)}</small>`:''}</p>`:''}</div></div>${link?`<a class="work-source-link" href="${safe(link.url)}" target="_blank" rel="noopener noreferrer" aria-label="Voir ${link.label} : ${esc(item.title)}">${link.label} ↗</a>`:''}<div class="work-hover-access"><h3>${(item.type==='film'||item.type==='tv')?'Où regarder · France':item.type==='game'?'Découvrir le jeu':'Lecteurs et édition française'}</h3>${loading?'<p class="muted" role="status">Recherche de la fiche et des disponibilités…</p>':''}${result?`<div class="work-hover-links">${(result.links||[]).map(l=>`<a href="${safe(l.url)}" target="_blank" rel="noopener noreferrer">${esc(l.label)}</a>`).join('')}</div>${result.offers?.length?`<ul>${result.offers.map(o=>`<li><strong>${esc(o.provider)}</strong><span>${esc(o.mode)}</span></li>`).join('')}</ul>`:(item.type==='film'||item.type==='tv')?`<p class="muted">${result.verified?(item.type==='tv'?'Consulte la fiche pour les offres par saison.':'Aucune offre référencée en France.'):'La fiche exacte ou ses offres ne sont pas encore identifiées.'}</p>`:''}${result.checked?`<small>Consulté le ${esc(new Date(result.checked).toLocaleDateString('fr-FR'))}${(item.type==='film'||item.type==='tv')?(item.type==='tv'?' · Les offres varient selon la saison.':' · Les offres peuvent évoluer.'):''}</small>`:''}`:''}</div><div class="work-status-actions" role="group" aria-label="État de l’œuvre"><button data-hover-status="done" aria-pressed="${item.status==='done'}">Terminé</button><button data-hover-status="doing" aria-pressed="${item.status==='doing'}">En cours</button></div>${item.status!=='todo'?'<button class="ghost" data-hover-status="todo">Remettre à découvrir</button>':''}`;
    box.querySelector('img')?.addEventListener('error',e=>{e.target.hidden=true;position();},{once:true});
    position();
  }
  async function show(button){
    clearTimeout(hideTimer);clearTimeout(showTimer);
    if(trigger===button&&box)return;
    hide();const found=lookup(button.dataset.pathWork);if(!found)return;
    trigger=button;item=found;const current=++generation;
    box=document.createElement('section');box.id='work-hover-card';box.className='work-hover-card';box.setAttribute('role','dialog');box.setAttribute('aria-modal','false');box.setAttribute('aria-labelledby','work-hover-title');document.body.append(box);
    button.setAttribute('aria-description','Flèche bas pour accéder à la fiche, Échap pour fermer.');button.setAttribute('aria-controls',box.id);button.setAttribute('aria-expanded','true');
    box.addEventListener('pointerenter',()=>clearTimeout(hideTimer));box.addEventListener('pointerleave',()=>{hideTimer=setTimeout(hide,250);});
    box.addEventListener('click',e=>{if(e.target.closest('[data-hover-close]')){const previous=trigger;hide();skipFocus=true;previous?.focus({preventScroll:true});}const status=e.target.closest('[data-hover-status]');if(status){const selected=item,value=status.dataset.hoverStatus;hide();onStatus(selected,value);}});
    if(cache.has(item.id)){render(cache.get(item.id));return;}
    render(null,true);
    try{const response=await fetch('/api/work-card?'+new URLSearchParams({id:item.id}));if(!response.ok)throw Error();const result=await response.json();cache.set(found.id,result);if(current===generation&&box)render(result);}
    catch{if(current===generation&&box)render({links:[],offers:[],message:'Source indisponible'});}
  }
  document.addEventListener('pointerover',e=>{const button=e.target.closest('[data-path-work]');if(!button||e.pointerType==='touch'||button.contains(e.relatedTarget))return;clearTimeout(hideTimer);clearTimeout(showTimer);showTimer=setTimeout(()=>show(button),250);});
  document.addEventListener('pointerout',e=>{const button=e.target.closest('[data-path-work]');if(!button||button.contains(e.relatedTarget)||box?.contains(e.relatedTarget))return;clearTimeout(showTimer);hideTimer=setTimeout(hide,250);});
  document.addEventListener('focusin',e=>{if(skipFocus){skipFocus=false;return;}const button=e.target.closest('[data-path-work]');if(button)show(button);else if(!box?.contains(e.target))hide();});
  document.addEventListener('pointerdown',e=>{touch=e.pointerType==='touch';});
  document.addEventListener('click',e=>{const button=e.target.closest('[data-path-work]');if(touch&&button){e.preventDefault();e.stopImmediatePropagation();show(button);touch=false;}else if(!box?.contains(e.target))hide();},true);
  document.addEventListener('keydown',e=>{if(e.key==='ArrowDown'&&box&&document.activeElement===trigger){e.preventDefault();box.querySelector('button,a')?.focus();}if(e.key==='Escape'&&box){const previous=trigger,inside=box.contains(document.activeElement);hide();if(inside){skipFocus=true;previous?.focus({preventScroll:true});}}});
  window.addEventListener('hashchange',hide);window.addEventListener('resize',position);window.addEventListener('scroll',position,true);
  return {hide};
}

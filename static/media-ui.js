export const mediaNames={film:'Film',tv:'Série TV',game:'Jeu vidéo',book:'Livre'};
export function sourceLink(item){
  if(['film','tv'].includes(item.type)){
    const id=String(item.catalogId||item.id||'').match(/^imdb:(tt\d+)$/)?.[1];
    const proof=item.evidence?.find(e=>e.source==='IMDb'&&/^https:\/\/(?:www\.)?imdb\.com\/title\/tt\d+(?:\/|$)/.test(e.url||''));
    const ident=id||proof?.url.match(/\/title\/(tt\d+)/)?.[1];
    return ident?{label:'IMDb',url:'https://www.imdb.com/title/'+ident+'/'}:null;
  }
  if(item.type==='game'){
    const proof=item.evidence?.find(e=>e.source==='Metacritic'&&/^https:\/\/(?:www\.)?metacritic\.com\/game\/[a-z0-9-]+\//.test(e.url||''));
    return proof?{label:'Metacritic',url:proof.url}:null;
  }
  return null;
}

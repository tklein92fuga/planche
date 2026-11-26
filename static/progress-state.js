const rank={todo:0,doing:1,done:2};
const norm=value=>String(value||'').normalize('NFKD').replace(/\p{Diacritic}/gu,'').toLocaleLowerCase('fr').replace(/[^a-z0-9]/g,'');
export function matchesWork(local,work,resolved={}){
  const id=local.catalogId||resolved[local.id];
  if(id)return id===work.id;
  return local.type===work.type&&norm(local.title)===norm(work.title)&&(!local.year||!work.year||String(local.year)===String(work.year));
}
export function workStatus(items,work,resolved={}){
  return items.filter(i=>matchesWork(i,work,resolved)).reduce((status,i)=>(rank[i.status]||0)>rank[status]?i.status:status,'todo');
}
export function updateWorkStatus(items,work,status,{resolved={},date,id}={}){
  if(!Object.hasOwn(rank,status))throw Error('Statut inconnu');
  let found=false;
  const next=items.map(local=>{
    if(!matchesWork(local,work,resolved))return local;
    found=true;
    return {...local,catalogId:work.id,status,completed:status==='done'?local.completed||date:'',updated:new Date().toISOString()};
  });
  if(!found)next.unshift({...work,id,catalogId:work.id,collection:'',status,rating:0,review:'',completed:status==='done'?date:'',updated:new Date().toISOString()});
  return next;
}

export const types = {
  film: {label:'Film', plural:'Films', icon:'◉', color:'#ded7fc'},
  book: {label:'Livre', plural:'Livres', icon:'▤', color:'#faddb8'},
  game: {label:'Jeu', plural:'Jeux', icon:'✚', color:'#dce99f'}
};
export const statuses = {todo:'À découvrir', doing:'En cours', done:'Terminé'};
const sample = [
  ['Blade Runner','film',1982,'Science-fiction','Ridley Scott','117','todo',0,'https://image.tmdb.org/t/p/w500/63N9uy8nd9j7Eog2axPQ8lbr3Wj.jpg'],
  ['Harakiri','film',1962,'Drame','Masaki Kobayashi','133','todo',0,''],
  ['Dune','book',1965,'Science-fiction','Frank Herbert','412','doing',0,'https://covers.openlibrary.org/b/isbn/9780441172719-L.jpg'],
  ['Disco Elysium','game',2019,'RPG','ZA/UM','','doing',0,'https://cdn.cloudflare.steamstatic.com/steam/apps/632470/library_600x900.jpg'],
  ['Ghost in the Shell','film',1995,'Science-fiction','Mamoru Oshii','83','done',5,'https://image.tmdb.org/t/p/w500/9gC88zYUBARRSThcG93MvW14sqx.jpg'],
  ['Perfect Blue','film',1997,'Thriller','Satoshi Kon','81','done',5,'https://image.tmdb.org/t/p/w500/6WTiOCfDPP8XV4jqfloiVWf7KHq.jpg'],
  ['La Métamorphose','book',1915,'Fantastique','Franz Kafka','96','done',4,''],
  ['Outer Wilds','game',2019,'Aventure','Mobius Digital','','done',5,'https://cdn.cloudflare.steamstatic.com/steam/apps/753640/library_600x900.jpg'],
  ['Stalker','film',1979,'Science-fiction','Andreï Tarkovski','162','todo',0,''],
  ['Le Septième Sceau','film',1957,'Drame','Ingmar Bergman','96','todo',0,''],
  ['Neuromancien','book',1984,'Science-fiction','William Gibson','271','todo',0,'https://covers.openlibrary.org/b/isbn/9780441569595-L.jpg'],
  ['Hades','game',2020,'RPG','Supergiant Games','','todo',0,'https://cdn.cloudflare.steamstatic.com/steam/apps/1145360/library_600x900.jpg']
];
export const today = (offset = 0) => {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return [date.getFullYear(), date.getMonth() + 1, date.getDate()].map(v=>String(v).padStart(2,'0')).join('-');
};
export const initial = () => ({
  demo:true,
  collections:[{id:'cinema', name:'Cinéma de répertoire'}, {id:'imaginaire',name:'Mondes imaginaires'}],
  goals:[{id:'g1', title:'Trois films ce mois-ci', target:3, type:'film', start:today().slice(0,7)+'-01'}],
  items:sample.map(([title,type,year,genre,creator,length,status,rating,image],i)=>({
    id:'demo-'+i,title,type,year,genre,creator,length,status,rating,image,review:'',
    collection:type==='film'?'cinema':'imaginaire', completed:status==='done'?today(-(i-3)*2):''
  }))
});
export const key = value => String(value ?? '').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
export function importRows(rows, fallback, collection) {
  const nonempty = rows.filter(row=>row.some(cell=>String(cell).trim()));
  const [header,...body] = nonempty;
  if (!header) throw Error('Le fichier est vide.');
  const headers = header.map(key);
  const index = (...aliases)=>headers.findIndex(h=>aliases.includes(h));
  const titleIndex = index('titre','title','nom','name','film','livre','jeu');
  if (titleIndex === -1) throw Error('Ajoute une colonne Titre à la première ligne.');
  return body.flatMap(row=>{
    const get = (...aliases)=>String(row[index(...aliases)] ?? '').trim();
    const title = String(row[titleIndex] ?? '').trim();
    if (!title) return [];
    const rawType=key(get('type','media','categorie','medium'));
    const type = Object.keys(types).find(t=>[t,key(types[t].label),key(types[t].plural)].includes(rawType))
      || ({movie:'film',movies:'film',books:'book',games:'game',jeuxvideo:'game',jeuvideo:'game'})[rawType] || fallback;
    const raw = key(get('statut','status','vu','lu','joue','termine','fini'));
    const status = ['termine','vu','lu','fini','joue','done','completed','oui','true','vrai','1','x'].includes(raw)?'done':
      ['encours','doing','inprogress'].includes(raw)?'doing':'todo';
    const rating = Math.max(0,Math.min(5,Math.round(Number(get('note','rating').replace(',','.'))||0)));
    return [{id:crypto.randomUUID(),title,type,status,rating,collection,completed:status==='done'?today():'',
      creator:get('auteur','realisateur','studio','creator','artiste'), year:get('annee','year'), genre:get('genre'),
      length:get('duree','minutes','pages','length'),review:get('critique','review','commentaire'),image:get('image','affiche','couverture','poster')}];
  });
}

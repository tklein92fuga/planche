/** Update existing nodes in place so focus, scroll and hover targets survive. */
const key=node=>node.nodeType===1?(node.id||['data-list-id','data-hover-status','data-path-work','data-cat','data-profile-path','data-path-list','data-motion-key'].map(k=>node.hasAttribute(k)?k+':'+node.getAttribute(k):'').filter(Boolean).join('|')):'';
const compatible=(a,b)=>a.nodeType===b.nodeType&&(a.nodeType!==1||(a.tagName===b.tagName&&key(a)===key(b)));
function sync(node,next){
  if(node.nodeType===3){if(node.nodeValue!==next.nodeValue)node.nodeValue=next.nodeValue;return;}
  if(node.nodeType!==1)return;
  for(const a of [...node.attributes])if(!next.hasAttribute(a.name)){
    if(['aria-controls','aria-description','aria-expanded'].includes(a.name)&&node.getAttribute('aria-controls')==='work-hover-card'&&document.getElementById('work-hover-card'))continue;
    node.removeAttribute(a.name);
  }
  for(const a of [...next.attributes])if(node.getAttribute(a.name)!==a.value)node.setAttribute(a.name,a.value);
  children(node,next);
  if(['INPUT','TEXTAREA','SELECT'].includes(node.tagName)&&node!==document.activeElement&&node.value!==next.value)node.value=next.value;
}
function children(parent,next){
  let cursor=parent.firstChild;
  for(const wanted of [...next.childNodes]){
    let match=cursor&&compatible(cursor,wanted)?cursor:null;
    if(!match&&key(wanted))match=[...parent.childNodes].find(n=>compatible(n,wanted));
    if(match){if(match!==cursor)parent.insertBefore(match,cursor);sync(match,wanted);cursor=match.nextSibling;}
    else{const fresh=wanted.cloneNode(true);parent.insertBefore(fresh,cursor);}
  }
  while(cursor){const removed=cursor;cursor=cursor.nextSibling;removed.remove();}
}
export function patchDOM(root,html){const template=document.createElement('template');template.innerHTML=html;children(root,template.content);}

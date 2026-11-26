/** Local GSAP motion: transforms only, finite animations, explicit lifecycle. */
export function startMotion(){
  const gsap=window.gsap;
  if(!gsap)return ()=>{};
  const mm=gsap.matchMedia();
  mm.add('(prefers-reduced-motion: no-preference)',()=>{
    const cards='.dash-heading,.path-heading,.page-title,.dash-kpis article,.dash-focus,.dash-activity,.dash-middle-grid>.dash-panel,.dash-list-card,.meta-index-card,.journey-row,.catalog-works>.work';
    const hoverCards='.meta-index-card,.dash-list-card,.catalog-works>.work';
    const queued=new WeakSet(),shown=new WeakSet(),active=new Set(),ratios=new Map();
    let frame=0,pending=null,expires=0;
    const main=document.querySelector('#main');
    const visible=el=>{const r=el.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth;};
    function track(animation,targets){const record={animation,targets};active.add(record);animation.eventCallback('onComplete',()=>active.delete(record));animation.eventCallback('onInterrupt',()=>active.delete(record));return animation;}
    function enter(elements){
      if(!elements.length)return;
      const targets=elements.filter(el=>el.isConnected&&!shown.has(el));
      targets.forEach(el=>shown.add(el));
      if(!targets.length)return;
      // Adapted from the supplied vanilla timeline/stagger example.
      const tl=gsap.timeline({defaults:{duration:.38,ease:'power2.out'}});
      tl.fromTo(targets,{autoAlpha:0,y:12},{autoAlpha:1,y:0,stagger:{amount:.18},clearProps:'opacity,visibility,transform'});
      track(tl,targets);
    }
    function progress(el){
      const bar=el.querySelector('i');if(!bar||shown.has(el))return;
      shown.add(el);
      const key=el.dataset.motionKey||el.getAttribute('aria-label');
      const max=Number(el.getAttribute('aria-valuemax')),value=Number(el.getAttribute('aria-valuenow'));
      const next=max?value/max:0,previous=ratios.get(key)||0;
      if(key)ratios.set(key,next);
      if(!next||previous===next)return;
      gsap.killTweensOf(bar);
      track(gsap.fromTo(bar,{scaleX:previous/next,transformOrigin:'left center'},{scaleX:1,duration:.55,ease:'power2.out',clearProps:'transform,transformOrigin'}),[bar]);
    }
    const intersection=new IntersectionObserver(entries=>{
      const incoming=entries.filter(e=>e.isIntersecting).map(e=>e.target);
      incoming.forEach(el=>intersection.unobserve(el));
      incoming.filter(el=>el.matches('.track')).forEach(progress);
      enter(incoming.filter(el=>!el.matches('.track')).slice(0,24));
    },{threshold:.08});
    function find(root,selector){return root.nodeType===1?[...(root.matches(selector)?[root]:[]),...root.querySelectorAll(selector)]:[];}
    function scan(root){
      const targets=find(root,cards+',.track[role="progressbar"]');
      for(const el of targets.slice(0,120))if(!queued.has(el)){queued.add(el);intersection.observe(el);}
      const tooltip=document.querySelector('.work-hover-card');
      if(tooltip&&!shown.has(tooltip)){
        shown.add(tooltip);
        // No scale/position tween: fixed placement remains stable as offers load.
        track(gsap.fromTo(tooltip,{opacity:0,y:5},{opacity:1,y:0,duration:.18,ease:'power2.out',clearProps:'opacity,visibility,transform'}),[tooltip]);
      }
      if(pending&&performance.now()<expires){
        const selector=pending.status==='todo'?'[data-path-work]':pending.status==='done'?'[data-path-work], [data-cat="done"]':'[data-path-work], [data-cat="doing"]';
        const matches=[...main.querySelectorAll(selector)].filter(el=>(el.dataset.pathWork||el.dataset.id)===pending.id&&visible(el)).slice(0,8);
        if(matches.length){
          pending=null;
          const tl=gsap.timeline();tl.fromTo(matches,{scale:.88},{scale:1.1,duration:.18,ease:'power2.out'}).to(matches,{scale:1,duration:.24,ease:'back.out(1.5)',clearProps:'transform'});
          track(tl,matches);
        }
      }
    }
    const observer=new MutationObserver(records=>{
      for(const record of records)if(record.type==='attributes'&&visible(record.target)){shown.delete(record.target);progress(record.target);}
      for(const record of records)for(const node of record.removedNodes){
        for(const bar of find(node,'.track[role="progressbar"]')){
          const key=bar.dataset.motionKey||bar.getAttribute('aria-label'),max=Number(bar.getAttribute('aria-valuemax'));
          if(key)ratios.set(key,max?Number(bar.getAttribute('aria-valuenow'))/max:0);
        }
        for(const el of find(node,cards+',.track[role="progressbar"]'))intersection.unobserve(el);
      }
      for(const record of [...active])if(!record.targets.some(el=>el.isConnected)){record.animation.revert();active.delete(record);}
      if(!frame)frame=requestAnimationFrame(()=>{frame=0;scan(main);});
    });
    observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-valuenow']});
    function status(event){pending=event.detail;expires=performance.now()+3000;scan(main);}
    function lift(event){
      if(!window.matchMedia('(hover: hover)').matches)return;
      const el=event.target.closest(hoverCards);if(!el||el.contains(event.relatedTarget))return;
      track(gsap.to(el,{y:event.type==='pointerover'?-3:0,duration:.2,ease:'power2.out',overwrite:'auto',...(event.type==='pointerout'?{clearProps:'transform'}:{})}),[el]);
    }
    document.addEventListener('planche:status',status);
    document.addEventListener('pointerover',lift);document.addEventListener('pointerout',lift);
    frame=requestAnimationFrame(()=>{frame=0;scan(main);});
    return ()=>{
      observer.disconnect();intersection.disconnect();cancelAnimationFrame(frame);
      document.removeEventListener('planche:status',status);
      document.removeEventListener('pointerover',lift);document.removeEventListener('pointerout',lift);
      active.forEach(({animation})=>animation.revert());active.clear();
      main.querySelectorAll(hoverCards).forEach(el=>gsap.set(el,{clearProps:'transform'}));
    };
  });
  const stop=()=>mm.revert();
  window.addEventListener('pagehide',stop,{once:true});
  return stop;
}

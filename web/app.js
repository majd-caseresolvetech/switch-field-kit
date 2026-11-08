(() => {
  'use strict';
  const main=document.querySelector('#main');
  let library, currentView='', cleanup=()=>{}, generation=0;
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const link=(text,href,cls='button')=>{const n=el('a',text,cls);n.href=href;return n;};
  const button=(text,fn,cls='')=>{const n=el('button',text,cls);n.type='button';n.onclick=fn;return n;};
  const saved=(key,fallback)=>{try{return localStorage.getItem(key)||fallback;}catch(_){return fallback;}};
  const save=(key,value)=>{try{localStorage.setItem(key,String(value));}catch(_){}};
  const fetchJSON=async url=>{const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error('A saved library file could not load: '+url);return r.json();};
  function command(text){
    const box=el('div',undefined,'command-box'),code=el('code',text.replace(/^fieldkit /gm,'~/.local/bin/fieldkit '),'command'),status=el('span','','meta');
    status.setAttribute('role','status');
    const copy=button('COPY COMMAND',async()=>{
      try{await navigator.clipboard.writeText(code.textContent);status.textContent='Copied. Paste into Ubuntu Terminal and press Enter.';}
      catch(_){const range=document.createRange();range.selectNodeContents(code);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);status.textContent='Command selected. Copy it, then paste into Ubuntu Terminal.';}
    });
    box.append(code,copy,status);return box;
  }
  function refreshButton(){return button('REFRESH LIBRARY',route);}
  function downloadSteps(){return el('p','Open Ubuntu Terminal, paste the command and press Enter. Keep Wi-Fi and the charger connected until it finishes, then refresh this library.','small-note');}
  function intro(title,text){main.append(el('h1',title),el('p',text));}
  function error(e){const p=el('p',e.message||String(e));p.id='app-error';p.setAttribute('role','alert');main.append(p);}
  function home(){
    intro('Expert original guides','Complete publications with the authors’ instructions and diagrams. Choose a topic, then jump to a method.');
    const ready=library.guides.filter(d=>d.installed).length;
    if(!ready){const n=el('div',undefined,'notice');n.append(el('strong','Your reader is ready. Add its guides while online.'),downloadSteps(),command('fieldkit guides all'),refreshButton(),el('p','About 128 MB to download. Allow 1 GB free for the complete pack. HELP explains setup and missing PDF tools.','small-note'));main.append(n);}
    const last=library.guides.find(d=>d.installed&&d.id===saved('last-guide',''));
    if(last)main.append(link('CONTINUE READING: '+last.title,'#guide='+encodeURIComponent(last.id),'button resume'));
    const bar=el('div',undefined,'toolbar'),query=el('input'),region=el('select'),topic=el('select'),only=el('button','READY OFFLINE');
    query.type='search';query.placeholder='Find water, shelter, plants…';query.setAttribute('aria-label','Find a guide');
    region.setAttribute('aria-label','Region');topic.setAttribute('aria-label','Topic');
    for(const [value,text] of [['all','All regions'],['UK','UK + international'],['Lebanon','Lebanon + international']]){const o=el('option',text);o.value=value;region.append(o);}
    const names={shelter:'Shelter',water:'Water',sanitation:'Sanitation',health:'First aid',forage:'Plant identification',mushrooms:'Mushroom identification',bushcraft:'Bushcraft',cooking:'Fire + cooking',transport:'Navigation',farming:'Growing food + trees',building:'Building',food:'Plant uses',refuge:'Refuge'};
    const all=el('option','All topics');all.value='all';topic.append(all);
    Object.entries(names).forEach(([value,text])=>{const o=el('option',text);o.value=value;topic.append(o);});
    let readyOnly=false;
    only.type='button';only.setAttribute('aria-pressed','false');only.onclick=()=>{readyOnly=!readyOnly;only.setAttribute('aria-pressed',readyOnly);render();};
    const count=el('p','','meta'),grid=el('div',undefined,'grid');grid.id='guide-cards';
    bar.append(query,region,topic,only);main.append(bar,count,grid);
    let timer;
    function render(){grid.replaceChildren();const q=query.value.trim().toLowerCase();const rows=library.guides.filter(d=>(!readyOnly||d.installed)&&(region.value==='all'||[region.value,'International'].includes(d.region))&&(topic.value==='all'||d.categories.includes(topic.value))&&[d.title,d.original,d.publisher,d.scope].join(' ').toLowerCase().includes(q));count.textContent=rows.length+' guides shown · '+ready+' saved offline';
      for(const d of rows){const card=el('article',undefined,'card');card.append(el('span',d.installed?'SAVED OFFLINE · PUBLISHER ORIGINAL':'AVAILABLE TO DOWNLOAD','status'+(d.installed?'':' pending')),el('h3',d.title),el('small',d.publisher+' · '+d.edition+' · '+d.region+' · '+d.language),el('p',d.scope));
        const foot=el('div',undefined,'open');foot.append(el('p',d.pages+' original PDF sheets','meta'));
        if(d.installed)foot.append(link('OPEN GUIDE','#guide='+encodeURIComponent(d.id),'button primary'));else foot.append(button('HOW TO DOWNLOAD',()=>{foot.replaceChildren(downloadSteps(),command('fieldkit guides '+d.id),refreshButton());}));card.append(foot);grid.append(card);}
      if(!rows.length)grid.append(el('p','No matching guides. Try a different topic or region.','empty'));
    }
    query.oninput=()=>{clearTimeout(timer);timer=setTimeout(render,150);};region.onchange=render;topic.onchange=render;cleanup=()=>clearTimeout(timer);render();
  }
  async function guide(id,turn){
    const record=library.guides.find(d=>d.id===id);if(!record||!record.installed)throw Error('This guide is not installed. Return to Expert Guides for its download command.');
    const d=await fetchJSON('/guides/'+encodeURIComponent(id)+'/publication.json');if(turn!==generation)return;
    const reader=el('article',undefined,'reader');main.append(reader);reader.append(link('‹ ALL GUIDES','#guides'),el('h1',d.title),el('p',d.publisher+' · '+d.edition+' · '+d.region+' · '+d.language,'meta'));
    if(['plantlife-id','aub-plants','bna-fungi'].includes(id))reader.append(el('p','Identification or plant-use reference. This is not a complete edible-species key.','notice'));
    let page=Math.max(1,Math.min(d.pages,Number(saved('page:'+id,d.start))||d.start));
    const controls=el('div',undefined,'reader-controls'),form=el('form'),input=el('input'),total=el('span','/ '+d.pages),image=el('img'),label=el('p','','page-label'),panel=el('section',undefined,'contents');
    image.className='page-image';image.alt='Original publication sheet';image.id='source-page';image.tabIndex=0;image.decoding='async';input.type='number';input.min=1;input.max=d.pages;input.setAttribute('aria-label','PDF sheet number');input.id='sheet-number';
    const prev=button('‹ PREV',()=>show(page-1)),next=button('NEXT ›',()=>show(page+1)),go=el('button','GO');go.type='submit';
    const sections=button('CONTENTS + FIND',()=>{panel.hidden=!panel.hidden;sections.setAttribute('aria-expanded',!panel.hidden);});sections.setAttribute('aria-expanded','false');
    form.append(el('label','SHEET'),input,total,go);form.onsubmit=e=>{e.preventDefault();show(Number(input.value));input.blur();};
    controls.append(prev,form,next,sections,button('ENLARGE',()=>zoom(image),'primary'));reader.append(controls,label,panel,image);panel.hidden=true;
    const sectionGrid=el('div',undefined,'grid');for(const [n,title] of d.sections){const b=button(title+' · sheet '+n,()=>{show(n);panel.hidden=true;sections.setAttribute('aria-expanded','false');});b.dataset.sheet=n;sectionGrid.append(b);}panel.append(el('p','Jump directly to the original method.'),sectionGrid);
    const search=el('form'),q=el('input'),searchButton=el('button','FIND'),results=el('div');q.type='search';q.placeholder=d.section_search_only?'Find a section…':'Find a word in the original…';q.setAttribute('aria-label','Search within this guide');searchButton.type='submit';search.append(q,searchButton);panel.append(search,results);
    const sectionAt=n=>[...d.sections].reverse().find(s=>s[0]<=n)?.[1]||'Front matter';
    search.onsubmit=e=>{e.preventDefault();results.replaceChildren();const terms=q.value.normalize('NFKC').toLowerCase().trim().split(/\s+/).filter(Boolean);if(!terms.length)return;let hits=0;for(let i=0;i<d.pages;i++){const text=((d.text[i]||'')+' '+d.sections.filter(s=>s[0]===i+1).map(s=>s[1]).join(' ')).normalize('NFKC').toLowerCase();if(terms.every(t=>text.includes(t))){hits++;results.append(button('Sheet '+(i+1)+' · '+sectionAt(i+1),()=>{show(i+1);panel.hidden=true;sections.setAttribute('aria-expanded','false');}));}}results.prepend(el('p',hits+' matching sheets'));};
    const about=el('details'),summary=el('summary','Author, scope and complete original PDF'),pdf=link('OPEN COMPLETE PDF','');pdf.id='original-pdf';pdf.target='_blank';pdf.rel='noopener';
    about.append(summary,el('p',d.original),el('p','Author: '+d.author),el('p',d.scope),el('p',d.note),pdf,el('p','The original PDF is unchanged. Sheet images preserve its full text and diagrams. Publication dates are shown because these are saved references, not live updates.','meta'),link('PUBLISHER SOURCE · INTERNET REQUIRED',d.source_page||d.url));
    reader.append(el('p','Tap the page to enlarge. Use + / −, drag or pinch. Your reading position is saved.','meta'),about);
    image.onclick=()=>zoom(image);image.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();zoom(image);}};
    image.onerror=()=>{label.textContent='This page image is missing. Open the complete PDF below or re-run: fieldkit guides '+id;};
    function show(n,scroll=true){page=Math.max(1,Math.min(d.pages,Math.floor(n)||d.start));input.value=page;label.textContent=sectionAt(page);image.src='/guides/'+id+'/'+String(page).padStart(3,'0')+'.jpg';image.alt=d.publisher+', '+d.original+', original sheet '+page+' of '+d.pages;prev.disabled=page===1;next.disabled=page===d.pages;pdf.href='/guides/'+id+'/original.pdf#page='+page;save('page:'+id,page);save('last-guide',id);if(scroll)window.scrollTo(0,0);}
    show(page,false);
  }
  function books(){intro('Wikipedia + books','Add ZIM books once, then read and search their full text without internet.');if(!library.books.length){const box=el('div',undefined,'empty');box.append(el('h2','1. Choose a book that fits your card'),el('p','Download a complete .zim book from the Kiwix library while online. Start with Simple English Wikipedia or a small topic collection. Note its filename and leave it in a permanent folder.'),link('OPEN KIWIX CATALOGUE · INTERNET REQUIRED','https://library.kiwix.org/'),el('h2','2. Install the book reader'),downloadSteps(),command('fieldkit kiwix'),el('h2','3. Add your downloaded file'),el('p','Replace the example path below with your .zim file. You can type ~/.local/bin/fieldkit add-book followed by a space, then drag the file into Terminal and press Enter.'),command('fieldkit add-book "/path/to/your-book.zim"'),el('h2','4. Start the book reader'),command('fieldkit restart'),refreshButton(),el('p','The file is registered in place, without a second copy. Files larger than 4 GB need Linux storage, not the FAT32 boot partition.','small-note'));main.append(box);return;}
    const ul=el('ul');for(const b of library.books)ul.append(el('li',b.title+(b.available?'':' · STORAGE NOT MOUNTED')));main.append(ul);
    if(library.kiwix_running){const frame=el('iframe');frame.className='book-frame';frame.title='Offline Kiwix library';frame.src='/kiwix/';main.append(frame);}else main.append(el('p','The book reader is not running. Keep your registered files in place, repair Kiwix while online, then restart.'),command('fieldkit kiwix &&\nfieldkit restart'),refreshButton());
  }
  function mapSetup(){
    const box=el('div',undefined,'empty'),select=el('select');select.setAttribute('aria-label','Map to download');
    for(const [value,title] of [['lebanon','Lebanon'],['uk','United Kingdom'],['prague','Prague'],['world','World overview'],['europe-levant','Europe to Levant overview']]){const o=el('option',title);o.value=value;select.append(o);}
    const instructions=el('div');const update=()=>instructions.replaceChildren(command('fieldkit map-tools &&\nfieldkit download-map '+select.value));select.onchange=update;
    box.append(el('h2','Add an offline map'),el('p','Choose an area. The download command calculates its size and asks before fetching map tiles. Only accept a size that fits your card.'),select,downloadSteps(),instructions,refreshButton(),el('p','The Europe to Levant preset is an overview, not detailed walking coverage. Maps do not calculate routes.','small-note'));update();return box;
  }
  function maps(){intro('Offline maps','Saved places, roads and paths. No internet, live GPS or route calculation.');if(!library.maps.length){main.append(mapSetup());return;}
    if(!library.map_tools_ready){main.append(el('p','Your map files are registered. Finish installing the local viewer while online, then refresh.'),command('fieldkit map-tools'),refreshButton());return;}
    const more=el('details');more.append(el('summary','Add another area'),mapSetup());main.append(more);
    const frame=el('iframe');frame.title='Offline map';frame.className='map-frame';frame.src='/web/map.html';main.append(frame);cleanup=()=>{frame.src='about:blank';};
  }
  function signals(){intro('Phrases + signals','A short communication card. Point to the phrase if pronunciation is difficult.');const box=el('div',undefined,'notice');box.append(el('h2','SOS in Morse'),el('div','···  ———  ···','signal'),el('p','Three short signals, three long signals, three short signals. This screen is a reference and does not transmit a radio message.'));main.append(box);
    const table=el('table'),head=el('tr');['English','Arabic','Czech'].forEach(t=>head.append(el('th',t)));table.append(head);
    for(const row of [['I need help.','أحتاج إلى مساعدة.','Potřebuji pomoc.'],['Please call an ambulance.','من فضلك اتصل بالإسعاف.','Zavolejte prosím sanitku.'],['Where is drinking water?','أين توجد مياه للشرب؟','Kde je pitná voda?'],['Where is a hospital?','أين يوجد مستشفى؟','Kde je nemocnice?'],['I do not understand.','لا أفهم.','Nerozumím.']]){const tr=el('tr');row.forEach((t,i)=>{const td=el('td',t);if(i===1){td.lang='ar';td.dir='rtl';}tr.append(td);});table.append(tr);}
    const scroll=el('div',undefined,'scroll-table');scroll.append(table);main.append(scroll,el('p','Basic project-written phrases, not a certified translation or interpreter service. See Help for radio limitations.','meta'));
  }
  function help(){intro('Using your field kit','Download while connected. Read from local storage when disconnected.');const box=el('div',undefined,'help');main.append(box);
    box.append(el('h2','First setup: add your content'),el('p','Installing the reader does not download Wikipedia or maps. Add only what you need, then check it with Wi-Fi off.'),downloadSteps(),command('fieldkit guides all'),link('ADD WIKIPEDIA OR BOOKS','#books'),link('ADD MAPS','#maps'),refreshButton(),el('p','If a guide download reports missing PDF tools, run this once in Ubuntu Terminal. Ubuntu asks for your account password.'),command('sudo apt install poppler-utils'),el('p','Then repeat the guide download command. Completed guides are kept.'));
    for(const [title,text] of [['Open a guide','EXPERT GUIDES shows complete publisher originals. Filter by region and topic. CONTENTS + FIND jumps to a method. ENLARGE makes drawings easier to inspect.'],['Keep stock boot','This app does not change Hekate, stock firmware or SD partitions. Return to stock using your existing boot-menu entry. Ubuntu and your stock fallback must be prepared before installing this app.'],['Save battery','Lower screen brightness to a comfortable level. Turn off Wi-Fi after downloads. Close Maps when reading. The reader loads one original sheet at a time and has no decorative animation. Set screen dimming and battery sleep in Ubuntu Settings.'],['Foraging coverage','The starter collection contains identification and plant-use references. It is not a complete edible-plant or mushroom key. Each guide shows its author, edition and scope.'],['Maps and radio','Map detail depends on the archive you downloaded. A drawn path does not establish access or safe passage. The Switch has no built-in AM/FM broadcast receiver or GPS. Use separate equipment for those functions.'],['Offline check','Open a guide and enlarge a diagram. Open a book and search it. Open a map and inspect the places you need. Then turn Wi-Fi off and repeat. If a page is unavailable, download or repair it before relying on that part of the library.']]){box.append(el('h2',title),el('p',text));}
    box.append(el('h2','Useful commands'),command('fieldkit guides all\nfieldkit doctor\nfieldkit restart\nfieldkit uninstall'),el('p','Uninstall removes this app and its service. Downloaded files are kept. The software is MIT licensed. Publisher books, maps and third-party tools retain their own licences.'));
  }
  async function route(){const turn=++generation;cleanup();cleanup=()=>{};document.querySelector('#zoom-dialog').close();main.replaceChildren();const hash=location.hash.slice(1)||'guides';currentView=hash;document.querySelectorAll('.tabs a').forEach(a=>{const active=hash.startsWith('guide=')?a.hash==='#guides':a.hash==='#'+hash;if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});window.scrollTo(0,0);try{library=await fetchJSON('/api/library');if(turn!==generation)return;if(hash.startsWith('guide='))await guide(decodeURIComponent(hash.slice(6)),turn);else if(hash==='books')books();else if(hash==='maps')maps();else if(hash==='help')help();else if(hash==='signals')signals();else home();}catch(e){if(turn===generation)error(e);}}
  const dialog=document.querySelector('#zoom-dialog'),stage=document.querySelector('#zoom-stage'),zoomImage=document.querySelector('#zoom-image');let factor=1,fit=1,drag,points=new Map(),pinch;
  function resize(){zoomImage.style.width=Math.round(zoomImage.naturalWidth*factor)+'px';}
  function change(value){factor=Math.max(fit*.5,Math.min(4,value));resize();}
  function zoom(image){if(!image.complete||!image.naturalWidth)return;zoomImage.src=image.currentSrc||image.src;zoomImage.alt=image.alt;dialog.showModal();zoomImage.onload=()=>{fit=Math.min((stage.clientWidth-12)/zoomImage.naturalWidth,(stage.clientHeight-12)/zoomImage.naturalHeight,1);factor=fit;resize();stage.scrollTo(0,0);};if(zoomImage.complete)zoomImage.onload();}
  document.querySelector('#zoom-close').onclick=()=>dialog.close();document.querySelector('#zoom-in').onclick=()=>change(factor*1.4);document.querySelector('#zoom-out').onclick=()=>change(factor/1.4);document.querySelector('#zoom-fit').onclick=()=>change(fit);dialog.onclose=()=>{points.clear();drag=null;pinch=null;};
  stage.onpointerdown=e=>{points.set(e.pointerId,[e.clientX,e.clientY]);stage.setPointerCapture(e.pointerId);if(points.size===1)drag={x:e.clientX,y:e.clientY,left:stage.scrollLeft,top:stage.scrollTop};if(points.size===2){const p=[...points.values()];pinch={distance:Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]),factor};drag=null;}};
  stage.onpointermove=e=>{if(!points.has(e.pointerId))return;points.set(e.pointerId,[e.clientX,e.clientY]);if(points.size===2&&pinch){const p=[...points.values()];change(pinch.factor*Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1])/pinch.distance);}else if(drag){stage.scrollLeft=drag.left-(e.clientX-drag.x);stage.scrollTop=drag.top-(e.clientY-drag.y);}};
  stage.onpointerup=stage.onpointercancel=e=>{points.delete(e.pointerId);drag=null;pinch=null;};
  window.addEventListener('hashchange',route);route();
})();

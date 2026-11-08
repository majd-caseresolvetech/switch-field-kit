const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const origin=process.env.FIELDKIT_TEST_URL||'http://127.0.0.1:8095';
const out=process.env.FIELDKIT_TEST_OUTPUT||'test-results';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.FIELDKIT_BROWSER_CHANNEL?{channel:process.env.FIELDKIT_BROWSER_CHANNEL}:{})});
 const context=await browser.newContext({viewport:{width:1280,height:720}}),page=await context.newPage();
 const errors=[],remote=[],bad=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)bad.push([r.status(),r.url()]);});
 await context.route('**/*',async route=>{const u=new URL(route.request().url());if(['data:','blob:'].includes(u.protocol)||u.origin===origin)return route.continue();remote.push(u.href);return route.abort();});
 try{
  await page.goto(origin);await page.locator('#guide-cards .card').first().waitFor();assert.equal(await page.locator('#guide-cards .card').count(),27);
  await page.locator('select[aria-label=Region]').selectOption('Lebanon');assert.equal(await page.locator('#guide-cards .card').count(),21);
  await page.locator('select[aria-label=Region]').selectOption('UK');assert.equal(await page.locator('#guide-cards .card').count(),23);
  await page.locator('select[aria-label=Region]').selectOption('all');
  await page.locator('input[type=search]').fill('water');await page.waitForTimeout(200);assert(await page.locator('#guide-cards .card').count()>0);
  await page.locator('input[type=search]').fill('');await page.waitForTimeout(200);
  await page.screenshot({path:path.join(out,'interface.png'),fullPage:false});
  const ready=await page.locator('#guide-cards a').count();
  if(ready){
   await page.locator('#guide-cards a').first().click();await page.locator('#source-page[src]').waitFor();await page.locator('#source-page').evaluate(i=>i.decode());
   const initial=Number(await page.locator('#sheet-number').inputValue());
   await page.getByRole('button',{name:'CONTENTS + FIND',exact:true}).click();await page.locator('.contents [data-sheet]').last().click();
   const selected=Number(await page.locator('#sheet-number').inputValue());assert(selected>=initial);
   await page.locator('#source-page').evaluate(i=>i.decode());
   await page.getByRole('button',{name:'ENLARGE',exact:true}).click();assert(await page.locator('#zoom-dialog').isVisible());
   const before=await page.locator('#zoom-image').evaluate(e=>e.getBoundingClientRect().width);await page.locator('#zoom-in').click();assert(await page.locator('#zoom-image').evaluate(e=>e.getBoundingClientRect().width)>before);await page.locator('#zoom-close').click();
   await page.reload();await page.locator('#source-page[src]').waitFor();assert.equal(Number(await page.locator('#sheet-number').inputValue()),selected);
   await page.getByRole('button',{name:'CONTENTS + FIND',exact:true}).click();await page.locator('.contents input').fill('shelter');await page.locator('.contents form button').click();assert((await page.locator('.contents').innerText()).includes('matching sheets'));
  }
  for(const hash of ['signals','help','books','guides']){await page.goto(origin+'/#'+hash);await page.locator('h1').waitFor();assert.equal(await page.locator('body').evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
  const state=await page.evaluate(()=>fetch('/api/library').then(r=>r.json()));
  if(state.maps.length){
   await page.goto(origin+'/#maps');const mapFrame=page.frameLocator('.map-frame');await mapFrame.locator('.maplibregl-canvas').waitFor();
   await mapFrame.locator('body').evaluate(()=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Map load timeout')),30000);const check=()=>{if(window.fieldMap&&window.fieldMap.areTilesLoaded()){clearTimeout(timer);resolve();}else setTimeout(check,100);};check();}));
   assert(!(await mapFrame.locator('#status').innerText()).includes('could not'));assert(await mapFrame.locator('body').evaluate(()=>window.fieldMap.queryRenderedFeatures().length)>0);
   await page.screenshot({path:path.join(out,'map.png')});
  }
  await page.setViewportSize({width:720,height:506});await page.goto(origin);await page.locator('#guide-cards .card').first().waitFor();assert.equal(await page.locator('body').evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);assert.deepEqual(bad,[]);
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({status:'passed',readyGuides:ready,errors,externalRequests:remote,badResponses:bad},null,2));
  console.log('Browser checks passed. Ready guides: '+ready);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});

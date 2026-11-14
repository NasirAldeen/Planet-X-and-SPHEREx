import {parseCoordinate, matchedFrames, percentile, sharedScale, difference, stack, fieldURL} from './science.js';

const $ = id => document.getElementById(id);
const state = {data:null, targets:[], active:[], index:0, reference:0, mode:'blink', timer:null, scale:null, token:0};
const sky = $('sky'), ctx = sky.getContext('2d');
const date = str => new Date(str).toLocaleDateString('en-GB', {day:'2-digit', month:'short', year:'numeric', timeZone:'UTC'});
const shortDate = str => new Date(str).toISOString().slice(0,10);
const status = (text, error=false) => { $('status').textContent=text; $('status').classList.toggle('error', error); };
const busy = (text, enabled=true) => { $('loading').hidden=!enabled; $('loading-text').textContent=text; $('search-button').disabled=enabled; };
const current = () => state.data?.frames[state.active[state.index]];

async function getJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.headers.get('content-type')?.includes('application/json'))
    throw Error('Live coordinate searches need the Python server. Run python server.py, or explore the five bundled targets.');
  const result = await response.json();
  if (!response.ok) throw Error(result.error || 'The request could not be completed.');
  return result;
}

function stop() {
  clearInterval(state.timer); state.timer=null;
  $('play').textContent='▶'; $('play').setAttribute('aria-label','Play time sequence');
}

function step(delta) {
  if (!state.active.length) return;
  state.index=(state.index+delta+state.active.length)%state.active.length;
  render();
}

function updateActive() {
  stop();
  state.active=matchedFrames(state.data.frames,state.reference,$('match-wave').checked);
  state.index=0;
  state.scale=sharedScale(state.active.map(i=>state.data.frames[i]));
  const waves=state.active.map(i=>state.data.frames[i].wavelength_um).filter(x=>x>0);
  const note=$('match-wave').checked ? `${state.active.length} of ${state.data.frames.length} exposures within 5% of reference λ. Center wavelength only; bandpass varies across the field.` : 'All wavelengths shown. Spectral differences can imitate changes in brightness. Use wavelength matching before comparison.';
  $('wavelength-note').textContent=note;
  if(state.active.length<2) status('Only one wavelength-matched exposure. Select another reference or disable wavelength matching to inspect all exposures.',true);
  else status(`${state.active.length} real exposures ready. ${$('match-wave').checked?'Wavelength matching is on.':'Wavelength matching is off.'} Use ← / → to step, or Space to play.`);
  $('timeline').max=Math.max(0,state.active.length-1);
  $('first-date').textContent=date(state.data.frames[state.active[0]].date);
  $('last-date').textContent=date(state.data.frames[state.active.at(-1)].date);
  const first=state.data.frames[state.active[0]], last=state.data.frames[state.active.at(-1)];
  $('baseline').textContent=`${(last.mjd-first.mjd).toFixed(1)} day baseline`;
  buildFilmstrip(); render();
}

function raster(pixels, diverging=false) {
  const {width,height}=state.data;
  const off=document.createElement('canvas');off.width=width;off.height=height;
  const c=off.getContext('2d'), image=c.createImageData(width,height);
  const contrast=Number($('stretch').value), invert=$('invert').checked;
  const scale=state.scale;
  const diffScale=diverging?Math.max(1e-9,percentile(pixels.filter(x=>x!==null).map(Math.abs),.99)):1;
  for(let i=0;i<pixels.length;i++){
    const v=pixels[i], at=i*4;
    let r=3,g=7,b=11;
    if(v!==null&&Number.isFinite(v)){
      if(diverging){
        const x=Math.min(1,Math.asinh(Math.abs(v)/diffScale*contrast)/Math.asinh(contrast));
        const base=18;
        r=v>=0?base+x*233:base+x*40;g=base+x*99;b=v<0?base+x*230:base+x*43;
      }else{
        const linear=Math.max(0,(v-scale.low)/(scale.high-scale.low));
        const x=Math.min(1,Math.asinh(linear*contrast*6)/Math.asinh(contrast*6));
        r=3+x*233;g=7+x*240;b=11+x*244;
      }
      if(invert){r=255-r;g=255-g;b=255-b;}
    }
    image.data[at]=r;image.data[at+1]=g;image.data[at+2]=b;image.data[at+3]=255;
  }
  c.putImageData(image,0,0);
  // FITS row zero is South on our north-up WCS; canvas row zero is at the top.
  const flipped=document.createElement('canvas');flipped.width=width;flipped.height=height;
  const fc=flipped.getContext('2d');fc.translate(0,height);fc.scale(1,-1);fc.drawImage(off,0,0);
  return flipped;
}

function render() {
  const f=current();if(!f)return;
  const d=state.data, ref=d.frames[state.reference];
  ctx.imageSmoothingEnabled=false;
  ctx.clearRect(0,0,600,600);
  let pixels=f.pixels;
  if(state.mode==='difference')pixels=difference(pixels,ref.pixels);
  if(state.mode==='stack')pixels=stack(state.active.map(i=>d.frames[i]));
  ctx.drawImage(raster(pixels,state.mode==='difference'),0,0,600,600);
  if(state.mode==='split'){
    const x=Number($('wipe').value)*6;
    ctx.save();ctx.beginPath();ctx.rect(0,0,x,600);ctx.clip();ctx.drawImage(raster(ref.pixels),0,0,600,600);ctx.restore();
    ctx.strokeStyle='#b6efd5';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,600);ctx.stroke();
  }
  if($('show-grid').checked){
    ctx.strokeStyle='#b6efd530';ctx.lineWidth=1;ctx.font='10px monospace';ctx.fillStyle='#adc8c8';
    for(let j=1;j<4;j++){
      const p=j*150;ctx.beginPath();ctx.moveTo(p,0);ctx.lineTo(p,600);ctx.moveTo(0,p);ctx.lineTo(600,p);ctx.stroke();
      const offset=(2-j)*d.fov_arcmin/4;
      ctx.fillText(`${offset>=0?'+':''}${offset.toFixed(1)}′ E`,p+4,588);
      ctx.fillText(`${offset>=0?'+':''}${offset.toFixed(1)}′ N`,5,p-5);
    }
  }
  $('frame-date').textContent=state.mode==='stack'?`${state.active.length} exposure mean`:date(f.date);
  $('frame-tag').textContent=state.mode==='difference'?'CURRENT − REFERENCE':state.mode==='split'?'REFERENCE / CURRENT':state.mode==='stack'?'STACKED OBSERVATIONS':'OBSERVED · UTC';
  $('frame-wave').textContent=state.mode==='stack'?'Selected exposures':f.wavelength_um?`${f.wavelength_um.toFixed(3)} µm`:'Unavailable';
  const caption=state.mode==='difference'?'Orange = brighter · Blue = dimmer · Masked overlap excluded':state.mode==='stack'?'Mean of valid pixels · Same display scale as individual frames':'North up · East left · Shared brightness scale';
  $('stage-caption').textContent=caption;
  $('split-control').hidden=state.mode!=='split';
  $('timeline').value=state.index;
  $('frame-counter').textContent=`${state.index+1} / ${state.active.length} exposures`;
  $('usable').textContent=`${((1-f.masked_fraction)*100).toFixed(1)}%`;
  $('health-dot').style.background=f.masked_fraction>.1?'#d4b27d':'#b6efd5';
  $('frame-detector').textContent=d.detector;
  $('release').textContent=f.collection.replace('spherex_','').toUpperCase();
  $('sampling').textContent=`${d.pixel_scale_arcsec.toFixed(2)}″ / px`;
  $('fits-link').href=f.cutout_url;
  $('scale-bar').style.width=`${Math.min(140,Math.max(12,sky.getBoundingClientRect().width/d.fov_arcmin))}px`;
  document.querySelectorAll('.thumbnail').forEach((button,i)=>button.setAttribute('aria-current',String(i===state.index)));
  sky.setAttribute('aria-label',`${state.mode} view of ${d.target?.name||'custom sky field'}, ${date(f.date)}, ${d.detector}, ${f.wavelength_um?.toFixed(3)||'unknown'} micrometers; north up, east left.`);
}

function buildFilmstrip(){
  $('filmstrip').replaceChildren();
  state.active.forEach((frameIndex,i)=>{
    const f=state.data.frames[frameIndex],button=document.createElement('button');
    button.className='thumbnail';button.setAttribute('aria-label',`Observation ${i+1}, ${date(f.date)}`);
    const thumb=document.createElement('canvas');thumb.width=100;thumb.height=100;
    thumb.getContext('2d').drawImage(raster(f.pixels),0,0,100,100);
    const label=document.createElement('span');label.textContent=shortDate(f.date);
    button.append(thumb,label);button.addEventListener('click',()=>{stop();state.index=i;render();});
    $('filmstrip').append(button);
  });
}

function loadData(data,target){
  if(!data.frames?.length||!data.frames.every(f=>f.pixels?.length===data.width*data.height))
    throw Error('This sequence has no valid image frames.');
  stop();state.data=data;state.reference=bestReference(data.frames);
  if(target)state.data.target=target;
  $('field-name').textContent=data.target?.name||`RA ${data.ra.toFixed(4)}° · Dec ${data.dec.toFixed(4)}°`;
  $('target-hint').textContent=data.target?.hint||'Look for position or brightness changes against neighboring sources. Compare similar wavelengths and check original FITS quality flags.';
  $('ra').value=data.ra.toFixed(8);$('dec').value=data.dec.toFixed(8);$('fov').value=data.fov_arcmin;$('detector').value=data.detector;
  $('data-badge').textContent=target?'REAL DATA · CACHED':'REAL DATA · IRSA';
  $('processing').textContent=`${data.source}. ${data.processing} Retrieved ${date(data.created_at)}. ${data.frames.length} sampled from ${data.available_observations} available exposures. `;
  $('coordinate-note').textContent=data.target?.coordinate_note||'Fixed ICRS coordinates. Fast-moving sources can leave this field; increase the field of view.';
  $('notices').textContent=data.notices?.length?data.notices.join(' '):'No archive download errors recorded for this sequence.';
  $('reference').replaceChildren();
  data.frames.forEach((f,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${shortDate(f.date)} · ${f.wavelength_um?.toFixed(3)||'?'} µm`;$('reference').append(o);});
  $('reference').value=state.reference;
  document.querySelectorAll('.target').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===data.target?.id)));
  busy('',false);updateActive();
  const query={ra:data.ra,dec:data.dec,fov:data.fov_arcmin,detector:data.detector};
  if(target)query.target=target.id;
  history.replaceState(null,'',fieldURL(location.href,query));
}

function bestReference(frames){
  // Choose a bandpass center that keeps the widest time baseline within the 5% window.
  let best=0,score=-1;
  frames.forEach((f,i)=>{const matches=matchedFrames(frames,i,true);const times=matches.map(j=>frames[j].mjd);const s=(Math.max(...times)-Math.min(...times))*100+matches.length;if(s>score){score=s;best=i;}});
  return best;
}

async function loadTarget(target){
  const token=++state.token;stop();busy(`Opening ${target.name}…`);
  try{const data=await getJSON(`data/${target.id}.json`);if(token===state.token)loadData(data,target);}
  catch(error){if(token===state.token){busy('',false);status(error.message,true);}}
}

async function searchSky(query){
  const token=++state.token;stop();busy('Searching the IRSA archive…');status('Fetching real observations. This may take a few minutes.');
  try{
    const job=await getJSON('api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(query)});
    while(token===state.token){
      await new Promise(resolve=>setTimeout(resolve,1500));
      if(token!==state.token)return;
      const progress=await getJSON(`api/jobs/${encodeURIComponent(job.id)}`);
      if(token!==state.token)return;
      if(progress.status==='error')throw Error(progress.message);
      if(progress.status==='done'){loadData(progress.result);return;}
      $('loading-text').textContent=progress.message;status(progress.message);
    }
  }catch(error){if(token===state.token){busy('',false);status(error.message,true);}}
}

$('search-form').addEventListener('submit',event=>{
  event.preventDefault();
  try{
    const query={ra:parseCoordinate($('ra').value,true),dec:parseCoordinate($('dec').value),fov:+$('fov').value,detector:$('detector').value};
    searchSky(query);
  }catch(error){status(error.message,true);}
});
$('play').addEventListener('click',()=>{
  if(state.timer){stop();return;}if(state.active.length<2)return;
  $('play').textContent='Ⅱ';$('play').setAttribute('aria-label','Pause time sequence');
  state.timer=setInterval(()=>step(1),+$('speed').value);
});
$('speed').addEventListener('change',()=>{if(state.timer){stop();$('play').click();}});
$('prev').addEventListener('click',()=>{stop();step(-1);});$('next').addEventListener('click',()=>{stop();step(1);});
$('timeline').addEventListener('input',()=>{stop();state.index=+$('timeline').value;render();});
$('reference').addEventListener('change',()=>{state.reference=+$('reference').value;updateActive();});
$('match-wave').addEventListener('change',()=>{if(state.data)updateActive();});
for(const id of ['wipe','show-grid','invert'])$(id).addEventListener('input',render);
$('stretch').addEventListener('input',()=>{$('stretch-value').value=Number($('stretch').value).toFixed(1);if(state.data){buildFilmstrip();render();}});
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{
  state.mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render();
}));
document.addEventListener('keydown',event=>{
  if(/INPUT|SELECT|TEXTAREA|BUTTON/.test(event.target.tagName))return;
  if(event.code==='Space'){event.preventDefault();$('play').click();}
  else if(event.key==='ArrowRight'){event.preventDefault();stop();step(1);}
  else if(event.key==='ArrowLeft'){event.preventDefault();stop();step(-1);}
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
$('share').addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText(location.href);status('Field link copied. It includes coordinates, field of view and detector.');}
  catch{status(`Copy this address from your browser: ${location.href}`);}
});
function download(url,name){const a=document.createElement('a');a.href=url;a.download=name;a.click();}
$('save-image').addEventListener('click',()=>{if(!state.data)return;download(sky.toDataURL('image/png'),`spherex-${state.mode}-${shortDate(current().date)}.png`);});
$('export').addEventListener('click',()=>{
  if(!state.data)return;
  const metadata={...state.data,frames:state.data.frames.map(({pixels,...rest})=>rest)};
  const url=URL.createObjectURL(new Blob([JSON.stringify(metadata,null,2)],{type:'application/json'}));
  download(url,'spherex-observations.json');setTimeout(()=>URL.revokeObjectURL(url),1000);
});
window.addEventListener('resize',render);

async function init(){
  try{
    state.targets=await getJSON('data/targets.json');
    const icons=['✦','◉','✧','✺','✳'];
    state.targets.forEach((target,i)=>{
      const b=document.createElement('button');b.className='target';b.dataset.id=target.id;b.setAttribute('aria-pressed','false');
      const icon=document.createElement('span');icon.className='target-icon';icon.textContent=icons[i];icon.setAttribute('aria-hidden','true');
      const words=document.createElement('span'),name=document.createElement('strong'),kind=document.createElement('small');name.textContent=target.name;kind.textContent=target.kind;words.append(name,kind);
      const arrow=document.createElement('span');arrow.className='arrow';arrow.textContent='↗';b.append(icon,words,arrow);b.addEventListener('click',()=>loadTarget(target));$('targets').append(b);
    });
    const params=new URLSearchParams(location.search),named=state.targets.find(t=>t.id===params.get('target'));
    if(params.has('ra')&&params.has('dec')){
      const query={ra:parseCoordinate(params.get('ra'),true),dec:parseCoordinate(params.get('dec')),fov:Number(params.get('fov')||6),detector:params.get('detector')||'D3'};
      if(named&&Math.abs(named.ra-query.ra)<1e-6&&Math.abs(named.dec-query.dec)<1e-6&&named.fov===query.fov&&named.detector===query.detector)await loadTarget(named);
      else await searchSky(query);
    }else await loadTarget(named||state.targets[0]);
  }catch(error){busy('',false);status(error.message,true);}
}
init();

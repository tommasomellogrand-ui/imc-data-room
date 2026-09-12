/* ================================================================
   IMC | RESULTS IMPORT · CLEAN
   REPOSITORY: IMC Results
   ================================================================ */

(function(){
"use strict";

/* CONFIG */
const GATEWAY_URL="https://www.italianmastersclub.it/imc-universal-gateway/";
const RESULTS="IMC Results";

const GW_ROUTE={
 "GW001":"Sql1956795_3",
 "GW002":"Sql1956795_2",
 "GW003":"Sql1956795_2",
 "GW004":"Sql1956795_3",
 "GW005":"Sql1956795_3",
 "GW006":"Sql1956795_3",
 "GW007":"Sql1956795_2",
 "GW008":"Sql1956795_2",
 "GW009":"Sql1956795_3"
};

const GWS=Object.keys(GW_ROUTE);

const S={
 gw:null,
 shortcutReleased:false,
 stop:false,
 importedAt:null,
 phase:"PRONTO",

 scanned:0,
 fresh:0,
 skip:0,
 saved:0,
 errors:0,

 done:0,
 sections:0,

 existingIds:new Set(),
 existingFingerprints:new Set()
};

/* HELPERS */
const clean=v=>String(v==null?"":v)
 .replace(/\u00a0/g," ")
 .replace(/\s+/g," ")
 .trim();

const norm=v=>clean(v)
 .toLocaleLowerCase("it-IT")
 .normalize("NFD")
 .replace(/[\u0300-\u036f]/g,"")
 .replace(/[^a-z0-9]+/g," ")
 .trim();

const attr=(e,n)=>{
 try{return e?e.getAttribute(n):null}
 catch(_){return null}
};

const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function visible(e){
 try{
  if(!e||e.closest&&e.closest("#workingCopy"))return false;
  const s=getComputedStyle(e);
  const r=e.getBoundingClientRect();
  return s.display!=="none"&&
         s.visibility!=="hidden"&&
         Number(s.opacity)!==0&&
         r.width>0&&r.height>0;
 }catch(_){
  return false;
 }
}

async function waitFor(fn,ms=15000){
 const t=Date.now();

 while(Date.now()-t<ms){
  if(S.stop)throw Error("Importazione interrotta");

  try{
   const x=fn();
   if(x)return x;
  }catch(_){}

  await sleep(150);
 }

 return null;
}

function stamp(){
 const d=new Date();
 const z=n=>String(n).padStart(2,"0");

 return d.getFullYear()+"-"+
        z(d.getMonth()+1)+"-"+
        z(d.getDate())+" "+
        z(d.getHours())+":"+
        z(d.getMinutes())+":"+
        z(d.getSeconds());
}

function hash(a){
 const s=a.map(clean).join("|");
 let h=2166136261;

 for(let i=0;i<s.length;i++){
  h^=s.charCodeAt(i);
  h=Math.imul(h,16777619);
 }

 const x=(h>>>0).toString(16).padStart(8,"0");
 return(x+x+x+x+x+x+x+x).slice(0,64);
}

function destination(){
 const database=GW_ROUTE[S.gw];

 if(!database){
  throw Error("Routing non configurato per "+S.gw);
 }

 return{
  database,
  table:S.gw+"_IMC Results"
 };
}

/* UI */
function buildUI(){
 const old=document.getElementById("__imc_results_clean");
 if(old)old.remove();

 const root=document.createElement("div");
 root.id="__imc_results_clean";

 root.style.cssText=[
  "position:fixed",
  "inset:0",
  "z-index:2147483647",
  "background:rgba(15,23,42,.25)",
  "backdrop-filter:blur(5px)",
  "-webkit-backdrop-filter:blur(5px)",
  "padding:8px",
  "box-sizing:border-box",
  "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
  "color:#172033"
 ].join(";");

 root.innerHTML=`
 <div style="
  width:100%;
  max-width:430px;
  height:100%;
  margin:0 auto;
  background:#fff;
  border-radius:26px;
  border:1px solid #e5e7ef;
  box-shadow:0 24px 70px rgba(15,23,42,.20);
  overflow:auto
 ">
  <div style="
   position:sticky;
   top:0;
   z-index:3;
   padding:13px;
   background:rgba(255,255,255,.96);
   border-bottom:1px solid #eef1f5;
   backdrop-filter:blur(12px)
  ">
   <div style="
    font-size:8px;
    letter-spacing:1.7px;
    font-weight:950;
    color:#7357df
   ">ITALIAN MASTERS CLUB</div>

   <div style="
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-top:4px
   ">
    <strong style="
     font-size:20px;
     letter-spacing:-.4px
    ">Results Import</strong>

    <span id="badge" style="
     font-size:9px;
     font-weight:950;
     padding:7px 10px;
     border-radius:999px;
     background:#f1edff;
     color:#6847dc
    ">PRONTO</span>
   </div>
  </div>

  <div id="body" style="padding:10px"></div>
 </div>`;

 document.body.appendChild(root);
}

function worldUI(){
 document.getElementById("body").innerHTML=`
  <div style="
   padding:12px;
   border:1px solid #e6e8f0;
   border-radius:18px;
   background:#fafbff
  ">
   <div style="
    font-size:13px;
    font-weight:950;
    margin-bottom:10px
   ">SELEZIONA GAME WORLD</div>

   <div style="
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:7px
   ">
    ${GWS.map(g=>`
     <button
      class="gw"
      data-g="${g}"
      style="
       height:48px;
       border:1px solid #dedfed;
       border-radius:13px;
       background:#fff;
       font-size:12px;
       font-weight:950;
       color:#4e4191
      "
     >${g}</button>
    `).join("")}
   </div>
  </div>`;
}

function chooseGW(){
 return new Promise(resolve=>{
  document.querySelectorAll(".gw").forEach(b=>{
   b.onclick=()=>resolve(b.dataset.g);
  });
 });
}

function progressUI(){
 document.getElementById("body").innerHTML=`
 <div style="display:flex;flex-direction:column;gap:8px">

  <div style="
   display:grid;
   grid-template-columns:1fr 1fr;
   gap:7px
  ">
   ${infoCard("GAME WORLD","gw","#7357df")}
   ${infoCard("FASE","phase","#7357df")}
   ${infoCard("COUNTRY","country","#3b82c4")}
   ${infoCard("DIVISION","division","#5f63d8")}
   ${infoCard("AZIONE","action","#8356cb")}
   ${infoCard("DATA / TURNO","date","#b36b2c")}
  </div>

  <div style="
   display:grid;
   grid-template-columns:repeat(4,1fr);
   gap:5px
  ">
   ${counterCard("SCANSIONATI","scanned","#475569")}
   ${counterCard("NUOVI","fresh","#16845b")}
   ${counterCard("SKIP","skip","#b96f17")}
   ${counterCard("SALVATI","saved","#4f55d7")}
  </div>

  <div style="
   background:#f3fbf6;
   border:1px solid #d8ecdf;
   border-radius:16px;
   padding:10px 12px
  ">
   <div style="
    font-size:7px;
    letter-spacing:1.2px;
    font-weight:950;
    color:#4d8d61
   ">DESTINAZIONE MYSQL</div>

   <div id="dest" style="
    margin-top:5px;
    font-size:10px;
    font-weight:900;
    color:#315d3e;
    overflow-wrap:anywhere
   ">-</div>
  </div>

  <div style="
   background:#fff;
   border:1px solid #e7eaf0;
   border-radius:16px;
   padding:10px
  ">
   <div style="
    display:flex;
    justify-content:space-between;
    align-items:center
   ">
    <div style="
     font-size:8px;
     letter-spacing:1.2px;
     font-weight:950;
     color:#7357df
    ">LOG LIVE</div>

    <div id="errors" style="
     font-size:7px;
     font-weight:950;
     color:#bf4444
    ">ERRORI 0</div>
   </div>

   <div id="log" style="
    height:240px;
    overflow:auto;
    margin-top:8px;
    background:#f7f8fa;
    border-radius:12px;
    padding:7px;
    font:8.5px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace
   "></div>
  </div>

  <div style="
   display:grid;
   grid-template-columns:1fr 1fr;
   gap:6px
  ">
   <button id="stop" style="
    height:46px;
    border:1px solid #efc7c7;
    border-radius:14px;
    background:#fff2f2;
    color:#b74444;
    font-size:11px;
    font-weight:950
   ">STOP</button>

   <button id="close" style="
    display:none;
    height:46px;
    border:1px solid #dfe2e8;
    border-radius:14px;
    background:#fff;
    color:#303443;
    font-size:11px;
    font-weight:950
   ">CHIUDI</button>
  </div>

 </div>`;

 document.getElementById("stop").onclick=()=>{
  S.stop=true;
  setPhase("ARRESTO");
  setBadge("ARRESTO...");
  log("STOP richiesto","error");
 };

 document.getElementById("close").onclick=()=>{
  document.getElementById("__imc_results_clean")?.remove();
 };

 updateUI();
}

function infoCard(label,id,color){
 return`
 <div style="
  background:#fff;
  border:1px solid #e7eaf0;
  border-radius:15px;
  padding:9px 10px;
  min-width:0
 ">
  <div style="
   font-size:6.8px;
   letter-spacing:1px;
   font-weight:950;
   color:${color}
  ">${label}</div>

  <div id="${id}" style="
   margin-top:5px;
   font-size:11px;
   font-weight:950;
   overflow-wrap:anywhere
  ">-</div>
 </div>`;
}

function counterCard(label,id,color){
 return`
 <div style="
  background:#fff;
  border:1px solid #e7eaf0;
  border-radius:15px;
  padding:9px 5px;
  text-align:center
 ">
  <div style="
   font-size:6.5px;
   letter-spacing:.8px;
   font-weight:950;
   color:${color}
  ">${label}</div>

  <div id="${id}" style="
   margin-top:5px;
   font-size:20px;
   font-weight:950
  ">0</div>
 </div>`;
}

function setBadge(x){
 const e=document.getElementById("badge");
 if(e)e.textContent=x;
}

function setPhase(x){
 S.phase=x;
 updateUI();
}

function setText(id,value){
 const e=document.getElementById(id);
 if(e)e.textContent=value;
}

function log(text,type="info"){
 const e=document.getElementById("log");
 if(!e)return;

 const row=document.createElement("div");

 let color="#394052";
 let bg="transparent";

 if(type==="new"){
  color="#16784f";
  bg="#edf9f3";
 }else if(type==="skip"){
  color="#ad6815";
  bg="#fff6e8";
 }else if(type==="error"){
  color="#b54040";
  bg="#fff0f0";
 }

 row.style.cssText=
  "padding:4px 6px;"+
  "margin:2px 0;"+
  "border-radius:8px;"+
  "font-weight:850;"+
  "color:"+color+";"+
  "background:"+bg;

 row.textContent="• "+clean(text);

 e.appendChild(row);
 e.scrollTop=e.scrollHeight;
}

function updateUI(){
 if(!S.gw)return;

 const c=context();
 const d=dateInfo();
 const dest=destination();

 setText("gw",S.gw);
 setText("phase",S.phase);
 setText("country",c.sm_country||"—");
 setText("division",c.sm_division||"—");
 setText("action",c.sm_action||"—");

 setText(
  "date",
  [
   d.match_date,
   d.competition_stage,
   d.competition_round
  ].filter(Boolean).join(" · ")||"—"
 );

 setText("scanned",String(S.scanned));
 setText("fresh",String(S.fresh));
 setText("skip",String(S.skip));
 setText("saved",String(S.saved));

 setText(
  "dest",
  dest.database+" · "+dest.table
 );

 setText(
  "errors",
  "ERRORI "+S.errors
 );
}

function finish(status){
 setBadge(status);
 setPhase(status);

 const stop=document.getElementById("stop");
 const close=document.getElementById("close");

 if(stop)stop.style.display="none";
 if(close)close.style.display="block";
}

/* GATEWAY */
async function gateway(body){
 const response=await fetch(GATEWAY_URL,{
  method:"POST",
  headers:{
   "Content-Type":"application/json",
   "Accept":"application/json",
   "X-IMC-Channel":"IMPORT"
  },
  body:JSON.stringify({
   ...body,
   channel:"IMPORT"
  })
 });

 const raw=await response.text();

 let json=null;
 try{
  json=raw?JSON.parse(raw):{};
 }catch(_){}

 if(!response.ok||!json||json.ok===false){
  const detail=
   (json&&(json.message||json.error))||
   raw||
   ("HTTP "+response.status);

  throw Error(
   "Gateway "+response.status+" · "+detail
  );
 }

 return json;
}

/* PRELOAD DUPLICATI */
async function preloadExisting(){
 setPhase("LETTURA DB");

 const dest=destination();
 let offset=0;
 const limit=5000;

 S.existingIds.clear();
 S.existingFingerprints.clear();

 while(true){
  const json=await gateway({
   action:"read",
   game_world_id:S.gw,
   repository:RESULTS,
   target_database:dest.database,
   target_table:dest.table,
   route_mode:"explicit",
   limit,
   offset
  });

  const rows=Array.isArray(json.rows)?json.rows:[];

  rows.forEach(r=>{
   const id=Number(r.sm_fixture_id);

   if(Number.isFinite(id)){
    S.existingIds.add(id);
   }

   if(clean(r.fingerprint)){
    S.existingFingerprints.add(
     clean(r.fingerprint)
    );
   }
  });

  if(!json.has_more)break;

  const next=Number(json.next_offset);

  if(!Number.isFinite(next)||next<=offset){
   throw Error("Paginazione READ non valida");
  }

  offset=next;
 }

 log(
  "DB caricato · "+
  S.existingIds.size+
  " fixture già presenti"
 );
}

function splitExisting(rows){
 const fresh=[];
 const skipped=[];

 rows.forEach(r=>{
  const id=Number(r.sm_fixture_id);

  const existsById=
   Number.isFinite(id)&&
   S.existingIds.has(id);

  const existsByFingerprint=
   clean(r.fingerprint)&&
   S.existingFingerprints.has(
    clean(r.fingerprint)
   );

  if(existsById||existsByFingerprint){
   skipped.push(r);
  }else{
   fresh.push(r);
  }
 });

 return{fresh,skipped};
}

async function insertRows(rows){
 if(!rows.length)return 0;

 const dest=destination();

 const json=await gateway({
  action:"insert_many",
  game_world_id:S.gw,
  repository:RESULTS,
  target_database:dest.database,
  target_table:dest.table,
  route_mode:"explicit",
  rows,
  atomic:true
 });

 const written=Number(json.written_rows);

 if(!Number.isFinite(written)){
  throw Error(
   "written_rows non dichiarato dal Gateway"
  );
 }

 rows.forEach(r=>{
  const id=Number(r.sm_fixture_id);

  if(Number.isFinite(id)){
   S.existingIds.add(id);
  }

  if(clean(r.fingerprint)){
   S.existingFingerprints.add(
    clean(r.fingerprint)
   );
  }
 });

 S.saved+=written;

 return written;
}

/* CONTEXT */
function macro(a){
 a=norm(a);

 if([
  "league",
  "leaguecup",
  "leagueshield",
  "charityshield",
  "playoff"
 ].includes(a))return"DOMESTIC";

 if([
  "smfacup",
  "smfashield",
  "supercup"
 ].includes(a))return"INTERNATIONAL";

 if([
  "interqualifier",
  "worldcup"
 ].includes(a))return"NATIONS";

 return null;
}

function divisionSelect(){
 return[
  ...document.querySelectorAll("select")
 ].find(s=>
  visible(s)&&
  [...s.options].some(o=>
   /^division(?:e)?\s+\d+$/i.test(
    clean(o.textContent)
   )
  )
 )||null;
}

function countrySelect(){
 const s=document.querySelector(
  "#country-selector select"
 );

 return s&&visible(s)?s:null;
}

function pagerContext(){
 const root=
  document.getElementById(
   "leagueResultsContainer"
  )||document;

 const e=root.querySelector(
  "#ResultsprevWeek_click a[action],"+
  "#ResultsnextWeek_click a[action],"+
  "#ResultssnextWeek_click a[action]"
 );

 return e?{
  sm_action:norm(attr(e,"action")),
  sm_country:clean(
   attr(e,"data-country")
  )||null,
  sm_division:clean(
   attr(e,"data-division")
  )||null
 }:{};
}

function context(){
 const p=pagerContext();
 const ds=divisionSelect();
 const cs=countrySelect();

 let action=p.sm_action||null;
 let country=p.sm_country||null;
 let division=p.sm_division||null;

 if(!action){
  const e=[
   ...document.querySelectorAll(
    "[action],[data-action]"
   )
  ].find(x=>[
   "league",
   "leaguecup",
   "leagueshield",
   "charityshield",
   "smfacup",
   "smfashield",
   "supercup",
   "interqualifier",
   "worldcup"
  ].includes(
   norm(
    attr(x,"action")||
    attr(x,"data-action")
   )
  ));

  if(e){
   action=clean(
    attr(e,"action")||
    attr(e,"data-action")
   );
  }
 }

 if(!country&&cs){
  country=
   clean(
    cs.options[cs.selectedIndex]?.textContent
   )||
   clean(cs.value)||
   null;
 }

 if(!division&&ds){
  division=
   clean(
    ds.options[ds.selectedIndex]?.textContent
   )||
   clean(ds.value)||
   null;
 }

 const group=macro(action);

 if(
  group==="INTERNATIONAL"||
  group==="NATIONS"
 ){
  country=null;
  division=null;
 }

 let groupName=null;

 [
  ...document.querySelectorAll(
   ".groupHeader,"+
   ".sectionheading,"+
   ".scheduleScreen-Heading,"+
   "h2,h3"
  )
 ].forEach(e=>{
  const t=clean(e.textContent);

  if(
   !groupName&&
   visible(e)&&
   /^(girone|group)\b/i.test(t)
  ){
   groupName=t;
  }
 });

 return{
  sm_action:action,
  sm_country:country,
  sm_division:division,
  competition_group:group,
  competition_group_name:groupName
 };
}

function competitionKey(c){
 return[
  S.gw,
  c.sm_country,
  c.competition_group,
  c.sm_action,
  c.sm_division
 ]
 .filter(x=>clean(x))
 .map(clean)
 .join("|");
}

/* RESULT PARSER */
const MONTH={
 gennaio:1,
 febbraio:2,
 marzo:3,
 aprile:4,
 maggio:5,
 giugno:6,
 luglio:7,
 agosto:8,
 settembre:9,
 ottobre:10,
 novembre:11,
 dicembre:12
};

function dateInfo(){
 const root=
  document.getElementById(
   "leagueResultsContainer"
  )||document;

 const h=[
  ...root.querySelectorAll(
   ".scheduleScreen-Heading"
  )
 ].find(visible);

 if(!h){
  return{
   match_date:null,
   competition_stage:null,
   competition_round:null
  };
 }

 const text=clean(h.textContent);

 const m=text.toLowerCase().match(
  /(?:lun|mar|mer|gio|ven|sab|dom)?\s*(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})/
 );

 if(!m){
  return{
   match_date:null,
   competition_stage:null,
   competition_round:null
  };
 }

 const date=
  m[3]+"-"+
  String(MONTH[m[2]]).padStart(2,"0")+"-"+
  String(Number(m[1])).padStart(2,"0");

 const prefix=clean(
  text.slice(
   0,
   text.toLowerCase().indexOf(m[0])
  ).replace(/[:·\-]\s*$/,"")
 );

 let stage=null;
 let round=null;

 if(prefix){
  const leg=prefix.match(
   /^(.*?)(?:\s+|[-·])\b(Andata|Ritorno)\b$/i
  );

  if(leg){
   stage=clean(leg[1])||null;
   round=clean(leg[2])||null;
  }else if(
   /finale|semifinale|quarti|ottavi|sedicesimi|qualificazion|finals|finali/i.test(prefix)
  ){
   stage=prefix;
  }else{
   round=prefix;
  }
 }

 return{
  match_date:date,
  competition_stage:stage,
  competition_round:round
 };
}

function resultButtons(){
 const root=
  document.getElementById(
   "leagueResultsContainer"
  )||document;

 const seen=new Set();

 return[
  ...root.querySelectorAll(
   '[id="matchResult"]'
  )
 ].filter(b=>{
  if(!visible(b))return false;

  const m=(
   attr(b,"onclick")||""
  ).match(
   /MATCHREPORT_[A-Za-z0-9_]*\s*\(\s*['"]?(\d+)/i
  );

  if(!m||seen.has(m[1])){
   return false;
  }

  seen.add(m[1]);
  return true;
 });
}

function fixtureId(button){
 const m=(
  attr(button,"onclick")||""
 ).match(
  /MATCHREPORT_[A-Za-z0-9_]*\s*\(\s*['"]?(\d+)/i
 );

 return m?Number(m[1]):null;
}

function team(row,side){
 const e=row.querySelector(
  '[id="'+(
   side==="home"
    ?"homeTeam"
    :"awayTeam"
  )+'"]'
 );

 const m=e&&(
  attr(e,"onclick")||""
 ).match(
  /MENU_clubOverviewDraw\s*\(\s*['"]?(\d+)/i
 );

 return{
  name:e?clean(e.textContent)||null:null,
  id:m?Number(m[1]):null
 };
}

function managerId(row,side){
 const e=row.querySelector(
  '[id="'+(
   side==="home"
    ?"homeManagerImage"
    :"awayManagerImage"
  )+'"]'
 );

 const m=e&&(
  attr(e,"onclick")||""
 ).match(
  /PROFILE_viewFriendsProfileNew\s*\(\s*['"]?(\d+)/i
 );

 return m?Number(m[1]):null;
}

function decision(row,homeName,awayName){
 const textParts=[];
 let next=row.nextElementSibling;

 while(next){
  if(
   next.querySelector&&
   next.querySelector(
    '[id="matchResult"]'
   )
  ){
   break;
  }

  const t=clean(next.textContent);

  if(t){
   textParts.push(t);
  }

  next=next.nextElementSibling;
 }

 const text=clean(textParts.join(" "));

 const out={
  penalty_home_score:null,
  penalty_away_score:null,
  aggregate_home_score:null,
  aggregate_away_score:null
 };

 let m=text.match(
  /La squadra\s+(.+?)\s+vince ai rigori con il punteggio di\s+(\d+)\s*[-–]\s*(\d+)/i
 );

 if(m){
  const winner=clean(m[1]);
  const a=Number(m[2]);
  const b=Number(m[3]);

  if(norm(winner)===norm(homeName)){
   out.penalty_home_score=a;
   out.penalty_away_score=b;
  }else if(norm(winner)===norm(awayName)){
   out.penalty_home_score=b;
   out.penalty_away_score=a;
  }
 }

 m=text.match(
  /La squadra\s+(.+?)\s+vince con il punteggio aggregato di\s+(\d+)\s*[-–]\s*(\d+)/i
 );

 if(m){
  const winner=clean(m[1]);
  const a=Number(m[2]);
  const b=Number(m[3]);

  if(norm(winner)===norm(homeName)){
   out.aggregate_home_score=a;
   out.aggregate_away_score=b;
  }else if(norm(winner)===norm(awayName)){
   out.aggregate_home_score=b;
   out.aggregate_away_score=a;
  }
 }

 return out;
}

function resultRows(){
 const c=context();
 const key=competitionKey(c);
 const d=dateInfo();

 return resultButtons().map(button=>{
  const row=
   button.closest("tr")||
   button.parentElement;

  const home=team(row,"home");
  const away=team(row,"away");

  const score=
   clean(button.textContent).match(
    /(\d+)\s*[-–]\s*(\d+)/
   );

  const extra=decision(
   row,
   home.name,
   away.name
  );

  const result={
   game_world_id:S.gw,
   sm_fixture_id:fixtureId(button),
   competition_key:key,

   sm_action:c.sm_action||null,
   sm_country:c.sm_country||null,
   sm_division:c.sm_division||null,

   competition_group:
    c.competition_group||null,

   competition_group_name:
    c.competition_group_name||null,

   competition_stage:
    d.competition_stage,

   competition_round:
    d.competition_round,

   match_date:
    d.match_date,

   home_sm_club_id:
    home.id,

   home_name:
    home.name,

   away_sm_club_id:
    away.id,

   away_name:
    away.name,

   home_sm_manager_id:
    managerId(row,"home"),

   away_sm_manager_id:
    managerId(row,"away"),

   home_score:
    score?Number(score[1]):null,

   away_score:
    score?Number(score[2]):null,

   penalty_home_score:
    extra.penalty_home_score,

   penalty_away_score:
    extra.penalty_away_score,

   aggregate_home_score:
    extra.aggregate_home_score,

   aggregate_away_score:
    extra.aggregate_away_score,

   result_status:
    score?"COMPLETED":null,

   fingerprint:null,

   imported_at:
    S.importedAt
  };

  result.fingerprint=hash([
   result.game_world_id,
   result.sm_fixture_id,
   result.competition_key,
   result.sm_action,
   result.sm_country,
   result.sm_division,
   result.competition_group,
   result.competition_group_name,
   result.competition_stage,
   result.competition_round,
   result.match_date,
   result.home_sm_club_id,
   result.home_name,
   result.away_sm_club_id,
   result.away_name,
   result.home_sm_manager_id,
   result.away_sm_manager_id,
   result.home_score,
   result.away_score,
   result.penalty_home_score,
   result.penalty_away_score,
   result.aggregate_home_score,
   result.aggregate_away_score,
   result.result_status
  ]);

  return result;
 });
}

/* NAVIGATION */
function clickReal(e){
 if(!e)return;

 const token=
  "imc_click_"+
  Date.now()+"_"+
  Math.random().toString(36).slice(2);

 e.setAttribute(
  "data-imc-click-token",
  token
 );

 document.documentElement.removeAttribute(
  "data-imc-click-error"
 );

 const script=document.createElement("script");

 script.textContent=
  "(function(){"+
   "var el=document.querySelector('[data-imc-click-token=\\\""+
   token+
   "\\\"]');"+
   "if(!el)return;"+
   "try{"+
    "if(typeof el.onclick==='function'){"+
     "el.onclick.call(el);"+
    "}else{"+
     "var raw=el.getAttribute('onclick')||'';"+
     "if(raw){(new Function(raw)).call(el);}"+
     "else{el.click();}"+
    "}"+
   "}catch(e){"+
    "document.documentElement.setAttribute("+
     "'data-imc-click-error',"+
     "String(e&&e.message||e)"+
    ");"+
   "}"+
  "})();";

 (
  document.documentElement||
  document.head||
  document.body
 ).appendChild(script);

 script.remove();

 e.removeAttribute(
  "data-imc-click-token"
 );

 const err=
  document.documentElement.getAttribute(
   "data-imc-click-error"
  );

 document.documentElement.removeAttribute(
  "data-imc-click-error"
 );

 if(err){
  throw Error(err);
 }
}

function pageIds(){
 return resultButtons()
  .map(fixtureId)
  .filter(v=>v!=null);
}

function prevButton(){
 const root=
  document.getElementById(
   "ResultsprevWeek_click"
  );

 if(root&&visible(root)){
  const e=
   root.querySelector("a,button")||
   root;

  if(visible(e)){
   return e;
  }
 }

 return[
  ...document.querySelectorAll(
   "a,button"
  )
 ].find(e=>
  visible(e)&&
  norm(e.textContent)==="precedenti"&&
  !/noclick|disabled/i.test(
   (e.id||"")+" "+
   ((e.closest("li")||{}).id||"")
  )
 )||null;
}

async function goPrevious(ids){
 const before=
  ids.slice().sort().join("|");

 for(let attempt=0;attempt<3;attempt++){
  const button=prevButton();

  if(!button){
   return false;
  }

  clickReal(button);

  const changed=await waitFor(()=>{
   const now=pageIds();

   return(
    now.length&&
    now.slice().sort().join("|")!==before
   )
    ?now
    :null;
  },22000);

  if(changed){
   await sleep(650);
   return true;
  }

  await sleep(700);
 }

 throw Error(
  "Precedenti disponibile ma turno non cambiato"
 );
}

function plan(kind){
 const select=
  kind==="country"
   ?countrySelect()
   :divisionSelect();

 if(!select){
  return null;
 }

 const options=[
  ...select.options
 ].map((o,i)=>({
  value:String(o.value||""),
  text:clean(o.textContent),
  index:i,
  disabled:o.disabled
 }))
 .filter(o=>
  !o.disabled&&
  (
   kind==="division"
    ?/^division(?:e)?\s+\d+$/i.test(o.text)
    :o.value&&o.text
  )
 );

 if(!options.length){
  return null;
 }

 let pos=options.findIndex(
  o=>o.index===select.selectedIndex
 );

 if(pos<0){
  pos=0;
 }

 return options
  .slice(pos)
  .concat(
   options.slice(0,pos)
  );
}

async function switchTo(kind,target){
 const select=
  kind==="country"
   ?countrySelect()
   :divisionSelect();

 if(!select){
  throw Error(
   "Menu "+kind+" non trovato"
  );
 }

 const idx=[
  ...select.options
 ].findIndex(o=>
  String(o.value)===
  String(target.value)
 );

 if(idx<0){
  return false;
 }

 select.selectedIndex=idx;
 select.value=select.options[idx].value;

 if(typeof select.onchange==="function"){
  select.onchange.call(
   select,
   new Event(
    "change",
    {bubbles:true}
   )
  );
 }else{
  select.dispatchEvent(
   new Event(
    "change",
    {bubbles:true}
   )
  );
 }

 await sleep(1000);

 const tab=
  document.getElementById(
   "resultsTableTab"
  );

 if(tab){
  clickReal(tab);
 }

 await waitFor(
  ()=>resultButtons().length||
      document.getElementById(
       "leagueResultsContainer"
      ),
  15000
 );

 await sleep(500);

 return true;
}

/* PROCESS */
async function processPage(){
 setPhase("LETTURA RESULTS");

 const rows=resultRows();
 const split=splitExisting(rows);

 S.scanned+=rows.length;
 S.fresh+=split.fresh.length;
 S.skip+=split.skipped.length;

 updateUI();

 const c=context();
 const d=dateInfo();

 if(split.skipped.length){
  log(
   "SKIP "+split.skipped.length+
   " · "+
   (c.sm_country||"-")+
   " · "+
   (c.sm_division||"-")+
   " · "+
   (d.match_date||"-"),
   "skip"
  );
 }

 if(split.fresh.length){
  setPhase("SALVATAGGIO");

  const written=
   await insertRows(
    split.fresh
   );

  log(
   "NUOVI "+split.fresh.length+
   " · SALVATI "+written+
   " · "+
   (c.sm_country||"-")+
   " · "+
   (c.sm_division||"-")+
   " · "+
   (d.match_date||"-"),
   "new"
  );
 }else if(rows.length){
  log(
   "Pagina già importata · "+
   (c.sm_country||"-")+
   " · "+
   (c.sm_division||"-")+
   " · "+
   (d.match_date||"-"),
   "skip"
  );
 }

 updateUI();

 return pageIds();
}


async function processSection(){
 setPhase("SCANSIONE");

 let ids=await processPage();

 while(ids.length){
  setPhase("PRECEDENTI");

  const moved=
   await goPrevious(ids);

  if(!moved){
   break;
  }

  ids=await processPage();
 }

 S.done++;
 updateUI();
}


async function run(){
 const countries=plan("country");

 if(countries){
  for(let i=0;i<countries.length;i++){
   if(S.stop){
    throw Error(
     "Importazione interrotta"
    );
   }

   if(i){
    setPhase("CAMBIO COUNTRY");

    await switchTo(
     "country",
     countries[i]
    );
   }

   const divisions=plan("division");

   if(divisions){
    for(let j=0;j<divisions.length;j++){
     if(S.stop){
      throw Error(
       "Importazione interrotta"
      );
     }

     if(j){
      setPhase("CAMBIO DIVISION");

      await switchTo(
       "division",
       divisions[j]
      );
     }

     await processSection();
    }
   }else{
    await processSection();
   }
  }

 }else{
  const divisions=plan("division");

  if(divisions){
   for(let i=0;i<divisions.length;i++){
    if(S.stop){
     throw Error(
      "Importazione interrotta"
     );
    }

    if(i){
     setPhase("CAMBIO DIVISION");

     await switchTo(
      "division",
      divisions[i]
     );
    }

    await processSection();
   }
  }else{
   await processSection();
  }
 }
}


/* SHORTCUT */
function completeShortcutImmediately(){
 if(S.shortcutReleased)return;

 try{
  completion(JSON.stringify({
   ok:true,
   started:true,
   importer:"IMC Results"
  }));
 }catch(_){}

 S.shortcutReleased=true;
}

/* MAIN */
async function main(){
 try{
  if(
   !resultButtons().length&&
   !document.getElementById(
    "resultsTableTab"
   )
  ){
   throw Error(
    "Apri una pagina RISULTATI valida di Soccer Manager"
   );
  }

  S.importedAt=stamp();
  S.gw=await chooseGW();

  progressUI();

  setBadge("IN CORSO");
  setPhase("AVVIO");

  const dest=destination();

  log(
   "START "+S.gw+
   " · "+
   dest.database+
   " · "+
   dest.table
  );

  await preloadExisting();
  await run();

  if(S.stop){
   finish("FERMATO");
   return;
  }

  finish("COMPLETATO");

  log(
   "COMPLETATO · scansionati "+
   S.scanned+
   " · nuovi "+
   S.fresh+
   " · skip "+
   S.skip+
   " · salvati "+
   S.saved,
   "new"
  );

 }catch(error){
  S.errors++;
  updateUI();

  log(
   error.message||String(error),
   "error"
  );

  finish(
   S.stop
    ?"FERMATO"
    :"ERRORE"
  );
 }
}

buildUI();
worldUI();
completeShortcutImmediately();

setTimeout(
 ()=>main(),
 0
);

})();

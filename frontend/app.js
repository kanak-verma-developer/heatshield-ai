// Backend location: same origin when served by the backend (http://host:8000/),
// http://localhost:8000 when this file is opened directly (file://),
// or override with ?api=https://your-host in the URL.
const API_BASE = (()=>{
  const q = new URLSearchParams(location.search).get('api');
  if(q) return q.replace(/\/+$/, '');
  return location.protocol === 'file:' ? 'http://localhost:8000' : location.origin;
})();
const WS_URL = API_BASE.replace(/^http/, 'ws') + '/ws/live';

function esc(s){
  return String(s ?? '').replace(/[&<>"']/g, c=>({
    '&':'&amp;',
    '<':'&lt;',
    '>':'&gt;',
    '"':'&quot;',
    "'":'&#39;'
  }[c]));
}

let modelAlgorithm = '—';

// ---------------------------------------------------------------------------
// DATA QUALITY
// ---------------------------------------------------------------------------
const LEVEL_TEXT = {
  OK:'Working',
  DEMO:'Demo',
  ESTIMATE:'Estimate',
  WARN:'Check',
  ERROR:'Error',
  MISSING:'Not connected',
  INFO:'Info'
};

function badge(level, text, title){
  return `<span class="badge lvl-${esc(level)}" title="${esc(title||'')}">${esc(text || LEVEL_TEXT[level] || level)}</span>`;
}

let statusById = {};
let statusLoadedAt = 0;

function setBadge(id, html){
  const el = document.getElementById(id);
  if(el) el.innerHTML = html;
}

async function loadStatus(){
  try{
    const r = await fetch(`${API_BASE}/api/status`);
    if(!r.ok) throw new Error('HTTP '+r.status);

    const d = await r.json();

    statusById = {};
    d.components.forEach(c=>statusById[c.id]=c);
    statusLoadedAt = Date.now();

    document.getElementById('statusList').innerHTML =
      d.components.map(c=>`
        <div class="status-row">
          <div class="sl">
            ${esc(c.label)} ${badge(c.level)}
          </div>
          <div class="sm">${esc(c.message)}</div>
        </div>
      `).join('');

    const ov = {
      OK:'ALL REAL',
      DEMO:'DEMO / SYNTHETIC',
      WARN:'NEEDS CHECK',
      ERROR:'ERROR'
    }[d.overall] || d.overall;

    setBadge(
      'overallChip',
      badge(
        d.overall,
        ov,
        'Worst status across all components - see the status panel'
      )
    );

    const CH = [
      ['weather','🌤️ Weather'],
      ['zone_priors','🗺️ Zone data'],
      ['model','🧠 Prediction model'],
      ['recommendations','💡 Advice'],
      ['history','📊 History']
    ];

    document.getElementById('statusChips').innerHTML =
      CH.map(([id,t])=>{
        const c=lv(id);
        return `
          <div class="chip" title="${esc(c.message||'')}">
            <span>${t}</span>
            ${badge(c.level||'INFO')}
          </div>
        `;
      }).join('');

    renderInlineBadges();

  }catch(e){

    document.getElementById('statusChips').innerHTML =
      '<span class="warnline">Status unavailable</span>';

    document.getElementById('statusList').innerHTML =
      `<div class="warnline">
        ⚠ Could not load status from backend (${esc(e.message)}).
      </div>`;

    setBadge(
      'overallChip',
      badge('ERROR','STATUS UNAVAILABLE')
    );
  }
}

function loadError(what, e){
  return (e instanceof TypeError)
    ? `<div class="warnline">
        ⚠ Can't reach the server, so ${what} can't load.
        Start it with <code>uvicorn backend.main:app --port 8000</code>.
      </div>`
    : `<div class="warnline">
        ⚠ The server returned an error while loading ${what}
        (${esc(e.message)}). Check the uvicorn terminal.
      </div>`;
}

function lv(id){
  return (statusById[id] || {});
}

function renderInlineBadges(){

  const w = lv('weather');
  const p = lv('zone_priors');
  const m = lv('model');
  const rc = lv('recommendations');

  if(w.level){
    setBadge(
      'badgeMap',
      badge(
        w.level,
        w.level==='OK'
          ? 'Live weather'
          : 'Weather: '+LEVEL_TEXT[w.level],
        w.message
      )
    );
  }

  if(p.level){
    setBadge(
      'badgeZone',
      badge(
        'ESTIMATE',
        'Estimated land values',
        p.message
      )
    );
  }

  setBadge('badgeTrend', '');
  setBadge('badgeHotspots', '');

  if(rc.level){
    setBadge(
      'badgeRecs',
      badge(
        rc.level,
        rc.level==='OK' ? 'AI written' : 'Rule based',
        rc.message
      )
    );
  }

  if(m.level){
    setBadge(
      'badgeModel',
      badge(
        m.level,
        m.level==='DEMO'
          ? 'Trained on demo data'
          : LEVEL_TEXT[m.level],
        m.message
      )
    );
  }
}

setInterval(()=>{
  if(usingBackend) loadStatus();
}, 30000);

// ---------------------------------------------------------------------------
// STALE DATA WATCHDOG
// ---------------------------------------------------------------------------
let lastMsgAt = 0;

setInterval(()=>{

  const el = document.getElementById('staleBadge');
  if(!el) return;

  const age = (Date.now() - lastMsgAt) / 1000;

  el.innerHTML =
    (usingBackend && lastMsgAt && age > 10)
      ? badge(
          'WARN',
          `Delayed ${Math.round(age)}s`,
          'No update received from the backend recently'
        )
      : '';

}, 2000);

// ---------------------------------------------------------------------------
// RISK
// ---------------------------------------------------------------------------
const RISK_COLORS = [
  [25, '#22c55e'],
  [50, '#eab308'],
  [70, '#f97316'],
  [85, '#ef4444'],
  [101, '#7f1d1d']
];

function riskColor(score){
  for(const [max,c] of RISK_COLORS){
    if(score<=max) return c;
  }
  return '#7f1d1d';
}

function riskCategory(score){

  if(score>=86)
    return {label:'Extreme', cls:'extreme'};

  if(score>=71)
    return {label:'Very High', cls:'vhigh'};

  if(score>=51)
    return {label:'High', cls:'high'};

  if(score>=26)
    return {label:'Moderate', cls:'mod'};

  return {label:'Low', cls:'low'};
}

// ---------------------------------------------------------------------------
// MORADABAD ZONE COORDINATES
// ---------------------------------------------------------------------------
const ZONES_META = [

  {
    id:'civil_lines',
    name:'Civil Lines',
    lat:28.8418,
    lon:78.7748
  },

  {
    id:'katghar',
    name:'Katghar',
    lat:28.8558,
    lon:78.7981
  },

  {
    id:'majhola',
    name:'Majhola',
    lat:28.8632,
    lon:78.7801
  },

  {
    id:'pakwara',
    name:'Pakwara',
    lat:28.8291,
    lon:78.7423
  },

  {
    id:'asalatpura',
    name:'Asalatpura',
    lat:28.8355,
    lon:78.7602
  },

  {
    id:'galshaheed',
    name:'Galshaheed',
    lat:28.8386,
    lon:78.7789
  },

  {
    id:'budh_bazaar',
    name:'Budh Bazaar',
    lat:28.8365,
    lon:78.7841
  },

  {
    id:'moradabad_central',
    name:'Moradabad Central',
    lat:28.8386,
    lon:78.7733
  },

  {
    id:'rampur_road',
    name:'Rampur Road',
    lat:28.8477,
    lon:78.8102
  },

  {
    id:'delhi_road',
    name:'Delhi Road',
    lat:28.8203,
    lon:78.7562
  },

  {
    id:'new_moradabad',
    name:'New Moradabad',
    lat:28.8156,
    lon:78.7891
  }
];

// ---------------------------------------------------------------------------
// BUILT-IN MAP PROJECTION
// ---------------------------------------------------------------------------
// This map does NOT use external map tiles.
// Coordinates are projected from the real zone latitude/longitude values.
// The visualization is a zone heat map, not an official ward-boundary map.
// ---------------------------------------------------------------------------
const MAP_W = 700;
const MAP_H = 520;
const GRID_COLS = 56;
const GRID_ROWS = 42;

const PAD = 0.01;

const LAT_MIN =
  Math.min(...ZONES_META.map(z=>z.lat)) - PAD;

const LAT_MAX =
  Math.max(...ZONES_META.map(z=>z.lat)) + PAD;

const LON_MIN =
  Math.min(...ZONES_META.map(z=>z.lon)) - PAD;

const LON_MAX =
  Math.max(...ZONES_META.map(z=>z.lon)) + PAD;

function project(lat, lon){

  return {
    x:
      (lon - LON_MIN) /
      (LON_MAX - LON_MIN) *
      MAP_W,

    y:
      (LAT_MAX - lat) /
      (LAT_MAX - LAT_MIN) *
      MAP_H
  };

}

const ZONE_POINTS = {};

ZONES_META.forEach(z=>{
  ZONE_POINTS[z.id] =
    project(z.lat,z.lon);
});

function nearestZoneId(x,y){

  let best = null;
  let bestD = Infinity;

  for(const id in ZONE_POINTS){

    const p = ZONE_POINTS[id];

    const d =
      (p.x-x)*(p.x-x) +
      (p.y-y)*(p.y-y);

    if(d < bestD){
      bestD = d;
      best = id;
    }
  }

  return best;
}

// ---------------------------------------------------------------------------
// MAP STATE
// ---------------------------------------------------------------------------
let latestZones = {};
let selectedZone = null;

let trendChart;
let donutChart;

let zoneCellMap = {};

let mapBuilt = false;

// ---------------------------------------------------------------------------
// MAP
// ---------------------------------------------------------------------------
// IMPORTANT:
// OpenStreetMap public tile loading has intentionally been removed.
//
// Previously this project used:
//
// L.tileLayer('https://{s}.tile.openstreetmap.org/...')
//
// That caused the OSM tile-policy blocking screen.
//
// The dashboard now uses its own SVG heat visualization with local
// map-base.jpg background. No external tile server is required.
// ---------------------------------------------------------------------------

let leafletMap = null;
let leafletMarkers = {};
let useLeaflet = false;

// Leaflet is intentionally disabled for the base map.
// We still keep this function so older code cannot break if it calls it.
function initLeafletMap(){

  // External map tiles are intentionally disabled.
  // This avoids dependency on third-party tile servers.
  return false;
}

// These functions are retained safely in case other UI code references them.
// They are not used by the active map renderer.

let leafletGlow = {};
let leafletPulse = {};
let pulseColor = {};

function zoneLabel(z){

  return `
    <b>${esc(z.zone_name)}</b><br>
    <b>${Math.round(z.risk_score)}</b>/100
  `;

}

function styleZoneOnMap(z){

  // Leaflet rendering is disabled.
  // Active visualization is the built-in SVG map.
  return;
}

function buildLeafletMarkers(zones){
  return;
}

function updateLeafletMarkers(zones){
  return;
}

// ---------------------------------------------------------------------------
// BUILD MAP
// ---------------------------------------------------------------------------
// Force the self-contained SVG map.
// No OSM request.
// No external tile request.
// ---------------------------------------------------------------------------
function buildMap(zones){

  useLeaflet = false;

  const leafletEl =
    document.getElementById('leafletMap');

  const svgEl =
    document.getElementById('map');

  const mapWrap =
    document.getElementById('mapwrap');

  if(leafletEl){
    leafletEl.style.display = 'none';
  }

  if(svgEl){
    svgEl.style.display = 'block';
  }

  if(mapWrap){
    mapWrap.classList.add('fb');
  }

  if(!mapBuilt){

    buildGridMap(zones);

    mapBuilt = true;

    return;
  }

  updateGridMapColors(zones);
}

function updateMapColors(zones){

  updateGridMapColors(zones);

}

// ---------------------------------------------------------------------------
// GRID / SVG MAP
// ---------------------------------------------------------------------------
function buildGridMap(zones){

  const svg =
    document.getElementById('map');

  if(!svg) return;

  svg.setAttribute(
    'preserveAspectRatio',
    'xMidYMid slice'
  );

  svg.setAttribute(
    'viewBox',
    `0 0 ${MAP_W} ${MAP_H}`
  );

  svg.innerHTML = '';

  zoneCellMap = {};

  const ns =
    'http://www.w3.org/2000/svg';

  const el = (n,at,parent)=>{

    const e =
      document.createElementNS(ns,n);

    for(const k in at){
      e.setAttribute(k,at[k]);
    }

    (parent || svg).appendChild(e);

    return e;
  };

  // -----------------------------------------------------------------------
  // Background grid
  // -----------------------------------------------------------------------
  const gridGroup =
    el('g',{
      class:'map-grid',
      opacity:'0.35',
      'pointer-events':'none'
    });

  const cellW =
    MAP_W / GRID_COLS;

  const cellH =
    MAP_H / GRID_ROWS;

  for(let row=0;row<GRID_ROWS;row++){

    for(let col=0;col<GRID_COLS;col++){

      const x =
        col * cellW;

      const y =
        row * cellH;

      const cx =
        x + cellW/2;

      const cy =
        y + cellH/2;

      const zoneId =
        nearestZoneId(cx,cy);

      el(
        'rect',
        {
          x,
          y,
          width:cellW+0.7,
          height:cellH+0.7,
          class:'heat-cell',
          'data-zone':zoneId
        },
        gridGroup
      );
    }
  }

  // -----------------------------------------------------------------------
  // Gradients / heat glows
  // -----------------------------------------------------------------------
  const defs =
    el('defs',{});

  const glowLayer =
    el('g',{});

  const topLayer =
    el('g',{});

  zones.forEach(z=>{

    const p =
      ZONE_POINTS[z.zone_id];

    if(!p) return;

    const gradient =
      el(
        'radialGradient',
        {
          id:'rg-'+z.zone_id,
          cx:'50%',
          cy:'50%',
          r:'50%'
        },
        defs
      );

    const s1 =
      el(
        'stop',
        {
          offset:'0',
          'stop-opacity':'.85'
        },
        gradient
      );

    const s2 =
      el(
        'stop',
        {
          offset:'1',
          'stop-opacity':'0'
        },
        gradient
      );

    const glow =
      el(
        'circle',
        {
          cx:p.x,
          cy:p.y,
          r:90,
          fill:`url(#rg-${z.zone_id})`,
          class:'glow',
          'pointer-events':'none'
        },
        glowLayer
      );

    const g =
      el(
        'g',
        {
          class:'zg',
          'data-zone':z.zone_id,
          tabindex:'0'
        },
        topLayer
      );

    el(
      'circle',
      {
        cx:p.x,
        cy:p.y,
        r:28,
        fill:'transparent',
        class:'zone-hit'
      },
      g
    );

    const ring =
      el(
        'circle',
        {
          cx:p.x,
          cy:p.y,
          r:12,
          class:'ring'
        },
        g
      );

    const core =
      el(
        'circle',
        {
          cx:p.x,
          cy:p.y,
          r:7,
          class:'core',
          stroke:'#fff',
          'stroke-width':2
        },
        g
      );

    const txt =
      el(
        'text',
        {
          x:p.x,
          y:p.y-14,
          class:'zs'
        },
        g
      );

    const nm =
      el(
        'text',
        {
          x:p.x,
          y:p.y+24,
          class:'zn'
        },
        g
      );

    nm.textContent =
      z.zone_name;

    // Click zone
    g.addEventListener(
      'click',
      ()=>{
        selectZone(z.zone_id);
      }
    );

    // Keyboard accessibility
    g.addEventListener(
      'keydown',
      e=>{
        if(e.key==='Enter' || e.key===' '){
          e.preventDefault();
          selectZone(z.zone_id);
        }
      }
    );

    zoneCellMap[z.zone_id] = {
      s1,
      s2,
      glow,
      core,
      ring,
      txt,
      nm,
      group:g
    };

  });

  updateGridMapColors(zones);

}

// ---------------------------------------------------------------------------
// UPDATE MAP COLORS
// ---------------------------------------------------------------------------
function updateGridMapColors(zones){

  // Update zone heat cells
  const svg =
    document.getElementById('map');

  if(svg){

    svg.querySelectorAll('.heat-cell')
      .forEach(cell=>{

        const zoneId =
          cell.getAttribute('data-zone');

        const z =
          latestZones[zoneId];

        if(!z) return;

        const c =
          riskColor(z.risk_score);

        cell.setAttribute(
          'fill',
          c
        );

        cell.setAttribute(
          'fill-opacity',
          '0.035'
        );

      });
  }

  zones.forEach(z=>{

    const r =
      zoneCellMap[z.zone_id];

    if(!r) return;

    const c =
      riskColor(z.risk_score);

    r.s1.setAttribute(
      'stop-color',
      c
    );

    r.s2.setAttribute(
      'stop-color',
      c
    );

    r.glow.setAttribute(
      'r',
      55 + z.risk_score * 1.15
    );

    r.core.setAttribute(
      'fill',
      c
    );

    r.ring.setAttribute(
      'stroke',
      c
    );

    r.ring.style.display =
      z.risk_score >= 50
        ? ''
        : 'none';

    r.txt.textContent =
      Math.round(z.risk_score);

  });

}

// ---------------------------------------------------------------------------
// KPI
// ---------------------------------------------------------------------------
let kpiBuilt = false;

function renderKpis(c){

  const live =
    lastDataMode === 'LIVE';

  const k = [

    {
      i:'🌡️',
      l:'Temperature',
      v:c.avg_air_temp+'°C',
      t:live ? 'Live weather' : 'Simulated'
    },

    {
      i:'🛡️',
      l:'Average heat risk',
      v:c.avg_heat_risk+' / 100',
      t:'Across all zones'
    },

    {
      i:'🔥',
      l:'Danger zones',
      v:String(c.critical_hotspots).padStart(2,'0'),
      t:c.critical_hotspots
        ? 'Need attention now'
        : 'All clear',
      dot:true,
      n:c.critical_hotspots
    },

    {
      i:'☀️',
      l:'Hottest surface',
      v:c.max_surface_temp+'°C',
      t:'Ground / rooftop heat'
    },

    {
      i:'🌿',
      l:'Greenery',
      v:c.avg_ndvi,
      t:'Higher means cooler'
    },

    {
      i:'🧠',
      l:'Prediction model',
      v:esc(modelAlgorithm),
      t:'Scores the risk'
    }

  ];

  const box =
    document.getElementById('kpiRow');

  if(!box) return;

  if(!kpiBuilt){

    box.innerHTML =
      k.map(x=>`
        <div class="kpi">

          <div class="label">
            <span class="ico">${x.i}</span>
            ${x.l}
          </div>

          <div class="value">
            <span class="v"></span>
            ${x.dot
              ? '<span class="alertdot"></span>'
              : ''
            }
          </div>

          <div class="trend"></div>

        </div>
      `).join('');

    kpiBuilt = true;
  }

  [...box.children].forEach((el,i)=>{

    el.querySelector('.v').innerHTML =
      k[i].v;

    el.querySelector('.trend').textContent =
      k[i].t;

    const d =
      el.querySelector('.alertdot');

    if(d){
      d.classList.toggle(
        'none',
        !k[i].n
      );
    }

  });

}

// ---------------------------------------------------------------------------
// SELECTED ZONE
// ---------------------------------------------------------------------------
let detailsFor = null;
let detailsFetchedAt = 0;

const DETAIL_REFRESH_MS = 30000;

function selectZone(zoneId){

  selectedZone =
    zoneId;

  renderSelectedZone(true);
}

function renderSelectedZone(force){

  const zoneId =
    selectedZone;

  const z =
    latestZones[zoneId];

  if(!z) return;

  const cat =
    riskCategory(z.risk_score);

  const name =
    document.getElementById('zName');

  const tag =
    document.getElementById('zTag');

  const score =
    document.getElementById('zScore');

  if(name)
    name.textContent =
      z.zone_name;

  if(tag){

    tag.className =
      'tag '+cat.cls;

    tag.textContent =
      cat.label;
  }

  if(score)
    score.textContent =
      Math.round(z.risk_score);

  const metrics =
    document.getElementById('zMetrics');

  if(metrics){

    metrics.innerHTML = `

      <div>
        <span>Air temperature</span>
        <b>${z.air_temp}°C</b>
      </div>

      <div>
        <span>Surface temperature</span>
        <b>${z.surface_temp}°C</b>
      </div>

      <div>
        <span>Humidity</span>
        <b>${z.humidity}%</b>
      </div>

      <div>
        <span>Greenery</span>
        <b>${z.ndvi}</b>
      </div>

      <div>
        <span>Built-up area</span>
        <b>${Math.round(z.built_up_density*100)}%</b>
      </div>

    `;
  }

  // -------------------------------------------------------------------------
  // Donut chart
  // -------------------------------------------------------------------------
  try{

    if(typeof Chart === 'undefined')
      throw new Error(
        'Chart.js not loaded yet'
      );

    const dData = [
      z.risk_score,
      100-z.risk_score
    ];

    if(donutChart){

      donutChart.data.datasets[0].data =
        dData;

      donutChart.data.datasets[0]
        .backgroundColor = [
          riskColor(z.risk_score),
          'rgba(255,255,255,.08)'
        ];

      donutChart.update('none');

    }else{

      const canvas =
        document.getElementById('zDonut');

      if(!canvas)
        throw new Error(
          'Donut canvas not found'
        );

      const ctx =
        canvas.getContext('2d');

      donutChart =
        new Chart(
          ctx,
          {
            type:'doughnut',

            data:{
              datasets:[
                {
                  data:dData,

                  backgroundColor:[
                    riskColor(z.risk_score),
                    'rgba(255,255,255,.08)'
                  ],

                  borderWidth:0
                }
              ]
            },

            options:{
              cutout:'72%',

              plugins:{
                tooltip:{
                  enabled:false
                },

                legend:{
                  display:false
                }
              }
            }
          }
        );
    }

  }catch(e){

    console.warn(
      'Donut chart skipped:',
      e.message
    );

    const dz =
      document.getElementById('badgeZone');

    if(
      dz &&
      !dz.dataset.chartWarned
    ){

      dz.dataset.chartWarned='1';

      dz.insertAdjacentHTML(
        'beforeend',
        badge(
          'WARN',
          'CHART LIBRARY NOT LOADED'
        )
      );
    }
  }

  if(
    force ||
    detailsFor !== zoneId ||
    Date.now()-detailsFetchedAt >
      DETAIL_REFRESH_MS
  ){

    loadZoneDetails(zoneId);
  }

}

// ---------------------------------------------------------------------------
// ZONE DETAILS
// ---------------------------------------------------------------------------
function loadZoneDetails(zoneId){

  detailsFor =
    zoneId;

  detailsFetchedAt =
    Date.now();

  const stillSelected =
    ()=>zoneId === selectedZone;

  fetch(
    `${API_BASE}/api/zones/${zoneId}`
  )
  .then(r=>{

    if(!r.ok)
      throw new Error(
        'HTTP '+r.status
      );

    return r.json();

  })
  .then(d=>{

    if(!stillSelected())
      return;

    const explain =
      document.getElementById(
        'zExplain'
      );

    if(explain){

      explain.innerHTML =
        `<b>Why this score?</b><br>
        ${esc(d.risk_explanation)}`;
    }

    const drivers =
      d.drivers || [];

    const maxAbs =
      Math.max(
        0.5,
        ...drivers.map(
          x=>Math.abs(
            x.risk_points_vs_city_avg
          )
        )
      );

    const factors =
      document.getElementById(
        'zFactors'
      );

    if(!factors)
      return;

    factors.innerHTML =
      '<div class="fhead">' +
      'What makes this zone hotter (+) or cooler (−) than average' +
      '</div>' +

      drivers.map(x=>{

        const pts =
          x.risk_points_vs_city_avg;

        const color =
          pts >= 0
            ? riskColor(
                Math.min(
                  100,
                  40 + pts*6
                )
              )
            : 'var(--green)';

        return `
          <div class="factor">

            <div class="flabel">
              <span>${esc(x.label)}</span>
              <span>
                ${pts>0?'+':''}${pts}
              </span>
            </div>

            <div class="bar">
              <i
                style="
                  width:${Math.abs(pts)/maxAbs*100}%;
                  background:${color}
                "
              ></i>
            </div>

          </div>
        `;

      }).join('');

  })
  .catch(e=>{

    if(!stillSelected())
      return;

    const explain =
      document.getElementById(
        'zExplain'
      );

    const factors =
      document.getElementById(
        'zFactors'
      );

    if(explain){

      explain.innerHTML =
        `<div class="warnline">
          ⚠ Could not load the explanation
          for this zone (${esc(e.message)}).
          The numbers above are still current.
        </div>`;
    }

    if(factors)
      factors.innerHTML='';
  });

  // -------------------------------------------------------------------------
  // Recommendations
  // -------------------------------------------------------------------------
  fetch(
    `${API_BASE}/api/recommendations/${zoneId}`
  )
  .then(r=>{

    if(!r.ok)
      throw new Error(
        'HTTP '+r.status
      );

    return r.json();

  })
  .then(rec=>{

    if(!stillSelected())
      return;

    const tag =
      document.getElementById(
        'recSourceTag'
      );

    if(tag){

      tag.textContent =
        'For '+
        (
          latestZones[zoneId]
            ? latestZones[zoneId].zone_name
            : 'this zone'
        );
    }

    const list =
      document.getElementById(
        'recList'
      );

    if(list){

      list.innerHTML = `

        <div class="rec-item">

          <div>🌱</div>

          <div>

            <div class="rec-why">
              ${esc(rec.reason)}
            </div>

            <div class="rec-priority">
              Priority:
              ${esc(rec.priority)}
            </div>

          </div>

        </div>

        ${(rec.actions||[])
          .map(a=>`

            <div class="rec-item">

              <div>✅</div>

              <div>${esc(a)}</div>

            </div>

          `).join('')}

        ${
          rec.note
            ? `
              <div class="warnline">
                ⚠ ${esc(rec.note)}
              </div>
            `
            : ''
        }

      `;
    }

    loadStatus();

  })
  .catch(e=>{

    if(!stillSelected())
      return;

    const list =
      document.getElementById(
        'recList'
      );

    if(list){

      list.innerHTML =
        `<div class="warnline">
          ⚠ Could not load recommendations
          (${esc(e.message)}).
        </div>`;
    }

  });

}

// ---------------------------------------------------------------------------
// HOTSPOTS
// ---------------------------------------------------------------------------
function renderHotspots(hotspots){

  const list =
    document.getElementById(
      'hotspotList'
    );

  if(!list) return;

  list.innerHTML =
    hotspots
      .slice(0,5)
      .map(h=>`

        <div class="hotspot-item">

          <div class="hs-badge ${h.severity}">
            ${h.severity}
          </div>

          <div>

            <b>${esc(h.zone_name)}</b>

            <br>

            <small class="dim">
              Risk ${h.risk_score} out of 100
              · ${h.anomaly_score}σ above normal
            </small>

          </div>

        </div>

      `).join('') ||

    `<div class="empty">

      <span class="big">✅</span>

      <div>
        <b>No hotspots right now</b>
        <br>
        Every zone is within its normal heat range.
      </div>

    </div>`;

  const top =
    Object.values(latestZones)
      .sort(
        (a,b)=>
          b.risk_score -
          a.risk_score
      )
      .slice(0,5);

  list.insertAdjacentHTML(
    'beforeend',

    `
      <div class="rank">

        <h4>
          Zones ranked by heat risk
        </h4>

        ${top.map(z=>`

          <div
            class="rrow"
            data-zone="${esc(z.zone_id)}"
          >

            <b style="font-weight:500">
              ${esc(z.zone_name)}
            </b>

            <div class="fbar">

              <i
                style="
                  width:${z.risk_score}%;
                  background:${riskColor(z.risk_score)}
                "
              ></i>

            </div>

            <span>
              ${Math.round(z.risk_score)}
            </span>

          </div>

        `).join('')}

      </div>
    `
  );
}

// ---------------------------------------------------------------------------
// TREND
// ---------------------------------------------------------------------------
async function refreshTrend(){

  if(typeof Chart === 'undefined'){

    setBadge(
      'badgeTrend',
      badge(
        'WARN',
        'Chart not loaded'
      )
    );

    return;
  }

  try{

    const r =
      await fetch(
        `${API_BASE}/api/history`
      );

    if(!r.ok)
      return;

    const d =
      await r.json();

    const ts =
      (
        d.city_average &&
        d.city_average.timestamps
      ) || [];

    const vals =
      (
        d.city_average &&
        d.city_average.risk
      ) || [];

    const labels =
      ts.map(
        t=>
          new Date(t*1000)
            .toLocaleTimeString(
              [],
              {
                hour:'2-digit',
                minute:'2-digit'
              }
            )
      );

    serverTrendOK =
      vals.length >= 3;

    if(serverTrendOK){

      drawTrend(
        labels.slice(-60),
        vals.slice(-60)
      );
    }

  }catch(e){

    console.warn(
      'Trend refresh failed:',
      e
    );

    setBadge(
      'badgeTrend',
      badge(
        'WARN',
        'Chart failed',
        String(e.message||e)
      )
    );
  }

}

let liveBuf = [];
let serverTrendOK = false;

function pushLive(v){

  liveBuf.push({

    l:
      new Date()
        .toLocaleTimeString(
          [],
          {
            hour:'2-digit',
            minute:'2-digit',
            second:'2-digit'
          }
        ),

    v:+v

  });

  liveBuf =
    liveBuf.slice(-40);

  if(
    !serverTrendOK &&
    typeof Chart !== 'undefined'
  ){

    drawTrend(
      liveBuf.map(p=>p.l),
      liveBuf.map(p=>p.v)
    );
  }

}

function drawTrend(labels,values){

  const pr =
    values.length < 3
      ? 3
      : 0;

  if(!trendChart){

    const canvas =
      document.getElementById(
        'trendChart'
      );

    if(!canvas)
      return;

    const ctx =
      canvas.getContext('2d');

    trendChart =
      new Chart(
        ctx,
        {
          type:'line',

          data:{
            labels,

            datasets:[
              {
                data:values,
                borderColor:'#2dd4bf',
                backgroundColor:
                  'rgba(45,212,191,.14)',
                fill:true,
                tension:.35,
                pointRadius:pr
              }
            ]
          },

          options:{
            maintainAspectRatio:false,

            scales:{

              x:{
                ticks:{
                  color:'#8c9bb5',
                  maxTicksLimit:6
                },
                grid:{
                  display:false
                }
              },

              y:{
                min:0,
                max:100,

                grid:{
                  color:
                    'rgba(255,255,255,.06)'
                },

                ticks:{
                  color:'#8c9bb5'
                }
              }

            },

            plugins:{
              legend:{
                display:false
              }
            }
          }
        }
      );

  }else{

    trendChart.data.labels =
      labels;

    trendChart.data.datasets[0]
      .data = values;

    trendChart.data.datasets[0]
      .pointRadius = pr;

    trendChart.update('none');
  }

}

setInterval(()=>{
  if(usingBackend)
    refreshTrend();
},60000);

// ---------------------------------------------------------------------------
// CONNECTION
// ---------------------------------------------------------------------------
let lastDataMode = 'DEMO';

function setConnectionState(
  mode,
  dataMode
){

  if(dataMode)
    lastDataMode =
      dataMode;

  const pulse =
    document.getElementById(
      'connPulse'
    );

  const label =
    document.getElementById(
      'connLabel'
    );

  const statusLine =
    document.getElementById(
      'dataStatusLine'
    );

  const statusDesc =
    document.getElementById(
      'dataStatusDesc'
    );

  if(!pulse || !label)
    return;

  pulse.className =
    'pulse '+
    (
      mode==='LIVE_BACKEND'
        ? ''
        : mode==='OFFLINE'
          ? 'offline'
          : 'demo'
    );

  const hdrSrc =
    document.getElementById(
      'hdrDataSource'
    );

  const sys =
    document.getElementById(
      'sysPill'
    );

  if(sys){

    sys.className =
      'pill '+
      (
        mode==='OFFLINE'
          ? ''
          : 'ok'
      );
  }

  if(mode==='LIVE_BACKEND'){

    const live =
      lastDataMode==='LIVE';

    label.textContent =
      live
        ? 'System online'
        : 'System online · demo data';

    if(statusLine){

      statusLine.textContent =
        live
          ? 'Live data'
          : 'Demo data';

      if(statusLine.previousElementSibling){

        statusLine
          .previousElementSibling
          .style.background =
            live
              ? 'var(--green)'
              : 'var(--orange)';
      }
    }

    if(statusDesc){

      statusDesc.textContent =
        live
          ? 'Real weather feeds the model. Land values are still estimates.'
          : 'Live weather is unreachable, so values are simulated.';
    }

    if(hdrSrc){

      hdrSrc.textContent =
        live
          ? 'Live weather'
          : 'Demo data';
    }

  }else if(mode==='OFFLINE'){

    label.textContent =
      'Offline · retrying…';

    if(statusLine)
      statusLine.textContent =
        'Offline';

    if(
      statusLine &&
      statusLine.previousElementSibling
    ){

      statusLine
        .previousElementSibling
        .style.background =
          'var(--red)';
    }

    if(statusDesc){

      statusDesc.textContent =
        'Server not reachable. Showing the last data received.';
    }

  }else{

    label.textContent =
      'Demo mode';

    if(statusLine)
      statusLine.textContent =
        'Demo data';
  }

}

// ---------------------------------------------------------------------------
// APPLY SNAPSHOT
// ---------------------------------------------------------------------------
function applySnapshot(
  zones,
  avgRisk,
  hotspots
){

  latestZones = {};

  zones.forEach(z=>{
    latestZones[z.zone_id] =
      z;
  });

  // Map
  try{

    if(!mapBuilt)
      buildMap(zones);
    else
      updateMapColors(zones);

  }catch(e){

    console.error(
      'Map render error:',
      e
    );
  }

  // KPIs
  renderKpis({

    avg_air_temp:
      (
        zones.reduce(
          (s,z)=>s+z.air_temp,
          0
        ) /
        zones.length
      ).toFixed(1),

    avg_heat_risk:
      avgRisk,

    critical_hotspots:
      hotspots.length,

    max_surface_temp:
      Math.max(
        ...zones.map(
          z=>z.surface_temp
        )
      ).toFixed(1),

    avg_ndvi:
      (
        zones.reduce(
          (s,z)=>s+z.ndvi,
          0
        ) /
        zones.length
      ).toFixed(3)

  });

  const avgTemp =
    (
      zones.reduce(
        (s,z)=>s+z.air_temp,
        0
      ) /
      zones.length
    ).toFixed(1);

  const hdrTemp =
    document.getElementById(
      'hdrTemp'
    );

  if(hdrTemp)
    hdrTemp.textContent =
      avgTemp+'°C';

  const ring =
    document.getElementById(
      'hdrRiskRing'
    );

  if(ring){

    ring.textContent =
      Math.round(avgRisk);

    ring.style.borderColor =
      riskColor(avgRisk);
  }

  const riskLabel =
    document.getElementById(
      'hdrRiskLabel'
    );

  if(riskLabel){

    riskLabel.textContent =
      riskCategory(avgRisk)
        .label;
  }

  pushLive(avgRisk);

  const now =
    new Date();

  const hdrTime =
    document.getElementById(
      'hdrTime'
    );

  if(hdrTime)
    hdrTime.textContent =
      now.toLocaleTimeString();

  const updated =
    document.getElementById(
      'lastUpdated'
    );

  if(updated){

    updated.textContent =
      'Last updated: '+
      now.toLocaleTimeString(
        [],
        {
          hour:'2-digit',
          minute:'2-digit',
          second:'2-digit'
        }
      );
  }

  renderHotspots(
    hotspots
  );

  if(
    !selectedZone &&
    zones.length
  ){

    selectZone(
      zones[0].zone_id
    );

  }else if(selectedZone){

    renderSelectedZone(false);
  }

}

// ---------------------------------------------------------------------------
// WEBSOCKET
// ---------------------------------------------------------------------------
let ws;
let usingBackend = false;
let reconnectDelay = 1000;
let reconnectTimer = null;

function showOffline(on){

  const el =
    document.getElementById(
      'offlineBanner'
    );

  if(el)
    el.style.display =
      on
        ? 'block'
        : 'none';
}

function scheduleReconnect(){

  if(reconnectTimer)
    return;

  reconnectTimer =
    setTimeout(
      ()=>{
        reconnectTimer = null;
        connectBackend();
      },
      reconnectDelay
    );

  reconnectDelay =
    Math.min(
      reconnectDelay*2,
      15000
    );
}

function connectBackend(){

  try{

    ws =
      new WebSocket(
        WS_URL
      );

  }catch(e){

    usingBackend =
      false;

    setConnectionState(
      'OFFLINE'
    );

    showOffline(true);

    scheduleReconnect();

    return;
  }

  ws.onopen = ()=>{

    usingBackend =
      true;

    reconnectDelay =
      1000;

    showOffline(false);

    setConnectionState(
      'LIVE_BACKEND'
    );

    refreshTrend();
    loadStatus();
  };

  ws.onmessage = ev=>{

    try{

      const msg =
        JSON.parse(ev.data);

      if(msg.model_algorithm){

        modelAlgorithm =
          msg.model_algorithm;

        const modelStatus =
          document.getElementById(
            'modelStatus'
          );

        if(modelStatus)
          modelStatus.textContent =
            modelAlgorithm;
      }

      lastMsgAt =
        Date.now();

      const modeChanged =
        msg.data_mode !==
        lastDataMode;

      setConnectionState(
        'LIVE_BACKEND',
        msg.data_mode
      );

      if(
        Array.isArray(msg.zones)
      ){

        applySnapshot(
          msg.zones,
          msg.avg_heat_risk,
          msg.hotspots || []
        );
      }

      if(
        modeChanged ||
        !statusLoadedAt
      ){

        loadStatus();
      }

    }catch(e){

      console.error(
        'WebSocket message error:',
        e
      );
    }
  };

  ws.onclose = ()=>{

    usingBackend =
      false;

    const modelStatus =
      document.getElementById(
        'modelStatus'
      );

    if(modelStatus)
      modelStatus.textContent =
        '—';

    setConnectionState(
      'OFFLINE'
    );

    showOffline(true);

    scheduleReconnect();
  };

  ws.onerror = ()=>{

    try{
      ws.close();
    }catch(e){}
  };

}

connectBackend();

// ---------------------------------------------------------------------------
// ANIMATED NETWORK BACKGROUND
// ---------------------------------------------------------------------------
(function(){

  const cv =
    document.getElementById(
      'bgnet'
    );

  if(
    !cv ||
    matchMedia(
      '(prefers-reduced-motion:reduce)'
    ).matches
  )
    return;

  const g =
    cv.getContext('2d');

  let W,H,pts=[];
  let seed=7;

  const rnd = ()=>
    (
      seed =
        (seed*16807)%2147483647
    ) / 2147483647;

  function size(){

    W =
      cv.width =
        innerWidth;

    H =
      cv.height =
        innerHeight;

    pts =
      Array.from(
        {
          length:
            Math.min(
              60,
              Math.floor(W/28)
            )
        },
        ()=>({
          x:rnd()*W,
          y:rnd()*H,
          vx:(rnd()-.5)*.25,
          vy:(rnd()-.5)*.25
        })
      );
  }

  size();

  addEventListener(
    'resize',
    size
  );

  (function tick(){

    g.clearRect(
      0,
      0,
      W,
      H
    );

    pts.forEach(p=>{

      p.x =
        (p.x+p.vx+W)%W;

      p.y =
        (p.y+p.vy+H)%H;

      g.fillStyle =
        'rgba(120,180,255,.55)';

      g.beginPath();

      g.arc(
        p.x,
        p.y,
        1.4,
        0,
        6.3
      );

      g.fill();
    });

    for(
      let i=0;
      i<pts.length;
      i++
    ){

      for(
        let j=i+1;
        j<pts.length;
        j++
      ){

        const d =
          Math.hypot(
            pts[i].x-pts[j].x,
            pts[i].y-pts[j].y
          );

        if(d<130){

          g.strokeStyle =
            `rgba(120,180,255,${
              .16*(1-d/130)
            })`;

          g.beginPath();

          g.moveTo(
            pts[i].x,
            pts[i].y
          );

          g.lineTo(
            pts[j].x,
            pts[j].y
          );

          g.stroke();
        }
      }
    }

    requestAnimationFrame(
      tick
    );

  })();

})();

// ---------------------------------------------------------------------------
// SIDEBAR NAVIGATION
// ---------------------------------------------------------------------------
document
  .querySelectorAll('#sideNav a')
  .forEach(a=>{

    a.addEventListener(
      'click',
      ()=>{

        document
          .querySelectorAll(
            '#sideNav a'
          )
          .forEach(x=>
            x.classList.remove(
              'active'
            )
          );

        a.classList.add(
          'active'
        );

        const target =
          a.dataset.target ||
          'sec-overview';

        document
          .querySelectorAll(
            '.section'
          )
          .forEach(s=>
            s.classList.remove(
              'active'
            )
          );

        const targetEl =
          document.getElementById(
            target
          );

        if(targetEl)
          targetEl.classList.add(
            'active'
          );

        window.scrollTo({
          top:0,
          behavior:'smooth'
        });

        if(
          target ===
          'sec-data-sources'
        )
          loadDataSources();

        if(
          target ===
          'sec-model-performance'
        )
          loadModelPerformance();

        if(
          target ===
          'sec-forecast'
        )
          loadForecastSection();

      }
    );

  });

// ---------------------------------------------------------------------------
// DATA SOURCES
// ---------------------------------------------------------------------------
async function loadDataSources(){

  const body =
    document.getElementById(
      'dataSourcesBody'
    );

  if(!body) return;

  body.textContent =
    'Checking sources…';

  try{

    const r =
      await fetch(
        `${API_BASE}/api/data-sources`
      );

    if(!r.ok)
      throw new Error(
        'bad response'
      );

    const d =
      await r.json();

    const rows =
      d.sources.map(s=>{

        const ok =
          /^(connected|available|configured)/i
            .test(s.status);

        const color =
          ok
            ? 'var(--low)'
            : 'var(--orange)';

        const updated =
          (
            typeof s.last_updated ===
            'number'
          )
            ? new Date(
                s.last_updated*1000
              ).toLocaleTimeString()
            : esc(
                s.last_updated ||
                '—'
              );

        return `

          <tr
            style="
              border-top:1px solid var(--border);
            "
          >

            <td style="padding:8px 6px;">
              ${esc(s.name)}
            </td>

            <td style="padding:8px 6px;">

              <b
                style="
                  color:${color};
                  text-transform:uppercase;
                  font-size:11px;
                "
              >
                ${esc(s.status)}
              </b>

            </td>

            <td
              style="padding:8px 6px;"
              class="dim"
            >
              ${updated}
            </td>

          </tr>
        `;

      }).join('');

    body.innerHTML = `

      <table
        style="
          width:100%;
          border-collapse:collapse;
          font-size:13px;
        "
      >

        <thead>

          <tr
            style="
              color:var(--muted);
              text-align:left;
            "
          >

            <th style="padding:8px 6px;">
              Source
            </th>

            <th style="padding:8px 6px;">
              Status
            </th>

            <th style="padding:8px 6px;">
              Last Updated
            </th>

          </tr>

        </thead>

        <tbody>
          ${rows}
        </tbody>

      </table>

      <div
        class="dim"
        style="margin-top:10px;"
      >
        ${esc(d.note||'')}
      </div>

    `;

  }catch(e){

    body.innerHTML =
      loadError(
        'data sources',
        e
      );
  }

}

// ---------------------------------------------------------------------------
// MODEL PERFORMANCE
// ---------------------------------------------------------------------------
async function loadModelPerformance(){

  const body =
    document.getElementById(
      'modelPerfBody'
    );

  if(!body) return;

  body.textContent =
    'Loading…';

  try{

    const r =
      await fetch(
        `${API_BASE}/api/model-performance`
      );

    if(!r.ok)
      throw new Error(
        'bad response'
      );

    const d =
      await r.json();

    const m =
      d.metrics || {};

    body.innerHTML = `

      <div
        class="kpis"
        style="
          grid-template-columns:
          repeat(4,1fr);
          margin-bottom:16px;
        "
      >

        <div class="kpi">

          <div class="label">
            Average error (MAE)
          </div>

          <div class="value">
            ${m.mae}
          </div>

          <div class="trend">
            Lower is better
          </div>

        </div>

        <div class="kpi">

          <div class="label">
            Typical miss (RMSE)
          </div>

          <div class="value">
            ${m.rmse}
          </div>

          <div class="trend">
            Lower is better
          </div>

        </div>

        <div class="kpi">

          <div class="label">
            Fit score (R²)
          </div>

          <div class="value">
            ${m.r2}
          </div>

          <div class="trend">
            Closer to 1 is better
          </div>

        </div>

        <div class="kpi">

          <div class="label">
            Cross-check (R²)
          </div>

          <div class="value">
            ${m.cv_r2_mean}
          </div>

          <div class="trend">
            Tested on unseen data
          </div>

        </div>

      </div>

      <div class="explain">

        The model
        <b>${esc(d.model_name || '—')}</b>
        was trained on
        <b>${d.dataset_rows ?? '—'}</b>
        simulated examples.

        High scores mean it learned the simulation well.
        They do not prove accuracy on real Moradabad readings yet.

      </div>

      <details class="more">

        <summary>
          Technical details
        </summary>

        <div
          class="dim"
          style="
            margin-top:8px;
            font-size:12.5px;
            line-height:1.6
          "
        >

          Algorithm:
          ${esc(d.algorithm || '—')}

          · Dataset:
          ${esc(d.dataset || '—')}

          (${d.train_rows ?? '—'}
          train /
          ${d.test_rows ?? '—'}
          test)

          <br>

          Noise ceiling R² ≈
          ${d.synthetic_noise_ceiling_r2 ?? '—'}

          <br>

          Importance method:
          ${esc(d.importance_method || '—')}

          <br>

          ${esc(m.note || '')}

        </div>

      </details>

    `;

  }catch(e){

    body.innerHTML =
      loadError(
        'model metrics',
        e
      );
  }

}

// ---------------------------------------------------------------------------
// FORECAST
// ---------------------------------------------------------------------------
async function loadForecastSection(){

  const body =
    document.getElementById(
      'forecastBody'
    );

  const label =
    document.getElementById(
      'forecastZoneLabel'
    );

  if(!body)
    return;

  const zid =
    selectedZone ||
    Object.keys(latestZones)[0];

  if(!zid){

    body.innerHTML =
      '<div class="dim">Pick a zone on the Overview map first, then come back here.</div>';

    return;
  }

  if(label){

    label.textContent =
      '— '+
      (
        latestZones[zid]
          ? latestZones[zid].zone_name
          : zid
      );
  }

  body.textContent =
    'Loading forecast…';

  try{

    const r =
      await fetch(
        `${API_BASE}/api/forecast?zone_id=${zid}&hours=6`
      );

    if(!r.ok)
      throw new Error(
        'bad response'
      );

    const d =
      await r.json();

    const rows =
      (d.forecast||[])
        .map(p=>`

          <div class="frow">

            <span class="dim">
              +${p.hour}h
            </span>

            <div class="fbar">

              <i
                style="
                  width:${p.predicted_risk}%;
                  background:${riskColor(p.predicted_risk)}
                "
              ></i>

            </div>

            <b>
              ${p.predicted_risk}/100

              <span
                class="dim"
                style="
                  font-weight:400;
                  font-size:12px
                "
              >
                (${p.lower}–${p.upper})
              </span>

            </b>

          </div>

        `).join('');

    setBadge(
      'badgeForecast',

      d.data_quality === 'LIVE_FORECAST'

        ? badge(
            'OK',
            'Real forecast weather',
            'Model run on Open-Meteo hourly forecast'
          )

        : badge(
            'ESTIMATE',
            'Rough estimate',
            'Live forecast unreachable: simple trend extrapolation, treat as rough'
          )
    );

    body.innerHTML = `

      <div
        class="dim"
        style="margin-bottom:10px;"
      >
        Predicted risk for each coming hour.
        The range in brackets shows how much it could vary.
      </div>

      ${rows}

      <details class="more">

        <summary>
          How is this calculated?
        </summary>

        <div
          class="dim"
          style="
            margin-top:8px;
            font-size:12.5px
          "
        >
          ${esc(
            d.method ||
            '—'
          )}

          The range is illustrative,
          not a calibrated interval.

        </div>

      </details>

    `;

    loadStatus();

  }catch(e){

    body.innerHTML =
      loadError(
        'the forecast',
        e
      );
  }

}

// ---------------------------------------------------------------------------
// ZONE RANKING CLICK
// ---------------------------------------------------------------------------
document.addEventListener(
  'click',
  e=>{

    const r =
      e.target.closest(
        '[data-zone]'
      );

    if(r)
      selectZone(
        r.dataset.zone
      );
  }
);

// ---------------------------------------------------------------------------
// SPLASH SCREEN
// ---------------------------------------------------------------------------
(function(){

  const sp =
    document.getElementById(
      'splash'
    );

  if(!sp)
    return;

  let seen = false;

  try{

    seen =
      sessionStorage.getItem(
        'hs_splash'
      ) === '1';

  }catch(e){}

  const mark =
    (k,ok)=>{

      const d =
        sp.querySelector(
          `[data-k="${k}"]`
        );

      if(d){

        d.className =
          ok
            ? 'ok'
            : 'bad';

        d.querySelector(
          'i'
        ).textContent =
          ok
            ? '✓'
            : '!';
      }
    };

  let closed =
    false;

  function close(){

    if(closed)
      return;

    closed =
      true;

    sp.classList.add(
      'done'
    );

    try{

      sessionStorage.setItem(
        'hs_splash',
        '1'
      );

    }catch(e){}

    setTimeout(
      ()=>sp.remove(),
      900
    );
  }

  if(seen){

    sp.remove();

    return;
  }

  const skip =
    document.getElementById(
      'spSkip'
    );

  if(skip)
    skip.addEventListener(
      'click',
      close
    );

  const minWait =
    new Promise(
      r=>
        setTimeout(
          r,
          3400
        )
    );

  (async()=>{

    try{

      const r =
        await fetch(
          `${API_BASE}/api/health`,
          {
            cache:'no-store'
          }
        );

      mark(
        'srv',
        r.ok
      );

      const h =
        r.headers;

      mark(
        'sec',
        !!(
          h.get(
            'x-content-type-options'
          ) &&
          h.get(
            'content-security-policy'
          )
        )
      );

    }catch(e){

      mark(
        'srv',
        false
      );

      mark(
        'sec',
        false
      );
    }

    try{

      const r2 =
        await fetch(
          `${API_BASE}/api/status`,
          {
            cache:'no-store'
          }
        );

      mark(
        'dat',
        r2.ok
      );

    }catch(e){

      mark(
        'dat',
        false
      );
    }

    await minWait;

    close();

  })();

})();

// ---------------------------------------------------------------------------
// SECURITY AUDIT
// ---------------------------------------------------------------------------
(function(){

  const modal =
    document.getElementById(
      'secModal'
    );

  const btn =
    document.getElementById(
      'secBtn'
    );

  if(!modal || !btn)
    return;

  const close = ()=>{

    modal.classList.remove(
      'open'
    );

    btn.focus();
  };

  async function open(){

    modal.classList.add(
      'open'
    );

    const closeBtn =
      document.getElementById(
        'secClose'
      );

    if(closeBtn)
      closeBtn.focus();

    const list =
      document.getElementById(
        'secList'
      );

    if(!list)
      return;

    list.innerHTML =
      '<div class="dim">Checking…</div>';

    try{

      const r =
        await fetch(
          `${API_BASE}/api/security`,
          {
            cache:'no-store'
          }
        );

      if(!r.ok)
        throw new Error(
          'HTTP '+r.status
        );

      const d =
        await r.json();

      const secure =
        location.protocol === 'https:' ||
        [
          'localhost',
          '127.0.0.1'
        ].includes(
          location.hostname
        );

      const checks =
        d.checks.concat([
          {
            label:'Encrypted connection',
            ok:secure,
            detail:
              location.protocol === 'https:'
                ? 'This page uses HTTPS.'
                : (
                  secure
                    ? 'Local machine only, no network exposure.'
                    : 'Plain HTTP. Put it behind HTTPS before sharing.'
                )
          }
        ]);

      const good =
        checks.filter(
          c=>c.ok
        ).length;

      const score =
        document.getElementById(
          'secScore'
        );

      const scoreTxt =
        document.getElementById(
          'secScoreTxt'
        );

      if(score)
        score.textContent =
          good+'/'+checks.length;

      if(scoreTxt){

        scoreTxt.textContent =
          good===checks.length
            ? 'All protections are on'
            : 'Some items need attention';
      }

      list.innerHTML =
        checks.map(c=>`

          <div class="srow">

            <span
              class="mk ${c.ok?'ok':'warn'}"
            >
              ${c.ok?'✓':'!'}
            </span>

            <div>

              <b>
                ${esc(c.label)}
              </b>

              <div class="dim">
                ${esc(c.detail)}
              </div>

            </div>

          </div>

        `).join('');

    }catch(e){

      list.innerHTML =
        loadError(
          'the security report',
          e
        );
    }

  }

  btn.addEventListener(
    'click',
    open
  );

  const closeBtn =
    document.getElementById(
      'secClose'
    );

  if(closeBtn){

    closeBtn.addEventListener(
      'click',
      close
    );
  }

  modal.addEventListener(
    'click',
    e=>{
      if(e.target===modal)
        close();
    }
  );

  document.addEventListener(
    'keydown',
    e=>{

      if(
        e.key==='Escape' &&
        modal.classList.contains(
          'open'
        )
      ){

        close();
      }
    }
  );

})();

// ---------------------------------------------------------------------------
// SAFETY AWARENESS VIDEO
// ---------------------------------------------------------------------------
(function(){

  const v =
    document.getElementById(
      'adVideo'
    );

  if(!v)
    return;

  const tips = [

    [
      'Drink water every 20 minutes, even if you do not feel thirsty.',
      'हर 20 मिनट में पानी पिएं, प्यास न लगे तब भी।'
    ],

    [
      'Avoid going outside between 12 pm and 4 pm on hot days.',
      'गर्मी में दोपहर 12 से 4 बजे तक बाहर जाने से बचें।'
    ],

    [
      'Wear light, loose cotton clothes and cover your head.',
      'हल्के, ढीले सूती कपड़े पहनें और सिर ढककर रखें।'
    ],

    [
      'Take ORS, lemon water or buttermilk to replace lost salts.',
      'ORS, नींबू पानी या छाछ लें, इससे शरीर में नमक-पानी की कमी पूरी होती है।'
    ],

    [
      'Check on elderly neighbours, children and pets.',
      'बुज़ुर्गों, बच्चों और पालतू जानवरों का ध्यान रखें।'
    ],

    [
      'Never leave children or pets alone in a parked vehicle.',
      'बंद खड़ी गाड़ी में बच्चों या जानवरों को कभी अकेला न छोड़ें।'
    ],

    [
      'Keep curtains closed by day and open windows at night.',
      'दिन में पर्दे बंद रखें और रात में खिड़कियाँ खोलें।'
    ],

    [
      'Dizzy, confused or very hot skin? Move to shade and call 108.',
      'चक्कर, उलझन या बहुत गर्म त्वचा हो तो छाँव में जाएँ और 108 पर कॉल करें।'
    ]

  ];

  const txt =
    document.getElementById(
      'adText'
    );

  const hi =
    document.getElementById(
      'adHi'
    );

  const num =
    document.getElementById(
      'adNum'
    );

  const dots =
    document.getElementById(
      'adDots'
    );

  if(!txt || !hi || !num || !dots)
    return;

  dots.innerHTML =
    tips.map(
      ()=>'<i></i>'
    ).join('');

  let i=0;

  function show(n){

    txt.classList.add(
      'swap'
    );

    hi.classList.add(
      'swap'
    );

    setTimeout(
      ()=>{

        txt.textContent =
          tips[n][0];

        hi.textContent =
          tips[n][1];

        num.textContent =
          `Tip ${n+1} of ${tips.length}`;

        [...dots.children]
          .forEach(
            (d,k)=>
              d.classList.toggle(
                'on',
                k===n
              )
          );

        txt.classList.remove(
          'swap'
        );

        hi.classList.remove(
          'swap'
        );

      },
      450
    );
  }

  show(0);

  setInterval(
    ()=>{
      i =
        (i+1)%tips.length;

      show(i);
    },
    7000
  );

  let userPaused =
    false;

  const tgl =
    document.getElementById(
      'adToggle'
    );

  v.addEventListener(
    'playing',
    ()=>{
      v.classList.add('on');

      if(tgl)
        tgl.textContent =
          '⏸ Pause';
    }
  );

  v.addEventListener(
    'error',
    ()=>{
      v.classList.remove('on');
    },
    true
  );

  const go =
    ()=>{
      if(!userPaused)
        v.play().catch(()=>{});
    };

  if(
    !matchMedia(
      '(prefers-reduced-motion:reduce)'
    ).matches
  ){

    go();

  }else{

    userPaused =
      true;

    if(tgl)
      tgl.textContent =
        '▶ Play';
  }

  document.addEventListener(
    'visibilitychange',
    ()=>{
      if(!document.hidden)
        go();
    }
  );

  v.addEventListener(
    'pause',
    ()=>{

      if(
        !userPaused &&
        !document.hidden
      ){

        go();
      }

    }
  );

  if(tgl){

    tgl.addEventListener(
      'click',
      ()=>{

        if(v.paused){

          userPaused =
            false;

          go();

          tgl.textContent =
            '⏸ Pause';

        }else{

          userPaused =
            true;

          v.pause();

          tgl.textContent =
            '▶ Play';
        }

      }
    );
  }

})();
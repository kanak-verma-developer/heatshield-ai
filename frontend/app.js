// HeatShield - simple public dashboard (Hindi / English).
(function () {
  'use strict';
  
  const API = location.protocol === 'file:'
    ? 'http://localhost:8000'
    : 'https://heatshield-ai-75xc.onrender.com';

  const CITIES = ['Moradabad', 'Delhi'];
  const COLORS = {safe:'#22c55e', caution:'#eab308', extreme_caution:'#f97316', danger:'#ef4444', extreme_danger:'#b91c1c'};
  const ORDER = ['safe', 'caution', 'extreme_caution', 'danger', 'extreme_danger'];
  const CITY_HI = {Moradabad:'मुरादाबाद', Delhi:'दिल्ली'};
  const ZONE_HI = {'Civil Lines':'सिविल लाइंस','Katghar':'कटघर','Majhola':'मझोला','Budh Bazaar':'बुध बाज़ार',
    'Rampur Road':'रामपुर रोड','Delhi Road':'दिल्ली रोड','New Moradabad':'न्यू मुरादाबाद','Moradabad Central':'मुरादाबाद सेंट्रल',
    'Galshaheed':'गलशहीद','Chandni Chowk':'चाँदनी चौक','Connaught Place':'कनॉट प्लेस','Karol Bagh':'करोल बाग','Dwarka':'द्वारका'};

  const T = {
    en: {
      tagline:'Heat safety for your city', uv:'UV index', aqi:'Air quality', sunrise:'Sunrise', sunset:'Sunset', hottest:'Hottest time today', best:'Best time to go out',
      dayTitle:'Today, hour by hour', daySub:'How hot it will feel through the day', nowLbl:'Now',
      bestTip:'Best time to go out', hotTip:'Hottest time', careTitle:'Who needs extra care', aidTitle:'Heat stroke: what to do',
      care:[['👵 Elderly','Check on them often. Keep them in a cool room with water nearby.'],['🧒 Children','Never leave them in a parked vehicle. Keep them hydrated and out of afternoon sun.'],['👷 Outdoor workers','Work early morning or evening. Rest in shade every hour and drink water.'],['🤰 Pregnant or ill','Avoid heat and exertion. Contact a doctor if you feel unwell.']],
      aidSigns:'Signs: very hot skin, confusion, fainting, fast pulse, headache or vomiting.',
      aid:['Call 108 immediately.','Move the person to shade or a cool room.','Cool the body with wet cloths, water or a fan.','Give sips of water only if the person is fully awake.'],
      uvN:['Low','Moderate','High','Very high','Extreme'],
      aqiN:['Good','Moderate','Unhealthy for sensitive people','Unhealthy','Very unhealthy','Hazardous'],
      aqiTip:['Air is clean.','Acceptable. Sensitive people should take care.','Children, elderly and people with asthma should limit time outside.','Everyone should reduce time and effort outdoors.','Avoid going out. Wear an N95 mask if you must.','Stay indoors. Wear an N95 mask if you must go out.'],
 now:'Right now in', feels:'Feels like', air:'Air temperature', hum:'Humidity', wind:'Wind',
      mapTitle:'Heat map', mapSub:'Tap a circle or a name to see that area', zoneFeels:'Feels like', updated:'Updated',
      fcTitle:'Next 6 hours', fcSub:'How hot it will feel', tipsTitle:'What you should do',
      sos:'🚑 Heatstroke emergency? Call 108', adBadge:'☀️ Heat safety awareness', pause:'⏸ Pause', play:'▶ Play', tipN:(a,b)=>'Tip '+a+' of '+b, loading:'Loading weather…',
      fail:'We cannot load the latest weather right now. Trying again shortly.',
      stale:(t)=>'Showing the last reading' + (t ? ' from ' + t : '') + '. New data is on its way.',
      fcNA:'Forecast is not available right now.',
      about:'About this page',
      aboutText:'“Feels like” combines temperature and humidity. Weather comes from Open-Meteo, a free weather service. Areas close to each other can show similar numbers.',
      credit:'Weather: Open-Meteo · Map © OpenStreetMap contributors',
      levels:{
        safe:['Comfortable','Normal activity is fine.'],
        caution:['Warm','Drink water often and rest in shade.'],
        extreme_caution:['Hot','Avoid long time in the sun. Tiredness and cramps are possible.'],
        danger:['Very hot','Stay out of the afternoon sun. Heat stroke is possible.'],
        extreme_danger:['Dangerous heat','Stay indoors. Heat stroke is likely if you go out.']
      }
    },
    hi: {
      tagline:'आपके शहर के लिए गर्मी से सुरक्षा', uv:'यूवी इंडेक्स', aqi:'हवा की गुणवत्ता', sunrise:'सूर्योदय', sunset:'सूर्यास्त', hottest:'आज सबसे गर्म समय', best:'बाहर जाने का सबसे अच्छा समय',
      dayTitle:'आज का दिन, घंटे-दर-घंटे', daySub:'दिन भर कितनी गर्मी महसूस होगी', nowLbl:'अभी',
      bestTip:'बाहर जाने का सबसे अच्छा समय', hotTip:'सबसे गर्म समय', careTitle:'किन्हें ज़्यादा ध्यान चाहिए', aidTitle:'लू लगने पर क्या करें',
      care:[['👵 बुज़ुर्ग','बार-बार हाल पूछें। उन्हें ठंडे कमरे में पानी के पास रखें।'],['🧒 बच्चे','बंद गाड़ी में कभी न छोड़ें। पानी पिलाते रहें और दोपहर की धूप से बचाएँ।'],['👷 बाहर काम करने वाले','सुबह जल्दी या शाम को काम करें। हर घंटे छाँव में आराम करें और पानी पिएं।'],['🤰 गर्भवती या बीमार','गर्मी और मेहनत से बचें। तबीयत ख़राब लगे तो डॉक्टर से मिलें।']],
      aidSigns:'लक्षण: बहुत गर्म त्वचा, उलझन, बेहोशी, तेज़ धड़कन, सिरदर्द या उल्टी।',
      aid:['तुरंत 108 पर कॉल करें।','व्यक्ति को छाँव या ठंडे कमरे में ले जाएँ।','गीले कपड़े, पानी या पंखे से शरीर ठंडा करें।','पानी की घूँट तभी दें जब व्यक्ति पूरी तरह होश में हो।'],
      uvN:['कम','मध्यम','ज़्यादा','बहुत ज़्यादा','अत्यधिक'],
      aqiN:['अच्छी','ठीक-ठाक','संवेदनशील लोगों के लिए हानिकारक','हानिकारक','बहुत हानिकारक','ख़तरनाक'],
      aqiTip:['हवा साफ़ है।','ठीक है। संवेदनशील लोग ध्यान रखें।','बच्चे, बुज़ुर्ग और अस्थमा के मरीज़ बाहर कम रहें।','सभी लोग बाहर कम समय और कम मेहनत करें।','बाहर जाने से बचें। जाना ज़रूरी हो तो N95 मास्क पहनें।','घर के अंदर रहें। बाहर जाना हो तो N95 मास्क पहनें।'],
 now:'अभी', feels:'महसूस होता है', air:'हवा का तापमान', hum:'नमी', wind:'हवा',
      mapTitle:'गर्मी का नक्शा', mapSub:'किसी गोले या नाम पर दबाकर उस इलाके की जानकारी देखें', zoneFeels:'महसूस होता है', updated:'अपडेट',
      fcTitle:'अगले 6 घंटे', fcSub:'कितनी गर्मी महसूस होगी', tipsTitle:'आपको क्या करना चाहिए',
      sos:'🚑 लू लगने की इमरजेंसी? 108 पर कॉल करें', adBadge:'☀️ गर्मी से बचाव की जानकारी', pause:'⏸ रोकें', play:'▶ चलाएँ', tipN:(a,b)=>'सुझाव '+a+' / '+b, loading:'मौसम लोड हो रहा है…',
      fail:'अभी ताज़ा मौसम लोड नहीं हो पा रहा। थोड़ी देर में फिर कोशिश होगी।',
      stale:(t)=>'आख़िरी जानकारी' + (t ? ' (' + t + ')' : '') + ' दिखा रहे हैं। नई जानकारी आ रही है।',
      fcNA:'अभी पूर्वानुमान उपलब्ध नहीं है।',
      about:'इस पेज के बारे में',
      aboutText:'“महसूस होता है” तापमान और नमी को मिलाकर बनता है। मौसम की जानकारी Open-Meteo (मुफ़्त मौसम सेवा) से आती है। पास-पास के इलाकों में आँकड़े एक जैसे हो सकते हैं।',
      credit:'मौसम: Open-Meteo · नक्शा © OpenStreetMap योगदानकर्ता',
      levels:{
        safe:['आरामदायक','सामान्य काम कर सकते हैं।'],
        caution:['गर्म','पानी पीते रहें और छाँव में आराम करें।'],
        extreme_caution:['बहुत गर्म','धूप में ज़्यादा देर न रहें। थकान और ऐंठन हो सकती है।'],
        danger:['ख़तरनाक गर्मी','दोपहर की धूप से बचें। लू लग सकती है।'],
        extreme_danger:['अत्यंत ख़तरनाक गर्मी','घर के अंदर रहें। बाहर जाने पर लू लगने की संभावना है।']
      }
    }
  };

  let lang = 'en', city = 'Moradabad', data = null, selected = null, lastGoodAt = 0, token = 0, timer = null, lastOk = true;

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const t = () => T[lang];
  const cityName = (c) => lang === 'hi' ? (CITY_HI[c] || c) : c;
  const zoneName = (n) => lang === 'hi' ? (ZONE_HI[n] || n) : n;
  const lvl = (k) => t().levels[k] || t().levels.safe;
  const col = (k) => COLORS[k] || COLORS.safe;
  const num = (x) => Math.round(x);

  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

  function fmtStamp(iso) {
    if (!iso || iso.length < 16) return '';
    let h = parseInt(iso.slice(11, 13), 10); const m = iso.slice(14, 16);
    const ap = h >= 12 ? 'pm' : 'am'; h = h % 12 || 12;
    return h + ':' + m + ' ' + ap;
  }

  // ------------------------------------------------------------- fetch
  async function refresh() {
    const tk = ++token;
    clearTimeout(timer);
    let ok = false;
    try {
      const r = await fetch(API + '/api/simple?city=' + encodeURIComponent(city), {cache: 'no-store'});
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const d = await r.json();
      if (tk !== token) return;
      data = d; lastGoodAt = Date.now(); ok = true;
      if (!selected || !d.zones.some((z) => z.id === selected)) {
        selected = d.zones.slice().sort((a, b) => b.feels_like - a.feels_like)[0].id;
      }
    } catch (e) {
      if (tk !== token) return;
    }
    render(ok);
    timer = setTimeout(refresh, ok ? 300000 : 30000);
  }

  // ------------------------------------------------------------- render
  function render(ok) {
    if (ok === undefined) ok = lastOk; else lastOk = ok;
    const L = t();
    document.documentElement.lang = lang;
    $('tagline').textContent = L.tagline; navLabels();
    $('cityTabs').innerHTML = CITIES.map((c) =>
      `<button type="button" role="tab" data-city="${c}" class="${c === city ? 'on' : ''}" aria-selected="${c === city}">${esc(cityName(c))}</button>`).join('');
    document.querySelectorAll('#langTabs button').forEach((b) => b.classList.toggle('on', b.dataset.lang === lang));
    $('sos').textContent = L.sos;
    if ($('adBadge')) videoLabels();
    $('foot').innerHTML = `<details><summary>${esc(L.about)}</summary><p>${esc(L.aboutText)}</p></details><div>${esc(L.credit)}</div>`;

    const notice = $('notice');
    if (!data) {
      notice.style.display = 'none';
      $('mainGrid').style.display = 'none';
      $('forecastCard').style.display = 'none';
      $('tipsCard').style.display = 'none';
      $('kpis').innerHTML = ''; if ($('ovBody')) $('ovBody').innerHTML = ''; $('dayCard').style.display = 'none'; $('careCard').style.display = 'none';
      $('hero').innerHTML = `<div class="loading" style="grid-column:1/-1">${esc(ok === false ? L.fail : L.loading)}</div>`;
      return;
    }
    if (ok === false) {
      notice.textContent = L.stale(fmtStamp(data.updated_at));
      notice.style.display = 'block';
    } else {
      notice.style.display = 'none';
    }

    renderHero(); renderOverview(); renderKpis(); renderTips(); renderDay(); renderMapArea(); renderForecast(); renderCare();
  }

  function renderHero() {
    const L = t(), n = data.city_now, c = col(n.level), lv = lvl(n.level);
    $('hero').innerHTML = `
      <div>
        <div class="lab">${esc(L.now)} ${esc(cityName(data.city))}</div>
        <div class="big" style="color:${c}">${num(n.feels_like)}°C</div>
        <div class="feels">${esc(L.feels)}</div>
        <div class="facts">
          <span>${esc(L.air)}: <b>${n.temp}°C</b></span>
          <span>${esc(L.hum)}: <b>${n.humidity}%</b></span>
          <span>${esc(L.wind)}: <b>${n.wind_kmh} km/h</b></span>
        </div>
        <div class="facts"><span>${esc(L.updated)}: <b>${esc(fmtStamp(data.updated_at) || '—')}</b></span></div>
      </div>
      <div class="levelbox" style="border-color:${c}"><b style="color:${c}">${esc(lv[0])}</b><p>${esc(lv[1])}</p></div>`;
  }

  function renderMapArea() {
    const L = t();
    $('mainGrid').style.display = '';
    $('mapTitle').textContent = L.mapTitle;
    $('mapSub').textContent = L.mapSub;
    $('legend').innerHTML = ORDER.map((k) => `<span><i style="background:${COLORS[k]}"></i>${esc(lvl(k)[0])}</span>`).join('');
    drawMap();
    $('zlist').innerHTML = data.zones.map((z) =>
      `<button type="button" class="zrow ${z.id === selected ? 'sel' : ''}" data-id="${esc(z.id)}"><i style="background:${col(z.level)}"></i>${esc(zoneName(z.name))}<span>${num(z.feels_like)}°</span></button>`).join('');
    const z = data.zones.find((q) => q.id === selected) || data.zones[0];
    const lv = lvl(z.level);
    $('zoneCard').innerHTML = `
      <div class="zonehead"><h2>${esc(zoneName(z.name))}</h2><span class="pill" style="background:${col(z.level)}">${esc(lv[0])}</span></div>
      <div class="zbig" style="color:${col(z.level)}">${num(z.feels_like)}°C</div>
      <div class="feels">${esc(L.zoneFeels)}</div>
      <div class="zline"><span>${esc(L.air)}</span><b>${z.temp}°C</b></div>
      <div class="zline"><span>${esc(L.hum)}</span><b>${z.humidity}%</b></div>
      <div class="zline"><span>${esc(L.wind)}</span><b>${z.wind_kmh} km/h</b></div>
      <div class="zmsg">${esc(lv[1])}</div>`;
  }

  // ------------------------------------------------------------- map
  // ---- sidebar: overview + quick-link labels (added by redesign) ----
  const OV = {
    en: {title:'Overview', city:'City', lang:'Language', rain:'Rain chance', sun:'Sunrise / Sunset', sos:'🚑 Call 108',
      nav:{now:'🌡️ Right now', tips:'✅ What to do', video:'🎬 Awareness', day:'📈 Today, hourly', map:'🗺️ Heat map', fc:'⏱️ Next 6 hours', care:'🩺 Who needs care'}},
    hi: {title:'एक नज़र में', city:'शहर', lang:'भाषा', rain:'बारिश की संभावना', sun:'सूर्योदय / सूर्यास्त', sos:'🚑 108 पर कॉल करें',
      nav:{now:'🌡️ अभी', tips:'✅ क्या करें', video:'🎬 जागरूकता', day:'📈 आज घंटे-दर-घंटे', map:'🗺️ गर्मी का नक्शा', fc:'⏱️ अगले 6 घंटे', care:'🩺 किन्हें ध्यान चाहिए'}}
  };

  function navLabels() {
    const o = OV[lang] || OV.en;
    const set = (id, v) => { const e = $(id); if (e) e.textContent = v; };
    set('lblCity', o.city); set('lblLang', o.lang); set('sideSos', o.sos);
    document.querySelectorAll('#nav a').forEach((a) => { if (o.nav[a.dataset.n]) a.textContent = o.nav[a.dataset.n]; });
  }

  function renderOverview() {
    const box = $('ovBody');
    if (!box || !data) return;
    const L = t(), o = OV[lang] || OV.en, n = data.city_now, c = col(n.level), lv = lvl(n.level);
    const ex = data.extras || {}, di = dayInfo();
    const row = (k, v, cc) => `<div class="ovr"><span>${esc(k)}</span><b${cc ? ' style="color:' + cc + '"' : ''}>${esc(v)}</b></div>`;
    let rows = '';
    const cur = ex.hourly && ex.hourly.find((q) => q.hour === ex.now_hour);
    if (cur && cur.uv != null) { const i = uvIdx(cur.uv); rows += row(L.uv, cur.uv + ' · ' + L.uvN[i], UVC[i]); }
    if (ex.aqi) { const i = aqiIdx(ex.aqi.us_aqi); rows += row(L.aqi, ex.aqi.us_aqi + ' · ' + L.aqiN[i], AQC[i]); }
    if (cur && cur.rain != null) rows += row(o.rain, cur.rain + '%');
    if (di) {
      rows += row(L.hottest, hr12(di.hot.hour) + ' · ' + num(di.hot.feels_like) + '°C', col(di.hot.level));
      if (di.best) rows += row(L.best, hr12(di.best.from) + ' – ' + hr12(di.best.to % 24), '#2dd4bf');
    }
    if (ex.sunrise && ex.sunset) rows += row(o.sun, hmFromIso(ex.sunrise) + ' / ' + hmFromIso(ex.sunset));
    box.innerHTML = `<div class="ovt">${esc(o.title)} · ${esc(cityName(data.city))}</div>
      <div class="ovbig" style="color:${c}">${num(n.feels_like)}°C</div>
      <span class="pill" style="background:${c}">${esc(lv[0])}</span>${rows}`;
  }

  const MW = 700, MH = 520;
  const mx = (lon) => (lon + 180) / 360;
  const my = (lat) => { const r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2; };

  function drawMap() {
    const svg = $('map'), zs = data.zones;
    const xs = zs.map((z) => mx(z.lon)), ys = zs.map((z) => my(z.lat));
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    const spanX = Math.max(maxX - minX, 1e-5), spanY = Math.max(maxY - minY, 1e-5);
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    const S = Math.min(MW / (spanX * 1.35), MH / (spanY * 1.35));
    const tz = Math.max(0, Math.min(18, Math.ceil(Math.log2(S / 256)))), n = Math.pow(2, tz), size = S / n;
    const x0 = cx - (MW / 2) / S, x1 = cx + (MW / 2) / S, y0 = cy - (MH / 2) / S, y1 = cy + (MH / 2) / S;
    const clamp = (v) => Math.max(0, Math.min(n - 1, v));
    let tiles = '';
    for (let tx = clamp(Math.floor(x0 * n) - 1); tx <= clamp(Math.floor(x1 * n) + 1); tx++) {
      for (let ty = clamp(Math.floor(y0 * n) - 1); ty <= clamp(Math.floor(y1 * n) + 1); ty++) {
        tiles += `<image href="https://${'abc'[(tx + ty) % 3]}.tile.openstreetmap.org/${tz}/${tx}/${ty}.png" x="${((tx / n - cx) * S + MW / 2).toFixed(1)}" y="${((ty / n - cy) * S + MH / 2).toFixed(1)}" width="${(size + 0.5).toFixed(1)}" height="${(size + 0.5).toFixed(1)}"/>`;
      }
    }
    const marks = zs.map((z) => {
      const x = ((mx(z.lon) - cx) * S + MW / 2).toFixed(1), y = ((my(z.lat) - cy) * S + MH / 2).toFixed(1);
      const sel = z.id === selected;
      return `<g class="zg ${sel ? 'sel' : ''}" data-id="${esc(z.id)}" transform="translate(${x} ${y})" tabindex="0" role="button" aria-label="${esc(zoneName(z.name))} ${num(z.feels_like)}">
        <circle r="24" fill="transparent"/>
        ${sel ? '<circle r="21" fill="none" stroke="#fff" stroke-width="3"/>' : ''}
        <circle r="16" fill="${col(z.level)}" stroke="#fff" stroke-width="2"/>
        <text class="zs" y="5">${num(z.feels_like)}</text>
        <text class="zn" y="-26">${esc(zoneName(z.name))}</text></g>`;
    }).join('');
    svg.innerHTML = `<g style="filter:brightness(.62) saturate(.85)" pointer-events="none">${tiles}</g>${marks}`;
  }

  // ------------------------------------------------------------- forecast + tips
  function renderForecast() {
    const L = t(), box = $('forecastCard');
    box.style.display = '';
    const rows = (data.forecast || []).map((p) => {
      const w = Math.max(6, Math.min(100, (p.feels_like - 15) / 35 * 100));
      return `<div class="frow"><span>${esc(p.label)}</span><div class="fbar"><i style="width:${w}%;background:${col(p.level)}"></i></div><b>${num(p.feels_like)}°C</b></div>`;
    }).join('');
    box.innerHTML = `<h2>${esc(L.fcTitle)}</h2><div class="sub">${esc(L.fcSub)}</div>${rows || `<div class="sub">${esc(L.fcNA)}</div>`}`;
  }

  function renderTips() {
    const L = t(), box = $('tipsCard');
    const tips = (data.advice && data.advice[lang]) || [];
    box.style.display = '';
    box.innerHTML = `<h2>${esc(L.tipsTitle)}</h2><ul class="tips">${tips.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`;
  }



  // ------------------------------------------------------------- KPIs, day chart, care
  const hr12 = (h) => (h % 12 || 12) + (h < 12 ? ' am' : ' pm');
  const hmFromIso = (s) => s ? fmtStamp(s) : '';
  const uvIdx = (v) => v < 3 ? 0 : v < 6 ? 1 : v < 8 ? 2 : v < 11 ? 3 : 4;
  const aqiIdx = (v) => v <= 50 ? 0 : v <= 100 ? 1 : v <= 150 ? 2 : v <= 200 ? 3 : v <= 300 ? 4 : 5;
  const UVC = ['#22c55e', '#eab308', '#f97316', '#ef4444', '#b91c1c'];
  const AQC = ['#22c55e', '#eab308', '#f97316', '#ef4444', '#a855f7', '#b91c1c'];

  function dayInfo() {
    const ex = data && data.extras, hs = ex && ex.hourly;
    if (!hs || hs.length < 6) return null;
    const hot = hs.reduce((a, b) => (b.feels_like > a.feels_like ? b : a));
    let best = null;
    for (let i = 0; i + 2 < hs.length; i++) {
      if (hs[i].hour < 5 || hs[i + 2].hour > 21) continue;
      const avg = (hs[i].feels_like + hs[i + 1].feels_like + hs[i + 2].feels_like) / 3;
      if (!best || avg < best.avg) best = {avg, from: hs[i].hour, to: hs[i + 2].hour + 1};
    }
    return {hs, hot, best};
  }

  function renderKpis() {
    const L = t(), ex = data.extras || {}, di = dayInfo(), cards = [];
    if (ex.hourly && ex.hourly.length) {
      const cur = ex.hourly.find((q) => q.hour === ex.now_hour);
      if (cur && cur.uv != null) { const i = uvIdx(cur.uv); cards.push(['☀️', L.uv, cur.uv, L.uvN[i], UVC[i]]); }
    }
    if (ex.aqi) { const i = aqiIdx(ex.aqi.us_aqi); cards.push(['🌫️', L.aqi, ex.aqi.us_aqi, L.aqiN[i], AQC[i]]); }
    if (di) {
      cards.push(['🔥', L.hottest, hr12(di.hot.hour), num(di.hot.feels_like) + '°C', col(di.hot.level)]);
      if (di.best) cards.push(['🌤️', L.best, hr12(di.best.from) + ' – ' + hr12(di.best.to % 24), '', '#2dd4bf']);
    }
    if (ex.sunrise) cards.push(['🌅', L.sunrise, hmFromIso(ex.sunrise), '', '']);
    if (ex.sunset) cards.push(['🌇', L.sunset, hmFromIso(ex.sunset), '', '']);
    $('kpis').innerHTML = cards.map((c) => `<div class="kpi"><div class="kl">${c[0]} ${esc(c[1])}</div><div class="kv" ${c[4] ? `style="color:${c[4]}"` : ''}>${esc(c[2])}</div><div class="ks">${esc(c[3])}</div></div>`).join('');
  }

  function renderDay() {
    const L = t(), box = $('dayCard'), di = dayInfo();
    if (!di) { box.style.display = 'none'; return; }
    box.style.display = '';
    const hs = di.hs, W = 700, H = 230, x0 = 38, x1 = W - 14, y0 = 16, y1 = H - 30;
    const lo = Math.floor(Math.min(...hs.map((p) => p.feels_like)) - 2), hi = Math.ceil(Math.max(...hs.map((p) => p.feels_like)) + 2);
    const X = (h) => x0 + (h / 23) * (x1 - x0), Y = (v) => y1 - ((v - lo) / (hi - lo)) * (y1 - y0);
    const path = hs.map((p, i) => (i ? 'L' : 'M') + X(p.hour).toFixed(1) + ' ' + Y(p.feels_like).toFixed(1)).join(' ');
    const grid = [0, 1, 2].map((k) => { const v = lo + (hi - lo) * k / 2; return `<line x1="${x0}" x2="${x1}" y1="${Y(v)}" y2="${Y(v)}" stroke="rgba(255,255,255,.08)"/><text x="4" y="${Y(v) + 4}">${Math.round(v)}°</text>`; }).join('');
    const xl = [0, 3, 6, 9, 12, 15, 18, 21].map((h) => `<text x="${X(h)}" y="${H - 8}" text-anchor="middle">${hr12(h)}</text>`).join('');
    const band = di.best ? `<rect x="${X(di.best.from)}" y="${y0}" width="${Math.max(4, X(Math.min(23, di.best.to)) - X(di.best.from))}" height="${y1 - y0}" fill="rgba(45,212,191,.14)"/>` : '';
    const dots = hs.map((p) => `<circle cx="${X(p.hour).toFixed(1)}" cy="${Y(p.feels_like).toFixed(1)}" r="${p.hour === di.hot.hour ? 6 : 3.5}" fill="${col(p.level)}"><title>${hr12(p.hour)}: ${num(p.feels_like)}°C</title></circle>`).join('');
    const nowH = data.extras.now_hour, nowL = `<line x1="${X(nowH)}" x2="${X(nowH)}" y1="${y0}" y2="${y1}" stroke="#fff" stroke-dasharray="4 4" opacity=".7"/><text x="${X(nowH)}" y="${y0 - 4}" text-anchor="middle" style="fill:#fff">${esc(L.nowLbl)}</text>`;
    box.innerHTML = `<h2>${esc(L.dayTitle)}</h2><div class="sub">${esc(L.daySub)}</div>
      <svg class="daychart" viewBox="0 0 ${W} ${H}" role="img">${grid}${band}<path d="${path}" fill="none" stroke="#2dd4bf" stroke-width="2.5"/>${dots}${nowL}${xl}</svg>
      <div class="daytips"><div class="daytip">${esc(L.bestTip)}<b style="color:#2dd4bf">${di.best ? hr12(di.best.from) + ' – ' + hr12(di.best.to % 24) : '—'}</b></div>
      <div class="daytip">${esc(L.hotTip)}<b style="color:${col(di.hot.level)}">${hr12(di.hot.hour)} · ${num(di.hot.feels_like)}°C</b></div></div>`;
  }

  function renderCare() {
    const L = t(), box = $('careCard'), aq = data.extras && data.extras.aqi;
    box.style.display = '';
    const air = aq ? `<div class="subh">${esc(L.aqi)}: ${aq.us_aqi} · ${esc(L.aqiN[aqiIdx(aq.us_aqi)])}</div><div class="sub">${esc(L.aqiTip[aqiIdx(aq.us_aqi)])}</div>` : '';
    box.innerHTML = `<h2>${esc(L.careTitle)}</h2><div class="care" style="margin-top:10px">${L.care.map((c) => `<div><b>${esc(c[0])}</b>${esc(c[1])}</div>`).join('')}</div>
      ${air}<div class="subh">${esc(L.aidTitle)}</div><div class="sub" style="margin-bottom:4px">${esc(L.aidSigns)}</div>
      <ol class="aid">${L.aid.map((a) => `<li>${esc(a)}</li>`).join('')}</ol>`;
  }

  // ------------------------------------------------------------- awareness video
  const VT = [
    ['Drink water every 20 minutes, even if you do not feel thirsty.','हर 20 मिनट में पानी पिएं, प्यास न लगे तब भी।'],
    ['Avoid going outside between 12 pm and 4 pm on hot days.','गर्मी में दोपहर 12 से 4 बजे तक बाहर जाने से बचें।'],
    ['Wear light, loose cotton clothes and cover your head.','हल्के, ढीले सूती कपड़े पहनें और सिर ढककर रखें।'],
    ['Take ORS, lemon water or buttermilk to replace lost salts.','ORS, नींबू पानी या छाछ लें, इससे शरीर में नमक-पानी की कमी पूरी होती है।'],
    ['Check on elderly neighbours, children and pets.','बुज़ुर्गों, बच्चों और पालतू जानवरों का ध्यान रखें।'],
    ['Never leave children or pets alone in a parked vehicle.','बंद खड़ी गाड़ी में बच्चों या जानवरों को कभी अकेला न छोड़ें।'],
    ['Keep curtains closed by day and open windows at night.','दिन में पर्दे बंद रखें और रात में खिड़कियाँ खोलें।'],
    ['Dizzy, confused or very hot skin? Move to shade and call 108.','चक्कर, उलझन या बहुत गर्म त्वचा हो तो छाँव में जाएँ और 108 पर कॉल करें।']
  ];
  let vi = 0, userPaused = false;

  function videoLabels() {
    const L = t(), v = $('adVideo'), tg = $('adToggle');
    $('adBadge').textContent = L.adBadge;
    $('adSos').textContent = L.sos;
    if (tg) tg.textContent = (v && !v.paused && !userPaused) ? L.pause : L.play;
    showTip(false);
  }

  function showTip(animate) {
    const L = t(), p = $('adText');
    const apply = () => {
      p.textContent = VT[vi][lang === 'hi' ? 1 : 0];
      $('adNum').textContent = L.tipN(vi + 1, VT.length);
      [...$('adDots').children].forEach((d, k) => d.classList.toggle('on', k === vi));
      p.classList.remove('swap');
    };
    if (animate) { p.classList.add('swap'); setTimeout(apply, 400); } else apply();
  }

  function initVideo() {
    const v = $('adVideo'), tg = $('adToggle');
    if (!v) return;
    $('adDots').innerHTML = VT.map(() => '<i></i>').join('');
    const play = () => { if (userPaused) return; try { const pr = v.play && v.play(); if (pr && pr.catch) pr.catch(() => {}); } catch (e) {} };
    v.addEventListener('playing', () => { v.classList.add('on'); videoLabels(); });
    v.addEventListener('error', () => v.classList.remove('on'), true);
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) userPaused = true; else play();
    document.addEventListener('visibilitychange', () => { if (!document.hidden) play(); });
    if (tg) tg.addEventListener('click', () => {
      if (v.paused || userPaused) { userPaused = false; play(); } else { userPaused = true; v.pause(); }
      videoLabels();
    });
    videoLabels();
    setInterval(() => { vi = (vi + 1) % VT.length; showTip(true); }, 7000);
  }

  // ------------------------------------------------------------- events
  document.addEventListener('click', (e) => {
    const cb = e.target.closest('#cityTabs button');
    if (cb) { setCity(cb.dataset.city); return; }
    const lb = e.target.closest('#langTabs button');
    if (lb) { lang = lb.dataset.lang; store('hs_lang', lang); render(); return; }
    const z = e.target.closest('[data-id]');
    if (z && data) { selected = z.dataset.id; renderMapArea(); }
  });
  document.addEventListener('keydown', (e) => {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.classList && e.target.classList.contains('zg')) {
      e.preventDefault(); selected = e.target.dataset.id; renderMapArea();
    }
  });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && Date.now() - lastGoodAt > 120000) refresh();
  });

  function setCity(c) {
    if (!CITIES.includes(c) || c === city) return;
    city = c; data = null; selected = null;
    history.replaceState(null, '', '#' + c);
    render(); refresh();
  }

  // ------------------------------------------------------------- start
  (function init() {
    const saved = load('hs_lang');
    lang = saved === 'hi' || saved === 'en' ? saved : ((navigator.language || '').toLowerCase().startsWith('hi') ? 'hi' : 'en');
    const h = decodeURIComponent((location.hash || '').replace('#', ''));
    if (CITIES.includes(h)) city = h;
    initVideo(); render(); refresh();
  })();
})();

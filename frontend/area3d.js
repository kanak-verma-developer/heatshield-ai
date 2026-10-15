(function () {
  if (window.__area3d) return;
  window.__area3d = 1;

  var st = document.createElement('style');
  st.textContent = [
    '.a3d-col{align-self:stretch;display:flex;flex-direction:column;gap:16px;min-width:0}',
    '.a3d-card{position:relative;flex:1;min-height:340px;border-radius:16px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);backdrop-filter:blur(10px);box-shadow:0 8px 30px rgba(0,0,0,.25);overflow:hidden}',
    '.a3d-stage{position:absolute;inset:0;transform:scale(.88);perspective:1300px;display:flex;align-items:center;justify-content:center}',
    '.a3d-world{position:relative;width:300px;height:300px;transform-style:preserve-3d;transform:rotateX(58deg) rotateZ(-30deg);animation:a3dspin 30s linear infinite}',
    '.a3d-stage:hover .a3d-world{animation-play-state:paused}',
    '@keyframes a3dspin{to{transform:rotateX(58deg) rotateZ(330deg)}}',
    '@media(prefers-reduced-motion:reduce){.a3d-world{animation:none}}',
    '.a3d-floor{position:absolute;inset:-18px;border-radius:14px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.12)}',
    '.a3d-bar{position:absolute;transform-style:preserve-3d;transition:transform .25s}',
    '.a3d-bar:hover{transform:translateZ(16px)}',
    '.a3d-bar>i{position:absolute;display:block}',
    '.a3d-tip{position:absolute;left:50%;top:14px;transform:translateX(-50%);padding:4px 12px;border-radius:999px;background:rgba(0,0,0,.65);color:#fff;font:600 13px system-ui,sans-serif;opacity:0;pointer-events:none;transition:opacity .15s;white-space:nowrap;z-index:2}',
    '@media(max-width:980px){.a3d-card{flex:none;height:260px;min-height:260px}.a3d-stage{transform:scale(.8)}}'
  ].join('\n');
  document.head.appendChild(st);

  var card, world, tip, last = '';

  function tcol(t) {
    return t < 28 ? '#1fc16b' : t < 35 ? '#e8c32a' : t < 41 ? '#f08a24' : '#e5413a';
  }

  function setup() {
    var heads = [].slice.call(document.querySelectorAll('h1,h2,h3,h4'));
    var h = heads.filter(function (x) { return /heat map/i.test(x.textContent); })[0];
    if (!h) return false;
    var c = h;
    while (c.parentElement && c.parentElement !== document.body) {
      var p = c.parentElement, d = getComputedStyle(p).display;
      if ((d === 'grid' || d === 'flex') && p.children.length >= 2 && c.nextElementSibling && c.offsetHeight > 300) break;
      c = p;
    }
    var right = c.nextElementSibling;
    if (!right || c.offsetHeight <= 300) return false;
    card = c;
    var wrap = document.createElement('div');
    wrap.className = 'a3d-col';
    right.parentNode.insertBefore(wrap, right);
    wrap.appendChild(right);
    var box = document.createElement('div');
    box.className = 'a3d-card';
    box.innerHTML = '<div class="a3d-stage"><div class="a3d-world"><div class="a3d-floor"></div></div></div><div class="a3d-tip"></div>';
    wrap.appendChild(box);
    world = box.querySelector('.a3d-world');
    tip = box.querySelector('.a3d-tip');
    return true;
  }

  function dotColor(el) {
    var found = null;
    el.querySelectorAll('*').forEach(function (k) {
      if (found) return;
      var b = getComputedStyle(k).backgroundColor;
      if (b && b !== 'rgba(0, 0, 0, 0)' && k.offsetWidth > 0 && k.offsetWidth <= 16) found = b;
    });
    return found;
  }

  function read() {
    var seen = {}, out = [];
    function take(el) {
      var txt = el.textContent.replace(/\s+/g, ' ').trim();
      if (txt.length > 40) return;
      var m = txt.match(/^(.*\D)\s*(-?\d+(?:\.\d+)?)\s*\u00b0/);
      if (!m) return;
      var n = m[1].trim();
      if (!n || seen[n]) return;
      seen[n] = 1;
      out.push({ n: n, t: parseFloat(m[2]), c: dotColor(el) });
    }
    card.querySelectorAll('[data-id]').forEach(take);
    if (!out.length) card.querySelectorAll('button,li,a,div').forEach(take);
    return out;
  }

  function face(css, c, sh) {
    var f = document.createElement('i');
    f.style.cssText = css + ';background:linear-gradient(rgba(0,0,0,' + sh + '),rgba(0,0,0,' + sh + ')),' + c;
    return f;
  }

  function render() {
    var list = read();
    var sig = JSON.stringify(list);
    if (!list.length || sig === last) return;
    last = sig;
    [].slice.call(world.querySelectorAll('.a3d-bar')).forEach(function (n) { n.remove(); });
    var cols = Math.ceil(Math.sqrt(list.length));
    var cell = 300 / cols, s = Math.round(cell * 0.62);
    list.forEach(function (d, i) {
      var x = (i % cols) * cell + (cell - s) / 2;
      var y = Math.floor(i / cols) * cell + (cell - s) / 2;
      var h = Math.min(180, Math.max(45, 45 + (d.t - 15) * 4));
      var c = d.c || tcol(d.t);
      var b = document.createElement('div');
      b.className = 'a3d-bar';
      b.style.cssText = 'left:' + x + 'px;top:' + y + 'px;width:' + s + 'px;height:' + s + 'px';
      b.appendChild(face('left:0;top:0;width:' + s + 'px;height:' + s + 'px;transform:translateZ(' + h + 'px)', c, 0));
      b.appendChild(face('left:0;top:' + s + 'px;width:' + s + 'px;height:' + h + 'px;transform-origin:top;transform:rotateX(90deg)', c, 0.25));
      b.appendChild(face('left:0;top:-' + h + 'px;width:' + s + 'px;height:' + h + 'px;transform-origin:bottom;transform:rotateX(-90deg)', c, 0.45));
      b.appendChild(face('left:' + s + 'px;top:0;width:' + h + 'px;height:' + s + 'px;transform-origin:left;transform:rotateY(-90deg)', c, 0.4));
      b.appendChild(face('left:-' + h + 'px;top:0;width:' + h + 'px;height:' + s + 'px;transform-origin:right;transform:rotateY(90deg)', c, 0.55));
      b.addEventListener('mouseenter', function () {
        tip.textContent = d.n + ' \u00b7 ' + d.t + '\u00b0';
        tip.style.opacity = 1;
      });
      b.addEventListener('mouseleave', function () { tip.style.opacity = 0; });
      world.appendChild(b);
    });
  }

  var tries = 0;
  var timer = setInterval(function () {
    tries++;
    if (setup()) {
      clearInterval(timer);
      render();
      var pending;
      new MutationObserver(function () {
        clearTimeout(pending);
        pending = setTimeout(render, 400);
      }).observe(card, { childList: true, subtree: true, characterData: true });
    } else if (tries > 60) {
      clearInterval(timer);
    }
  }, 500);
})();

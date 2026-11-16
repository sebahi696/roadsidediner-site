/* Live menu: pages are pre-built for search engines, then refreshed here from the same
   database the app and admin panel use, so admin changes show on the next page load. */
(function () {
  var C = window.RS; if (!C || !window.fetch) return;
  var H = { apikey: C.key, Authorization: 'Bearer ' + C.key };
  function get(p) { return fetch(C.url + '/rest/v1/' + p, { headers: H }).then(function (r) { if (!r.ok) throw r; return r.json(); }); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function img(p) { return p ? C.url + '/storage/v1/object/public/menu/' + p : ''; }
  var ar = C.L === 'ar';
  function nm(o) { return (ar && o.name_ar) ? o.name_ar : o.name_en; }
  function ds(i) { return (ar && i.desc_ar) ? i.desc_ar : (i.desc_en || ''); }
  function pr(i) { var p = '$' + Number(i.price).toFixed(2).replace('.00', ''); return i.from_price ? C.t.from + ' ' + p : p; }
  function card(i, off, br) {
    var na = '';
    if (off[i.id]) {
      var names = br.filter(function (b) { return off[i.id][b.id]; }).map(nm).join(', ');
      if (names) na = '<p class="na">' + esc(C.t.notAt) + ' ' + esc(names) + '</p>';
    }
    var tag = (i.tag || i.is_deal) ? '<span class="tag">' + esc(i.tag || C.t.deal) + '</span>' : '';
    return '<article class="item" data-id="' + i.id + '"><div class="ph"><img src="' + img(i.thumb_path || i.image_path) + '" alt="' + esc(nm(i)) +
      '" loading="lazy" decoding="async" width="400" height="300">' + tag + '</div><div class="tx"><h3>' + esc(nm(i)) + '</h3><p>' + esc(ds(i)) + '</p>' + na +
      '<span class="pr" dir="ltr">' + esc(pr(i)) + '</span></div></article>';
  }
  Promise.all([
    get('branches?select=id,name_en,name_ar,phone,opens,closes,sort&order=sort'),
    get('categories?select=id,name_en,name_ar,sort&active=eq.true&order=sort'),
    get('items?select=id,category_id,name_en,name_ar,desc_en,desc_ar,price,from_price,image_path,thumb_path,tag,is_deal,sort&active=eq.true&order=sort'),
    get('item_branch?select=item_id,branch_id,available&available=eq.false')
  ]).then(function (r) {
    var br = r[0], cats = r[1], items = r[2], off = {};
    r[3].forEach(function (a) { (off[a.item_id] = off[a.item_id] || {})[a.branch_id] = 1; });
    var byId = {}; items.forEach(function (i) { byId[i.id] = i; });

    // full menu page: rebuild sections + category chips
    var menu = document.getElementById('menu-live');
    if (menu) {
      var html = '', chips = '';
      cats.forEach(function (c) {
        var its = items.filter(function (i) { return i.category_id === c.id; });
        if (!its.length) return;
        chips += '<a href="#c' + c.id + '">' + esc(nm(c)) + '</a>';
        html += '<section id="c' + c.id + '" class="cat"><h2>' + esc(nm(c)) + '</h2><div class="grid">' + its.map(function (i) { return card(i, off, br); }).join('') + '</div></section>';
      });
      if (html) { menu.innerHTML = html; var ch = document.querySelector('.chips'); if (ch) ch.innerHTML = chips; }
    }
    // any other item cards (home favourites): refresh or drop removed items
    document.querySelectorAll('#fav .item[data-id]').forEach(function (el) {
      var i = byId[el.getAttribute('data-id')];
      if (!i) { el.remove(); return; }
      var tmp = document.createElement('div'); tmp.innerHTML = card(i, off, br); el.replaceWith(tmp.firstChild);
    });
    // branch hours + phones
    br.forEach(function (b) {
      document.querySelectorAll('[data-hours="' + b.id + '"]').forEach(function (el) { el.textContent = b.opens.slice(0, 5) + ' – ' + b.closes.slice(0, 5); });
      document.querySelectorAll('[data-phone="' + b.id + '"]').forEach(function (el) { el.textContent = b.phone; });
    });
  }).catch(function () { /* keep the pre-built content */ });
})();

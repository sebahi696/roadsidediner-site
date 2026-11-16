#!/usr/bin/env python3
"""Builds the public Roadside website (roadsidediner.app) as static HTML from the live
Supabase catalog.  usage: python3 web-site/build.py [out_dir]   (default web-site/dist)

English pages at /, Arabic at /ar/. Everything is plain HTML + one CSS file so Google,
AI search engines and slow phones all get the full content without running JavaScript."""
import datetime as dt, html, json, os, shutil, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist'
SITE = json.loads((ROOT / 'site.json').read_text())
CFG = json.loads((REPO / 'config/prod.json').read_text())
D = SITE['domain']
TODAY = dt.date.today().isoformat()
E = lambda s: html.escape(str(s or ''), quote=True)


# ---------------------------------------------------------------- data
def rest(path):
    req = urllib.request.Request(f"{CFG['SUPABASE_URL']}/rest/v1/{path}",
                                 headers={'apikey': CFG['SUPABASE_KEY'], 'Authorization': 'Bearer ' + CFG['SUPABASE_KEY']})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def img(path):
    return f"{CFG['SUPABASE_URL']}/storage/v1/object/public/menu/{path}" if path else ''

branches = rest('branches?select=id,name_en,name_ar,area_en,area_ar,phone,lat,lng,opens,closes,sort&order=sort')
cats = rest('categories?select=id,name_en,name_ar,sort&active=eq.true&order=sort')
items = rest('items?select=id,category_id,name_en,name_ar,desc_en,desc_ar,price,from_price,image_path,thumb_path,tag,is_deal,sort&active=eq.true&order=sort')
avail = rest('item_branch?select=item_id,branch_id,available')
off = {}  # item_id -> set of branch ids where it is NOT available
for a in avail:
    if a['available'] is False:
        off.setdefault(a['item_id'], set()).add(a['branch_id'])
by_cat = {c['id']: [i for i in items if i['category_id'] == c['id']] for c in cats}
cats = [c for c in cats if by_cat[c['id']]]
SLUG = {'hadath': 'karout-mall-hadath', 'jnah': 'centro-mall-jnah', 'mansourieh': 'town-village-mansourieh'}
for b in branches:
    b['slug'] = SLUG.get(b['id'], b['id'])
    b['tel'] = '+' + ''.join(ch for ch in b['phone'] if ch.isdigit())
    b['o'], b['c'] = b['opens'][:5], b['closes'][:5]

# ---------------------------------------------------------------- copy
T = {
 'en': dict(
  dir='ltr', other='ar', other_label='عربي', home='Home', menu='Menu', locs='Locations', app='App', faq='FAQ',
  tagline='Your pit stop for tasty delights',
  title_home='The Roadside Diner | American Burgers & Fried Chicken in Beirut',
  desc_home='American diner in Lebanon: smash-good burgers, crispy chicken, loaded fries and shakes. 3 branches – Karout Mall Hadath, Centro Mall Jnah, The Town Village Mansourieh. Order delivery or pickup.',
  hero='Burgers, crispy chicken & loaded fries.',
  hero_sub='An American roadside diner in Lebanon, with three branches around Beirut. Eat in, pick up or get it delivered.',
  see_menu='See the menu', find='Find a branch', get_app='Get the app',
  open_daily='Open daily', call='Call', directions='Directions', from_='from', deal='Deal',
  why=[('🍔', 'Built to share', 'Combos for two, loaded fries and our viral Mozzarella Breaks.'),
       ('⚡', 'Fast pit stop', 'Delivery and pickup from three branches, hot and on time.'),
       ('⭐', 'Road Points', 'Earn points on every app order and turn them into free food.')],
  popular='Fan favourites', all_menu='Full menu',
  title_menu='Menu & Prices | The Roadside Diner Lebanon',
  desc_menu='Full Roadside Diner menu with prices in USD: burgers, fried chicken, appetizers, salads, pasta, kids meals, mains, desserts, shakes and drinks.',
  menu_h='Our menu', menu_note='Prices in US dollars and may vary slightly between branches. Some items are not served at every branch.',
  not_at='Not available at',
  title_locs='Locations & Opening Hours | The Roadside Diner',
  desc_locs='Find The Roadside Diner near you: Karout Mall (Al Hadath), Centro Mall (Jnah) and The Town Village (Mansourieh). Phone numbers, opening hours and directions.',
  locs_h='Our branches', hours='Opening hours', phone='Phone', order_here='Order from this branch in the app',
  delivery='Delivery & pickup available. Delivery areas and fees are shown in the app.',
  title_app='Roadside App – Order, Track & Earn Rewards',
  desc_app='Order from The Roadside Diner with the Roadside app: live order tracking, Road Points rewards and the Roadside Rush game. Android and iPhone, English and Arabic.',
  app_h='The Roadside app', app_sub='Order in a few taps, follow your order live, earn Road Points on every order and play Roadside Rush for weekly prizes.',
  app_pts=['Full menu with customisations and combos', 'Delivery or pickup from the nearest branch', 'Live order tracking with notifications', 'Road Points rewards and app-only deals', 'English and Arabic'],
  soon='Coming soon to Google Play and the App Store', gp='Get it on Google Play', as_='Download on the App Store',
  title_faq='FAQ | The Roadside Diner',
  desc_faq='Answers about The Roadside Diner: branches, opening hours, delivery, ordering, payment, kids menu and the Roadside app.',
  faq_h='Frequently asked questions',
  privacy='Privacy', terms='Terms', delete='Delete account', rights='All rights reserved.',
  nf_h='Wrong turn!', nf_p="This page doesn't exist. Let's get you back on the road.",
 ),
 'ar': dict(
  dir='rtl', other='en', other_label='English', home='الرئيسية', menu='القائمة', locs='الفروع', app='التطبيق', faq='أسئلة',
  tagline='محطتك للأكل الطيّب',
  title_home='ذا رود سايد داينر | برغر ودجاج مقرمش أميركي في بيروت',
  desc_home='داينر أميركي في لبنان: برغر، دجاج مقرمش، بطاطا محمّلة وميلك شيك. ٣ فروع – كاروت مول الحدث، سنترو مول الجناح، ذا تاون فيلاج المنصورية. توصيل أو استلام.',
  hero='برغر، دجاج مقرمش وبطاطا محمّلة.',
  hero_sub='داينر أميركي على الطريق في لبنان، بثلاثة فروع حول بيروت. كُل عنا، استلم طلبك أو خلّيه يوصلك.',
  see_menu='شوف القائمة', find='لاقي فرع', get_app='نزّل التطبيق',
  open_daily='مفتوح يومياً', call='اتصل', directions='الاتجاهات', from_='من', deal='عرض',
  why=[('🍔', 'للمشاركة', 'عروض لشخصين، بطاطا محمّلة وموزاريلا بريكس الشهيرة.'),
       ('⚡', 'محطة سريعة', 'توصيل واستلام من ثلاثة فروع، سخن وعلى الوقت.'),
       ('⭐', 'نقاط رود', 'اجمع نقاط على كل طلب من التطبيق وبدّلها بأكل مجاني.')],
  popular='الأكثر طلباً', all_menu='القائمة الكاملة',
  title_menu='القائمة والأسعار | ذا رود سايد داينر لبنان',
  desc_menu='قائمة ذا رود سايد داينر الكاملة مع الأسعار بالدولار: برغر، دجاج مقلي، مقبلات، سلطات، معكرونة، وجبات أطفال، أطباق رئيسية، حلويات، ميلك شيك ومشروبات.',
  menu_h='قائمتنا', menu_note='الأسعار بالدولار الأميركي وقد تختلف قليلاً بين الفروع. بعض الأصناف غير متوفرة في كل الفروع.',
  not_at='غير متوفر في',
  title_locs='الفروع وأوقات الدوام | ذا رود سايد داينر',
  desc_locs='لاقي أقرب فرع لذا رود سايد داينر: كاروت مول (الحدث)، سنترو مول (الجناح) وذا تاون فيلاج (المنصورية). أرقام الهاتف، أوقات الدوام والاتجاهات.',
  locs_h='فروعنا', hours='أوقات الدوام', phone='الهاتف', order_here='اطلب من هالفرع عبر التطبيق',
  delivery='التوصيل والاستلام متوفّران. مناطق التوصيل والرسوم تظهر في التطبيق.',
  title_app='تطبيق رود سايد – اطلب، تابع واربح',
  desc_app='اطلب من ذا رود سايد داينر عبر تطبيق رود سايد: تتبّع الطلب مباشرة، نقاط رود ولعبة رود سايد راش. على أندرويد وآيفون، بالعربي والإنكليزي.',
  app_h='تطبيق رود سايد', app_sub='اطلب بكم كبسة، تابع طلبك مباشرة، اجمع نقاط رود على كل طلب والعب رود سايد راش لجوائز أسبوعية.',
  app_pts=['القائمة كاملة مع الإضافات والعروض', 'توصيل أو استلام من أقرب فرع', 'تتبّع الطلب مباشرة مع إشعارات', 'نقاط رود وعروض حصرية للتطبيق', 'عربي وإنكليزي'],
  soon='قريباً على Google Play وApp Store', gp='حمّله من Google Play', as_='حمّله من App Store',
  title_faq='أسئلة شائعة | ذا رود سايد داينر',
  desc_faq='أجوبة عن ذا رود سايد داينر: الفروع، أوقات الدوام، التوصيل، الطلب، الدفع، قائمة الأطفال وتطبيق رود سايد.',
  faq_h='أسئلة شائعة',
  privacy='الخصوصية', terms='الشروط', delete='حذف الحساب', rights='جميع الحقوق محفوظة.',
  nf_h='ضيّعت الطريق!', nf_p='هالصفحة مش موجودة. يلّا نرجّعك عالطريق.',
 ),
}

def bname(b, L): return b['name_ar'] if L == 'ar' else b['name_en']
def barea(b, L): return b['area_ar'] if L == 'ar' else b['area_en']

def faqs(L):
    bl = ' · '.join(f"{bname(b, L)} ({barea(b, L)})" for b in branches)
    hrs = '; '.join(f"{bname(b, L)} {b['o']}–{b['c']}" for b in branches)
    if L == 'ar':
        return [
         ('وين فروع ذا رود سايد داينر؟', f'عنا ثلاثة فروع حول بيروت: {bl}.'),
         ('شو أوقات الدوام؟', f'كل الفروع مفتوحة يومياً: {hrs}.'),
         ('في توصيل؟', 'إيه، منوصّل من الفروع الثلاثة لمناطق بيروت وجبل لبنان. مناطق التوصيل والرسوم بتبيّن بالتطبيق حسب موقعك. وفيك تستلم طلبك من الفرع.'),
         ('كيف بطلب؟', 'أسهل طريقة هي تطبيق رود سايد. فيك كمان تتصل بالفرع مباشرة.'),
         ('كيف بدفع؟', 'حالياً الدفع نقداً عند الاستلام أو التوصيل. الدفع الإلكتروني جايي قريباً.'),
         ('في قائمة للأولاد؟', 'إيه، ركن الأطفال فيه وجبات مع بطاطا، براوني وعصير.'),
         ('في خيارات خفيفة؟', 'إيه، عنا قائمة خفيفة فيها برغر فِت أند لايت، سلطات وأطباق مشوية (مش بكل الفروع).'),
         ('شو هي نقاط رود؟', 'نقاط بتجمعها على كل طلب من التطبيق وبتبدّلها بمكافآت. وفي كمان لعبة رود سايد راش بالتطبيق مع جائزة أسبوعية.'),
         ('بالدولار ولا بالليرة؟', 'الأسعار بالدولار الأميركي.'),
        ]
    return [
     ('Where is The Roadside Diner?', f'We have three branches around Beirut: {bl}.'),
     ('What are your opening hours?', f'All branches are open every day: {hrs}.'),
     ('Do you deliver?', 'Yes. We deliver from all three branches across Beirut and Mount Lebanon. The app shows the delivery areas and fee for your location. You can also order for pickup.'),
     ('How do I order?', 'The easiest way is the Roadside app. You can also call your nearest branch directly.'),
     ('How can I pay?', 'Right now you pay cash on delivery or at pickup. Online payment is coming soon.'),
     ('Do you have a kids menu?', 'Yes – the Kids Corner has meals served with fries, a brownie and juice.'),
     ('Do you have lighter options?', 'Yes – our Light Menu has Fit & Light burgers, salads and grilled dishes (not served at every branch).'),
     ('What are Road Points?', 'Points you earn on every app order and exchange for rewards. The app also has the Roadside Rush game with a weekly prize.'),
     ('Are prices in dollars?', 'Yes, menu prices are in US dollars.'),
    ]

# ---------------------------------------------------------------- layout
def url(L, p=''):  # p like '' | 'menu/' | 'locations/x/'
    return ('/ar/' if L == 'ar' else '/') + p

GA = SITE.get('ga4_id', '').strip()
def head(L, title, desc, path, extra_ld=(), og_img='/assets/og.jpg'):
    alt = 'ar' if L == 'en' else 'en'
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False, separators=(",", ":"))}</script>' for x in extra_ld)
    ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script><script>window.dataLayer=window.dataLayer||[];'
          f'function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA}");</script>') if GA else ''
    gsc = f'<meta name="google-site-verification" content="{E(SITE["gsc_meta"])}">' if SITE.get('gsc_meta') else ''
    return f'''<!doctype html><html lang="{L}" dir="{T[L]['dir']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)}</title>
<meta name="description" content="{E(desc)}"><link rel="canonical" href="{D}{url(L, path)}">
<link rel="alternate" hreflang="en" href="{D}{url('en', path)}"><link rel="alternate" hreflang="ar" href="{D}{url('ar', path)}"><link rel="alternate" hreflang="x-default" href="{D}{url('en', path)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{E(SITE['name'])}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{D}{url(L, path)}"><meta property="og:image" content="{D}{og_img}"><meta property="og:locale" content="{'ar_LB' if L == 'ar' else 'en_US'}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#F05424">
<link rel="icon" href="/assets/favicon.png" type="image/png"><link rel="apple-touch-icon" href="/assets/icon-192.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Cairo:wght@400;700;900&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css?v={TODAY}">{gsc}{ga}{ld}</head>
<body class="{L}"><a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap nav"><a class="brand" href="{url(L)}"><img src="/assets/logo.png" alt="The Roadside Diner" width="116" height="40"></a>
<nav><a href="{url(L, 'menu/')}">{T[L]['menu']}</a><a href="{url(L, 'locations/')}">{T[L]['locs']}</a><a href="{url(L, 'app/')}">{T[L]['app']}</a><a href="{url(L, 'faq/')}">{T[L]['faq']}</a>
<a class="lang" href="{url(alt, path)}" hreflang="{alt}" lang="{alt}">{T[L]['other_label']}</a></nav></div></header><main id="main">'''

def foot(L):
    t = T[L]
    br = ''.join(f'<li><a href="{url(L, "locations/" + b["slug"] + "/")}">{E(bname(b, L))} – {E(barea(b, L))}</a> · <a href="tel:{b["tel"]}" dir="ltr">{E(b["phone"])}</a></li>' for b in branches)
    return f'''</main><footer class="foot"><div class="wrap cols"><div><img src="/assets/logo.png" alt="" width="116" height="40"><p>{t['tagline']}</p>
<p class="soc"><a href="{SITE['instagram']}" rel="noopener">Instagram</a> · <a href="{SITE['facebook']}" rel="noopener">Facebook</a> · <a href="{SITE['tiktok']}" rel="noopener">TikTok</a></p></div>
<div><h3>{t['locs']}</h3><ul>{br}</ul></div><div><h3>{t['app']}</h3><ul><li><a href="{url(L, 'app/')}">{t['get_app']}</a></li><li><a href="/privacy">{t['privacy']}</a></li><li><a href="/terms">{t['terms']}</a></li><li><a href="/delete-account">{t['delete']}</a></li><li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li></ul></div></div>
<p class="copy">© {dt.date.today().year} {SITE['name']}. {t['rights']}</p></footer></body></html>'''

def price(i, L):
    p = f"${float(i['price']):.2f}".replace('.00', '')
    return (f"{T[L]['from_']} {p}" if i.get('from_price') else p)

def iname(i, L): return (i['name_ar'] if L == 'ar' and i.get('name_ar') else i['name_en'])
def idesc(i, L): return (i['desc_ar'] if L == 'ar' and i.get('desc_ar') else i.get('desc_en') or '')
def cname(c, L): return c['name_ar'] if L == 'ar' else c['name_en']

def card(i, L, big=False):
    note = ''
    if i['id'] in off:
        names = ', '.join(bname(b, L) for b in branches if b['id'] in off[i['id']])
        note = f'<p class="na">{T[L]["not_at"]} {E(names)}</p>'
    tag = f'<span class="tag">{E(i["tag"] or T[L]["deal"])}</span>' if (i.get('tag') or i.get('is_deal')) else ''
    src = img(i['image_path'] if big else (i.get('thumb_path') or i['image_path']))
    return (f'<article class="item"><div class="ph"><img src="{src}" alt="{E(iname(i, L))}" loading="lazy" decoding="async" width="400" height="300">{tag}</div>'
            f'<div class="tx"><h3>{E(iname(i, L))}</h3><p>{E(idesc(i, L))}</p>{note}<span class="pr" dir="ltr">{price(i, L)}</span></div></article>')

# ---------------------------------------------------------------- structured data
ORG_ID = D + '/#org'
def restaurant_ld(b, L):
    return {
     '@context': 'https://schema.org', '@type': 'Restaurant', '@id': f"{D}/locations/{b['slug']}/#restaurant",
     'name': f"{SITE['name']} – {b['name_en']}", 'alternateName': f"ذا رود سايد داينر – {b['name_ar']}",
     'url': f"{D}{url(L, 'locations/' + b['slug'] + '/')}", 'telephone': b['tel'], 'image': f'{D}/assets/og.jpg', 'logo': f'{D}/assets/icon-512.png',
     'priceRange': SITE['price_range'], 'servesCuisine': SITE['cuisine'], 'currenciesAccepted': 'USD', 'paymentAccepted': 'Cash',
     'address': {'@type': 'PostalAddress', 'streetAddress': b['name_en'], 'addressLocality': b['area_en'], 'addressRegion': 'Mount Lebanon' if b['id'] != 'jnah' else 'Beirut', 'addressCountry': 'LB'},
     'geo': {'@type': 'GeoCoordinates', 'latitude': b['lat'], 'longitude': b['lng']},
     'hasMap': f"https://www.google.com/maps/search/?api=1&query={b['lat']},{b['lng']}",
     'openingHoursSpecification': [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 'opens': b['o'], 'closes': b['c']}],
     'hasMenu': f"{D}{url(L, 'menu/')}", 'acceptsReservations': False, 'parentOrganization': {'@id': ORG_ID},
    }

def org_ld():
    return {'@context': 'https://schema.org', '@type': 'Organization', '@id': ORG_ID, 'name': SITE['name'], 'alternateName': ['Roadside', 'The Roadside', 'ذا رود سايد داينر'],
            'url': D + '/', 'logo': f'{D}/assets/icon-512.png', 'email': SITE['email'], 'sameAs': [SITE['instagram'], SITE['facebook'], SITE['tiktok']],
            'subOrganization': [{'@id': f"{D}/locations/{b['slug']}/#restaurant"} for b in branches]}

def website_ld(L):
    return {'@context': 'https://schema.org', '@type': 'WebSite', '@id': D + '/#website', 'url': D + '/', 'name': SITE['name'], 'inLanguage': ['en', 'ar'], 'publisher': {'@id': ORG_ID}}

def menu_ld(L):
    return {'@context': 'https://schema.org', '@type': 'Menu', '@id': f"{D}{url(L, 'menu/')}#menu", 'name': f"{SITE['name']} {T[L]['menu']}", 'inLanguage': L,
            'hasMenuSection': [{'@type': 'MenuSection', 'name': cname(c, L), 'hasMenuItem': [
                {'@type': 'MenuItem', 'name': iname(i, L), 'description': idesc(i, L)[:300], 'image': img(i['image_path']),
                 'offers': {'@type': 'Offer', 'price': f"{float(i['price']):.2f}", 'priceCurrency': 'USD'}} for i in by_cat[c['id']]]} for c in cats]}

def faq_ld(L):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': L,
            'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs(L)]}

def crumbs(L, *pairs):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': n + 1, 'name': name, 'item': D + u} for n, (name, u) in enumerate([(T[L]['home'], url(L))] + list(pairs))]}

def app_ld(L):
    return {'@context': 'https://schema.org', '@type': 'MobileApplication', 'name': 'Roadside', 'operatingSystem': 'Android, iOS', 'applicationCategory': 'FoodAndDrinkApplication',
            'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}, 'publisher': {'@id': ORG_ID}, 'url': f"{D}{url(L, 'app/')}", 'inLanguage': ['en', 'ar']}

# ---------------------------------------------------------------- pages
def store_buttons(L):
    t, s = T[L], SITE['stores']
    if not s['live']:
        return f'<p class="soon">{t["soon"]}</p>'
    return f'<div class="stores"><a class="btn" href="{s["android"]}" rel="noopener">{t["gp"]}</a><a class="btn alt" href="{s["ios"]}" rel="noopener">{t["as_"]}</a></div>'

def page_home(L):
    t = T[L]
    fav = [i for i in items if i.get('tag') or i.get('is_deal')][:3] + [i for c in cats if c['name_en'] in ('Burgers', 'Appetizers', 'Sandwiches') for i in by_cat[c['id']][:3]]
    seen, picks = set(), []
    for i in fav:
        if i['id'] not in seen: seen.add(i['id']); picks.append(i)
    why = ''.join(f'<div class="why"><span aria-hidden="true">{a}</span><h3>{b}</h3><p>{c}</p></div>' for a, b, c in t['why'])
    br = ''.join(branch_card(b, L) for b in branches)
    body = f'''<section class="hero"><div class="wrap"><p class="kicker">{t['tagline']}</p><h1>{t['hero']}</h1><p class="lead">{t['hero_sub']}</p>
<div class="ctas"><a class="btn" href="{url(L, 'menu/')}">{t['see_menu']}</a><a class="btn ghost" href="{url(L, 'locations/')}">{t['find']}</a></div></div></section>
<section class="wrap whys">{why}</section>
<section class="wrap"><h2>{t['popular']}</h2><div class="grid">{''.join(card(i, L) for i in picks[:8])}</div><p class="more"><a class="btn" href="{url(L, 'menu/')}">{t['all_menu']}</a></p></section>
<section class="band"><div class="wrap"><h2>{t['locs_h']}</h2><div class="branches">{br}</div></div></section>
<section class="wrap appcta"><h2>{t['app_h']}</h2><p>{t['app_sub']}</p>{store_buttons(L)}<p><a href="{url(L, 'app/')}">{t['get_app']} →</a></p></section>'''
    ld = [org_ld(), website_ld(L)] + [restaurant_ld(b, L) for b in branches]
    return head(L, t['title_home'], t['desc_home'], '', ld) + body + foot(L)

def branch_card(b, L, full=False):
    t = T[L]
    maps = f"https://www.google.com/maps/search/?api=1&query={b['lat']},{b['lng']}"
    h = f'<h3><a href="{url(L, "locations/" + b["slug"] + "/")}">{E(bname(b, L))}</a></h3>' if not full else ''
    return (f'<div class="branch">{h}<p class="area">{E(barea(b, L))}</p><p>{t["open_daily"]} <b dir="ltr">{b["o"]} – {b["c"]}</b></p>'
            f'<p><a class="btn sm" href="tel:{b["tel"]}">{t["call"]} <span dir="ltr">{E(b["phone"])}</span></a> <a class="btn sm ghost" href="{maps}" rel="noopener">{t["directions"]}</a></p></div>')

def page_menu(L):
    t = T[L]
    chips = ''.join(f'<a href="#c{c["id"]}">{E(cname(c, L))}</a>' for c in cats)
    secs = ''.join(f'<section id="c{c["id"]}" class="cat"><h2>{E(cname(c, L))}</h2><div class="grid">{"".join(card(i, L) for i in by_cat[c["id"]])}</div></section>' for c in cats)
    body = f'<section class="wrap pagehead"><h1>{t["menu_h"]}</h1><p class="note">{t["menu_note"]}</p><nav class="chips" aria-label="{t["menu"]}">{chips}</nav></section><div class="wrap">{secs}</div>'
    return head(L, t['title_menu'], t['desc_menu'], 'menu/', [menu_ld(L), crumbs(L, (t['menu'], url(L, 'menu/')))]) + body + foot(L)

def page_locs(L):
    t = T[L]
    body = f'<section class="wrap pagehead"><h1>{t["locs_h"]}</h1><p class="note">{t["delivery"]}</p></section><div class="wrap branches">{"".join(branch_card(b, L) for b in branches)}</div>'
    return head(L, t['title_locs'], t['desc_locs'], 'locations/', [restaurant_ld(b, L) for b in branches] + [crumbs(L, (t['locs'], url(L, 'locations/')))]) + body + foot(L)

def page_branch(b, L):
    t = T[L]
    nm = f"{bname(b, L)} – {barea(b, L)}"
    title = (f"ذا رود سايد داينر {bname(b, L)}، {barea(b, L)} | الهاتف والدوام" if L == 'ar' else f"The Roadside Diner {b['name_en']}, {b['area_en']} | Hours, Phone & Delivery")
    desc = (f"فرع ذا رود سايد داينر في {bname(b, L)}، {barea(b, L)}: مفتوح يومياً {b['o']}–{b['c']}. اتصل {b['phone']}. برغر، دجاج مقرمش، توصيل واستلام." if L == 'ar'
            else f"The Roadside Diner at {b['name_en']}, {b['area_en']}, Lebanon: open daily {b['o']}–{b['c']}. Call {b['phone']}. Burgers, crispy chicken, delivery and pickup.")
    mz = f"https://www.openstreetmap.org/export/embed.html?bbox={b['lng']-0.006},{b['lat']-0.004},{b['lng']+0.006},{b['lat']+0.004}&layer=mapnik&marker={b['lat']},{b['lng']}"
    na = [i for i in items if b['id'] in off.get(i['id'], set())]
    others = ''.join(f'<li><a href="{url(L, "locations/" + o["slug"] + "/")}">{E(bname(o, L))} – {E(barea(o, L))}</a></li>' for o in branches if o is not b)
    body = f'''<section class="wrap pagehead"><h1>{E(nm)}</h1><p class="lead">{t['delivery']}</p></section>
<div class="wrap two">{branch_card(b, L, True)}<iframe class="map" title="{E(nm)}" src="{mz}" loading="lazy"></iframe></div>
<section class="wrap"><h2>{t['hours']}</h2><table class="hours"><tr><td>{t['open_daily']}</td><td dir="ltr">{b['o']} – {b['c']}</td></tr><tr><td>{t['phone']}</td><td dir="ltr"><a href="tel:{b['tel']}">{E(b['phone'])}</a></td></tr></table>
<p><a class="btn" href="{url(L, 'menu/')}">{t['see_menu']}</a> <a class="btn ghost" href="{url(L, 'app/')}">{t['order_here']}</a></p>
{f'<p class="note">{t["not_at"]} {E(bname(b, L))}: {E(", ".join(iname(i, L) for i in na[:30]))}{"…" if len(na) > 30 else ""}</p>' if na else ''}
<h2>{'فروع أخرى' if L == 'ar' else 'Other branches'}</h2><ul>{others}</ul></section>'''
    return head(L, title, desc, f"locations/{b['slug']}/", [restaurant_ld(b, L), crumbs(L, (t['locs'], url(L, 'locations/')), (nm, url(L, f"locations/{b['slug']}/")))]) + body + foot(L)

def page_app(L):
    t = T[L]
    pts = ''.join(f'<li>{p}</li>' for p in t['app_pts'])
    shots = ''.join(f'<img src="/assets/shot-{n}.webp" alt="" loading="lazy" width="270" height="585">' for n in (2, 3, 6))
    body = f'''<section class="hero small"><div class="wrap"><h1>{t['app_h']}</h1><p class="lead">{t['app_sub']}</p>{store_buttons(L)}</div></section>
<div class="wrap two"><ul class="ticks">{pts}</ul><div class="shots">{shots}</div></div>'''
    return head(L, t['title_app'], t['desc_app'], 'app/', [app_ld(L), crumbs(L, (t['app'], url(L, 'app/')))]) + body + foot(L)

def page_faq(L):
    t = T[L]
    qa = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faqs(L))
    body = f'<section class="wrap pagehead"><h1>{t["faq_h"]}</h1></section><div class="wrap faq">{qa}</div>'
    return head(L, t['title_faq'], t['desc_faq'], 'faq/', [faq_ld(L), crumbs(L, (t['faq'], url(L, 'faq/')))]) + body + foot(L)

def page_404():
    t = T['en']
    return head('en', 'Page not found | The Roadside Diner', t['desc_home'], '').replace('<link rel="canonical"', '<meta name="robots" content="noindex"><link rel="x-canonical"') + \
        f'<section class="hero small"><div class="wrap"><h1>{t["nf_h"]}</h1><p class="lead">{t["nf_p"]}</p><p><a class="btn" href="/">{t["home"]}</a> <a class="btn ghost" href="/menu/">{t["menu"]}</a></p><p lang="ar" dir="rtl">{T["ar"]["nf_p"]}</p></div></section>' + foot('en')

def llms_txt():
    lines = [f"# {SITE['name']}", '', f"> American roadside diner in Lebanon (burgers, fried chicken, loaded fries, shakes) with {len(branches)} branches around Beirut, delivery, pickup and the Roadside ordering app.", '',
             '## Branches']
    for b in branches:
        lines.append(f"- [{b['name_en']}, {b['area_en']}]({D}/locations/{b['slug']}/): open daily {b['o']}–{b['c']}, phone {b['phone']}, coordinates {b['lat']:.5f},{b['lng']:.5f}")
    lines += ['', '## Key pages', f'- [Menu with prices (USD)]({D}/menu/)', f'- [Locations]({D}/locations/)', f'- [Roadside app]({D}/app/)', f'- [FAQ]({D}/faq/)', f'- [Arabic site]({D}/ar/)', '',
              '## Facts', '- Payment: cash on delivery or pickup (online payment coming soon).', '- Prices in US dollars; some items vary by branch.', f"- Contact: {SITE['email']}", f"- Instagram: {SITE['instagram']}", '',
              '## Menu summary']
    for c in cats:
        its = by_cat[c['id']]
        lines.append(f"- {c['name_en']}: " + '; '.join(f"{i['name_en']} ${float(i['price']):.2f}" for i in its))
    return '\n'.join(lines) + '\n'

# ---------------------------------------------------------------- write
def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(ROOT / 'static', OUT)
paths = []
for L in ('en', 'ar'):
    pre = 'ar/' if L == 'ar' else ''
    write(pre + 'index.html', page_home(L)); paths.append(url(L))
    write(pre + 'menu/index.html', page_menu(L)); paths.append(url(L, 'menu/'))
    write(pre + 'locations/index.html', page_locs(L)); paths.append(url(L, 'locations/'))
    for b in branches:
        write(f"{pre}locations/{b['slug']}/index.html", page_branch(b, L)); paths.append(url(L, f"locations/{b['slug']}/"))
    write(pre + 'app/index.html', page_app(L)); paths.append(url(L, 'app/'))
    write(pre + 'faq/index.html', page_faq(L)); paths.append(url(L, 'faq/'))
write('404.html', page_404())

# legal pages (same files the apps link to), restyled header links stay root-relative
for f in ('privacy', 'terms', 'delete-account'):
    write(f + '.html', (REPO / 'web-legal' / f'{f}.html').read_text().replace('<head>', f'<head><link rel="canonical" href="{D}/{f}">', 1))
    paths.append('/' + f)
shutil.copy(REPO / 'web-legal/logo.png', OUT / 'logo.png')

def alt_of(p):
    if p.startswith('/ar/'): return '/' + p[4:], p
    if p in ('/privacy', '/terms', '/delete-account'): return None
    return p, '/ar' + p
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for p in paths:
    pri = '1.0' if p in ('/', '/ar/') else '0.8' if 'menu' in p or 'locations' in p else '0.5'
    pair = alt_of(p)
    alts = (f'<xhtml:link rel="alternate" hreflang="en" href="{D}{pair[0]}"/><xhtml:link rel="alternate" hreflang="ar" href="{D}{pair[1]}"/>') if pair else ''
    sm.append(f'<url><loc>{D}{p}</loc><lastmod>{TODAY}</lastmod>{alts}<priority>{pri}</priority></url>')
sm.append('</urlset>')
write('sitemap.xml', '\n'.join(sm))
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {D}/sitemap.xml\n')
write('llms.txt', llms_txt())
write('CNAME', D.split('//')[1] + '\n')
write('.nojekyll', '')
print(f'built {len(paths)} pages, {len(items)} items, {len(cats)} categories -> {OUT}')

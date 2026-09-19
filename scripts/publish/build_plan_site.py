#!/usr/bin/env python3
"""Build the ZümreAsist website without changing published curriculum data or URLs."""
from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INDEX = REPO_ROOT / 'public/years/2026-2027/index.json'
DEFAULT_SITE_URL = 'https://teach-bot-sys.github.io/dersdefter-data-publish'
APP_STORE_URL = 'https://apps.apple.com/tr/app/id6762494643?ct=zumreasist-website&mt=8'
PLAY_STORE_URL = 'https://play.google.com/store/apps/details?id=com.kairalabs.dersdefter&referrer=utm_source%3Dzumreasist_website%26utm_medium%3Dweb'
DESCRIPTION = 'ZümreAsist öğretmen asistanı: yıllık plan, haftalık kazanım, sınav, çalışma kağıdı ve öğretmen evrakları. iPhone ve Android için keşfedin.'
FEATURES = [
    ('Yıllık plan ve kazanım takibi', 'Sınıf, ders ve plan türünü seçin. Kaynak plandaki tarihleri, konuları ve haftalık kazanımları birlikte takip edin.', 'ders-planlama'),
    ('Sınav ve çalışma kağıdı', 'Kazanıma uygun sorular ve çalışma kağıtları hazırlayın. Yapay zekâ destekli taslakları sınıfınıza göre gözden geçirin.', 'sinav-calisma-kagidi'),
    ('Öğretmen evrakları', 'Toplantı tutanakları ve yıllık çalışma planları için şablonları kullanın. Okul bilgilerinizi ekleyip PDF veya Word olarak dışa aktarın.', 'ogretmen-evraklari'),
    ('Ders programı', 'Haftalık ders programınızı düzenleyin; ders hazırlığınızı programınızla birlikte takip edin.', 'ders-planlama'),
    ('Materyal ve PDF hazırlama', 'Dersiniz için içerik oluşturun, materyallerinizi saklayın ve PDF olarak paylaşın.', 'sinav-calisma-kagidi'),
    ('Kaydedilen planlara erişim', 'İndirdiğiniz yıllık planları çevrimdışı açın. Yeni planlara erişmek ve yapay zekâ ile içerik üretmek için internete bağlanın.', 'ders-planlama'),
]
GUIDES = {
    'ders-planlama': {
        'title': 'Yıllık Plan ve Haftalık Kazanım Takibi',
        'description': 'ZümreAsist ile 2026-2027 yıllık planlarını bulun, haftalık kazanımları takip edin ve ders programınızı düzenleyin. iOS ve Android öğretmen uygulaması.',
        'intro': 'ZümreAsist, yıllık plan arayan ve haftalık ders hazırlığını düzenlemek isteyen öğretmenler için planları sınıf ve ders başlıkları altında toplar. İlkokul, ortaokul, lise ve hazırlık düzeylerindeki mevcut seçenekleri aynı katalogda inceleyebilirsiniz.',
        'sections': [
            ('Yıllık plan nasıl bulunur?', 'Önce sınıf düzeyini, ardından dersinizi seçin. Kültür dersleri, meslek dersleri, MESEM ve rehberlik seçeneklerini kontrol edin. Aynı dersin birden fazla planı varsa yayınevi, alan ve sistem bilgisini karşılaştırarak ihtiyacınıza uygun planı açın.'),
            ('Bu haftanın kazanımı nasıl takip edilir?', 'Planın zaman çizelgesinde tarih, konu ve kazanım birlikte görünür. Uygulama güncel tarihe karşılık gelen haftayı işaretler. Böylece uzun bir dosyada haftayı baştan aramadan ders içeriğini inceleyebilirsiniz. Tarihler kaynak plandaki aralıklardan gelir.'),
            ('Ders programı ve çevrimdışı kullanım', 'Haftalık ders programınızı düzenleyebilir, indirdiğiniz yıllık planlara çevrimdışı erişebilirsiniz. Güncel katalog ve yeni planlar için internet gerekir. Önceki dönem planları uygulamanın geçmiş bölümünde bulunur.'),
            ('Hangi planı kullanmalıyım?', 'Sınıfınıza, ders saatinize ve okulunuzun uyguladığı programa uygun seçeneği kontrol edin. Katalogdaki planlar hazırlığa yardımcı kaynaklardır; okulunuzun kararları ve güncel öğretim programıyla uygunluğunu öğretmen değerlendirir.'),
        ],
    },
    'sinav-calisma-kagidi': {
        'title': 'Sınav ve Çalışma Kağıdı Hazırlama',
        'description': 'ZümreAsist ile kazanıma uygun sınav soruları, çalışma kağıtları ve ders materyalleri hazırlayın. Yapay zekâ destekli taslakları düzenleyip PDF paylaşın.',
        'intro': 'ZümreAsist, kazanımdan sınav sorusuna ve çalışma kağıdına geçmek isteyen öğretmenlere içerik hazırlama araçları sunar. Yapay zekâ destekli üretim, öğretmenin inceleyip düzenleyebileceği bir taslak oluşturur.',
        'sections': [
            ('Kazanımdan soruya geçin', 'Sınıfınızı ve dersinizi belirleyip üzerinde çalışacağınız kazanımı seçin. Sınav veya çalışma kağıdı hazırlarken hedeflediğiniz öğrenme çıktısına odaklanın. Oluşan soruların kazanımı gerçekten ölçtüğünü ve öğrencilerinizin seviyesine uyduğunu kontrol edin.'),
            ('Taslağı sınıfınıza uyarlayın', 'Soru ifadelerini, cevapları ve varsa çözüm adımlarını tek tek gözden geçirin. Yapay zekâ çıktıları hata içerebilir. Dersinizde kullanmadan önce belirsiz ifadeleri düzeltin ve gerekli değişiklikleri yapın.'),
            ('Materyalleri saklayın ve paylaşın', 'Hazırladığınız materyalleri uygulamada saklayıp PDF olarak paylaşabilirsiniz. Aynı dersin yıllık planını ve haftalık kazanımlarını takip ederken ihtiyaç duyduğunuz içerik hazırlığına geçebilirsiniz.'),
            ('İnternet gerekir mi?', 'Yapay zekâ ile içerik üretimi internet bağlantısı gerektirir. Kullanılabilir üretim hakları ve varsa reklam veya kredi koşulları uygulama içinde gösterilir. İndirilmiş yıllık planların çevrimdışı erişimi ayrı bir özelliktir.'),
        ],
    },
    'ogretmen-evraklari': {
        'title': 'Öğretmen Evrakları ve Toplantı Tutanakları',
        'description': 'ZümreAsist öğretmen evrakları: toplantı tutanağı ve yıllık çalışma planı şablonları. Okul bilgilerinizi ekleyin, PDF veya Word olarak dışa aktarın.',
        'intro': 'ZümreAsist, ders hazırlığının yanında öğretmen evraklarını düzenlemek için şablonlar sunar. Toplantı tutanakları, yıllık çalışma planları ve diğer belge türleri için uygulamadaki evrak bölümünü kullanabilirsiniz.',
        'sections': [
            ('İhtiyacınıza uygun şablonu seçin', 'Hazırlayacağınız belgenin türünü belirleyin ve uygulamadaki şablonları inceleyin. Okul bilgilerini ve belgeye özgü alanları ekleyerek bir taslak oluşturun. Şablon kapsamı belge türüne göre değişir.'),
            ('Toplantı tutanaklarını gözden geçirin', 'Toplantı tarihi, katılımcılar, gündem maddeleri ve kararlar gibi alanları gerçek toplantı bilgileriyle doldurun. Şablon metnini okulunuzun uygulamasına göre düzenleyin; alınmayan kararları tutanağa eklemeyin.'),
            ('PDF veya Word olarak dışa aktarın', 'Tamamladığınız belgeyi PDF veya Word olarak dışa aktarabilirsiniz. Yazdırmadan ya da paylaşmadan önce isimleri, tarihleri, okul bilgilerini ve sayfa düzenini kontrol edin.'),
            ('Resmî belge yerine geçer mi?', 'ZümreAsist, Kaira Labs tarafından geliştirilen bağımsız bir öğretmen uygulamasıdır; MEB ile resmî bağlantısı yoktur. Şablonlar hazırlığa yardımcı olur. Belgenin doğruluğu ve okulunuzun güncel gerekliliklerine uygunluğu kullanıcı tarafından kontrol edilmelidir.'),
        ],
    },
}


def esc(value):
    return html.escape(str(value), quote=True)


def slugify(value):
    normalized = unicodedata.normalize('NFKD', value.casefold()).replace('ı', 'i')
    text = ''.join(c for c in normalized if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')


def grade_label(grade):
    return grade if grade.casefold() == 'hazırlık' else f'{grade}. Sınıf'


def format_number(value):
    return f'{value:,}'.replace(',', '.')


def build_entries(payload, site_url):
    legacy = json.loads((Path(__file__).parent / 'plan-url-map.json').read_text())
    grouped = defaultdict(list)
    for plan in payload['dosyalar']:
        grouped[(str(plan['sinif']), plan['ders'])].append(plan)
    entries, used = [], set()
    for (grade, subject), plans in grouped.items():
        previous = {legacy[str(p['id'])] for p in plans if str(p['id']) in legacy}
        if len(previous) > 1:
            raise ValueError(f'Merged plan URLs need explicit redirects: {previous}')
        slug = next(iter(previous), f'{slugify(grade_label(grade))}-{slugify(subject)}-yillik-plani')
        if slug in used:
            raise ValueError(f'Duplicate plan URL: {slug}')
        used.add(slug)
        entries.append({'sinif': grade, 'ders': subject, 'slug': slug,
            'baslik': f'{grade_label(grade)} {subject} Yıllık Planı {payload["egitim_yili"]}',
            'url': f'{site_url}/plan/{slug}/', 'planlar': sorted(plans, key=lambda p: int(p['id']))})
    return sorted(entries, key=lambda e: (int(e['sinif']) if e['sinif'].isdigit() else 0, e['ders'].casefold()))


def store_links():
    return f'<div class="actions"><a class="button" href="{esc(APP_STORE_URL)}">App Store’dan indir</a><a class="button alt" href="{esc(PLAY_STORE_URL)}">Google Play’den indir</a></div>'


def breadcrumbs(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': name, 'item': url}
        for i, (name, url) in enumerate(items)]}


def page_shell(title, description, canonical, body, graph, site_url):
    data = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    root = esc(site_url)
    return f'''<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="theme-color" content="#0f5b43">
<meta name="apple-itunes-app" content="app-id=6762494643">
<meta name="application-name" content="ZümreAsist">
<link rel="canonical" href="{esc(canonical)}">
<link rel="icon" type="image/png" href="{root}/assets/zumreasist-logo.png">
<link rel="apple-touch-icon" href="{root}/assets/zumreasist-logo.png">
<link rel="manifest" href="{root}/site.webmanifest">
<link rel="stylesheet" href="{root}/assets/site.css">
<link rel="alternate" type="text/plain" href="{root}/llms.txt" title="ZümreAsist uygulama özeti">
<meta property="og:type" content="website">
<meta property="og:locale" content="tr_TR">
<meta property="og:site_name" content="ZümreAsist">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{root}/assets/zumreasist-logo.png">
<meta property="og:image:width" content="1024">
<meta property="og:image:height" content="1024">
<meta property="og:image:alt" content="ZümreAsist öğretmen asistanı uygulama simgesi">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{root}/assets/zumreasist-logo.png">
<meta name="twitter:image:alt" content="ZümreAsist uygulama simgesi">
<script type="application/ld+json">{data}</script>
</head>
<body>
<a class="skip-link" href="#icerik">İçeriğe geç</a>
<header class="shell site-header"><a class="brand" href="{root}/"><img src="{root}/assets/zumreasist-logo.png" alt="" width="48" height="48">ZümreAsist</a><nav class="nav" aria-label="Ana menü"><a href="{root}/#neler-yapar">Özellikler</a><a href="{root}/yillik-planlar/">Yıllık planlar</a><a class="button" href="{root}/#indir">Uygulamayı indir</a></nav></header>
<main id="icerik">{body}</main>
<footer class="site-footer"><div class="shell footer-grid"><div class="footer-copy"><a class="brand" href="{root}/">ZümreAsist</a><p>Plan, sınav, materyal ve öğretmen evrakları için öğretmen asistanı. DersDefter’in yeni adı.</p><p>Kaira Labs tarafından geliştirilmiştir. MEB ile resmî bağlantısı yoktur.</p></div><nav class="footer-links" aria-label="Alt menü"><a href="{root}/yillik-planlar/">Yıllık planlar</a><a href="{esc(APP_STORE_URL)}">App Store</a><a href="{esc(PLAY_STORE_URL)}">Google Play</a><a href="https://docs.google.com/document/d/1ELciG67yDvMh2TghdIK_BXzvzpAz4qXOuVQKdviaiDs/edit?usp=sharing">Gizlilik (iOS)</a><a href="https://docs.google.com/document/d/e/2PACX-1vQ-Cmf1MYDfHLxFimzwlRR-Kq0OfzhNAutOtavQVatK9OuXBy1lg_6vrMN7ZPJ9txfmGBvAHMWQNeRl/pub">Gizlilik (Android)</a><a href="{root}/#sss">Destek ve SSS</a><a href="{root}/llms.txt">Uygulama özeti</a></nav></div></footer>
</body></html>
'''


def faq_items(period):
    return [
        ('ZümreAsist nedir, kimler için uygundur?', 'ZümreAsist; yıllık plan, haftalık kazanım, ders programı, sınav, çalışma kağıdı, materyal ve öğretmen evraklarını bir araya getiren iPhone ve Android öğretmen asistanıdır. Kaira Labs tarafından geliştirilmiştir.'),
        ('DersDefter ile ZümreAsist aynı uygulama mı?', 'Evet. DersDefter’in yeni adı ZümreAsist’tir. Mevcut uygulama kaydı üzerinden güncellenir; yeniden hesap oluşturmanız gerekmez. Mağaza bağlantılarındaki DersDefter kimliği aynı uygulamaya aittir.'),
        ('Hangi eğitim yılının planları var?', f'Güncel katalog {period} eğitim yılına aittir. 1–12. sınıf ve hazırlık düzeylerinde kültür, meslek, MESEM ve rehberlik planları bulunur. 2025-2026 planlarına uygulamanın geçmiş bölümünden erişilir. Her sınıf ve ders için seçenek sayısı farklıdır.'),
        ('İnternetsiz kullanabilir miyim?', 'İndirdiğiniz yıllık planlara çevrimdışı erişebilirsiniz. Yeni planları almak, güncel verileri kontrol etmek ve yapay zekâ ile içerik üretmek için internet bağlantısı gerekir.'),
        ('ZümreAsist ücretli mi?', 'ZümreAsist mağazalardan ücretsiz indirilebilir. Uygulama reklam içerir. İçerik üretimi için geçerli kullanım veya kredi koşulları uygulama içinde gösterilir; güncel koşulları mağaza sayfasından ve uygulamadan kontrol edebilirsiniz.'),
        ('Yapay zekâ ile hazırlanan sınav doğrudan kullanılabilir mi?', 'Üretilen soru, cevap ve materyaller taslaktır. Doğruluğunu, kazanımla ilişkisini ve sınıf seviyesine uygunluğunu kullanmadan önce öğretmen kontrol etmelidir.'),
        ('Öğretmen evrakları hangi formatlarda dışa aktarılır?', 'Öğretmen evrakları PDF veya Word olarak dışa aktarılabilir. Materyaller PDF olarak paylaşılabilir. Belgeyi paylaşmadan önce okul bilgilerini, isimleri ve tarihleri kontrol edin.'),
        ('ZümreAsist MEB’in resmî uygulaması mı?', 'Hayır. ZümreAsist, Kaira Labs tarafından geliştirilen bağımsız bir uygulamadır; MEB ile resmî bağlantısı yoktur.'),
        ('Destek için nereye başvurabilirim?', 'Uygulamanın mağaza sayfasındaki geliştirici iletişim veya uygulama desteği alanını kullanabilirsiniz. Bildiriminizde cihazınızı, uygulama sürümünü ve karşılaştığınız sorunu belirtin.'),
    ]


def home_page(entries, period, site_url):
    plans = [p for e in entries for p in e['planlar']]
    features = ''.join(f'<article class="feature"><span class="feature-num">{i+1:02}</span><h3>{esc(title)}</h3><p>{esc(text)}</p><a class="text-link" href="{site_url}/{slug}/">Nasıl kullanılır?</a></article>' for i,(title,text,slug) in enumerate(FEATURES))
    faqs = faq_items(period)
    faq_html = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q,a in faqs)
    body = f'''
<section class="shell hero"><div class="hero-copy"><div class="eyebrow">DersDefter artık ZümreAsist</div><h1>Öğretmen asistanınız.<br><strong>ZümreAsist.</strong></h1><p class="lead">Yıllık planı bulun, haftanın kazanımını takip edin. Sınav, çalışma kağıdı ve öğretmen evraklarını aynı uygulamada hazırlayın.</p><p>Planla. Hazırla. Derse gir.</p>{store_links()}<div class="trust-line"><span>iPhone ve Android</span><span>Hesap açmadan başlayın</span><span>Ücretsiz indirin</span></div></div>
<div class="brand-board" aria-label="ZümreAsist özellik özeti"><div class="board-heading"><img src="{site_url}/assets/zumreasist-logo.png" alt="ZümreAsist uygulama simgesi" width="84" height="84"><div><strong>ZümreAsist</strong><span>Öğretmen Asistanı</span></div></div><p class="board-caption">Ders hazırlığınız bir arada.</p><div class="board-card"><span>01 · PLANLA</span><h2>Bu hafta ne işleyeceğim?</h2><p>Yıllık plan · Haftalık kazanım · Ders programı</p></div><div class="board-card rose"><span>02 · HAZIRLA</span><h2>Dersinize uygun içerik.</h2><p>Sınav · Çalışma kağıdı · Materyal</p></div><div class="board-card cream"><span>03 · TAMAMLA</span><h2>Evraklarınız da hazır.</h2><p>Toplantı tutanağı · PDF ve Word</p></div></div></section>
<section class="shell stats" aria-label="Güncel plan kataloğu"><div class="stat"><b>{format_number(len(plans))}</b><span>yıllık plan</span></div><div class="stat"><b>{format_number(sum(p['kayit_sayisi'] for p in plans))}</b><span>haftalık kayıt</span></div><div class="stat"><b>{len({p['sinif'] for p in plans})}</b><span>sınıf düzeyi</span></div><div class="stat"><b>{esc(period)}</b><span>güncel eğitim yılı</span></div></section>
<section class="section mint" id="neler-yapar"><div class="shell"><div class="section-head"><div class="eyebrow">Ders hazırlığından öğretmen evraklarına</div><h2>ZümreAsist ile neler yapabilirsiniz?</h2><p>Öğretmenin günlük iş akışına uygun araçlar. İhtiyacınız olan bölümü seçerek başlayın.</p></div><div class="feature-grid">{features}</div></div></section>
<section class="section" id="planlar"><div class="shell"><div class="section-head"><div class="eyebrow">{esc(period)} yıllık planları</div><h2>Sınıfınızın planını bulun.</h2><p>Kültür, meslek, MESEM ve rehberlik planlarını inceleyin. Kaynak planın tarih, hafta ve kazanım bilgilerine uygulamada ulaşın.</p></div>{grade_cards(entries,site_url)}<p class="catalog-note"><a href="{site_url}/yillik-planlar/">Tüm yıllık planları sınıfa göre inceleyin</a></p></div></section>
<section class="section mint"><div class="shell"><div class="section-head"><div class="eyebrow">Nasıl başlanır?</div><h2>Üç adımda ders hazırlığı.</h2></div><div class="feature-grid"><article class="feature"><h3>1. Uygulamayı indirin</h3><p>iPhone için App Store, Android için Google Play bağlantısını açın. Mevcut DersDefter kullanıcıları aynı uygulamayı güncelleyebilir.</p></article><article class="feature"><h3>2. Sınıfı ve dersi seçin</h3><p>Plan seçeneklerini inceleyin, okulunuza uygun yıllık planı açın ve haftanın kazanımlarına bakın.</p></article><article class="feature"><h3>3. İçeriğinizi hazırlayın</h3><p>Sınav, çalışma kağıdı veya evrak taslağını oluşturun. Kontrol edip düzenledikten sonra paylaşın.</p></article></div></div></section>
<section class="section" id="indir"><div class="shell"><div class="cta"><div><h2>ZümreAsist’i indirin.</h2><p>Plan, sınav ve öğretmen evrakları cebinizde. iPhone ve Android için ücretsiz indirme.</p><p class="small-print">Reklam içerir. İçerik üretiminde uygulama içindeki kullanım koşulları geçerlidir.</p></div>{store_links()}</div></div></section>
<section class="section mint" id="sss"><div class="shell faq"><div><div class="eyebrow">Sorular ve yanıtlar</div><h2>ZümreAsist hakkında.</h2><p>Uygulamayı indirmeden önce bilmeniz gerekenler.</p></div><div>{faq_html}</div></div></section>
'''
    graph = [
        {'@type':'Organization','@id':site_url+'/#organization','name':'Kaira Labs','url':site_url+'/'},
        {'@type':'WebSite','@id':site_url+'/#website','name':'ZümreAsist','alternateName':['ZumreAsist','DersDefter'],'url':site_url+'/','inLanguage':'tr-TR','publisher':{'@id':site_url+'/#organization'}},
        {'@type':'MobileApplication','@id':site_url+'/#app','name':'ZümreAsist: Öğretmen Asistanı','alternateName':['ZümreAsist','DersDefter'],'url':site_url+'/','description':DESCRIPTION,'operatingSystem':'Android, iOS','applicationCategory':'EducationalApplication','inLanguage':'tr-TR','image':site_url+'/assets/zumreasist-logo.png','author':{'@id':site_url+'/#organization'},'featureList':[f[0] for f in FEATURES],'downloadUrl':[APP_STORE_URL,PLAY_STORE_URL],'sameAs':['https://apps.apple.com/tr/app/id6762494643','https://play.google.com/store/apps/details?id=com.kairalabs.dersdefter'],'offers':{'@type':'Offer','price':'0','priceCurrency':'TRY','description':'Ücretsiz indirme. Reklam içerir; içerik üretiminde uygulama içindeki kullanım koşulları geçerlidir.'}},
        {'@type':'WebPage','@id':site_url+'/#webpage','url':site_url+'/','name':'ZümreAsist Öğretmen Asistanı','isPartOf':{'@id':site_url+'/#website'},'about':{'@id':site_url+'/#app'},'inLanguage':'tr-TR'},
        {'@type':'FAQPage','@id':site_url+'/#sss','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in faqs]},
    ]
    return page_shell('ZümreAsist | Öğretmen Asistanı, Yıllık Plan ve Sınav',DESCRIPTION,site_url+'/',body,graph,site_url)


def grade_cards(entries,site_url):
    grades = list(dict.fromkeys(e['sinif'] for e in entries))
    return '<div class="plan-grid">'+''.join(f'<a class="plan-card" href="{site_url}/yillik-planlar/{slugify(grade_label(g))}/"><h3>{esc(grade_label(g))}</h3><p>{sum(e["sinif"]==g for e in entries)} ders başlığı · Planları inceleyin</p></a>' for g in grades)+'</div>'


def listing_page(entries, period, site_url, grade=None):
    title = f'{grade_label(grade)+" " if grade else ""}{period} Yıllık Planları'
    path = '/yillik-planlar/'+(slugify(grade_label(grade))+'/' if grade else '')
    description = f'{title}: ders ve plan seçeneklerini ZümreAsist kataloğunda inceleyin. Haftalık kazanımlara iPhone ve Android uygulamasından erişin.'
    selected = [e for e in entries if e['sinif']==grade] if grade else entries
    cards = ''.join(f'<a class="plan-card" href="{e["url"]}"><h2>{esc(e["ders"])}</h2><p>{len(e["planlar"])} plan seçeneği</p></a>' for e in selected) if grade else grade_cards(entries,site_url)
    body = f'<section class="section shell"><p><a href="{site_url}/">ZümreAsist</a> / <a href="{site_url}/yillik-planlar/">Yıllık planlar</a></p><h1 class="page-title">{esc(title)}</h1><p class="lead">{esc(description)}</p><div class="plan-grid">{cards}</div></section>' if grade else f'<section class="section shell"><h1 class="page-title">{esc(title)}</h1><p class="lead">{esc(description)}</p>{cards}</section>'
    graph=[{'@type':'CollectionPage','name':title,'url':site_url+path,'description':description,'inLanguage':'tr-TR','isPartOf':{'@id':site_url+'/#website'}},breadcrumbs([('ZümreAsist',site_url+'/'),(title,site_url+path)])]
    return path, page_shell(title+' | ZümreAsist',description,site_url+path,body,graph,site_url)


def variant_label(plan):
    return ' · '.join(dict.fromkeys(str(plan[k]) for k in ('grup','brans','sistem','yayinevi') if plan.get(k))) or 'Standart plan'


def plan_page(entry,period,site_url):
    title=entry['baslik']
    description=f'{title}. ZümreAsist’te {len(entry["planlar"])} plan seçeneğini karşılaştırın; hafta, tarih ve kazanımları iPhone veya Android’de takip edin.'
    variants=''.join(f'<article class="variant"><div class="meta">Plan {p["id"]}</div><h3>{esc(variant_label(p))}</h3><p>{p["kayit_sayisi"]} haftalık kayıt</p></article>' for p in entry['planlar'])
    grade_url=site_url+'/yillik-planlar/'+slugify(grade_label(entry['sinif']))+'/'
    body=f'''<section class="shell plan-hero"><article class="plan-hero-copy"><p><a href="{site_url}/yillik-planlar/">Yıllık planlar</a> / <a href="{grade_url}">{esc(grade_label(entry['sinif']))}</a></p><div class="eyebrow">{esc(period)} eğitim yılı</div><h1>{esc(grade_label(entry['sinif']))}<br>{esc(entry['ders'])}</h1><p class="lead">{esc(description)}</p>{store_links()}</article><aside class="plan-preview"><h2>Haftanın kazanımına ulaşın.</h2><p>ZümreAsist’te sınıfı ve dersi seçin, okulunuza uygun planı açın. Kaynak plandaki tarih, konu ve kazanımları birlikte inceleyin.</p><div class="preview-row"><b>1</b><span>Plan seçeneğini kontrol edin</span></div><div class="preview-row"><b>2</b><span>İlgili haftayı açın</span></div><div class="preview-row"><b>3</b><span>Ders hazırlığına geçin</span></div></aside></section><section class="section mint"><div class="shell"><h2>Bu dersin plan seçenekleri</h2><div class="variant-grid">{variants}</div><p class="catalog-note">Planı kullanmadan önce sınıf, ders saati ve okulunuzun programına uygunluğunu kontrol edin.</p></div></section><section class="section shell"><h2>Planı nasıl kullanabilirsiniz?</h2><p>Haftalık ayrıntılar ZümreAsist uygulamasında açılır. İndirdiğiniz yıllık planlara çevrimdışı erişebilir, yeni planları internet bağlantısıyla alabilirsiniz.</p><p><a href="{site_url}/ders-planlama/">Yıllık plan ve kazanım takibi</a> · <a href="{site_url}/sinav-calisma-kagidi/">Sınav ve çalışma kağıdı hazırlama</a> · <a href="{grade_url}">Bu sınıfın diğer dersleri</a></p></section>'''
    graph=[{'@type':'WebPage','name':title,'description':description,'url':entry['url'],'inLanguage':'tr-TR','isPartOf':{'@id':site_url+'/#website'},'about':{'@id':site_url+'/#app'}},breadcrumbs([('ZümreAsist',site_url+'/'),(grade_label(entry['sinif']),grade_url),(title,entry['url'])])]
    return page_shell(title+' | ZümreAsist',description,entry['url'],body,graph,site_url)


def guide_page(slug,guide,site_url):
    sections=''.join(f'<section><h2>{esc(title)}</h2><p>{esc(text)}</p></section>' for title,text in guide['sections'])
    body=f'<article class="shell guide"><p><a href="{site_url}/">ZümreAsist</a> / Kullanım rehberi</p><h1 class="page-title">{esc(guide["title"])}</h1><p class="lead">{esc(guide["intro"])}</p>{sections}<p><a href="{site_url}/yillik-planlar/">Sınıfınıza uygun yıllık planları inceleyin</a></p>{store_links()}</article>'
    url=site_url+'/'+slug+'/'
    graph=[{'@type':'WebPage','name':guide['title'],'description':guide['description'],'url':url,'inLanguage':'tr-TR','isPartOf':{'@id':site_url+'/#website'},'about':{'@id':site_url+'/#app'}},breadcrumbs([('ZümreAsist',site_url+'/'),(guide['title'],url)])]
    return page_shell(guide['title']+' | ZümreAsist',guide['description'],url,body,graph,site_url)


def write_text(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')


def build_site(index_path,output_root,site_url):
    payload=json.loads(index_path.read_text())
    period=payload['egitim_yili'];site_url=site_url.rstrip('/')
    entries=build_entries(payload,site_url)
    pages={'/':home_page(entries,period,site_url)}
    for e in entries:pages['/plan/'+e['slug']+'/']=plan_page(e,period,site_url)
    for grade in [None,*dict.fromkeys(e['sinif'] for e in entries)]:
        path,content=listing_page(entries,period,site_url,grade);pages[path]=content
    for slug,guide in GUIDES.items():pages['/'+slug+'/']=guide_page(slug,guide,site_url)
    # Keep lastmod stable on rebuild when a page's actual content is unchanged.
    import xml.etree.ElementTree as ET
    old_dates={}
    sitemap_path=output_root/'sitemap.xml'
    if sitemap_path.exists():
        ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        old_dates={u.findtext('s:loc',namespaces=ns):u.findtext('s:lastmod',namespaces=ns) for u in ET.parse(sitemap_path).getroot()}
    urls=[]
    for path,content in pages.items():
        target=output_root/path.lstrip('/')/'index.html'
        unchanged=target.exists() and target.read_text()==content
        lastmod=old_dates.get(site_url+path) if unchanged else None
        write_text(target,content)
        urls.append(f'  <url><loc>{esc(site_url+path)}</loc><lastmod>{lastmod or date.today().isoformat()}</lastmod></url>')
    write_text(sitemap_path,'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+'\n'.join(urls)+'\n</urlset>\n')
    write_text(output_root/'robots.txt',f'# The authoritative robots.txt is at the origin root, /robots.txt.\nUser-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n')
    manifest={'name':'ZümreAsist Öğretmen Asistanı','short_name':'ZümreAsist','description':DESCRIPTION,'lang':'tr-TR','start_url':urlsplit(site_url).path+'/','scope':urlsplit(site_url).path+'/','display':'standalone','background_color':'#fbfaf5','theme_color':'#0f5b43','icons':[{'src':'assets/zumreasist-logo.png','sizes':'1024x1024','type':'image/png'}]}
    write_text(output_root/'site.webmanifest',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    lines=['# ZümreAsist','','> ZümreAsist (eski adı DersDefter), Kaira Labs tarafından geliştirilen iPhone ve Android öğretmen asistanıdır. Yıllık plan, haftalık kazanım, ders programı, sınav, çalışma kağıdı, materyal ve öğretmen evraklarını bir araya getirir.','','## Uygulama bilgileri','',f'- Resmî site: {site_url}/','- Geliştirici: Kaira Labs','- Önceki adı: DersDefter','- Platformlar: iOS ve Android','- Dil: Türkçe','- Hedef kullanıcılar: Öğretmenler','- İndirme: Ücretsiz; reklam içerir. İçerik üretiminde uygulama içindeki kullanım ve kredi koşulları geçerlidir.','- MEB ile resmî bağlantısı yoktur.',f'- Güncel plan dönemi: {period}',f'- Yıllık plan: {len(payload["dosyalar"])}',f'- Haftalık kayıt: {sum(p["kayit_sayisi"] for p in payload["dosyalar"])}','- İndirilen planlara çevrimdışı erişilir; yeni planlar ve yapay zekâ üretimi internet gerektirir.','- Yapay zekâ çıktıları kullanımdan önce öğretmen tarafından kontrol edilmelidir.','- Öğretmen evrakları PDF veya Word, materyaller PDF olarak dışa aktarılabilir.','','## Resmî bağlantılar','',f'- [Ana sayfa]({site_url}/)',f'- [App Store]({APP_STORE_URL})',f'- [Google Play]({PLAY_STORE_URL})',f'- [Sık sorulan sorular]({site_url}/#sss)',f'- [Yıllık plan kataloğu]({site_url}/yillik-planlar/)']
    lines += [f'- [{g["title"]}]({site_url}/{slug}/)' for slug,g in GUIDES.items()]
    lines += [f'- [Tüm ders sayfaları]({site_url}/llms-full.txt)','- [iOS gizlilik politikası](https://docs.google.com/document/d/1ELciG67yDvMh2TghdIK_BXzvzpAz4qXOuVQKdviaiDs/edit?usp=sharing)', '- [Android gizlilik politikası](https://docs.google.com/document/d/e/2PACX-1vQ-Cmf1MYDfHLxFimzwlRR-Kq0OfzhNAutOtavQVatK9OuXBy1lg_6vrMN7ZPJ9txfmGBvAHMWQNeRl/pub)']
    write_text(output_root/'llms.txt','\n'.join(lines)+'\n')
    write_text(output_root/'llms-full.txt','\n'.join(lines+['','## Ders sayfaları','']+[f'- [{e["baslik"]}]({e["url"]}) — {len(e["planlar"])} plan seçeneği' for e in entries])+'\n')
    return entries


def main():
    p=argparse.ArgumentParser(description='ZümreAsist ürün ve yıllık plan sitesini üretir.')
    p.add_argument('--index',type=Path,default=DEFAULT_INDEX)
    p.add_argument('--output',type=Path,default=REPO_ROOT)
    p.add_argument('--site-url',default=DEFAULT_SITE_URL)
    a=p.parse_args();entries=build_site(a.index,a.output,a.site_url)
    print(json.dumps({'plan_pages':len(entries),'site':a.site_url},ensure_ascii=False))

if __name__=='__main__':main()

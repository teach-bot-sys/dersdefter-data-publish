#!/usr/bin/env python3
"""Check generated HTML, discovery files, internal links and legacy plan URLs."""
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('site_builder', ROOT / 'scripts/publish/build_plan_site.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
BASE = builder.DEFAULT_SITE_URL + '/'

class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.headings = 0
        self.ids = set()
        self.links = []
        self.meta = {}
        self.canonical = []
        self.jsons = []
        self.script = None
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h1': self.headings += 1
        if 'id' in a:
            assert a['id'] not in self.ids, f'Duplicate id: {a["id"]}'
            self.ids.add(a['id'])
        if tag == 'meta': self.meta[a.get('name', a.get('property'))] = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical': self.canonical.append(a['href'])
        if tag in ('a', 'link') and 'href' in a: self.links.append(a['href'])
        if tag == 'img':
            assert 'alt' in a and a.get('width') and a.get('height'), 'Image accessibility or dimensions missing'
            self.links.append(a['src'])
        if tag == 'script' and a.get('type') == 'application/ld+json': self.script = ''
    def handle_data(self, data):
        if self.script is not None: self.script += data
    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.jsons.append(json.loads(self.script))
            self.script = None

sitemap = ET.parse(ROOT / 'sitemap.xml')
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
urls = [u.findtext('s:loc', namespaces=ns) for u in sitemap.getroot()]
assert len(urls) == len(set(urls))
pages = {}
for url in urls:
    assert url.startswith(BASE), url
    path = ROOT / unquote(url[len(BASE):]) / 'index.html'
    source = path.read_text()
    page = Page(source)
    assert page.headings == 1, path
    assert page.canonical == [url], path
    assert page.meta['application-name'] == 'ZümreAsist', path
    assert page.meta['og:site_name'] == 'ZümreAsist', path
    assert page.meta['og:url'] == url, path
    assert len(page.meta['description']) > 40, path
    assert page.meta['robots'].startswith('index,follow'), path
    assert len(page.jsons) == 1 and page.jsons[0]['@context'] == 'https://schema.org', path
    assert 'dersdefter-home.png' not in source and 'dersdefter-og.png' not in source, path
    pages[url] = page
for url, page in pages.items():
    for link in page.links:
        target = urljoin(url, link)
        if not target.startswith(BASE): continue
        parsed = urlsplit(target)
        clean = parsed._replace(fragment='', query='').geturl()
        relative = unquote(clean[len(BASE):])
        disk = ROOT / relative
        assert disk.exists(), f'Broken internal link: {url} -> {target}'
        if parsed.fragment:
            assert clean in pages and unquote(parsed.fragment) in pages[clean].ids, target
legacy = json.loads((ROOT / 'scripts/publish/plan-url-map.json').read_text())
for slug in set(legacy.values()): assert BASE+'plan/'+slug+'/' in pages, slug
# Every generated page must be reachable through ordinary HTML links from home.
seen = set()
pending = [BASE]
while pending:
    url = pending.pop()
    if url in seen: continue
    seen.add(url)
    for link in pages[url].links:
        candidate = urlsplit(urljoin(url, link))._replace(fragment='', query='').geturl()
        if candidate in pages and candidate not in seen: pending.append(candidate)
assert seen == set(pages), f'{len(set(pages)-seen)} orphaned pages'
manifest = json.loads((ROOT/'site.webmanifest').read_text())
assert manifest['short_name'] == 'ZümreAsist'
assert (ROOT/manifest['icons'][0]['src']).exists()
index = json.loads(builder.DEFAULT_INDEX.read_text())
faqs = next(x for x in pages[BASE].jsons[0]['@graph'] if x['@type']=='FAQPage')
assert [(q['name'], q['acceptedAnswer']['text']) for q in faqs['mainEntity']] == builder.faq_items(index['egitim_yili'])
summary = (ROOT/'llms.txt').read_text()
assert f'- Yıllık plan: {len(index["dosyalar"])}' in summary
assert 'yönlendirin' not in summary
print(json.dumps({'html_pages':len(pages), 'legacy_urls_preserved':len(set(legacy.values())), 'orphaned_pages':0, 'broken_internal_links':0, 'json_ld_valid':True, 'faq_consistent':True},ensure_ascii=False))

#!/usr/bin/env python3
"""Build searchable, AI-readable yearly-plan landing pages from public index JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote, urlencode


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INDEX = REPO_ROOT / "public" / "years" / "2026-2027" / "index.json"
DEFAULT_SITE_URL = "https://teach-bot-sys.github.io/dersdefter-data-publish"
APP_STORE_URL = "https://apps.apple.com/app/id6762494643"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.kairalabs.dersdefter"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold()).replace("ı", "i")
    ascii_value = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


def grade_label(grade: str) -> str:
    return grade if grade.casefold() == "hazırlık" else f"{grade}. Sınıf"


def sort_key(item: dict[str, object]) -> tuple[int, str, str]:
    grade = str(item["sinif"])
    grade_order = 0 if grade.casefold() == "hazırlık" else int(grade) if grade.isdigit() else 99
    return grade_order, str(item["ders"]).casefold(), str(item["slug"])


def build_entries(payload: dict[str, object], site_url: str) -> list[dict[str, object]]:
    period = str(payload["egitim_yili"])
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for plan in payload["dosyalar"]:  # type: ignore[index]
        grouped[(str(plan["sinif"]), str(plan["ders"]))].append(plan)

    entries: list[dict[str, object]] = []
    seen_slugs: set[str] = set()
    for (grade, subject), variants in grouped.items():
        slug = f"{slugify(grade_label(grade))}-{slugify(subject)}-yillik-plani"
        if slug in seen_slugs:
            raise ValueError(f"Tekrarlı site yolu: {slug}")
        seen_slugs.add(slug)
        title = f"{grade_label(grade)} {subject} Yıllık Planı {period}"
        query = urlencode({"period": period, "grade": grade, "subject": subject})
        entries.append(
            {
                "sinif": grade,
                "sinif_etiketi": grade_label(grade),
                "ders": subject,
                "baslik": title,
                "slug": slug,
                "url": f"{site_url}/plan/{quote(slug)}/",
                "uygulama_url": f"dersdefter://plans?{query}",
                "etiketler": [
                    f"{grade_label(grade)} {subject} yıllık planı",
                    f"{subject} yıllık planı {period}",
                    f"{period} {subject} yıllık planı",
                    f"{subject} ders planı",
                    "DersDefter yıllık plan",
                ],
                "plan_sayisi": len(variants),
                "hafta_sayisi": sum(int(item.get("kayit_sayisi", 0)) for item in variants),
                "planlar": sorted(variants, key=lambda item: int(item["id"])),
            }
        )
    return sorted(entries, key=sort_key)


def page_shell(title: str, description: str, canonical: str, keywords: list[str], body: str, schema: object) -> str:
    escaped_title = html.escape(title)
    escaped_description = html.escape(description, quote=True)
    escaped_keywords = html.escape(", ".join(keywords), quote=True)
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{escaped_title}</title>
  <meta name="description" content="{escaped_description}">
  <meta name="keywords" content="{escaped_keywords}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="theme-color" content="#176b4d">
  <meta name="apple-itunes-app" content="app-id=6762494643">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="tr_TR">
  <meta property="og:site_name" content="DersDefter">
  <meta property="og:title" content="{escaped_title}">
  <meta property="og:description" content="{escaped_description}">
  <meta property="og:url" content="{html.escape(canonical, quote=True)}">
  <script type="application/ld+json">{schema_json}</script>
  <style>
    :root{{--green:#176b4d;--green-dark:#0d4935;--mint:#eaf7f0;--ink:#12251e;--muted:#52675f;--line:#cfe3d8}}
    *{{box-sizing:border-box}} body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:var(--ink);background:linear-gradient(145deg,#f7fbf8,#e7f4ed);min-height:100vh}}
    a{{color:inherit}} .shell{{width:min(1080px,calc(100% - 32px));margin:auto;padding:24px 0 64px}} header{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:28px}}
    .brand{{font-weight:850;font-size:1.25rem;text-decoration:none;color:var(--green-dark)}} .pill,.button{{border-radius:999px;padding:12px 18px;text-decoration:none;font-weight:750;display:inline-flex;align-items:center;justify-content:center}}
    .pill{{background:white;border:1px solid var(--line);color:var(--muted)}} .button{{background:var(--green);color:white;border:0}} .button.alt{{background:white;color:var(--green-dark);border:1px solid var(--line)}}
    .hero,.card{{background:rgba(255,255,255,.86);border:1px solid white;border-radius:28px;box-shadow:0 18px 50px rgba(15,73,53,.10)}} .hero{{padding:clamp(24px,5vw,52px)}} h1{{font-size:clamp(2rem,5vw,4rem);line-height:1.02;margin:12px 0 18px;letter-spacing:-.04em}} h2{{margin:0 0 10px}} p{{line-height:1.65;color:var(--muted)}}
    .actions{{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin-top:22px}} .card{{padding:20px;text-decoration:none}} .card:hover{{border-color:#8cc8aa;transform:translateY(-1px)}}
    .meta{{color:var(--green);font-weight:750;font-size:.92rem}} ul{{padding-left:20px}} input{{width:100%;padding:15px 18px;border-radius:16px;border:1px solid var(--line);font:inherit;margin-top:18px;background:white}}
    footer{{margin-top:34px;color:var(--muted);font-size:.9rem}} @media(max-width:560px){{header{{align-items:flex-start;flex-direction:column}}.pill{{display:none}}.shell{{width:min(100% - 20px,1080px)}}}}
  </style>
</head>
<body><main class="shell"><header><a class="brand" href="/dersdefter-data-publish/">DersDefter</a><span class="pill">2026-2027 yıllık planları</span></header>{body}<footer>Plan tarihleri kaynak Excel dosyalarından alınır. Güncel veri kaynağı GitHub’dır.</footer></main></body>
</html>
"""


def plan_page(entry: dict[str, object], period: str) -> str:
    title = str(entry["baslik"])
    description = (
        f"{title}: {entry['plan_sayisi']} plan çeşidi ve {entry['hafta_sayisi']} haftalık kayıt. "
        "Planı webde inceleyin veya DersDefter uygulamasında doğrudan açın."
    )
    variants = []
    for plan in entry["planlar"]:  # type: ignore[index]
        labels = [plan.get("grup"), plan.get("brans"), plan.get("yayinevi"), plan.get("sistem")]
        variant = " • ".join(html.escape(str(value)) for value in labels if value)
        variants.append(f"<li><strong>Plan {int(plan['id'])}</strong> — {variant or 'Standart plan'} ({int(plan['kayit_sayisi'])} kayıt)</li>")
    body = f"""
<article class="hero">
  <div class="meta">{html.escape(period)} • {html.escape(str(entry['sinif_etiketi']))}</div>
  <h1>{html.escape(title)}</h1>
  <p>{html.escape(description)}</p>
  <div class="actions">
    <a class="button" href="{html.escape(str(entry['uygulama_url']), quote=True)}">DersDefter’de aç</a>
    <a class="button alt" href="{APP_STORE_URL}">App Store</a>
    <a class="button alt" href="{PLAY_STORE_URL}">Google Play</a>
  </div>
</article>
<section class="card" style="margin-top:18px">
  <h2>Mevcut plan çeşitleri</h2>
  <p>Aynı dersin yayınevi, sistem, alan ve grup çeşitleri birleştirilmeden korunur.</p>
  <ul>{''.join(variants)}</ul>
</section>"""
    schema = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": title,
        "description": description,
        "url": entry["url"],
        "inLanguage": "tr-TR",
        "temporalCoverage": period,
        "creator": {"@type": "Organization", "name": "DersDefter"},
        "keywords": entry["etiketler"],
        "distribution": {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": "https://raw.githubusercontent.com/teach-bot-sys/dersdefter-data-publish/main/public/years/2026-2027/index.json",
        },
    }
    return page_shell(title, description, str(entry["url"]), list(entry["etiketler"]), body, schema)


def home_page(entries: list[dict[str, object]], period: str, site_url: str) -> str:
    cards = "".join(
        f'<a class="card plan-card" data-search="{html.escape(" ".join(entry["etiketler"]), quote=True)}" href="plan/{entry["slug"]}/">'
        f'<div class="meta">{html.escape(str(entry["sinif_etiketi"]))}</div><h2>{html.escape(str(entry["ders"]))}</h2>'
        f'<p>{entry["plan_sayisi"]} plan çeşidi • {entry["hafta_sayisi"]} haftalık kayıt</p></a>'
        for entry in entries
    )
    description = f"{period} eğitim yılı için {len(entries)} ders ve sınıf başlığındaki yıllık planları arayın, webde bulun veya DersDefter uygulamasında açın."
    body = f"""
<section class="hero"><div class="meta">GitHub kaynaklı • Excel tarihleri korunur</div><h1>{period} Yıllık Planları</h1><p>{html.escape(description)}</p><input id="search" type="search" placeholder="Sınıf veya ders ara" aria-label="Sınıf veya ders ara"></section>
<section class="grid" id="plans">{cards}</section>
<script>const q=document.getElementById('search');q.addEventListener('input',()=>{{const v=q.value.toLocaleLowerCase('tr-TR');document.querySelectorAll('.plan-card').forEach(c=>c.hidden=!c.dataset.search.toLocaleLowerCase('tr-TR').includes(v))}});</script>"""
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{period} Yıllık Planları",
        "description": description,
        "url": f"{site_url}/",
        "inLanguage": "tr-TR",
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(entries),
            "itemListElement": [
                {"@type": "ListItem", "position": index + 1, "name": entry["baslik"], "url": entry["url"]}
                for index, entry in enumerate(entries)
            ],
        },
    }
    keywords = ["2026-2027 yıllık planları", "MEB yıllık plan", "DersDefter"]
    return page_shell(f"{period} Yıllık Planları | DersDefter", description, f"{site_url}/", keywords, body, schema)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_site(index_path: Path, output_root: Path, site_url: str) -> list[dict[str, object]]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    period = str(payload["egitim_yili"])
    site_url = site_url.rstrip("/")
    entries = build_entries(payload, site_url)
    plan_root = output_root / "plan"
    if plan_root.exists():
        shutil.rmtree(plan_root)
    for entry in entries:
        write_text(plan_root / str(entry["slug"]) / "index.html", plan_page(entry, period))
    public_entries = [{key: value for key, value in entry.items() if key != "planlar"} for entry in entries]
    write_text(output_root / "index.html", home_page(entries, period, site_url))
    write_text(output_root / "plan-index.json", json.dumps({"egitim_yili": period, "dersler": public_entries}, ensure_ascii=False, indent=2) + "\n")
    sitemap_urls = [f"{site_url}/"] + [str(entry["url"]) for entry in entries]
    write_text(output_root / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{html.escape(url)}</loc></url>\n" for url in sitemap_urls) + "</urlset>\n")
    write_text(output_root / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n")
    llm_lines = [
        "# DersDefter 2026-2027 Yıllık Planları",
        "",
        "DersDefter, yıllık planları kaynak Excel tarih aralıklarını koruyarak yayımlar.",
        f"Ana katalog: {site_url}/plan-index.json",
        f"Uygulama JSON'u: https://raw.githubusercontent.com/teach-bot-sys/dersdefter-data-publish/main/public/years/{period}/index.json",
        "",
        "## Dersler",
        *[f"- [{entry['baslik']}]({entry['url']})" for entry in entries],
    ]
    write_text(output_root / "llms.txt", "\n".join(llm_lines) + "\n")
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Yıllık planlar için statik arama ve AI keşif sitesi üretir.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path, default=REPO_ROOT)
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL)
    args = parser.parse_args()
    entries = build_site(args.index, args.output, args.site_url)
    print(json.dumps({"sayfa": len(entries), "site": args.site_url}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

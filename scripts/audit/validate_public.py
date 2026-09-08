#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.common.paths import PUBLIC_DIR


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Yayınlanmış yıllık plan verisini doğrular.")
    parser.add_argument("--period", help="Versioned dönem; ör. 2026-2027")
    parser.add_argument("--expected-plans", type=int, default=0)
    parser.add_argument("--expected-rows", type=int, default=0)
    parser.add_argument("--check-xlsx", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    period_root = PUBLIC_DIR / "years" / args.period if args.period else PUBLIC_DIR
    index_path = period_root / "index.json"
    catalog_path = period_root / "meta" / "catalog.json"

    if not index_path.exists():
        print(f"Eksik dosya: {index_path.relative_to(REPO_ROOT)}")
        return 1
    if not catalog_path.exists():
        print(f"Eksik dosya: {catalog_path.relative_to(REPO_ROOT)}")
        return 1

    index_payload = load_json(index_path)
    catalog_payload = load_json(catalog_path)
    entries = index_payload.get("dosyalar", [])

    missing_files = []
    row_mismatches = []
    ids = []

    for entry in entries:
        plan_path = PUBLIC_DIR / entry["dosya"]
        ids.append(entry["id"])
        if not plan_path.exists():
            missing_files.append(entry["dosya"])
            continue
        plan_payload = load_json(plan_path)
        row_count = len(plan_payload.get("plan", []))
        if row_count != entry["kayit_sayisi"]:
            row_mismatches.append((entry["id"], entry["kayit_sayisi"], row_count))

    duplicate_ids = [plan_id for plan_id, count in Counter(ids).items() if count > 1]
    suspect_count = len(catalog_payload.get("suspect_names", []))
    total_rows = sum(entry.get("kayit_sayisi", 0) for entry in entries)

    if missing_files:
        print("Eksik yayın dosyaları:")
        for path in missing_files[:20]:
            print(path)
        return 1

    if duplicate_ids:
        print("Tekrarlı plan ID bulundu:", duplicate_ids[:20])
        return 1

    if row_mismatches:
        print("Kayıt sayısı uyumsuzlukları:")
        for item in row_mismatches[:20]:
            print(item)
        return 1

    if args.expected_plans and len(entries) != args.expected_plans:
        print(f"Plan sayısı uyuşmuyor: {len(entries)} != {args.expected_plans}")
        return 1

    if args.expected_rows and total_rows != args.expected_rows:
        print(f"Hafta kaydı uyuşmuyor: {total_rows} != {args.expected_rows}")
        return 1

    if args.check_xlsx:
        if not args.period:
            print("--check-xlsx için --period zorunlu.")
            return 1
        archive_root = REPO_ROOT / "archive" / args.period
        manifest_path = archive_root / "manifest.json"
        if not manifest_path.exists():
            print(f"Eksik dosya: {manifest_path.relative_to(REPO_ROOT)}")
            return 1
        manifest = load_json(manifest_path).get("dosyalar", [])
        if len(manifest) != len(entries):
            print("XLSX manifesti ile plan indexi farklı sayıda kayıt içeriyor.")
            return 1
        for item in manifest:
            xlsx_path = archive_root / item["arsiv_dosya"]
            if not xlsx_path.exists() or sha256(xlsx_path) != item["sha256"]:
                print(f"XLSX doğrulaması başarısız: {item['id']}")
                return 1

    print(f"Toplam plan: {len(entries)}")
    print(f"Toplam hafta kaydı: {total_rows}")
    print(f"Şüpheli ad sayısı: {suspect_count}")
    print("Yayın doğrulaması geçti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

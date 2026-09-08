#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = REPO_ROOT / "public"
ARCHIVE_DIR = REPO_ROOT / "archive"

MONTHS = (
    "OCAK",
    "ŞUBAT",
    "MART",
    "NİSAN",
    "MAYIS",
    "HAZİRAN",
    "TEMMUZ",
    "AĞUSTOS",
    "EYLÜL",
    "EKİM",
    "KASIM",
    "ARALIK",
)

IGNORED_SOURCE_PARTS = {".venv", "venv", "__pycache__", "tests"}


class ImportValidationError(RuntimeError):
    pass


class XlsxCell:
    def __init__(self, value: Any) -> None:
        self.value = value


class XlsxSheet:
    def __init__(self, values: dict[tuple[int, int], Any], max_row: int, max_column: int) -> None:
        self.values = values
        self.max_row = max_row
        self.max_column = max_column

    def cell(self, row: int, column: int) -> XlsxCell:
        return XlsxCell(self.values.get((row, column)))


def column_number(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference.upper())
    if not letters:
        return 0
    value = 0
    for character in letters.group():
        value = value * 26 + ord(character) - ord("A") + 1
    return value


def read_xlsx_sheet(path: Path) -> XlsxSheet:
    spreadsheet_ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    try:
        with zipfile.ZipFile(path) as archive:
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
                shared_strings = [
                    "".join(node.text or "" for node in item.iter(f"{spreadsheet_ns}t"))
                    for item in shared_root.iter(f"{spreadsheet_ns}si")
                ]

            sheet_name = "xl/worksheets/sheet1.xml"
            if sheet_name not in archive.namelist():
                raise ImportValidationError("İlk çalışma sayfası bulunamadı.")
            root = ElementTree.fromstring(archive.read(sheet_name))
    except ImportValidationError:
        raise
    except Exception as error:
        raise ImportValidationError(f"XLSX açılamadı: {error}") from error

    values: dict[tuple[int, int], Any] = {}
    max_row = 0
    max_column = 0
    for row_node in root.iter(f"{spreadsheet_ns}row"):
        row_number = int(row_node.attrib.get("r", "0") or 0)
        for cell_node in row_node.findall(f"{spreadsheet_ns}c"):
            reference = cell_node.attrib.get("r", "")
            column = column_number(reference)
            cell_type = cell_node.attrib.get("t", "")
            if cell_type == "inlineStr":
                value: Any = "".join(node.text or "" for node in cell_node.iter(f"{spreadsheet_ns}t"))
            else:
                value_node = cell_node.find(f"{spreadsheet_ns}v")
                raw = value_node.text if value_node is not None else ""
                if cell_type == "s" and raw:
                    value = shared_strings[int(raw)]
                elif cell_type == "b":
                    value = raw == "1"
                elif raw and re.fullmatch(r"-?\d+(?:\.0+)?", raw):
                    value = int(float(raw))
                else:
                    value = raw
            if row_number and column:
                values[(row_number, column)] = value
                max_row = max(max_row, row_number)
                max_column = max(max_column, column)
    return XlsxSheet(values, max_row, max_column)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(re.sub(r"[ \t]+", " ", part).strip() for part in text.split("\n"))
    return "\n".join(part for part in text.split("\n") if part).strip()


def normalized_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", clean_text(value).casefold())
    ascii_like = "".join(character for character in decomposed if not unicodedata.combining(character))
    ascii_like = ascii_like.replace("ı", "i")
    return re.sub(r"[^a-z0-9]+", " ", ascii_like).strip()


def normalize_grade(value: str) -> str:
    cleaned = clean_text(value)
    key = normalized_key(cleaned)
    if "hazirlik" in key:
        return "Hazırlık"
    match = re.search(r"\b(1[0-2]|[1-9])\b", key)
    if match:
        return match.group(1)
    raise ImportValidationError(f"Geçersiz sınıf: {cleaned or 'boş'}")


def normalize_subject(value: str, grade: str) -> str:
    subject = clean_text(value)
    if not subject:
        raise ImportValidationError("Ders adı boş.")
    suffixes = (
        rf"\s*-\s*{re.escape(grade)}(?:\s*\.\s*sınıf)?\s*$",
        r"\s*-\s*hazırlık\s*$" if grade == "Hazırlık" else r"(?!)",
    )
    for suffix in suffixes:
        subject = re.sub(suffix, "", subject, flags=re.IGNORECASE).strip()
    return subject


def canonical_header(header: str) -> str | None:
    key = normalized_key(header)
    if key == "hafta":
        return "WEEK_NUMBER"
    if key == "ders tarihi":
        return "DATE"
    if key == "ders saati":
        return "SAAT"
    if key.startswith("unite tema ogrenme alani") or key in {"unite", "tema", "ogrenme alani"}:
        return "ÜNİTE"
    if key.startswith("konu icerik cercevesi") or key in {"konu", "icerik cercevesi"}:
        return "KONU"
    if "ogrenme ciktisi" in key and "kod" not in key:
        return "KAZANIM"
    if key in {"kazanim", "kazanimlar"}:
        return "KAZANIM"
    if key in {"sosyal duygusal becerileri", "sosyal duygusal beceriler", "sdb"}:
        return "SDB"
    if key in {"okur yazarlik becerileri", "okuryazarlik becerileri", "ob"}:
        return "OB"
    if "belirli gun ve hafta" in key:
        return "BELİRLİ GÜN VE HAFTALAR"
    return None


def month_from_date(value: str) -> str:
    key = normalized_key(value)
    for month in MONTHS:
        if normalized_key(month) in key:
            return month
    return ""


def read_metadata(sheet: Any) -> tuple[dict[str, str], int]:
    metadata: dict[str, str] = {}
    header_row = 0
    for row_number in range(1, min(sheet.max_row, 30) + 1):
        label = clean_text(sheet.cell(row_number, 1).value)
        if label == "Hafta":
            header_row = row_number
            break
        if label:
            metadata[label] = clean_text(sheet.cell(row_number, 2).value)
    if not header_row:
        raise ImportValidationError("'Hafta' başlık satırı bulunamadı.")
    return metadata, header_row


def append_value(target: dict[str, str], key: str, value: str) -> None:
    if not value:
        return
    current = target.get(key, "")
    if not current:
        target[key] = value
    elif value not in current.split("\n"):
        target[key] = f"{current}\n{value}"


def read_rows(sheet: Any, header_row: int) -> list[dict[str, Any]]:
    headers = [clean_text(sheet.cell(header_row, column).value) for column in range(1, sheet.max_column + 1)]
    if not headers or headers[0] != "Hafta":
        raise ImportValidationError("İlk plan sütunu 'Hafta' olmalı.")

    rows: list[dict[str, Any]] = []
    for row_number in range(header_row + 1, sheet.max_row + 1):
        values = [clean_text(sheet.cell(row_number, column).value) for column in range(1, len(headers) + 1)]
        if not any(values):
            continue

        week_text = values[0]
        week_match = re.search(r"\d+", week_text)
        week_number = int(week_match.group()) if week_match else len(rows) + 1
        canonical: dict[str, str] = {}
        extras: dict[str, str] = {}
        date_text = ""

        for header, value in zip(headers, values):
            if not header or not value:
                continue
            mapped = canonical_header(header)
            if mapped == "WEEK_NUMBER":
                continue
            if mapped == "DATE":
                date_text = value
            elif mapped:
                append_value(canonical, mapped, value)
            else:
                extras[header] = value

        row: dict[str, Any] = {
            "HAFTA": f"{week_number}. Hafta:\n{date_text}" if date_text else f"{week_number}. Hafta",
            "AY": month_from_date(date_text),
            "SAAT": canonical.pop("SAAT", ""),
            "ÜNİTE": canonical.pop("ÜNİTE", ""),
            "KONU": canonical.pop("KONU", ""),
            "KAZANIM": canonical.pop("KAZANIM", ""),
            "BELİRLİ GÜN VE HAFTALAR": canonical.pop("BELİRLİ GÜN VE HAFTALAR", ""),
            "SDB": canonical.pop("SDB", ""),
            "OB": canonical.pop("OB", ""),
        }
        extras.update(canonical)
        if extras:
            row["EK_ALANLAR"] = extras
        rows.append(row)

    if not rows:
        raise ImportValidationError("Haftalık plan kaydı bulunamadı.")
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_value(metadata: dict[str, str], label: str, required: bool = False) -> str:
    value = clean_text(metadata.get(label))
    if required and not value:
        raise ImportValidationError(f"Zorunlu metadata eksik: {label}")
    return value


def import_workbook(path: Path, source_root: Path, period: str) -> tuple[dict[str, Any], dict[str, Any]]:
    sheet = read_xlsx_sheet(path)
    metadata, header_row = read_metadata(sheet)
    plan_id_text = metadata_value(metadata, "Plan No", required=True)
    if not plan_id_text.isdigit():
        raise ImportValidationError(f"Plan No sayısal olmalı: {plan_id_text}")
    plan_id = int(plan_id_text)
    source_period = metadata_value(metadata, "Yıl", required=True)
    if source_period != period:
        raise ImportValidationError(f"Dönem uyuşmuyor: {source_period} != {period}")
    grade = normalize_grade(metadata_value(metadata, "Sınıf", required=True))
    subject = normalize_subject(metadata_value(metadata, "Ders", required=True), grade)
    group = metadata_value(metadata, "Ders Grubu", required=True)
    branch = metadata_value(metadata, "Branş/Alan", required=True)
    rows = read_rows(sheet, header_row)

    relative_source = path.relative_to(source_root).as_posix()
    plan_payload = {
        "egitim_yili": period,
        "sinif": grade,
        "ders": subject,
        "grup": group,
        "brans": branch,
        "sistem": metadata_value(metadata, "Sistem"),
        "yayinevi": metadata_value(metadata, "Yayınevi"),
        "kaynak": metadata_value(metadata, "Kaynak"),
        "plan": rows,
    }
    manifest_entry = {
        "id": plan_id,
        "kaynak_dosya": relative_source,
        "arsiv_dosya": f"xlsx/{plan_id}.xlsx",
        "sha256": sha256(path),
        "grup": group,
        "brans": branch,
        "sinif": grade,
        "ders": subject,
        "sistem": plan_payload["sistem"],
        "yayinevi": plan_payload["yayinevi"],
        "kaynak": plan_payload["kaynak"],
    }
    return plan_payload, manifest_entry


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def validate_outputs(
    index_payload: dict[str, Any],
    manifest_payload: dict[str, Any],
    public_plans_dir: Path,
    archive_xlsx_dir: Path,
    expected_plans: int,
    expected_rows: int,
) -> None:
    entries = index_payload["dosyalar"]
    manifest_entries = manifest_payload["dosyalar"]
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise ImportValidationError("Tekrarlı plan ID bulundu.")
    if expected_plans and len(entries) != expected_plans:
        raise ImportValidationError(f"Plan sayısı {len(entries)}; beklenen {expected_plans}.")
    if expected_rows and index_payload["toplam_kayit"] != expected_rows:
        raise ImportValidationError(
            f"Hafta kaydı {index_payload['toplam_kayit']}; beklenen {expected_rows}."
        )
    if len(manifest_entries) != len(entries):
        raise ImportValidationError("XLSX manifesti ile plan indexi farklı sayıda kayıt içeriyor.")
    for entry in entries:
        plan_path = public_plans_dir / f"{entry['id']}.json"
        if not plan_path.is_file():
            raise ImportValidationError(f"Eksik plan JSON'u: {plan_path.name}")
    for entry in manifest_entries:
        archive_path = archive_xlsx_dir / f"{entry['id']}.xlsx"
        if not archive_path.is_file() or sha256(archive_path) != entry["sha256"]:
            raise ImportValidationError(f"XLSX doğrulaması başarısız: {entry['id']}")


def source_workbooks(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*.xlsx")
        if not any(part in IGNORED_SOURCE_PARTS for part in path.relative_to(source_root).parts)
    )


def replace_directory(source: Path, target: Path) -> None:
    backup = target.with_name(f".{target.name}.backup")
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        os.replace(target, backup)
    try:
        os.replace(source, target)
    except Exception:
        if backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def run_import(source_root: Path, period: str, expected_plans: int, expected_rows: int) -> dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    if not source_root.is_dir():
        raise ImportValidationError(f"Kaynak klasör bulunamadı: {source_root}")
    workbooks = source_workbooks(source_root)
    if not workbooks:
        raise ImportValidationError("Kaynak klasörde XLSX bulunamadı.")

    build_root = REPO_ROOT / "build" / "yearly_import"
    build_root.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=f"{period}-", dir=build_root))
    staged_archive = staging_root / "archive"
    staged_xlsx = staged_archive / "xlsx"
    staged_public = staging_root / "public"
    staged_plans = staged_public / "plans"
    staged_xlsx.mkdir(parents=True)
    staged_plans.mkdir(parents=True)

    index_entries: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []
    total_rows = 0
    try:
        for workbook_path in workbooks:
            try:
                plan_payload, manifest_entry = import_workbook(workbook_path, source_root, period)
            except Exception as error:
                raise ImportValidationError(f"{workbook_path.relative_to(source_root)}: {error}") from error
            plan_id = manifest_entry["id"]
            if any(entry["id"] == plan_id for entry in index_entries):
                raise ImportValidationError(f"Tekrarlı Plan No: {plan_id}")
            rows = plan_payload["plan"]
            total_rows += len(rows)
            public_path = f"years/{period}/plans/{plan_id}.json"
            index_entries.append(
                {
                    "id": plan_id,
                    "sinif": plan_payload["sinif"],
                    "ders": plan_payload["ders"],
                    "kayit_sayisi": len(rows),
                    "dosya": public_path,
                    "egitim_yili": period,
                    "grup": plan_payload["grup"],
                    "brans": plan_payload["brans"],
                    "sistem": plan_payload["sistem"],
                    "yayinevi": plan_payload["yayinevi"],
                }
            )
            manifest_entries.append(manifest_entry)
            json_dump(staged_plans / f"{plan_id}.json", plan_payload)
            shutil.copy2(workbook_path, staged_xlsx / f"{plan_id}.xlsx")

        index_entries.sort(key=lambda item: (0 if item["sinif"] == "Hazırlık" else int(item["sinif"]), item["ders"], item["id"]))
        manifest_entries.sort(key=lambda item: item["id"])
        generated_at = datetime.fromtimestamp(
            max(path.stat().st_mtime for path in workbooks),
            timezone.utc,
        ).isoformat()
        index_payload = {
            "surum": 2,
            "egitim_yili": period,
            "uretildi_at": generated_at,
            "toplam": len(index_entries),
            "toplam_kayit": total_rows,
            "dosyalar": index_entries,
        }
        manifest_payload = {
            "surum": 1,
            "egitim_yili": period,
            "uretildi_at": generated_at,
            "toplam": len(manifest_entries),
            "dosyalar": manifest_entries,
        }
        grade_counts = Counter(entry["sinif"] for entry in index_entries)
        group_counts = Counter(entry["grup"] for entry in index_entries)
        catalog_payload = {
            "egitim_yili": period,
            "total_plans": len(index_entries),
            "total_rows": total_rows,
            "grade_counts": dict(sorted(grade_counts.items())),
            "group_counts": dict(sorted(group_counts.items())),
            "all_variants_preserved": True,
        }
        json_dump(staged_public / "index.json", index_payload)
        json_dump(staged_public / "meta" / "catalog.json", catalog_payload)
        json_dump(staged_archive / "manifest.json", manifest_payload)
        validate_outputs(
            index_payload,
            manifest_payload,
            staged_plans,
            staged_xlsx,
            expected_plans,
            expected_rows,
        )

        target_public = PUBLIC_DIR / "years" / period
        target_archive = ARCHIVE_DIR / period
        target_public.parent.mkdir(parents=True, exist_ok=True)
        target_archive.parent.mkdir(parents=True, exist_ok=True)
        replace_directory(staged_public, target_public)
        replace_directory(staged_archive, target_archive)
        json_dump(PUBLIC_DIR / "index.json", index_payload)
        json_dump(PUBLIC_DIR / "meta" / "catalog.json", catalog_payload)
        return catalog_payload
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Yıllık plan XLSX arşivini uygulama JSON'una dönüştürür.")
    parser.add_argument("--source", type=Path, required=True, help="XLSX dosyalarının kök klasörü")
    parser.add_argument("--period", required=True, help="Eğitim yılı; ör. 2026-2027")
    parser.add_argument("--expected-plans", type=int, default=0)
    parser.add_argument("--expected-rows", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_import(args.source, args.period, args.expected_plans, args.expected_rows)
    except ImportValidationError as error:
        print(f"HATA: {error}")
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

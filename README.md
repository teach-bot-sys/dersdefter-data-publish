# Dersdefter Plan Kaynağı

Bu repo artık iki katmanla düşünülmeli:

- `data/`: mevcut ham yayın deposu. Uygulamanın bugün kullandığı kaynak burada duruyor.
- `public/`: GitHub üzerinden servis edilecek hedef yayın yüzeyi. `scripts/publish/build_public.py` ile üretilir.

## Dizinler

- `scripts/fetch/`: kaynak indirme işleri için ayrılan alan
- `scripts/transform/`: DOCX -> JSON ve normalizasyon işleri için ayrılan alan
- `scripts/publish/`: uygulamanın tüketeceği yayın çıktısını üretir
- `scripts/audit/`: kalite kontrol ve doğrulama araçları
- `word_planlar/`: ham DOCX arşivi
- `json_planlar/`: ara JSON çıktıları
- `public/index.json`: yayınlanan plan listesi
- `public/plans/<id>.json`: ID bazlı tekil plan dosyaları
- `public/meta/catalog.json`: sınıf dağılımı, tekrar eden dersler, şüpheli adlar ve legacy dosya eşlemeleri

## Akış

1. Ham planlar `word_planlar/` içine indirilir.
2. DOCX dosyaları ara JSON olarak `json_planlar/` içine dönüştürülür.
3. Gerekli isim temizliği ve yayın biçimi `public/` altında üretilir.
4. Yayın öncesi `scripts/audit/validate_public.py` çalıştırılır.

## Komutlar

```bash
python3 scripts/publish/build_public.py
python3 scripts/audit/validate_public.py
```

## XLSX yıllık plan yayını

Yeni dönem XLSX arşivi, eski `public/plans/` dosyalarını silmeden versioned JSON olarak yayımlanır:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/import/import_yearly_plan_xlsx.py \
  --source '/Users/fatihkorkmaz/Desktop/2026-2027 yıllık planı' \
  --period 2026-2027 \
  --expected-plans 1696 \
  --expected-rows 69555
python3 scripts/audit/validate_public.py \
  --period 2026-2027 \
  --expected-plans 1696 \
  --expected-rows 69555 \
  --check-xlsx
```

- `archive/<dönem>/xlsx/<id>.xlsx`: SHA-256 manifestli kaynak arşiv
- `public/years/<dönem>/`: uygulamanın dönem bazlı JSON yayını
- `public/index.json`: eski uygulamalar için güncel dönem giriş noktası

# ZümreAsist web yayını

Resmî ürün sitesi: https://teach-bot-sys.github.io/dersdefter-data-publish/

Site, mevcut GitHub Pages yapılandırmasıyla `main` dalının kökünden yayımlanır. Mobil uygulamanın JSON ve Excel kaynakları aynı depoda bulunur; web sitesi üreticisi `public/` ve `data/` içeriğini değiştirmez.

## Üretim ve doğrulama

```sh
python3 scripts/publish/build_plan_site.py
python3 scripts/audit/validate_plan_site.py
```

Üretici güncel `public/years/2026-2027/index.json` dosyasını okur. Plan sayıları, sınıf katalogları ve makine tarafından okunabilir özetler bu kaynaktan üretilir. `scripts/publish/plan-url-map.json`, marka değişiminden önceki 1.677 ders adresini plan kimlikleri üzerinden korur. Ders başlığı düzeltildiğinde eski bağlantı çalışmaya devam eder. Birden fazla eski adresin tek plana birleşmesi durumunda üretim durur; yönlendirme kararı açıkça verilmelidir.

Görsel stil `assets/site.css` dosyasındadır. Logo uygulamanın ZümreAsist simgesidir. Eski marka taşıyan ekran görüntüleri yeni sayfalarda kullanılmaz. Kaynak ders dosyaları, uygulama paket kimliği ve mağaza kayıtları korunur.

## Arama ve yapay zekâ erişimi

Sayfaların temel içeriği JavaScript gerektirmeyen HTML olarak yayımlanır. Her sayfada tek ana başlık, açıklama, kendisine işaret eden canonical, sosyal paylaşım bilgileri ve görünür içerikle uyumlu JSON-LD bulunur. Ana sayfada uygulama, geliştirici, önceki ad, platformlar, kullanım koşulları ve SSS açıklanır. Puan ve yorum uydurulmaz; yapılandırılmış veri zengin sonuç garantisi vermez.

Sınıf katalogları tüm ders sayfalarını normal HTML bağlantılarıyla erişilebilir kılar. Site haritasının `lastmod` alanı yalnız sayfa içeriği değiştiğinde güncellenir. `llms.txt` kısa uygulama özeti, `llms-full.txt` bu özet ve ders bağlantılarıdır. Bunlar yardımcı keşif dosyalarıdır; arama sıralaması veya yapay zekâ önerisi garantisi değildir.

GitHub Pages proje dizinindeki `robots.txt`, alan adı kökündeki dosyanın yerine geçmez. Geçerli dosya `https://teach-bot-sys.github.io/robots.txt` adresindedir ve `teach-bot-sys/teach-bot-sys.github.io` deposunda yönetilir. Kök dosya taramaya izin verir ve bu sitenin haritasını bildirir. Kök `llms.txt` aynı uygulamayı tanımlar; uygulama bilgileri değişirse bu kopya da güncellenmelidir. Eski `dersdefter-site/` adresi canonical ve HTML yönlendirmesiyle resmî siteye gider. GitHub Pages sunucu taraflı 301 kuralı sunmadığı için HTML yönlendirmesi kullanılır.

## Yayın sonrası ölçüm

Google Search Console ve Bing Webmaster Tools üzerinde site sahipliği doğrulandıktan sonra `sitemap.xml` gönderilebilir; ana sayfa ve rehberler URL denetimiyle kontrol edilebilir. Bu çalışma sırasında bu hesaplarda sahiplik doğrulaması veya indeksleme talebi gönderilmedi. Search Console gösterimleri ve marka sorguları, mağazaya yönlenen bağlantılar ve mağaza konsollarındaki edinme verileriyle sonuçlar takip edilmelidir. Mağaza bağlantılarında kampanya parametreleri bulunur. Bu web çalışması mağaza metinlerini veya uygulama sürümünü değiştirmez.

Başvuru kaynakları:

- Google AI özellikleri ve web siteleri: https://developers.google.com/search/docs/appearance/ai-features
- Google yazılım uygulaması yapılandırılmış verisi: https://developers.google.com/search/docs/appearance/structured-data/software-app
- Google robots.txt kapsamı: https://developers.google.com/search/docs/crawling-indexing/robots/intro
- OpenAI arama tarayıcıları: https://developers.openai.com/api/docs/bots

## 19 Eylül 2026 doğrulaması

- 1.700 HTML sayfasında canonical, metadata, JSON-LD, tek H1, iç bağlantı ve gezinme erişimi kontrol edildi.
- Önceden yayımlanan 1.677 ders adresi korundu; güncel katalog 1.701 plan ve 69.754 haftalık kaydı içeriyor.
- Ana sayfa, üç rehber, genel katalog, 11. sınıf kataloğu ve Seçmeli İngilizce plan sayfası başsız Chromium ile mobil ve masaüstünde render edildi. Axe WCAG A/AA kontrolleri, yatay taşma, görsel yükleme ve SSS açma işlemi kontrol edildi.
- App Store ve Google Play bağlantıları HTTP 200 döndü. Önceki `kairalabs.com/privacy` adresinin DNS çözümü başarısız olduğu için alt menüde her mağazanın mevcut, HTTP 200 dönen gizlilik politikası bağlantısı kullanıldı; politikaların metni değiştirilmedi.
- Mobil uygulamanın `public/` ve `data/` kaynakları ile `app-ads.txt` değiştirilmedi.

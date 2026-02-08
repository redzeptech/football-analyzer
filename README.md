# Futbol Analiz Aracı

CSV veya API-Football ile takım performans analizi. Dünya liglerini destekler.

## Kurulum

```bash
# Sanal ortam (isteğe bağlı)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Linux/Mac

# Bağımlılıklar
pip install -r requirements.txt
```

### API Anahtarı (Dünya Ligleri)

API-Football (api-sports.io) ile lig listesi, takım arama ve maç verisi almak için:

1. [api-football.com](https://www.api-football.com/) adresinden ücretsiz hesap açın
2. Dashboard'dan API key alın
3. Proje kökünde `.env` dosyası oluşturun:
   ```
   API_FOOTBALL_KEY=your_api_key_here
   ```
4. `.env.example` dosyasını referans alabilirsiniz

**API anahtarı yoksa** program `sample_matches.csv` ile çalışır (CSV modu).

## Kullanım

### API Modu (Dünya Ligleri)

```bash
# Ligleri listele (league_id, league_name, country)
python main.py --list-leagues

# Takım ara (team_id, team_name, country)
python main.py --search-team "Arsenal"

# Tek takım analizi (lig + sezon + takım ID)
python main.py --team-id 42 --league-id 39 --season 2025 --last 10

# İki takım karşılaştırma
python main.py --team1-id 42 --team2-id 49 --league-id 39 --season 2025 --last 10
```

### CSV Modu (API anahtarı olmadan)

```bash
# Tek takım
python main.py --team Fenerbahce

# Karşılaştırma
python main.py --team1 Fenerbahce --team2 Galatasaray

# Farklı CSV
python main.py --team Galatasaray --csv matches.csv -o rapor.html
```

### Argümanlar

| Argüman | Açıklama |
|---------|----------|
| `--list-leagues` | Ligleri listele (API) |
| `--search-team QUERY` | Takım ara (API, min 3 karakter) |
| `--team-id ID` | API: Takım ID (tek takım) |
| `--team1-id`, `--team2-id` | API: Karşılaştırma takım ID'leri |
| `--league-id ID` | API: Lig ID |
| `--season YYYY` | API: Sezon (varsayılan: 2025) |
| `--team`, `--team1`, `--team2` | CSV: Takım adı |
| `--last`, `-n` | Son maç sayısı (varsayılan: 10) |
| `--csv` | CSV dosya yolu |
| `--output`, `-o` | HTML rapor dosyası |

## Örnek Akış (API)

```bash
# 1. Ligleri gör
python main.py --list-leagues

# 2. Premier League = 39, Arsenal ara
python main.py --search-team "Arsenal"

# 3. Arsenal (42) analizi, Premier League (39), 2025 sezonu
python main.py --team-id 42 --league-id 39 --season 2025 -n 10

# 4. Arsenal vs Chelsea karşılaştırma
python main.py --team1-id 42 --team2-id 49 --league-id 39 --season 2025
```

## Çıktılar

- **Terminal**: Form, gol ortalaması, Over 2.5, BTTS, iç saha/deplasman özeti
- **report.html**: UTF-8, temiz HTML rapor
- **TAHMİN ÖZETİ**: Karşılaştırma modunda heuristic tahminler

## Hata Mesajları

- **API anahtarı yok**: `.env` dosyasına `API_FOOTBALL_KEY` ekleyin
- **Rate limit aşıldı**: Birkaç dakika bekleyip tekrar deneyin
- **Timeout**: İnternet bağlantısını kontrol edin

## Dosya Yapısı

```
FootballAnalyzer/
├── main.py              # CLI ve ana akış
├── analysis.py          # Metrik hesapları
├── report.py            # Terminal ve HTML rapor
├── api_client.py        # API-Football istekleri
├── data_client.py       # API / CSV veri katmanı
├── sample_matches.csv   # Örnek CSV verisi
├── .env.example         # API key şablonu
├── requirements.txt
└── README.md
```
## Quick Start (Windows)

1) Projeyi indir: https://github.com/redzeptech/football-analyzer.git

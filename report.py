# -*- coding: utf-8 -*-
"""
Rapor Oluşturma Modülü
HTML ve terminal çıktısı üretir.
"""

from typing import Optional
from analysis import TeamAnalysis, MatchStats


def _format_ratio(count: int, total: int) -> str:
    """Oranı yüzde olarak formatlar."""
    if total == 0:
        return "0.0%"
    return f"{(count / total) * 100:.1f}%"


def _format_avg(num: float, denom: int) -> str:
    """Ortalamayı formatlar."""
    if denom == 0:
        return "0.00"
    return f"{num / denom:.2f}"


def _stats_row(label: str, stats: MatchStats, include_ratios: bool = True) -> list:
    """Tek satır için değerler listesi."""
    row = [
        label,
        stats.played,
        stats.wins,
        stats.draws,
        stats.losses,
        stats.form_points,
        _format_avg(stats.goals_for, stats.played),
        _format_avg(stats.goals_against, stats.played),
    ]
    if include_ratios:
        row.append(_format_ratio(stats.over_25_count, stats.played))
        row.append(_format_ratio(stats.btts_count, stats.played))
    return row


def print_terminal_report(analysis: TeamAnalysis) -> None:
    """
    Terminalde özet tablo yazdırır.
    
    Args:
        analysis: TeamAnalysis sonucu
    """
    a = analysis
    t, h, away = a.total, a.home, a.away
    
    print("\n" + "=" * 70)
    print(f"  FUTBOL ANALİZ RAPORU - {a.team_name} (Son {t.played} maç)")
    print("=" * 70)
    
    headers = [
        "Kategori", "O", "G", "B", "M", "Puan",
        "Atılan Ort.", "Yenen Ort.", "Over 2.5", "BTTS"
    ]
    
    # Tablo başlığı
    header_line = " | ".join(f"{h:^12}" for h in headers)
    print("\n" + "-" * len(header_line))
    print(header_line)
    print("-" * len(header_line))
    
    for label, stats in [
        ("Toplam", t),
        ("İç Saha", h),
        ("Deplasman", away),
    ]:
        row = _stats_row(label, stats)
        row_line = " | ".join(f"{str(x):^12}" for x in row)
        print(row_line)
    
    print("-" * len(header_line))
    print("\nAçıklama: O=Oynanan, G=Galibiyet, B=Beraberlik, M=Mağlubiyet")
    print("Over 2.5: Toplam gol > 2, BTTS: Her iki takım da gol attı")
    print()


def generate_html_report(analysis: TeamAnalysis, output_path: str = "report.html") -> None:
    """
    HTML rapor dosyası oluşturur.
    
    Args:
        analysis: TeamAnalysis sonucu
        output_path: Çıktı dosya yolu
    """
    a = analysis
    t, h, away = a.total, a.home, a.away
    
    # Tablo satırları
    rows_html = ""
    for label, stats in [
        ("Toplam", t),
        ("İç Saha", h),
        ("Deplasman", away),
    ]:
        row = _stats_row(label, stats)
        first_cell = f"<td><strong>{label}</strong></td>"
        rest_cells = "".join(f"<td>{x}</td>" for x in row[1:])
        rows_html += f"<tr>{first_cell}{rest_cells}</tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Futbol Analiz - {a.team_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: #e94560;
        }}
        .subtitle {{
            color: #a0a0a0;
            margin-bottom: 2rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        th, td {{
            padding: 0.9rem 1rem;
            text-align: center;
        }}
        th {{
            background: #e94560;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{ background: rgba(255,255,255,0.03); }}
        tr:hover {{ background: rgba(233,69,96,0.15); }}
        .footer {{
            margin-top: 2rem;
            font-size: 0.85rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚽ Futbol Analiz Raporu</h1>
        <p class="subtitle">{a.team_name} — Son {t.played} maç</p>
        
        <table>
            <thead>
                <tr>
                    <th>Kategori</th>
                    <th>O</th>
                    <th>G</th>
                    <th>B</th>
                    <th>M</th>
                    <th>Puan</th>
                    <th>Atılan Ort.</th>
                    <th>Yenen Ort.</th>
                    <th>Over 2.5</th>
                    <th>BTTS</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        
        <p class="footer">
            O = Oynanan | G = Galibiyet | B = Beraberlik | M = Mağlubiyet<br>
            Over 2.5 = Toplam gol &gt; 2 | BTTS = Her iki takım da gol attı
        </p>
    </div>
</body>
</html>"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def _get_comparison_commentary(a1: TeamAnalysis, a2: TeamAnalysis) -> str:
    """Hangi takımın daha formda göründüğüne dair basit yorum üretir."""
    t1, t2 = a1.total, a2.total
    if t1.played == 0 or t2.played == 0:
        return "Yeterli veri yok."
    
    avg1 = t1.goals_for / t1.played
    avg2 = t2.goals_for / t2.played
    over1 = (t1.over_25_count / t1.played) * 100
    over2 = (t2.over_25_count / t2.played) * 100
    btts1 = (t1.btts_count / t1.played) * 100
    btts2 = (t2.btts_count / t2.played) * 100
    
    score1 = 0
    score2 = 0
    if t1.form_points > t2.form_points:
        score1 += 1
    elif t2.form_points > t1.form_points:
        score2 += 1
    if avg1 > avg2:
        score1 += 1
    elif avg2 > avg1:
        score2 += 1
    if over1 > over2:
        score1 += 1
    elif over2 > over1:
        score2 += 1
    if btts1 > btts2:
        score1 += 1
    elif btts2 > btts1:
        score2 += 1
    
    if score1 > score2:
        return f"Son {t1.played} maça göre {a1.team_name} daha formda görünüyor."
    elif score2 > score1:
        return f"Son {t2.played} maça göre {a2.team_name} daha formda görünüyor."
    else:
        return "İki takım da benzer formda; maç dengeli geçebilir."


def print_comparison_report(a1: TeamAnalysis, a2: TeamAnalysis) -> None:
    """
    İki takım karşılaştırma raporunu terminale yazdırır.
    """
    t1, t2 = a1.total, a2.total
    avg1 = _format_avg(t1.goals_for, t1.played)
    avg2 = _format_avg(t2.goals_for, t2.played)
    over1 = _format_ratio(t1.over_25_count, t1.played)
    over2 = _format_ratio(t2.over_25_count, t2.played)
    btts1 = _format_ratio(t1.btts_count, t1.played)
    btts2 = _format_ratio(t2.btts_count, t2.played)
    
    print("\n" + "=" * 50)
    print("  TAKIM KARŞILAŞTIRMA RAPORU")
    print("=" * 50)
    print()
    print(f"{a1.team_name} (Son {t1.played} maç):")
    print(f"  Form puanı:    {t1.form_points}")
    print(f"  Gol ortalaması: {avg1}")
    print(f"  Over 2.5:     {over1}")
    print(f"  BTTS:         {btts1}")
    print()
    print(f"{a2.team_name} (Son {t2.played} maç):")
    print(f"  Form puanı:    {t2.form_points}")
    print(f"  Gol ortalaması: {avg2}")
    print(f"  Over 2.5:     {over2}")
    print(f"  BTTS:         {btts2}")
    print()
    print("-" * 50)
    commentary = _get_comparison_commentary(a1, a2)
    print(f"Yorum: {commentary}")
    print()


def print_prediction_summary(summary: dict) -> None:
    """TAHMİN ÖZETİ bölümünü terminale yazdırır."""
    print("TAHMİN ÖZETİ")
    print("-" * 50)
    print(f"- BTTS: {summary['btts']['level']} — {summary['btts']['gerekce']}")
    print(f"- Over 2.5: {summary['over25']['level']} — {summary['over25']['gerekce']}")
    print(f"- Gollü maç eğilimi: {summary['gollu_mac']['level']} — {summary['gollu_mac']['gerekce']}")
    print(f"- 1X2 eğilimi: {summary['eğilim_1x2']['sonuc']} — {summary['eğilim_1x2']['gerekce']}")
    if summary.get("risk_notu"):
        print(f"- Risk notu: {summary['risk_notu']}")
    print()


def _prediction_summary_to_html(summary: dict) -> str:
    """Tahmin özeti dict'ini HTML'e çevirir."""
    lines = [
        f"<li><strong>BTTS:</strong> {summary['btts']['level']} — {summary['btts']['gerekce']}</li>",
        f"<li><strong>Over 2.5:</strong> {summary['over25']['level']} — {summary['over25']['gerekce']}</li>",
        f"<li><strong>Gollü maç:</strong> {summary['gollu_mac']['level']} — {summary['gollu_mac']['gerekce']}</li>",
        f"<li><strong>1X2 eğilimi:</strong> {summary['eğilim_1x2']['sonuc']} — {summary['eğilim_1x2']['gerekce']}</li>",
    ]
    if summary.get("risk_notu"):
        lines.append(f"<li><strong>Risk notu:</strong> {summary['risk_notu']}</li>")
    return "<ul style='margin-top: 0.5rem; line-height: 1.6;'>" + "".join(lines) + "</ul>"


def generate_comparison_html_report(
    a1: TeamAnalysis,
    a2: TeamAnalysis,
    output_path: str = "report.html",
    match_comment: str = "",
    prediction_summary: Optional[dict] = None,
) -> None:
    """İki takım karşılaştırması için HTML rapor oluşturur."""
    t1, t2 = a1.total, a2.total
    avg1 = _format_avg(t1.goals_for, t1.played)
    avg2 = _format_avg(t2.goals_for, t2.played)
    over1 = _format_ratio(t1.over_25_count, t1.played)
    over2 = _format_ratio(t2.over_25_count, t2.played)
    btts1 = _format_ratio(t1.btts_count, t1.played)
    btts2 = _format_ratio(t2.btts_count, t2.played)
    commentary = _get_comparison_commentary(a1, a2)

    tahmin_html = ""
    if prediction_summary:
        tahmin_html = f"""
    <h2 style="margin-top: 2rem; color: #e94560;">TAHMİN ÖZETİ</h2>
    {_prediction_summary_to_html(prediction_summary)}
"""

    comparison_html = f"""
    <h2 style="margin-top: 2.5rem; color: #e94560;">Team Comparison</h2>
    <table style="margin-top: 1rem;">
        <thead>
            <tr>
                <th>Metrik</th>
                <th>{a1.team_name}</th>
                <th>{a2.team_name}</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>Form puanı</td><td>{t1.form_points}</td><td>{t2.form_points}</td></tr>
            <tr><td>Gol ortalaması</td><td>{avg1}</td><td>{avg2}</td></tr>
            <tr><td>Over 2.5</td><td>{over1}</td><td>{over2}</td></tr>
            <tr><td>BTTS</td><td>{btts1}</td><td>{btts2}</td></tr>
        </tbody>
    </table>
    <p class="footer" style="margin-top: 1rem; font-style: italic;">{commentary}</p>
    <h2 style="margin-top: 2rem; color: #e94560;">MAÇ YORUMU</h2>
    <p class="footer" style="margin-top: 0.5rem;">{match_comment}</p>
    {tahmin_html}
"""
    
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Takım Karşılaştırma - {a1.team_name} vs {a2.team_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: #e94560;
        }}
        .subtitle {{
            color: #a0a0a0;
            margin-bottom: 2rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        th, td {{
            padding: 0.9rem 1rem;
            text-align: center;
        }}
        th {{
            background: #e94560;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{ background: rgba(255,255,255,0.03); }}
        tr:hover {{ background: rgba(233,69,96,0.15); }}
        .footer {{
            margin-top: 2rem;
            font-size: 0.85rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚽ Takım Karşılaştırma Raporu</h1>
        <p class="subtitle">{a1.team_name} vs {a2.team_name} — Son {t1.played} maç</p>
        {comparison_html}
    </div>
</body>
</html>"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

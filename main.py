# -*- coding: utf-8 -*-
"""
Futbol Analiz Aracı
CSV veya API-Football ile takım performans analizi.
"""

import argparse
import sys
from pathlib import Path

from analysis import (
    analyze_team,
    analyze_team_from_df,
    generate_match_comment,
    predict_summary,
)
from report import (
    print_terminal_report,
    generate_html_report,
    print_comparison_report,
    print_prediction_summary,
    generate_comparison_html_report,
)
from data_client import (
    has_api_key,
    get_api_client,
    fetch_team_fixtures_from_api,
    load_csv_matches,
)
from api_client import APIError


def parse_args() -> argparse.Namespace:
    """Komut satırı argümanlarını ayrıştırır."""
    parser = argparse.ArgumentParser(
        description="Futbol takımı analiz aracı. CSV veya API-Football ile veri alır."
    )
    # API modu
    parser.add_argument("--list-leagues", action="store_true", help="Ligleri listele (API)")
    parser.add_argument("--search-team", type=str, metavar="QUERY", help="Takım ara (API)")
    parser.add_argument("--team-id", type=int, help="API: Takım ID (tek takım analizi)")
    parser.add_argument("--team1-id", type=int, help="API: 1. takım ID (karşılaştırma)")
    parser.add_argument("--team2-id", type=int, help="API: 2. takım ID (karşılaştırma)")
    parser.add_argument("--league-id", type=int, help="API: Lig ID")
    parser.add_argument("--season", type=int, default=2025, help="API: Sezon yılı (varsayılan: 2025)")
    # CSV modu
    parser.add_argument("--team", "-t", type=str, help="CSV: Analiz edilecek takım adı")
    parser.add_argument("--team1", type=str, help="CSV: Karşılaştırma 1. takım")
    parser.add_argument("--team2", type=str, help="CSV: Karşılaştırma 2. takım")
    # Ortak
    parser.add_argument("--last", "-n", type=int, default=10, help="Son maç sayısı (varsayılan: 10)")
    parser.add_argument("--csv", type=str, default="sample_matches.csv", help="CSV dosya yolu")
    parser.add_argument("--output", "-o", type=str, default="report.html", help="HTML rapor dosyası")
    return parser.parse_args()


def main() -> int:
    """Ana giriş noktası."""
    args = parse_args()

    # 1) Lig listeleme
    if args.list_leagues:
        return _run_list_leagues()

    # 2) Takım arama
    if args.search_team:
        return _run_search_team(args.search_team)

    # 3) API tek takım
    if args.team_id is not None and args.league_id is not None:
        return _run_api_single_team(args)

    # 4) API karşılaştırma
    if args.team1_id is not None and args.team2_id is not None and args.league_id is not None:
        return _run_api_comparison(args)

    # 5) CSV tek takım
    if args.team is not None:
        return _run_csv_single_team(args)

    # 6) CSV karşılaştırma
    if args.team1 is not None and args.team2 is not None:
        return _run_csv_comparison(args)

    print("Hata: Geçerli bir komut belirtin.")
    print("Örnek: --list-leagues, --search-team QUERY, --team-id X --league-id Y, --team ADI")
    return 1


def _run_list_leagues() -> int:
    if not has_api_key():
        print("Hata: API anahtarı yok. .env dosyasına API_FOOTBALL_KEY ekleyin.")
        print("CSV modu için: --team ADI veya --team1 A --team2 B kullanın.")
        return 1
    try:
        client = get_api_client()
        leagues = client.get_leagues()
        if not leagues:
            print("Lig bulunamadı.")
            return 0
        print("\nLig Listesi (league_id | league_name | country)")
        print("-" * 60)
        for r in leagues[:100]:  # ilk 100
            print(f"{r['league_id']:>10} | {r['league_name']:<30} | {r['country']}")
        if len(leagues) > 100:
            print(f"... ve {len(leagues) - 100} lig daha")
        return 0
    except APIError as e:
        print(f"Hata: {e}")
        return 1


def _run_search_team(query: str) -> int:
    if not has_api_key():
        print("Hata: API anahtarı yok. .env dosyasına API_FOOTBALL_KEY ekleyin.")
        return 1
    try:
        client = get_api_client()
        teams = client.search_teams(query)
        if not teams:
            print(f"'{query}' için takım bulunamadı.")
            return 0
        print(f"\nTakım Arama: '{query}'")
        print("-" * 50)
        for r in teams[:20]:
            print(f"  team_id: {r['team_id']:<6} | {r['team_name']:<25} | {r['country']}")
        return 0
    except APIError as e:
        print(f"Hata: {e}")
        return 1


def _run_api_single_team(args) -> int:
    if not has_api_key():
        print("Hata: API anahtarı yok. .env dosyasına API_FOOTBALL_KEY ekleyin.")
        return 1
    try:
        df, team_name = fetch_team_fixtures_from_api(
            args.team_id, args.league_id, args.season, args.last
        )
        if df.empty:
            print("Maç verisi bulunamadı. Lig/Sezon/Takım kombinasyonunu kontrol edin.")
            return 1
        analysis = analyze_team_from_df(df, team_name, args.last, exact_match=True)
        if analysis is None:
            print("Analiz yapılamadı.")
            return 1
        print_terminal_report(analysis)
        generate_html_report(analysis, output_path=args.output)
        print(f"HTML rapor kaydedildi: {args.output}")
        return 0
    except APIError as e:
        print(f"Hata: {e}")
        return 1


def _run_api_comparison(args) -> int:
    if not has_api_key():
        print("Hata: API anahtarı yok.")
        return 1
    try:
        df1, name1 = fetch_team_fixtures_from_api(
            args.team1_id, args.league_id, args.season, args.last
        )
        df2, name2 = fetch_team_fixtures_from_api(
            args.team2_id, args.league_id, args.season, args.last
        )
        if df1.empty:
            print(f"Takım 1 ({name1}) için maç bulunamadı.")
            return 1
        if df2.empty:
            print(f"Takım 2 ({name2}) için maç bulunamadı.")
            return 1
        a1 = analyze_team_from_df(df1, name1, args.last, exact_match=True)
        a2 = analyze_team_from_df(df2, name2, args.last, exact_match=True)
        if a1 is None or a2 is None:
            print("Analiz yapılamadı.")
            return 1
        print_comparison_report(a1, a2)
        match_comment = generate_match_comment(a1.total, a2.total)
        print("MAÇ YORUMU")
        print("-" * 50)
        print(match_comment)
        print()
        pred = predict_summary(a1.total, a2.total, team1_name=a1.team_name, team2_name=a2.team_name)
        print_prediction_summary(pred)
        generate_comparison_html_report(
            a1, a2, match_comment=match_comment, prediction_summary=pred, output_path=args.output
        )
        print(f"HTML rapor kaydedildi: {args.output}")
        return 0
    except APIError as e:
        print(f"Hata: {e}")
        return 1


def _run_csv_single_team(args) -> int:
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Hata: '{csv_path}' bulunamadı.")
        return 1
    analysis = analyze_team(str(csv_path), args.team, args.last)
    if analysis is None:
        print(f"Hata: '{args.team}' verilerde bulunamadı.")
        return 1
    print_terminal_report(analysis)
    generate_html_report(analysis, output_path=args.output)
    print(f"HTML rapor kaydedildi: {args.output}")
    return 0


def _run_csv_comparison(args) -> int:
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Hata: '{csv_path}' bulunamadı.")
        return 1
    analysis1 = analyze_team(str(csv_path), args.team1, args.last)
    analysis2 = analyze_team(str(csv_path), args.team2, args.last)
    if analysis1 is None:
        print(f"Hata: '{args.team1}' verilerde bulunamadı.")
        return 1
    if analysis2 is None:
        print(f"Hata: '{args.team2}' verilerde bulunamadı.")
        return 1
    print_comparison_report(analysis1, analysis2)
    match_comment = generate_match_comment(analysis1.total, analysis2.total)
    print("MAÇ YORUMU")
    print("-" * 50)
    print(match_comment)
    print()
    pred = predict_summary(
        analysis1.total, analysis2.total,
        team1_name=analysis1.team_name, team2_name=analysis2.team_name,
    )
    print_prediction_summary(pred)
    generate_comparison_html_report(
        analysis1, analysis2,
        match_comment=match_comment,
        prediction_summary=pred,
        output_path=args.output,
    )
    print(f"HTML rapor kaydedildi: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

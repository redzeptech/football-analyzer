# -*- coding: utf-8 -*-
"""
Futbol Analiz Modülü
Takım performans metriklerini hesaplar.
"""

import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class MatchStats:
    """Tek maç veya maç grubu için istatistikler."""
    played: int
    wins: int
    draws: int
    losses: int
    form_points: int
    goals_for: int
    goals_against: int
    over_25_count: int
    btts_count: int


@dataclass
class TeamAnalysis:
    """Takım analiz sonucu."""
    team_name: str
    total: MatchStats
    home: MatchStats
    away: MatchStats
    matches_df: pd.DataFrame


def load_matches(csv_path: str) -> pd.DataFrame:
    """
    CSV dosyasından maç verilerini yükler.
    
    Args:
        csv_path: CSV dosya yolu
        
    Returns:
        Tarih sıralı maç DataFrame'i
    """
    df = pd.read_csv(csv_path, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


def _normalize_team_name(name: str) -> str:
    """Türkçe karakterleri ASCII karşılıklarına çevirir (eşleştirme için)."""
    tr_map = {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
              "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"}
    for tr, ascii_char in tr_map.items():
        name = name.replace(tr, ascii_char)
    return name.lower()


def _resolve_team_name(df: pd.DataFrame, team: str) -> Optional[str]:
    """Verideki takım adını bulur; Türkçe/ASCII varyasyonlarına toleranslı."""
    all_teams = set(df["home_team"].unique()) | set(df["away_team"].unique())
    team_norm = _normalize_team_name(team)
    for t in all_teams:
        if t == team or _normalize_team_name(t) == team_norm:
            return t
    return None


def get_team_matches(df: pd.DataFrame, team: str, last_n: int) -> pd.DataFrame:
    """
    Belirtilen takımın son N maçını filtreler.
    
    Args:
        df: Tüm maçlar
        team: Takım adı (birebir veya normalize eşleşme)
        last_n: Kaç maç alınacak
        
    Returns:
        Takımın son N maçı
    """
    resolved = _resolve_team_name(df, team)
    if resolved is None:
        return pd.DataFrame()
    mask = (df["home_team"] == resolved) | (df["away_team"] == resolved)
    team_df = df[mask].head(last_n)
    return team_df


def _calculate_stats(df: pd.DataFrame, team: str) -> MatchStats:
    """
    Maç listesinden istatistik hesaplar.
    
    Args:
        df: Maç DataFrame'i (sadece bu takımın maçları)
        team: Takım adı
        
    Returns:
        Hesaplanan MatchStats
    """
    if df.empty:
        return MatchStats(0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    # Takım ev sahibi mi deplasmanda mı?
    is_home = df["home_team"] == team
    
    goals_for = (
        df.loc[is_home, "home_goals"].sum() + 
        df.loc[~is_home, "away_goals"].sum()
    )
    goals_against = (
        df.loc[is_home, "away_goals"].sum() + 
        df.loc[~is_home, "home_goals"].sum()
    )
    
    # Sonuç hesaplama (W=3, D=1, L=0)
    wins = 0
    draws = 0
    losses = 0
    
    for _, row in df.iterrows():
        if row["home_team"] == team:
            hg, ag = row["home_goals"], row["away_goals"]
        else:
            hg, ag = row["away_goals"], row["home_goals"]
        
        if hg > ag:
            wins += 1
        elif hg < ag:
            losses += 1
        else:
            draws += 1
    
    form_points = wins * 3 + draws * 1 + losses * 0
    
    # Over 2.5: toplam gol > 2
    total_goals = df["home_goals"] + df["away_goals"]
    over_25_count = (total_goals > 2).sum()
    
    # BTTS: her iki takım da gol attı
    btts_count = ((df["home_goals"] > 0) & (df["away_goals"] > 0)).sum()
    
    played = len(df)
    
    return MatchStats(
        played=played,
        wins=wins,
        draws=draws,
        losses=losses,
        form_points=form_points,
        goals_for=int(goals_for),
        goals_against=int(goals_against),
        over_25_count=int(over_25_count),
        btts_count=int(btts_count),
    )


def analyze_team_from_df(
    df: pd.DataFrame,
    team: str,
    last_n: int = 10,
    exact_match: bool = False,
) -> Optional[TeamAnalysis]:
    """
    Önceden yüklenmiş DataFrame'den takım analizi yapar.
    API veya CSV kaynaklı df için kullanılır.
    
    Args:
        df: date, home_team, away_team, home_goals, away_goals kolonlu DataFrame
        team: Takım adı
        last_n: Son maç sayısı
        exact_match: True ise sadece tam eşleşme (API için genelde True)
        
    Returns:
        TeamAnalysis veya None
    """
    if df.empty:
        return None
    resolved = team if exact_match else _resolve_team_name(df, team)
    if resolved is None:
        return None
    mask = (df["home_team"] == resolved) | (df["away_team"] == resolved)
    team_df = df[mask].head(last_n)
    if team_df.empty:
        return None
    home_df = team_df[team_df["home_team"] == resolved]
    away_df = team_df[team_df["away_team"] == resolved]
    total_stats = _calculate_stats(team_df, resolved)
    home_stats = _calculate_stats(home_df, resolved)
    away_stats = _calculate_stats(away_df, resolved)
    return TeamAnalysis(
        team_name=resolved,
        total=total_stats,
        home=home_stats,
        away=away_stats,
        matches_df=team_df,
    )


def analyze_team(
    csv_path: str, 
    team: str, 
    last_n: int = 10
) -> Optional[TeamAnalysis]:
    """
    Takımın son N maçını CSV'den analiz eder.
    
    Args:
        csv_path: CSV dosya yolu
        team: Takım adı
        last_n: Analiz edilecek son maç sayısı
        
    Returns:
        TeamAnalysis veya takım bulunamazsa None
    """
    df = load_matches(csv_path)
    return analyze_team_from_df(df, team, last_n, exact_match=False)


def generate_match_comment(team1_stats: MatchStats, team2_stats: MatchStats) -> str:
    """
    İki takımın istatistiklerine göre kısa maç yorumu üretir.
    
    Args:
        team1_stats: 1. takımın toplam istatistikleri
        team2_stats: 2. takımın toplam istatistikleri
        
    Returns:
        Kısa Türkçe yorum metni
    """
    if team1_stats.played == 0 or team2_stats.played == 0:
        return "Yeterli veri yok."
    
    comments = []
    
    # Gol ortalaması 1.5 üzerinde (her iki takım)
    avg1 = team1_stats.goals_for / team1_stats.played
    avg2 = team2_stats.goals_for / team2_stats.played
    if avg1 >= 1.5 and avg2 >= 1.5:
        comments.append("Gollü maç eğilimi")
    
    # BTTS oranı %60 üzerinde (her iki takım)
    btts1 = (team1_stats.btts_count / team1_stats.played) * 100
    btts2 = (team2_stats.btts_count / team2_stats.played) * 100
    if btts1 >= 60 and btts2 >= 60:
        comments.append("İki takım da gol bulabilir")
    
    # Form puanı çok farklı (6+ puan farkı = ~2 maç)
    diff = abs(team1_stats.form_points - team2_stats.form_points)
    if diff >= 6:
        comments.append("Formda takım avantajlı")
    
    # Over 2.5 oranı yüksek (her iki takımda %50+)
    over1 = (team1_stats.over_25_count / team1_stats.played) * 100
    over2 = (team2_stats.over_25_count / team2_stats.played) * 100
    if over1 >= 50 and over2 >= 50:
        comments.append("Over eğilimi")
    
    if not comments:
        return "Belirgin bir eğilim görünmüyor."
    return ". ".join(comments) + "."


def predict_summary(
    team1_stats: MatchStats,
    team2_stats: MatchStats,
    team1_name: str = "Takım 1",
    team2_name: str = "Takım 2",
) -> dict:
    """
    Heuristic kurallarla tahmin özeti üretir (ML yok).
    
    Returns:
        btts, over25, gollu_mac, eğilim_1x2, risk_notu içeren dict
    """
    if team1_stats.played == 0 or team2_stats.played == 0:
        return {
            "btts": {"level": "-", "gerekce": "Yeterli veri yok"},
            "over25": {"level": "-", "gerekce": "Yeterli veri yok"},
            "gollu_mac": {"level": "-", "gerekce": "Yeterli veri yok"},
            "eğilim_1x2": {"sonuc": "-", "gerekce": "Yeterli veri yok"},
            "risk_notu": "Veri yetersiz.",
        }

    # Hesaplamalar
    goals_avg1 = team1_stats.goals_for / team1_stats.played
    goals_avg2 = team2_stats.goals_for / team2_stats.played
    goals_against_avg1 = team1_stats.goals_against / team1_stats.played
    goals_against_avg2 = team2_stats.goals_against / team2_stats.played
    btts1 = (team1_stats.btts_count / team1_stats.played) * 100
    btts2 = (team2_stats.btts_count / team2_stats.played) * 100
    over1 = (team1_stats.over_25_count / team1_stats.played) * 100
    over2 = (team2_stats.over_25_count / team2_stats.played) * 100
    over_avg = (over1 + over2) / 2
    form_diff = team1_stats.form_points - team2_stats.form_points

    # BTTS (her iki takım >= %60 → Yüksek)
    if btts1 >= 60 and btts2 >= 60:
        btts_level, btts_gerekce = "Yüksek", f"Her iki takım BTTS oranı yüksek (%{btts1:.0f}, %{btts2:.0f})"
    elif (btts1 + btts2) / 2 >= 45:
        btts_level, btts_gerekce = "Orta", f"Ortalama BTTS %{(btts1 + btts2) / 2:.0f}"
    else:
        btts_level, btts_gerekce = "Düşük", f"Düşük BTTS eğilimi (%{btts1:.0f}, %{btts2:.0f})"

    # Over 2.5 (ortalama >= %55 → Yüksek)
    if over_avg >= 55:
        over_level, over_gerekce = "Yüksek", f"Ortalama Over 2.5 oranı %{over_avg:.0f}"
    elif over_avg >= 40:
        over_level, over_gerekce = "Orta", f"Ortalama Over 2.5 %{over_avg:.0f}"
    else:
        over_level, over_gerekce = "Düşük", f"Düşük gol ortalaması (%{over_avg:.0f})"

    # Gollü maç (goals_for_avg1 + goals_for_avg2 >= 2.8)
    toplam_gol_avg = goals_avg1 + goals_avg2
    if toplam_gol_avg >= 2.8:
        gollu_level, gollu_gerekce = "Yüksek", f"Maç başı ortalama {toplam_gol_avg:.1f} gol beklentisi"
    elif toplam_gol_avg >= 2.2:
        gollu_level, gollu_gerekce = "Orta", f"Toplam gol ortalaması {toplam_gol_avg:.1f}"
    else:
        gollu_level, gollu_gerekce = "Düşük", f"Düşük gol eğilimi ({toplam_gol_avg:.1f})"

    # 1X2 (form farkı >= 6 → formda takım)
    if form_diff >= 6:
        eğilim_sonuc, eğilim_gerekce = team1_name, f"{team1_name} {form_diff} puan önde"
    elif form_diff <= -6:
        eğilim_sonuc, eğilim_gerekce = team2_name, f"{team2_name} {-form_diff} puan önde"
    else:
        eğilim_sonuc, eğilim_gerekce = "Dengeli", "Form puanları yakın"

    # Risk notları
    riskler = []
    if goals_against_avg1 >= 1.3 and goals_against_avg2 >= 1.3:
        riskler.append("Savunmalar kırılgan")
    if team1_stats.played < 5 or team2_stats.played < 5:
        riskler.append("Örneklem küçük, veri sınırlı")
    risk_notu = ". ".join(riskler) if riskler else None

    return {
        "btts": {"level": btts_level, "gerekce": btts_gerekce},
        "over25": {"level": over_level, "gerekce": over_gerekce},
        "gollu_mac": {"level": gollu_level, "gerekce": gollu_gerekce},
        "eğilim_1x2": {"sonuc": eğilim_sonuc, "gerekce": eğilim_gerekce},
        "risk_notu": risk_notu,
    }

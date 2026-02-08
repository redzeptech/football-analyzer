# -*- coding: utf-8 -*-
"""
Veri katmanı: API veya CSV fallback seçimi.
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from api_client import APIClient, APIError


def has_api_key() -> bool:
    """API anahtarı tanımlı mı kontrol eder."""
    key = os.getenv("API_FOOTBALL_KEY", "").strip()
    return bool(key)


def get_api_client() -> Optional[APIClient]:
    """API istemcisi döner; anahtar yoksa None."""
    key = os.getenv("API_FOOTBALL_KEY", "").strip()
    if not key:
        return None
    return APIClient(key)


def fixtures_to_df(fixtures: list[dict]) -> pd.DataFrame:
    """
    API fixtures listesini analysis modülünün beklediği DataFrame'e çevirir.
    Kolonlar: date, home_team, away_team, home_goals, away_goals
    """
    rows = []
    for f in fixtures:
        fixture = f.get("fixture", {})
        teams = f.get("teams", {})
        goals = f.get("goals", {}) or {}
        date_str = fixture.get("date", "")
        if date_str:
            date_str = date_str.split("T")[0]
        hg = goals.get("home")
        ag = goals.get("away")
        rows.append({
            "date": date_str,
            "home_team": (teams.get("home") or {}).get("name", ""),
            "away_team": (teams.get("away") or {}).get("name", ""),
            "home_goals": int(hg) if hg is not None else 0,
            "away_goals": int(ag) if ag is not None else 0,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


def fetch_team_fixtures_from_api(
    team_id: int,
    league_id: int,
    season: int,
    last_n: int = 10,
) -> tuple[pd.DataFrame, str]:
    """
    API'den takım maçlarını çeker.
    Returns:
        (fixtures_df, team_name)
    """
    client = get_api_client()
    if not client:
        raise RuntimeError("API anahtarı tanımlı değil.")
    fixtures = client.get_team_fixtures(team_id, league_id, season, last_n)
    team_name = client.get_team_name(team_id) or ""
    if not team_name and fixtures:
        # İlk maçtan takım adını al
        for f in fixtures:
            teams = f.get("teams", {})
            home = teams.get("home", {}).get("name", "")
            away = teams.get("away", {}).get("name", "")
            if str(teams.get("home", {}).get("id")) == str(team_id):
                team_name = home
                break
            if str(teams.get("away", {}).get("id")) == str(team_id):
                team_name = away
                break
    df = fixtures_to_df(fixtures)
    return df, team_name


def load_csv_matches(csv_path: str) -> pd.DataFrame:
    """CSV'den maç verilerini yükler (mevcut analysis uyumlu)."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV bulunamadı: {csv_path}")
    df = pd.read_csv(path, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df

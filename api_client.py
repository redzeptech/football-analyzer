# -*- coding: utf-8 -*-
"""
API-Football (api-sports.io) istemci modülü.
API çağrıları, rate limit ve hata yönetimi.
"""

import time
from typing import Any, Optional

import requests
import os
API_KEY = os.getenv("ef9f5ef1fcmsh48dfb0dfb41909cp13eda9jsn1202260361f1")

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
TIMEOUT = 15
CACHE_TTL = 60  # saniye
headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}


class APIClient:
    """API-Football v3 istemcisi."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"x-apisports-key": api_key})
        self._cache: dict[str, tuple[float, Any]] = {}

    def _request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        use_cache: bool = False,
    ) -> dict:
        """
        API'ye istek atar.
        Returns:
            response JSON veya hata durumunda exception
        """
        url = f"{BASE_URL}/{endpoint}"
        cache_key = f"{endpoint}:{sorted((params or {}).items())}"

        if use_cache and cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if time.time() - ts < CACHE_TTL:
                return data

        try:
            r = self.session.get(url, params=params or {}, timeout=TIMEOUT)
        except requests.exceptions.Timeout:
            raise APIError("API yanıt vermedi (timeout). Daha sonra tekrar deneyin.")
        except requests.exceptions.ConnectionError:
            raise APIError("API'ye bağlanılamadı. İnternet bağlantınızı kontrol edin.")

        if r.status_code == 429:
            raise APIError(
                "API rate limit aşıldı. Birkaç dakika bekleyip tekrar deneyin."
            )
        if r.status_code >= 500:
            raise APIError(f"API sunucu hatası ({r.status_code}). Daha sonra deneyin.")
        if r.status_code != 200:
            raise APIError(f"API hatası: HTTP {r.status_code}")

        try:
            data = r.json()
        except ValueError:
            raise APIError("API geçersiz JSON döndürdü.")

        errors = data.get("errors", {})
        if errors:
            msg = errors.get("message", str(errors))
            if "rate" in str(msg).lower() or "limit" in str(msg).lower():
                raise APIError("API rate limit aşıldı. Lütfen bekleyin.")
            raise APIError(f"API hatası: {msg}")

        if use_cache:
            self._cache[cache_key] = (time.time(), data)

        return data

    def get_leagues(self) -> list[dict]:
        """Tüm ligleri listeler."""
        data = self._request("leagues", use_cache=True)
        rows = []
        for item in data.get("response", []):
            league = item.get("league", {}) or item
            country = item.get("country", {}) or {}
            cname = country.get("name", "") if isinstance(country, dict) else ""
            rows.append({
                "league_id": league.get("id") if isinstance(league, dict) else None,
                "league_name": league.get("name", "") if isinstance(league, dict) else "",
                "country": cname or league.get("country", ""),
            })
        return rows

    def search_teams(self, query: str) -> list[dict]:
        """Takım adıyla arama yapar (min 3 karakter)."""
        if len(query.strip()) < 3:
            return []
        data = self._request("teams", params={"search": query.strip()}, use_cache=True)
        rows = []
        for item in data.get("response", []):
            team = item.get("team", item) if isinstance(item, dict) else {}
            if isinstance(team, dict):
                rows.append({
                    "team_id": team.get("id"),
                    "team_name": team.get("name", ""),
                    "country": team.get("country", ""),
                })
        return rows

    def get_team_fixtures(
        self,
        team_id: int,
        league_id: int,
        season: int,
        last_n: int = 10,
    ) -> list[dict]:
        """
        Takımın ligdeki maçlarını getirir (tamamlanmış).
        Son maçlardan itibaren sıralı.
        """
        data = self._request(
            "fixtures",
            params={
                "team": team_id,
                "league": league_id,
                "season": season,
                "status": "FT",
            },
            use_cache=False,
        )
        fixtures = data.get("response", [])
        # Tarihe göre azalan sıra (en son maç önce)
        fixtures.sort(key=lambda f: f.get("fixture", {}).get("date", ""), reverse=True)
        return fixtures[:last_n]

    def get_team_name(self, team_id: int) -> Optional[str]:
        """Takım ID'sinden isim alır."""
        data = self._request("teams", params={"id": team_id}, use_cache=True)
        for item in data.get("response", []):
            team = item.get("team", item) if isinstance(item, dict) else {}
            if isinstance(team, dict):
                return team.get("name", "")
        return None


class APIError(Exception):
    """API hata sınıfı."""

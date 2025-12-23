import httpx
from typing import Any
from datetime import datetime, timedelta

from app.config import settings


class HHClient:
    """HeadHunter API client."""

    BASE_URL = "https://api.hh.ru"
    OAUTH_URL = "https://hh.ru/oauth"

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token

    def get_auth_url(self) -> str:
        """Get OAuth authorization URL."""
        params = {
            "response_type": "code",
            "client_id": settings.hh_client_id,
            "redirect_uri": settings.hh_redirect_uri,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.OAUTH_URL}/authorize?{query}"

    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.OAUTH_URL}/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.hh_client_id,
                    "client_secret": settings.hh_client_secret,
                    "code": code,
                    "redirect_uri": settings.hh_redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """Refresh access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.OAUTH_URL}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()

    def _headers(self) -> dict:
        """Get headers for API requests."""
        headers = {"User-Agent": "JobSearchAssistant/1.0"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}{endpoint}",
                headers=self._headers(),
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    async def get_me(self) -> dict:
        """Get current user info."""
        return await self._request("GET", "/me")

    async def search_vacancies(
        self,
        text: str | None = None,
        area: str | None = None,
        salary: int | None = None,
        experience: str | None = None,
        employment: str | None = None,
        schedule: str | None = None,
        page: int = 0,
        per_page: int = 20,
    ) -> dict:
        """Search vacancies."""
        params = {"page": page, "per_page": per_page}

        if text:
            params["text"] = text
        if area:
            params["area"] = area
        if salary:
            params["salary"] = salary
        if experience:
            params["experience"] = experience
        if employment:
            params["employment"] = employment
        if schedule:
            params["schedule"] = schedule

        return await self._request("GET", "/vacancies", params=params)

    async def get_vacancy(self, vacancy_id: str) -> dict:
        """Get vacancy details."""
        return await self._request("GET", f"/vacancies/{vacancy_id}")

    async def get_my_resumes(self) -> dict:
        """Get list of user's resumes."""
        return await self._request("GET", "/resumes/mine")

    async def create_resume(self, resume_data: dict) -> dict:
        """Create new resume."""
        return await self._request("POST", "/resumes", json=resume_data)

    async def update_resume(self, resume_id: str, resume_data: dict) -> dict:
        """Update existing resume."""
        return await self._request("PUT", f"/resumes/{resume_id}", json=resume_data)

    async def get_resume(self, resume_id: str) -> dict:
        """Get resume by ID."""
        return await self._request("GET", f"/resumes/{resume_id}")

    async def get_dictionaries(self) -> dict:
        """Get HH dictionaries (skills, areas, etc.)."""
        return await self._request("GET", "/dictionaries")

    async def get_areas(self) -> list:
        """Get regions/areas list."""
        return await self._request("GET", "/areas")

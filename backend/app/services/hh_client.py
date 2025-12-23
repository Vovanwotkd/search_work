import httpx
import logging
from typing import Any
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


class HHClient:
    """HeadHunter API client."""

    BASE_URL = "https://api.hh.ru"
    OAUTH_URL = "https://hh.ru/oauth"

    # Endpoints that can work without auth
    PUBLIC_ENDPOINTS = ["/vacancies", "/areas", "/dictionaries"]

    def __init__(self, access_token: str | None = None, refresh_token: str | None = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.new_tokens = None  # Store refreshed tokens for caller to save

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
                    "client_id": settings.hh_client_id,
                    "client_secret": settings.hh_client_secret,
                },
            )
            response.raise_for_status()
            return response.json()

    def _headers(self, with_auth: bool = True) -> dict:
        """Get headers for API requests."""
        # HH.ru requires HH-User-Agent header with email for API access
        headers = {"HH-User-Agent": "JobSearchAssistant/1.0 (ivlych@inbox.ru)"}
        if with_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _is_public_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint is public (works without auth)."""
        return any(endpoint.startswith(pub) for pub in self.PUBLIC_ENDPOINTS)

    async def _request(self, method: str, endpoint: str, require_auth: bool = False, **kwargs) -> Any:
        """Make API request with automatic retry on auth failure."""
        url = f"{self.BASE_URL}{endpoint}"

        async with httpx.AsyncClient() as client:
            # First attempt with auth if available
            headers = self._headers()
            logger.info(f"HH API request: {method} {endpoint}")

            response = await client.request(method, url, headers=headers, **kwargs)

            # If 403 and we have refresh token, try to refresh
            if response.status_code == 403 and self.refresh_token:
                logger.info("Got 403, trying to refresh token...")
                try:
                    self.new_tokens = await self.refresh_tokens(self.refresh_token)
                    self.access_token = self.new_tokens.get("access_token")
                    self.refresh_token = self.new_tokens.get("refresh_token")

                    # Retry with new token
                    headers = self._headers()
                    response = await client.request(method, url, headers=headers, **kwargs)
                    logger.info(f"Retry after refresh: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")

            # If still 403/400 and this is a public endpoint, try without auth
            if response.status_code in (403, 400) and self._is_public_endpoint(endpoint):
                logger.info("Trying public endpoint without auth...")
                headers = self._headers(with_auth=False)
                response = await client.request(method, url, headers=headers, **kwargs)
                logger.info(f"Public request result: {response.status_code}")

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

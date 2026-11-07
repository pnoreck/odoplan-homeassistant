"""A small client for OdoPlan's interface for automations."""

from __future__ import annotations

from datetime import date
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout


class OdoPlanError(Exception):
    """OdoPlan could not be reached or refused the request."""


class OdoPlanAuthError(OdoPlanError):
    """The key is missing, wrong or was renewed in OdoPlan."""


class OdoPlanClient:
    """Reads a car's numbers and enters readings with a personal key.

    The key comes from a car's "Automation" page in OdoPlan and works for
    every car of the account.
    """

    def __init__(self, session: ClientSession, url: str, api_key: str) -> None:
        self._session = session
        self._url = url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

    @property
    def url(self) -> str:
        """OdoPlan's address, without a trailing slash."""
        return self._url

    async def cars(self) -> list[dict[str, Any]]:
        """The cars of the account: slug, name and the address of their numbers."""
        data = await self._request("GET", "/api/cars")
        return list(data.get("cars", []))

    async def car(self, slug: str) -> dict[str, Any]:
        """One car's numbers, the same as on its tiles in OdoPlan."""
        return await self._request("GET", f"/api/cars/{slug}")

    async def add_reading(self, slug: str, km: float, day: date | None = None) -> dict[str, Any]:
        """Enters the odometer, for today unless a day is given.

        Sent again the same day, OdoPlan corrects that day's reading.
        """
        payload: dict[str, Any] = {"km": km}
        if day is not None:
            payload["date"] = day.isoformat()
        return await self._request("POST", f"/api/cars/{slug}/readings", payload)

    async def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            async with self._session.request(
                method,
                self._url + path,
                headers=self._headers,
                json=payload,
                timeout=ClientTimeout(total=20),
            ) as response:
                return await self._answer(response)
        except ClientError as err:
            raise OdoPlanError(str(err)) from err
        except TimeoutError as err:
            raise OdoPlanError("OdoPlan did not answer in time") from err

    @staticmethod
    async def _answer(response: ClientResponse) -> dict[str, Any]:
        try:
            data = await response.json(content_type=None)
        except ValueError:
            data = None
        message = data.get("message") if isinstance(data, dict) else None
        if response.status == 401:
            raise OdoPlanAuthError(message or "The key is not valid")
        if response.status >= 400 or not isinstance(data, dict):
            raise OdoPlanError(message or f"OdoPlan answered with status {response.status}")
        return data

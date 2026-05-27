import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
from fastapi import status
from app.services.auth import create_access_token


class TestSpeaker:
    """Regression tests for speaker profile endpoint authentication (issue #33)."""

    async def test_train_without_token_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/speaker/train",
            json={"name": "Alice", "sample_text": "Hello world"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_profiles_without_token_returns_401(self, client: AsyncClient):
        response = await client.get("/speaker/profiles")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_train_with_invalid_token_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/speaker/train",
            json={"name": "Alice", "sample_text": "Hello world"},
            headers={"Authorization": "Bearer this-is-not-a-valid-token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_profiles_with_invalid_token_returns_401(self, client: AsyncClient):
        response = await client.get(
            "/speaker/profiles",
            headers={"Authorization": "Bearer this-is-not-a-valid-token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_train_with_valid_token_succeeds(self, client: AsyncClient, monkeypatch):
        monkeypatch.setattr("app.routes.speaker.get_embedding", lambda text: [0.1] * 128)
        mock_add = MagicMock()
        monkeypatch.setattr("app.routes.speaker.add_voice", mock_add)
        token = create_access_token("test_user")
        response = await client.post(
            "/speaker/train",
            json={"name": "Alice", "sample_text": "Hello world"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["msg"] == "voice profile saved"
        assert data["name"] == "Alice"
        mock_add.assert_called_once()

    async def test_profiles_with_valid_token_returns_list(self, client: AsyncClient, monkeypatch):
        monkeypatch.setattr("app.routes.speaker.get_voice_profiles", lambda: ["Alice", "Bob"])
        token = create_access_token("test_user")
        response = await client.get(
            "/speaker/profiles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "profiles" in data
        assert data["profiles"] == ["Alice", "Bob"]

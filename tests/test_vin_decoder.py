"""
Tests for VIN decoder service.

Covers validation, NHTSA response parsing, and graceful degradation.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.vin_decoder import (
    validate_vin,
    decode_vin,
    _parse_nhtsa_response,
    VinDecodeResult,
)


class TestVinValidation:
    def test_valid_us_vin(self):
        assert validate_vin("1HGBH41JXMN109186") is True

    def test_valid_japanese_vin(self):
        assert validate_vin("JTDKN3DU5A0123456") is True

    def test_valid_german_vin(self):
        assert validate_vin("WVWZZZ3CZWE123456") is True

    def test_rejects_short_vin(self):
        assert validate_vin("1HGBH41JXM") is False

    def test_rejects_long_vin(self):
        assert validate_vin("1HGBH41JXMN1091861") is False

    def test_rejects_invalid_chars_I(self):
        assert validate_vin("1HGBH41IXMN109186") is False

    def test_rejects_invalid_chars_O(self):
        assert validate_vin("1HGBH41OXMN109186") is False

    def test_rejects_invalid_chars_Q(self):
        assert validate_vin("1HGBH41QXMN109186") is False

    def test_rejects_empty(self):
        assert validate_vin("") is False

    def test_rejects_spaces(self):
        assert validate_vin("1HGBH41J XMN10918") is False


class TestNhtsaResponseParsing:
    def test_clean_decode(self):
        data = {
            "Results": [
                {"Variable": "Make", "Value": "HONDA"},
                {"Variable": "Model", "Value": "Civic"},
                {"Variable": "Model Year", "Value": "2021"},
                {"Variable": "Engine Configuration", "Value": "In-Line"},
                {"Variable": "Displacement (L)", "Value": "1.5"},
                {"Variable": "Fuel Type - Primary", "Value": "Gasoline"},
                {"Variable": "Error Code", "Value": "0"},
            ]
        }
        result = _parse_nhtsa_response(data)
        assert result.make == "HONDA"
        assert result.model == "Civic"
        assert result.year == "2021"
        assert result.displacement == "1.5"
        assert result.fuel_type == "Gasoline"
        assert result.partial is False
        assert result.is_useful() is True
        assert result.engine_summary == "1.5L In-Line Gasoline"

    def test_partial_decode_non_us_vehicle(self):
        data = {
            "Results": [
                {"Variable": "Make", "Value": "TOYOTA"},
                {"Variable": "Model", "Value": ""},
                {"Variable": "Model Year", "Value": "2018"},
                {"Variable": "Engine Configuration", "Value": ""},
                {"Variable": "Displacement (L)", "Value": ""},
                {"Variable": "Fuel Type - Primary", "Value": ""},
                {"Variable": "Error Code", "Value": "1 - Check Digit (9th position) does not calculate properly"},
            ]
        }
        result = _parse_nhtsa_response(data)
        assert result.make == "TOYOTA"
        assert result.model is None
        assert result.partial is True
        assert result.is_useful() is False

    def test_empty_response(self):
        data = {"Results": []}
        result = _parse_nhtsa_response(data)
        assert result.make is None
        assert result.is_useful() is False

    def test_ignores_whitespace_only_values(self):
        data = {
            "Results": [
                {"Variable": "Make", "Value": "   "},
                {"Variable": "Model", "Value": "  "},
            ]
        }
        result = _parse_nhtsa_response(data)
        assert result.make is None
        assert result.model is None


class TestDecodeVin:
    @pytest.mark.asyncio
    async def test_invalid_vin_returns_none(self):
        result = await decode_vin("INVALID")
        assert result is None

    @pytest.mark.asyncio
    async def test_vin_with_forbidden_chars_returns_none(self):
        result = await decode_vin("1HGBH41IXMN10918Q")
        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.vin_decoder._get_cache", return_value=None)
    @patch("app.services.vin_decoder._set_cache")
    async def test_successful_api_call(self, mock_set_cache, mock_get_cache):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "Results": [
                {"Variable": "Make", "Value": "HONDA"},
                {"Variable": "Model", "Value": "Accord"},
                {"Variable": "Model Year", "Value": "2020"},
                {"Variable": "Engine Configuration", "Value": "In-Line"},
                {"Variable": "Displacement (L)", "Value": "1.5"},
                {"Variable": "Fuel Type - Primary", "Value": "Gasoline"},
                {"Variable": "Error Code", "Value": "0"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await decode_vin("1HGCV1F34LA012345")

        assert result is not None
        assert result.make == "HONDA"
        assert result.model == "Accord"
        assert result.year == "2020"
        assert result.is_useful() is True
        mock_set_cache.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.vin_decoder._get_cache")
    async def test_cache_hit_skips_api(self, mock_get_cache):
        mock_get_cache.return_value = {
            "vin": "1HGCV1F34LA012345",
            "make": "HONDA",
            "model": "Accord",
            "year": "2020",
            "engine_config": "In-Line",
            "displacement": "1.5",
            "fuel_type": "Gasoline",
            "partial": False,
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            result = await decode_vin("1HGCV1F34LA012345")
            mock_client_cls.assert_not_called()

        assert result.make == "HONDA"
        assert result.model == "Accord"

    @pytest.mark.asyncio
    @patch("app.services.vin_decoder._get_cache", return_value=None)
    @patch("app.services.vin_decoder._set_cache")
    async def test_timeout_returns_none(self, mock_set_cache, mock_get_cache):
        import httpx as _httpx

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=_httpx.TimeoutException("timed out"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await decode_vin("1HGCV1F34LA012345")

        assert result is None
        mock_set_cache.assert_not_called()

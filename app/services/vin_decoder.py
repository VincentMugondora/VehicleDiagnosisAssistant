"""
VIN decoding service using NHTSA's free vPIC API.

Decodes Vehicle Identification Numbers to extract make, model, year, and engine
details. Results are cached in Supabase to avoid repeat API calls.
"""
import re
import httpx
from app.db.client import get_supabase_client
from app.core.config import settings
from app.core.logging import logger

_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.IGNORECASE)
_NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"
_TIMEOUT = httpx.Timeout(5.0, connect=3.0)

_FIELD_MAP = {
    "Make": "make",
    "Model": "model",
    "Model Year": "year",
    "Engine Configuration": "engine_config",
    "Displacement (L)": "displacement",
    "Fuel Type - Primary": "fuel_type",
}


class VinDecodeResult:
    __slots__ = ("make", "model", "year", "engine_config", "displacement", "fuel_type", "partial")

    def __init__(self, make, model, year, engine_config, displacement, fuel_type, partial=False):
        self.make = make
        self.model = model
        self.year = year
        self.engine_config = engine_config
        self.displacement = displacement
        self.fuel_type = fuel_type
        self.partial = partial

    @property
    def engine_summary(self) -> str | None:
        parts = []
        if self.displacement:
            parts.append(f"{self.displacement}L")
        if self.engine_config:
            parts.append(self.engine_config)
        if self.fuel_type:
            parts.append(self.fuel_type)
        return " ".join(parts) if parts else None

    def is_useful(self) -> bool:
        return bool(self.make and self.model)


def validate_vin(vin: str) -> bool:
    return bool(_VIN_PATTERN.match(vin))


def _get_cache(vin: str) -> dict | None:
    client = get_supabase_client()
    if not client:
        return None
    try:
        result = client.table("vin_cache")\
            .select("*")\
            .eq("vin", vin.upper())\
            .execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        logger.warning("vin_cache_read_failed", error=str(e))
    return None


def _set_cache(vin: str, decoded: "VinDecodeResult"):
    client = get_supabase_client()
    if not client:
        return
    try:
        client.table("vin_cache").upsert({
            "vin": vin.upper(),
            "make": decoded.make,
            "model": decoded.model,
            "year": decoded.year,
            "engine_config": decoded.engine_config,
            "displacement": decoded.displacement,
            "fuel_type": decoded.fuel_type,
            "partial": decoded.partial,
        }, on_conflict="vin").execute()
    except Exception as e:
        logger.warning("vin_cache_write_failed", error=str(e))


def _parse_nhtsa_response(data: dict) -> VinDecodeResult:
    results = data.get("Results", [])
    fields = {}
    has_error = False

    for item in results:
        var = item.get("Variable")
        val = item.get("Value")
        if var in _FIELD_MAP and val and val.strip():
            fields[_FIELD_MAP[var]] = val.strip()
        if var == "Error Code" and val and val.strip() != "0":
            has_error = True

    return VinDecodeResult(
        make=fields.get("make"),
        model=fields.get("model"),
        year=fields.get("year"),
        engine_config=fields.get("engine_config"),
        displacement=fields.get("displacement"),
        fuel_type=fields.get("fuel_type"),
        partial=has_error,
    )


async def decode_vin(vin: str) -> VinDecodeResult | None:
    """
    Decode a VIN using NHTSA vPIC API with caching.

    Returns VinDecodeResult on success, None if VIN is invalid or decode
    fails entirely (network error, timeout, etc.).
    """
    vin = vin.strip().upper()

    if not validate_vin(vin):
        return None

    cached = _get_cache(vin)
    if cached:
        logger.info("vin_cache_hit", vin=vin)
        return VinDecodeResult(
            make=cached.get("make"),
            model=cached.get("model"),
            year=cached.get("year"),
            engine_config=cached.get("engine_config"),
            displacement=cached.get("displacement"),
            fuel_type=cached.get("fuel_type"),
            partial=cached.get("partial", False),
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_NHTSA_URL.format(vin=vin))
            resp.raise_for_status()
            data = resp.json()
    except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as e:
        logger.warning("vin_decode_api_failed", vin=vin, error=str(e))
        return None

    decoded = _parse_nhtsa_response(data)
    _set_cache(vin, decoded)

    logger.info(
        "vin_decoded",
        vin=vin,
        make=decoded.make,
        model=decoded.model,
        useful=decoded.is_useful(),
    )
    return decoded

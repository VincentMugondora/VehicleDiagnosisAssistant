import os
import re
import json
from typing import List, Dict, Optional
from urllib.parse import urlparse
from datetime import datetime

import httpx

try:
    from google import genai as genai_new  # type: ignore
except Exception:
    genai_new = None  # Gemini optional

_GENAI_CLIENT = None


def _get_env_bool(name: str, default: bool = False) -> bool:
    return (os.getenv(name, str(default)).strip().lower() == "true")


def _trusted_domains() -> List[str]:
    raw = os.getenv("TRUSTED_SITES", "obd-codes.com,autocodes.com,obdii.com")
    return [d.strip().lower() for d in raw.split(",") if d.strip()]


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


async def _search_brave(query: str) -> List[Dict[str, str]]:
    api_key = os.getenv("BRAVE_API_KEY", "").strip()
    if not api_key:
        return []
    headers = {"X-Subscription-Token": api_key}
    params = {
        "q": query,
        "count": 6,
        "search_lang": "en",
        "country": "US",
        "safesearch": "off",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)
        if r.status_code != 200:
            return []
        data = r.json()
        items = []
        for it in (data.get("web", {}) or {}).get("results", []) or []:
            url = it.get("url") or ""
            title = it.get("title") or ""
            snippet = it.get("description") or ""
            if url and title:
                items.append({"url": url, "title": title, "snippet": snippet})
        return items


async def _search_serpapi(query: str) -> List[Dict[str, str]]:
    key = os.getenv("SERPAPI_KEY", "").strip()
    if not key:
        return []
    params = {"engine": "google", "q": query, "api_key": key, "num": 6}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get("https://serpapi.com/search.json", params=params)
        if r.status_code != 200:
            return []
        data = r.json()
        items = []
        for it in data.get("organic_results", []) or []:
            url = it.get("link") or ""
            title = it.get("title") or ""
            snippet = it.get("snippet") or ""
            if url and title:
                items.append({"url": url, "title": title, "snippet": snippet})
        return items


async def _web_search_for_code(code: str) -> List[Dict[str, str]]:
    domains = _trusted_domains()
    # Build site-restricted query
    site_filters = " OR ".join([f"site:{d}" for d in domains])
    query = f"{code} OBD-II meaning causes fixes {site_filters}".strip()

    provider = os.getenv("SEARCH_PROVIDER", "brave").lower()
    results: List[Dict[str, str]] = []
    if provider == "serpapi":
        results = await _search_serpapi(query)
    else:
        results = await _search_brave(query)

    if not results:
        return []

    # Filter to trusted domains and dedupe by domain
    seen = set()
    filtered: List[Dict[str, str]] = []
    for r in results:
        dom = _domain(r.get("url", ""))
        if not any(dom.endswith(td) for td in domains):
            continue
        if dom in seen:
            continue
        seen.add(dom)
        filtered.append(r)
        if len(filtered) >= 3:
            break

    return filtered or results[:3]


def _configure_gemini() -> None:
    if genai_new is None:
        return
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        return
    global _GENAI_CLIENT
    if _GENAI_CLIENT is None:
        _GENAI_CLIENT = genai_new.Client(api_key=api_key)  # type: ignore


def _summarize_with_gemini(code: str, results: List[Dict[str, str]], vehicle: Dict[str, Optional[str]]) -> Optional[Dict[str, object]]:
    if genai_new is None:
        return None
    _configure_gemini()
    if _GENAI_CLIENT is None:
        return None
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    # Build a compact prompt with citations
    sources_text = "\n\n".join([
        f"Source: {r['url']}\nTitle: {r.get('title','')}\nSnippet: {r.get('snippet','')}" for r in results
    ])
    make = (vehicle.get("make") or "").strip()
    model = (vehicle.get("model") or "").strip()
    year = (vehicle.get("year") or "").strip()
    engine = (vehicle.get("engine") or "").strip()
    prompt = (
        "You are an automotive diagnostics assistant for mechanics.\n"
        "Task: Summarize OBD-II code details ONLY using the provided sources.\n"
        "Do NOT invent causes or checks. If unclear, say 'generic'.\n"
        "Return STRICT JSON with keys: description (string), causes (array of 3-6 short strings), checks (array of 3-6 short strings).\n"
        f"Code: {code}\n\n"
        f"Vehicle: {make} {model} {year} {engine}\n\n"
        f"SOURCES:\n{sources_text}\n\n"
        "Return only JSON."
    )
    try:
        resp = _GENAI_CLIENT.models.generate_content(model=model_name, contents=[prompt])  # type: ignore
        txt = (resp.text or "").strip()
        # extract JSON block
        m = re.search(r"\{[\s\S]*\}$", txt)
        raw = m.group(0) if m else txt
        data = json.loads(raw)
        desc = str(data.get("description", "")).strip()
        causes = [str(x).strip() for x in data.get("causes", []) if str(x).strip()]
        checks = [str(x).strip() for x in data.get("checks", []) if str(x).strip()]
        if not (desc and causes and checks):
            return None
        return {"description": desc, "causes": causes[:6], "checks": checks[:6]}
    except Exception:
        return None


async def get_external_obd(db, code: str, vehicle: Dict[str, Optional[str]]) -> Optional[Dict[str, object]]:
    if not _get_env_bool("INTERNET_FALLBACK_ENABLED", False):
        return None

    # 1) Cache check
    cached = await db["external_obd_cache"].find_one({"code": code.upper()})
    if cached:
        return {
            "description": cached.get("description", ""),
            "causes": cached.get("causes", []) or [],
            "checks": cached.get("checks", []) or [],
            "sources": cached.get("sources", []) or [],
        }

    # 2) Search
    results = await _web_search_for_code(code)
    if not results:
        return None

    # 3) Summarize (prefer Gemini if enabled)
    summary: Optional[Dict[str, object]] = None
    if _get_env_bool("AI_ENRICH_ENABLED", False) and os.getenv("AI_PROVIDER", "").lower() == "gemini":
        summary = _summarize_with_gemini(code, results, vehicle)

    # basic fallback if no AI: use snippets to craft minimal output
    if summary is None:
        # heuristic extraction from snippets
        desc = f"OBD-II code {code}"
        text = "\n".join([r.get("snippet", "") for r in results])
        # naive split for causes/checks candidates
        tokens = [t.strip() for t in re.split(r",|;|\n|•|\-|—|:\s*", text) if t.strip()]
        causes = tokens[:5] or ["Vacuum leak", "Sensor issue", "Wiring problem"]
        checks = [f"Check: {c}" for c in causes][:5]
        summary = {"description": desc, "causes": causes, "checks": checks}

    # 4) Cache
    try:
        await db["external_obd_cache"].update_one(
            {"code": code.upper()},
            {
                "$set": {
                    "code": code.upper(),
                    "description": summary.get("description", ""),
                    "causes": summary.get("causes", []),
                    "checks": summary.get("checks", []),
                    "sources": [r.get("url") for r in results],
                    "fetched_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
    except Exception:
        pass
    # Optionally promote to primary collection for future use without internet
    try:
        if os.getenv("EXTERNAL_PROMOTE_TO_PRIMARY", "false").strip().lower() == "true":
            primary_doc = {
                "code": code.upper(),
                "description": summary.get("description", "") or "",
                "symptoms": "",
                "common_causes": ", ".join(summary.get("causes", []) or []),
                "generic_fixes": ", ".join(summary.get("checks", []) or []),
            }
            await db["obd_codes"].update_one({"code": code.upper()}, {"$set": primary_doc}, upsert=True)
    except Exception:
        pass

    # Optionally save a per-vehicle summary document
    try:
        if os.getenv("EXTERNAL_SAVE_PER_VEHICLE", "true").strip().lower() == "true":
            v_norm = {
                "make": (vehicle.get("make") or "").strip().lower(),
                "model": (vehicle.get("model") or "").strip().lower(),
                "year": (vehicle.get("year") or "").strip().lower(),
                "engine": (vehicle.get("engine") or "").strip().lower(),
            }
            doc = {
                "code": code.upper(),
                **v_norm,
                "description": summary.get("description", "") or "",
                "causes": summary.get("causes", []) or [],
                "checks": summary.get("checks", []) or [],
                "sources": [r.get("url") for r in results],
                "created_at": datetime.utcnow(),
            }
            await db["obd_summaries"].update_one(
                {"code": code.upper(), **v_norm},
                {"$set": doc},
                upsert=True,
            )
    except Exception:
        pass

    return summary

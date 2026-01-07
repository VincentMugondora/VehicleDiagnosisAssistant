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


def _dedupe_str_list(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for it in items:
        s = str(it or "").strip()
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


def _suggest_checks_from_causes(causes: List[str]) -> List[str]:
    text = " ".join(causes).lower()
    checks: List[str] = []
    if any(k in text for k in ["wire", "wiring", "harness", "connector", "communication", "bus", "can", "ecm", "pcm", "tcm"]):
        checks.extend([
            "Inspect wiring harness and connectors",
            "Ensure connectors are seated and corrosion-free",
            "Scan for communication errors and module connectivity",
        ])
    if any(k in text for k in ["vacuum", "intake"]):
        checks.append("Check intake and vacuum lines for leaks")
    if any(k in text for k in ["spark", "coil", "ignition", "misfire"]):
        checks.append("Inspect spark plugs and ignition coils")
    if any(k in text for k in ["sensor", "maf", "o2", "oxygen"]):
        checks.append("Verify sensor readings with a scan tool")
    if any(k in text for k in ["fuel", "injector", "pressure"]):
        checks.append("Test fuel pressure and injector operation")
    checks = _dedupe_str_list(checks)
    if not checks:
        checks = ["Perform visual inspection and scan for related DTCs"]
    return checks[:6]


def _sanitize_summary(summary: Dict[str, object]) -> Dict[str, object]:
    desc = str(summary.get("description", "") or "").strip()
    # collapse whitespace
    desc = re.sub(r"\s+", " ", desc)
    # remove obvious QA noise terms from description
    bad_desc_terms = ["what is the meaning", "stack overflow", "stackexchange", "reddit", "quora"]
    if any(t in desc.lower() for t in bad_desc_terms):
        # keep only first sentence before such terms
        for t in bad_desc_terms:
            idx = desc.lower().find(t)
            if idx != -1:
                desc = desc[:idx].strip().rstrip("-:;,")
                break
    # sanitize causes
    raw_causes = [str(x).strip() for x in (summary.get("causes") or []) if str(x).strip()]
    causes: List[str] = []
    bad_tokens = ["what is the meaning", "asked", "stack overflow", "stackexchange", "reddit", "quora", "http", "www."]
    for c in raw_causes:
        cl = c.lower()
        if any(b in cl for b in bad_tokens):
            continue
        if len(c) > 120:
            continue
        causes.append(c)
    causes = _dedupe_str_list(causes)[:6]
    # If description is generic, derive from causes when they indicate communication/harness
    if not desc or re.match(r"(?i)^obd-ii code\b", desc):
        joined = " ".join(causes).lower()
        if any(k in joined for k in ["communication", "can", "bus", "link", "harness", "connector", "ecm", "pcm", "tcm"]):
            desc = "Malfunction in the communication link between ECM and related control modules (wiring/connectors)."

    # sanitize checks
    raw_checks = [str(x).strip() for x in (summary.get("checks") or []) if str(x).strip()]
    checks: List[str] = []
    for ck in raw_checks:
        s = re.sub(r"^\s*check:\s*", "", ck, flags=re.IGNORECASE).strip()
        if not s or len(s) > 140:
            continue
        if any(b in s.lower() for b in bad_tokens):
            continue
        checks.append(s)
    if not checks:
        checks = _suggest_checks_from_causes(causes)
    checks = _dedupe_str_list(checks)[:6]
    return {"description": desc, "causes": causes, "checks": checks}


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
        try:
            print("[external] serpapi key missing")
        except Exception:
            pass
        return []
    params = {"engine": "google", "q": query, "api_key": key, "num": 6}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get("https://serpapi.com/search.json", params=params)
        if r.status_code != 200:
            try:
                print(f"[external] serpapi status={r.status_code}")
            except Exception:
                pass
            return []
        data = r.json()
        if data.get("error"):
            try:
                print(f"[external] serpapi error={data.get('error')}")
            except Exception:
                pass
            return []
        items = []
        for it in data.get("organic_results", []) or []:
            url = it.get("link") or ""
            title = it.get("title") or ""
            snippet = it.get("snippet") or ""
            if url and title:
                items.append({"url": url, "title": title, "snippet": snippet})
        return items


async def _web_search_for_code(code: str, vehicle: Dict[str, Optional[str]]) -> List[Dict[str, str]]:
    domains = _trusted_domains()
    # Build site-restricted query with vehicle context
    make = (vehicle.get("make") or "").strip()
    model = (vehicle.get("model") or "").strip()
    year = (vehicle.get("year") or "").strip()
    engine = (vehicle.get("engine") or "").strip()
    v_terms = " ".join([t for t in [make, model, year, engine] if t]).strip()
    site_filters = " OR ".join([f"site:{d}" for d in domains])
    query = f"{code} {v_terms} OBD-II meaning causes fixes {site_filters}".strip()

    provider = os.getenv("SEARCH_PROVIDER", "brave").strip().lower()
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

    # Do not fall back to non-trusted domains; keep results empty if filter removed all
    if not filtered:
        try:
            print("[external] filtered_results=0 (all non-trusted)")
        except Exception:
            pass
    return filtered


def _configure_gemini() -> None:
    if genai_new is None:
        return
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        try:
            print("[gemini] GOOGLE_API_KEY missing")
        except Exception:
            pass
        return
    global _GENAI_CLIENT
    if _GENAI_CLIENT is None:
        _GENAI_CLIENT = genai_new.Client(api_key=api_key)  # type: ignore
        try:
            print("[gemini] client_configured=true")
        except Exception:
            pass


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
        try:
            print("[gemini] generate start")
        except Exception:
            pass
        resp = _GENAI_CLIENT.models.generate_content(model=model_name, contents=[prompt])  # type: ignore
        txt = (resp.text or "").strip()
        # robust JSON extraction
        start = txt.find("{")
        end = txt.rfind("}")
        raw = txt[start:end+1] if start != -1 and end != -1 and end > start else txt
        data = json.loads(raw)
        desc = str(data.get("description", "")).strip()
        causes = [str(x).strip() for x in data.get("causes", []) if str(x).strip()]
        checks = [str(x).strip() for x in data.get("checks", []) if str(x).strip()]
        if not (desc and causes and checks):
            return None
        try:
            print("[gemini] generate ok, parsed=true")
        except Exception:
            pass
        return {"description": desc, "causes": causes[:6], "checks": checks[:6]}
    except Exception as e:
        try:
            print(f"[gemini] generate/parse failed: {type(e).__name__}")
        except Exception:
            pass
        return None


async def get_external_obd(db, code: str, vehicle: Dict[str, Optional[str]]) -> Optional[Dict[str, object]]:
    internet = _get_env_bool("INTERNET_FALLBACK_ENABLED", False)
    try:
        print(f"[external] code={code} internet={internet} provider={os.getenv('SEARCH_PROVIDER', 'brave')}")
    except Exception:
        pass
    if not internet:
        return None

    # 1) Cache check (per code + vehicle)
    v_norm = {
        "make": (vehicle.get("make") or "").strip().lower(),
        "model": (vehicle.get("model") or "").strip().lower(),
        "year": (vehicle.get("year") or "").strip().lower(),
        "engine": (vehicle.get("engine") or "").strip().lower(),
    }
    cached = await db["external_obd_cache"].find_one({"code": code.upper(), **v_norm})
    if cached:
        try:
            print("[external] cache_hit=true")
        except Exception:
            pass
        return {
            "description": cached.get("description", ""),
            "causes": cached.get("causes", []) or [],
            "checks": cached.get("checks", []) or [],
            "sources": cached.get("sources", []) or [],
        }

    # 2) Search
    results = await _web_search_for_code(code, vehicle)
    if not results:
        try:
            print("[external] search_results=0")
        except Exception:
            pass
        return None
    try:
        print(f"[external] search_results={len(results)}")
    except Exception:
        pass

    # 3) Summarize (prefer Gemini if enabled)
    summary: Optional[Dict[str, object]] = None
    ai_gemini = _get_env_bool("AI_ENRICH_ENABLED", False) and os.getenv("AI_PROVIDER", "").strip().lower() == "gemini"
    try:
        print(f"[external] ai_gemini={ai_gemini}")
    except Exception:
        pass
    if ai_gemini:
        summary = _summarize_with_gemini(code, results, vehicle)

    # basic fallback if no AI: use snippets to craft minimal output
    if summary is None:
        try:
            print("[external] using_heuristic_fallback=true")
        except Exception:
            pass
        # heuristic extraction from snippets
        desc = f"OBD-II code {code}"
        text = "\n".join([r.get("snippet", "") for r in results])
        # naive split for causes/checks candidates
        tokens = [t.strip() for t in re.split(r",|;|\n|•|\-|—|:\s*", text) if t.strip()]
        # remove noisy/QA phrases
        bad_subs = [
            "what is the meaning", "asked", "stack overflow", "stackexchange",
            "reddit", "quora", "how do i fix", "may ", "nov ", "dec ", "jan ", "feb ", "mar ", "apr "
        ]
        cleaned = []
        seen_lc = set()
        for t in tokens:
            tl = t.lower()
            if any(b in tl for b in bad_subs):
                continue
            if len(t) > 120:
                continue
            # simple dedupe
            if tl in seen_lc:
                continue
            seen_lc.add(tl)
            cleaned.append(t)
        causes = cleaned[:5] or ["Communication bus fault", "Harness/connector issue", "Control module fault"]
        checks = [f"Check: {c}" for c in causes][:5]
        summary = {"description": desc, "causes": causes, "checks": checks}

    # Sanitize final summary
    clean = _sanitize_summary(summary)

    # 4) Cache
    try:
        await db["external_obd_cache"].update_one(
            {"code": code.upper(), **v_norm},
            {
                "$set": {
                    "code": code.upper(),
                    **v_norm,
                    "description": clean.get("description", ""),
                    "causes": clean.get("causes", []),
                    "checks": clean.get("checks", []),
                    "sources": [r.get("url") for r in results],
                    "fetched_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        try:
            print("[external] cache_write=ok")
        except Exception:
            pass
    except Exception:
        pass
    # Optionally promote to primary collection for future use without internet
    try:
        if os.getenv("EXTERNAL_PROMOTE_TO_PRIMARY", "false").strip().lower() == "true":
            primary_doc = {
                "code": code.upper(),
                "description": clean.get("description", "") or "",
                "symptoms": "",
                "common_causes": ", ".join(clean.get("causes", []) or []),
                "generic_fixes": ", ".join(clean.get("checks", []) or []),
            }
            await db["obd_codes"].update_one({"code": code.upper()}, {"$set": primary_doc}, upsert=True)
            try:
                print("[external] promoted_to_primary=ok")
            except Exception:
                pass
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
                "description": clean.get("description", "") or "",
                "causes": clean.get("causes", []) or [],
                "checks": clean.get("checks", []) or [],
                "sources": [r.get("url") for r in results],
                "created_at": datetime.utcnow(),
            }
            await db["obd_summaries"].update_one(
                {"code": code.upper(), **v_norm},
                {"$set": doc},
                upsert=True,
            )
            try:
                print("[external] saved_per_vehicle=ok")
            except Exception:
                pass
    except Exception:
        pass

    return clean

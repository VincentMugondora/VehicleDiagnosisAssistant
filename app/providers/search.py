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


def _sanitize_summary(code: str, summary: Dict[str, object]) -> Dict[str, object]:
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
    bad_tokens = [
        "what is the meaning", "asked", "stack overflow", "stackexchange", "reddit", "quora", "http", "www.",
        "i bought", "my car", "yesterday", "today", "please", "thanks", "anyone", "someone said", "forum", "thread", "help"
    ]
    # remove causes that reference other DTCs
    dtc_re = re.compile(r"\b[PBCU][0-9]{4}\b", re.IGNORECASE)
    for c in raw_causes:
        cl = c.lower()
        if any(b in cl for b in bad_tokens):
            continue
        # drop unrelated DTC mentions
        m = dtc_re.search(c)
        if m and m.group(0).upper() != code.upper():
            continue
        # remove obvious broken fragments
        if len(c) < 8:
            continue
        if c.strip(". ").endswith("..."):
            continue
        if cl.startswith("this ") or cl.startswith("specifically ") or cl.startswith("use "):
            continue
        if len(c) > 120:
            continue
        causes.append(c)
    causes = _dedupe_str_list(causes)[:6]
    # If description is generic or mismatched, derive from code pattern/causes
    if not desc or re.match(r"(?i)^obd-ii code\b", desc):
        c_up = code.upper().strip()
        # Common mappings
        if re.match(r"^P0300$", c_up):
            desc = "Random/multiple cylinder misfire detected"
        elif re.match(r"^P03\d\d$", c_up):
            # e.g. P0301 -> cylinder 1 misfire
            cyl = c_up[-2:]
            if cyl.isdigit() and cyl != "00":
                desc = f"Cylinder {int(cyl)%100} misfire detected"
            else:
                desc = "Engine misfire detected"
        elif c_up == "P0420":
            desc = "Catalyst system efficiency below threshold (Bank 1)"
        elif c_up == "P0720":
            desc = "Output speed sensor circuit malfunction"
        elif c_up == "P0600":
            desc = "Serial communication link malfunction"
        else:
            # Fall back to causes keywords
            joined = " ".join(causes).lower()
            if any(k in joined for k in ["communication", "can", "bus", "link", "harness", "connector", "ecm", "pcm", "tcm"]):
                desc = "Malfunction in the communication link between ECM and related control modules (wiring/connectors)."

    # sanitize checks
    raw_checks = [str(x).strip() for x in (summary.get("checks") or []) if str(x).strip()]
    checks: List[str] = []
    allowed_verbs = ["inspect", "check", "test", "scan", "verify", "clean", "replace", "tighten", "swap", "measure", "perform"]
    for ck in raw_checks:
        s = re.sub(r"^\s*check:\s*", "", ck, flags=re.IGNORECASE).strip()
        sl = s.lower()
        if not s or len(s) > 140:
            continue
        if len(s) < 12:
            continue
        if any(b in sl for b in bad_tokens):
            continue
        if not any(v in sl for v in allowed_verbs):
            continue
        # drop checks that reference other DTCs
        m = dtc_re.search(s)
        if m and m.group(0).upper() != code.upper():
            continue
        checks.append(s)
    if not checks or len(checks) < 2:
        checks = _suggest_checks_from_causes(causes)
    checks = _dedupe_str_list(checks)[:6]

    # Canonicalize misfire (P03xx) when results are weak
    c_up = code.upper().strip()
    if re.match(r"^P03\d\d$", c_up):
        cyl = c_up[-2:]
        cyl_num = int(cyl) % 100 if cyl.isdigit() else None
        if len(causes) < 3:
            base_c = [
                f"Ignition coil failure (cylinder {cyl_num})" if cyl_num else "Ignition coil failure",
                f"Spark plug fouled/worn (cylinder {cyl_num})" if cyl_num else "Spark plug fouled/worn",
                f"Fuel injector issue (cylinder {cyl_num})" if cyl_num else "Fuel injector issue",
                "Vacuum leak near intake manifold",
                f"Low compression (cylinder {cyl_num})" if cyl_num else "Low compression",
                f"Wiring/connector issue at coil/injector (cylinder {cyl_num})" if cyl_num else "Wiring/connector issue at coil/injector",
            ]
            causes = _dedupe_str_list(base_c)[:6]
        if len(checks) < 3:
            base_chk = [
                f"Inspect/replace spark plug (cylinder {cyl_num})" if cyl_num else "Inspect/replace spark plug",
                f"Swap ignition coil with another cylinder and re-scan (cylinder {cyl_num})" if cyl_num else "Swap ignition coil with another cylinder and re-scan",
                f"Inspect coil/injector wiring and connectors (cylinder {cyl_num})" if cyl_num else "Inspect coil/injector wiring and connectors",
                f"Perform compression test (cylinder {cyl_num})" if cyl_num else "Perform compression test",
                f"Injector balance/leak test (cylinder {cyl_num})" if cyl_num else "Injector balance/leak test",
                "Check for vacuum leaks around intake hoses/gaskets",
            ]
            checks = _dedupe_str_list(base_chk)[:6]
    # Canonicalize P0705 (TRS circuit) when results are weak
    if c_up == "P0705":
        if len(causes) < 3:
            causes = _dedupe_str_list([
                "Transmission range sensor (TRS) faulty or misaligned",
                "Damaged or corroded TRS connector/wiring",
                "Selector linkage out of adjustment",
                "TCM input fault (less common)",
            ])[:6]
        if len(checks) < 3:
            checks = _dedupe_str_list([
                "Verify TRS alignment and selector linkage adjustment",
                "Inspect TRS wiring and connector for damage/corrosion",
                "Read PRNDL status with scan tool and compare to lever position",
                "Check continuity/voltage at TRS according to service manual",
            ])[:6]
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
    make = (vehicle.get("make") or "").strip()
    model = (vehicle.get("model") or "").strip()
    year = (vehicle.get("year") or "").strip()
    engine = (vehicle.get("engine") or "").strip()
    v_terms = " ".join([t for t in [make, model, year, engine] if t]).strip()
    base_terms = f"{code} OBD-II meaning causes fixes".strip()
    site_filters = " OR ".join([f"site:{d}" for d in domains])

    queries = [
        f"{base_terms} {v_terms} {site_filters}".strip() if v_terms else f"{base_terms} {site_filters}".strip(),
        f"{base_terms} {site_filters}".strip(),
        base_terms,
    ]

    provider = os.getenv("SEARCH_PROVIDER", "brave").strip().lower()
    for idx, q in enumerate(queries, start=1):
        try:
            print(f"[external] search_attempt={idx} q='{q[:120]}'")
        except Exception:
            pass
        if provider == "serpapi":
            results = await _search_serpapi(q)
        else:
            results = await _search_brave(q)
        if not results:
            continue
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
        if filtered:
            return filtered
        # For the last attempt (without site filters), allow untrusted fallback if enabled
        if idx == len(queries) and _get_env_bool("ALLOW_UNTRUSTED_FALLBACK", False):
            try:
                print("[external] untrusted_fallback=true")
            except Exception:
                pass
            return results[:3]

    # As a final trusted-only fallback, query each trusted domain separately and aggregate
    agg: List[Dict[str, str]] = []
    for d in domains:
        if len(agg) >= 3:
            break
        q = f"{base_terms} {v_terms} site:{d}".strip() if v_terms else f"{base_terms} site:{d}".strip()
        try:
            print(f"[external] per_domain_try domain={d} q='{q[:120]}'")
        except Exception:
            pass
        if provider == "serpapi":
            res = await _search_serpapi(q)
        else:
            res = await _search_brave(q)
        for r in res:
            dom = _domain(r.get("url", ""))
            if not dom.endswith(d):
                continue
            # ensure uniqueness by domain
            if any(_domain(x.get("url", "")) == dom for x in agg):
                continue
            agg.append(r)
            break
    if agg:
        return agg[:3]

    try:
        print("[external] filtered_results=0 (no suitable results)")
    except Exception:
        pass
    return []


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
            "from_ai": True,
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
    summary_from_ai = False
    ai_gemini = _get_env_bool("AI_ENRICH_ENABLED", False) and os.getenv("AI_PROVIDER", "").strip().lower() == "gemini"
    try:
        print(f"[external] ai_gemini={ai_gemini}")
    except Exception:
        pass
    if ai_gemini:
        summary = _summarize_with_gemini(code, results, vehicle)
        if summary is not None:
            summary_from_ai = True

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
    clean = _sanitize_summary(code, summary)
    clean["from_ai"] = bool(summary_from_ai)

    # 4) Persist only if AI summary
    if summary_from_ai:
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
    else:
        try:
            print("[external] skip_persist_heuristic=true")
        except Exception:
            pass
    # Do not promote external summaries into the authoritative primary KB
    try:
        if os.getenv("EXTERNAL_PROMOTE_TO_PRIMARY", "false").strip().lower() == "true":
            print("[external] skip_promote_to_primary=true")
    except Exception:
        pass

    # Optionally save a per-vehicle summary document
    if summary_from_ai:
        try:
            if os.getenv("EXTERNAL_SAVE_PER_VEHICLE", "false").strip().lower() == "true":
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

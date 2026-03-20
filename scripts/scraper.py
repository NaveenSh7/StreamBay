"""
╔══════════════════════════════════════════════════════════════════╗
║   🎬  Movie & Series Scraper  —  TMDB + Embed APIs              ║
║                                                                  ║
║   Metadata  →  TMDB API  (free key, never goes down)            ║
║   Streams   →  vidsrc.me / vidsrc.cc / vidlink.pro /            ║
║                autoembed.cc / 2embed.cc / player.videasy.net    ║
║                                                                  ║
║   Works for: Movies • TV Series • Anime • K-Drama               ║
║   No Docker. No BeautifulSoup. No browser needed.               ║
╚══════════════════════════════════════════════════════════════════╝

SETUP
─────
1.  pip install requests
2.  Get a FREE TMDB API key (30 seconds):
       → https://www.themoviedb.org/settings/api
       → Sign up → Developer → Copy "API Read Access Token"
3.  Paste it into TMDB_API_KEY below (or set env var TMDB_KEY)
4.  python scraper.py

HOW THE STREAMS WORK
─────────────────────
These embed providers are the same backend that powers multimovies,
lookmovie, fmovies clones, etc. They accept a TMDB or IMDB id and
return a working iframe player — no scraping of the video itself.

    https://vidsrc.me/embed/movie?tmdb=550
    https://vidsrc.me/embed/tv?tmdb=1396&season=1&episode=1

Open the URL in any browser → video plays immediately.
"""

import os
import sys
import json
import time
import requests
import webbrowser
from urllib.parse import quote_plus

# ─── YOUR TMDB API KEY ────────────────────────────────────────────────────────
# Option A: paste directly here
# Option B: set TMDB_KEY env var in main.py or .env — it will be picked up automatically
TMDB_API_KEY = "46aa19c9afc3d3d86b13366099cee99e"   # ← paste key here, OR leave and set in main.py

def _get_key() -> str:
    """Read key at call-time so env vars set after import are picked up."""
    # Env var always wins over the module-level default
    env = os.environ.get("TMDB_KEY", "")
    if env and env != "YOUR_TMDB_API_KEY_HERE":
        return env
    return TMDB_API_KEY

# ─── Embed providers (all free, no key needed) ────────────────────────────────
# Each entry: (name, movie_url_template, tv_url_template)
# Placeholders: {tmdb}, {imdb}, {season}, {episode}
EMBED_PROVIDERS = [
    (
        "VidSrc.me",
        "https://vidsrc.me/embed/movie?tmdb={tmdb}",
        "https://vidsrc.me/embed/tv?tmdb={tmdb}&season={season}&episode={episode}",
    ),
    (
        "VidSrc.cc  (v2)",
        "https://vidsrc.cc/v2/embed/movie/{tmdb}",
        "https://vidsrc.cc/v2/embed/tv/{tmdb}/{season}/{episode}",
    ),
    (
        "VidSrc.cc  (v3)",
        "https://vidsrc.cc/v3/embed/movie/{tmdb}",
        "https://vidsrc.cc/v3/embed/tv/{tmdb}/{season}/{episode}",
    ),
    (
        "VidLink.pro",
        "https://vidlink.pro/movie/{tmdb}",
        "https://vidlink.pro/tv/{tmdb}/{season}/{episode}",
    ),
    (
        "AutoEmbed.cc",
        "https://autoembed.cc/movie/tmdb/{tmdb}",
        "https://autoembed.cc/tv/tmdb/{tmdb}-{season}-{episode}",
    ),
    (
        "2Embed.cc",
        "https://www.2embed.cc/embed/{imdb}",
        "https://www.2embed.cc/embedtv/{imdb}&s={season}&e={episode}",
    ),
    (
        "Videasy",
        "https://player.videasy.net/movie/{tmdb}",
        "https://player.videasy.net/tv/{tmdb}/{season}/{episode}",
    ),
    (
        "VidSrc.pro",
        "https://vidsrc.pro/embed/movie/{tmdb}",
        "https://vidsrc.pro/embed/tv/{tmdb}/{season}/{episode}",
    ),
    (
        "SuperEmbed",
        "https://www.superembed.stream/embed/tmdb:{tmdb}",
        "https://www.superembed.stream/embed/tmdb:{tmdb}:{season}:{episode}",
    ),
]

# ─── TMDB config ──────────────────────────────────────────────────────────────
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"
REQ_TIMEOUT  = 10


# ─── Terminal colours ─────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    DIM    = "\033[2m"
    MAG    = "\033[95m"

def ok(m):   print(f"{C.GREEN}✅  {m}{C.RESET}")
def warn(m): print(f"{C.YELLOW}⚠️   {m}{C.RESET}")
def err(m):  print(f"{C.RED}❌  {m}{C.RESET}")
def head(m): print(f"\n{C.BOLD}{C.CYAN}{m}{C.RESET}")


# ─── TMDB helper ─────────────────────────────────────────────────────────────

def _is_bearer_token(key: str) -> bool:
    """
    TMDB has two credential types:
      - Short API key  : 32 hex chars  e.g. "46aa19c9afc3d3d86b13366099cee99e"
      - Bearer token   : long JWT      e.g. "eyJhbGciOiJIUzI1NiJ9.eyJ..."
    The short key must be passed as ?api_key= query param.
    The Bearer token must be passed as Authorization: Bearer <token>.
    """
    return len(key) > 40  # Bearer tokens are ~200+ chars; short keys are 32


def tmdb_get(endpoint: str, params: dict = None) -> dict | None:
    """
    Make an authenticated TMDB API call.
    Auto-detects whether TMDB_API_KEY is a short key or Bearer token.
    """
    params = dict(params or {})
    headers = {"accept": "application/json"}

    if _is_bearer_token(TMDB_API_KEY):
        # Long JWT — use Authorization header
        headers["Authorization"] = f"Bearer {TMDB_API_KEY}"
    else:
        # Short 32-char key — use query param
        params["api_key"] = TMDB_API_KEY

    url = f"{TMDB_BASE}/{endpoint}"
    try:
        r = requests.get(url, params=params, headers=headers, timeout=REQ_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError:
        if r.status_code == 401:
            err("TMDB: Invalid API key.")
            print(f"\n  You have two options for the key — pick whichever you see on TMDB:")
            print(f"  ┌─────────────────────────────────────────────────────────┐")
            print(f"  │  Option A — API Key (short, 32 chars):                  │")
            print(f"  │    TMDB_API_KEY = \"46aa19c9...\"                         │")
            print(f"  │                                                          │")
            print(f"  │  Option B — API Read Access Token (long JWT):           │")
            print(f"  │    TMDB_API_KEY = \"eyJhbGciOiJIUzI1NiJ9...\"            │")
            print(f"  └─────────────────────────────────────────────────────────┘")
            print(f"  Get either at: https://www.themoviedb.org/settings/api\n")
            sys.exit(1)
        err(f"TMDB HTTP {r.status_code} — {endpoint}")
    except requests.exceptions.ConnectionError:
        err("Cannot reach TMDB. Check your internet connection.")
    except requests.exceptions.Timeout:
        err("TMDB request timed out.")
    return None


def validate_key() -> bool:
    """
    Check API key works. /configuration works with BOTH short key and Bearer token.
    Reads key lazily so env vars set after import (e.g. from main.py) are picked up.
    """
    key = _get_key()
    if not key or key == "YOUR_TMDB_API_KEY_HERE":
        err("No TMDB API key set!")
        print(f"  Option A: edit scraper.py → paste key into TMDB_API_KEY")
        print(f"  Option B: edit main.py    → paste key into os.environ.setdefault(\"TMDB_KEY\", \"your_key\")")
        print(f"  Get one free at: https://www.themoviedb.org/settings/api")
        print(f"\n  Both key types work:")
        print(f"    Short key  (32 chars) : \"46aa19c9...\"")
        print(f"    Bearer token (long)   : \"eyJhbGci...\"")
        return False
    key_type = "Bearer token" if _is_bearer_token(key) else "short API key"
    print(f"  Key type detected: {key_type}")
    data = tmdb_get("configuration")
    return data is not None and "images" in data


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Search
# ══════════════════════════════════════════════════════════════════════════════

def search(query: str) -> dict | None:
    """
    Search TMDB for movies + TV shows simultaneously.
    Returns selected result or None.
    """
    head(f"🔍  Searching: '{query}' ...")

    data = tmdb_get("search/multi", params={"query": query, "page": 1})
    if not data:
        return None

    # Filter to movies and TV only, sort by popularity
    results = [
        r for r in data.get("results", [])
        if r.get("media_type") in ("movie", "tv")
    ]
    results.sort(key=lambda x: x.get("popularity", 0), reverse=True)

    if not results:
        warn("No results found. Try a different spelling.")
        return None

    # Display top 8
    total = min(len(results), 8)
    print(f"\n   {'#':<4} {'Title':<45} {'Type':<8} {'Year':<6} {'Rating'}")
    print(f"   {'─'*4} {'─'*45} {'─'*8} {'─'*6} {'─'*6}")

    for i, r in enumerate(results[:total], 1):
        mtype = r["media_type"]
        title = r.get("title") or r.get("name", "Unknown")
        year  = (r.get("release_date") or r.get("first_air_date") or "????")[:4]
        score = r.get("vote_average", 0)
        label = "🎬 Movie" if mtype == "movie" else "📺 TV   "
        score_str = f"{score:.1f}⭐" if score else "N/A"
        print(f"   {C.BOLD}{i:<4}{C.RESET} {title:<45} {label} {year:<6} {score_str}")

    print()
    raw = input(f"   Pick (1–{total}), Enter = #1: ").strip()
    idx = (int(raw) - 1) if raw.isdigit() and 1 <= int(raw) <= total else 0
    chosen = results[idx]
    title = chosen.get("title") or chosen.get("name", "?")
    ok(f"Selected: {title}  [{chosen['media_type'].upper()}]")
    return chosen


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Full Metadata
# ══════════════════════════════════════════════════════════════════════════════

def get_metadata(item: dict) -> dict:
    """Fetch full metadata from TMDB for the selected movie/show."""
    head("📄  Fetching full metadata ...")

    mtype = item["media_type"]
    tmdb_id = item["id"]
    endpoint = f"movie/{tmdb_id}" if mtype == "movie" else f"tv/{tmdb_id}"

    data = tmdb_get(endpoint, params={"append_to_response": "external_ids,credits,videos"})
    if not data:
        # Fallback to search result data
        return _basic_meta(item)

    # External IDs (IMDB)
    ext = data.get("external_ids", {})
    imdb_id = ext.get("imdb_id", "N/A")

    # Cast (top 8)
    cast = [
        p["name"] for p in data.get("credits", {}).get("cast", [])[:8]
    ]

    # Trailer
    trailer = next(
        (
            f"https://youtube.com/watch?v={v['key']}"
            for v in data.get("videos", {}).get("results", [])
            if v.get("type") == "Trailer" and v.get("site") == "YouTube"
        ),
        "N/A"
    )

    # Seasons (TV only)
    seasons = []
    if mtype == "tv":
        seasons = [
            {
                "number"   : s["season_number"],
                "name"     : s.get("name", f"Season {s['season_number']}"),
                "episodes" : s.get("episode_count", "?"),
                "air_date" : (s.get("air_date") or "?")[:4],
            }
            for s in data.get("seasons", [])
            if s.get("season_number", 0) > 0   # skip "Specials" season 0
        ]

    meta = {
        "tmdb_id"    : tmdb_id,
        "imdb_id"    : imdb_id,
        "media_type" : mtype,
        "title"      : data.get("title") or data.get("name", "N/A"),
        "tagline"    : data.get("tagline", ""),
        "overview"   : data.get("overview", "N/A"),
        "status"     : data.get("status", "N/A"),
        "year"       : (data.get("release_date") or data.get("first_air_date") or "?")[:4],
        "runtime"    : data.get("runtime") or data.get("episode_run_time", [None])[0],
        "rating"     : data.get("vote_average", "N/A"),
        "votes"      : data.get("vote_count", 0),
        "genres"     : [g["name"] for g in data.get("genres", [])],
        "languages"  : [l["english_name"] for l in data.get("spoken_languages", [])],
        "countries"  : [c["name"] for c in data.get("production_countries", [])],
        "poster"     : f"{TMDB_IMG}{data['poster_path']}" if data.get("poster_path") else "N/A",
        "backdrop"   : f"{TMDB_IMG}{data['backdrop_path']}" if data.get("backdrop_path") else "N/A",
        "cast"       : cast,
        "trailer"    : trailer,
        "seasons"    : seasons,
        # TV specific
        "total_eps"  : data.get("number_of_episodes", "N/A"),
        "total_seas" : data.get("number_of_seasons", "N/A"),
        "networks"   : [n["name"] for n in data.get("networks", [])],
    }
    return meta


def _basic_meta(item: dict) -> dict:
    """Minimal metadata from search result when detail fetch fails."""
    mtype = item["media_type"]
    return {
        "tmdb_id"    : item["id"],
        "imdb_id"    : "N/A",
        "media_type" : mtype,
        "title"      : item.get("title") or item.get("name", "N/A"),
        "tagline"    : "",
        "overview"   : item.get("overview", "N/A"),
        "status"     : "N/A",
        "year"       : (item.get("release_date") or item.get("first_air_date") or "?")[:4],
        "runtime"    : "N/A",
        "rating"     : item.get("vote_average", "N/A"),
        "votes"      : item.get("vote_count", 0),
        "genres"     : [],
        "languages"  : [],
        "countries"  : [],
        "poster"     : f"{TMDB_IMG}{item['poster_path']}" if item.get("poster_path") else "N/A",
        "backdrop"   : "N/A",
        "cast"       : [],
        "trailer"    : "N/A",
        "seasons"    : [],
        "total_eps"  : "N/A",
        "total_seas" : "N/A",
        "networks"   : [],
    }


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Season / Episode Picker (TV only)
# ══════════════════════════════════════════════════════════════════════════════

def pick_episode(meta: dict) -> tuple[int, int] | None:
    """
    For TV shows: let user pick season and episode.
    Returns (season_num, episode_num) or None for movies.
    """
    if meta["media_type"] == "movie":
        return None

    seasons = meta["seasons"]
    if not seasons:
        warn("No season info available.")
        s = input("   Enter season number manually: ").strip()
        e = input("   Enter episode number: ").strip()
        return (int(s) if s.isdigit() else 1, int(e) if e.isdigit() else 1)

    head("📺  Season Selection")
    print()
    for s in seasons:
        print(f"   Season {s['number']:>2}  │  {s['name']:<35}  "
              f"{C.DIM}{s['episodes']} eps  ({s['air_date']}){C.RESET}")

    print()
    s_raw = input(f"   Season (1–{seasons[-1]['number']}), Enter = 1: ").strip()
    s_num = int(s_raw) if s_raw.isdigit() else 1

    # Get episode count for chosen season
    chosen_season = next((s for s in seasons if s["number"] == s_num), seasons[0])
    ep_count = chosen_season["episodes"]

    e_raw = input(f"   Episode (1–{ep_count}), Enter = 1: ").strip()
    e_num = int(e_raw) if e_raw.isdigit() else 1

    ok(f"Season {s_num}, Episode {e_num}")
    return (s_num, e_num)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Build Embed URLs
# ══════════════════════════════════════════════════════════════════════════════

def build_embed_urls(meta: dict, season: int = None, episode: int = None) -> list[dict]:
    """
    Build embed URLs from all providers using TMDB/IMDB IDs.
    Returns list of { provider, url, type }
    """
    tmdb_id = meta["tmdb_id"]
    imdb_id = meta["imdb_id"] if meta["imdb_id"] != "N/A" else ""
    mtype   = meta["media_type"]
    links   = []

    for name, movie_tpl, tv_tpl in EMBED_PROVIDERS:
        if mtype == "movie":
            url = movie_tpl.format(
                tmdb=tmdb_id,
                imdb=imdb_id,
            )
        else:
            url = tv_tpl.format(
                tmdb=tmdb_id,
                imdb=imdb_id,
                season=season or 1,
                episode=episode or 1,
            )

        # Skip providers that need imdb_id when we don't have it
        if "{imdb}" in url and not imdb_id:
            continue

        links.append({"provider": name, "url": url})

    return links


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — Validate Links (optional, fast HEAD check)
# ══════════════════════════════════════════════════════════════════════════════

def validate_links(links: list[dict]) -> list[dict]:
    """
    Quick HEAD request to each embed URL.
    Only keep ones that return 200. Skips if too slow.
    """
    head(f"🔗  Validating {len(links)} embed URLs ...")
    valid = []

    for item in links:
        url = item["url"]
        try:
            r = requests.head(
                url,
                timeout=6,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if r.status_code == 200:
                ok(f"{item['provider']:<20}  {C.DIM}{url[:65]}{C.RESET}")
                valid.append(item)
            else:
                print(f"   {C.DIM}✗  {item['provider']:<20}  [{r.status_code}]{C.RESET}")
        except requests.exceptions.Timeout:
            print(f"   {C.DIM}⏱  {item['provider']:<20}  [timeout]{C.RESET}")
        except requests.exceptions.RequestException:
            print(f"   {C.DIM}✗  {item['provider']:<20}  [error]{C.RESET}")
        time.sleep(0.2)

    return valid if valid else links   # if all fail validation, return all anyway


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 6 — Print Results
# ══════════════════════════════════════════════════════════════════════════════

def print_results(meta: dict, links: list[dict], season=None, episode=None) -> None:
    SEP  = "═" * 68
    sep2 = "─" * 68

    print(f"\n{C.BOLD}{SEP}{C.RESET}")
    print(f"{C.BOLD}  {'🎬' if meta['media_type']=='movie' else '📺'}  RESULTS{C.RESET}")
    print(f"{C.BOLD}{SEP}{C.RESET}")

    # ── Metadata ──────────────────────────────────────────────────────────────
    print(f"\n{C.CYAN}  METADATA{C.RESET}")
    print(f"  {sep2}")
    print(f"  Title      : {C.BOLD}{meta['title']}{C.RESET}  {C.DIM}({meta['year']}){C.RESET}")
    if meta["tagline"]:
        print(f"  Tagline    : {C.DIM}\"{meta['tagline']}\"{C.RESET}")
    print(f"  Type       : {meta['media_type'].upper()}")
    print(f"  Status     : {meta['status']}")
    print(f"  Rating     : {meta['rating']} / 10  ({meta['votes']:,} votes)")
    print(f"  Runtime    : {meta['runtime']} min" if meta['runtime'] else f"  Runtime    : N/A")
    print(f"  Genres     : {', '.join(meta['genres']) or 'N/A'}")
    print(f"  Languages  : {', '.join(meta['languages']) or 'N/A'}")
    print(f"  Countries  : {', '.join(meta['countries']) or 'N/A'}")
    print(f"  TMDB ID    : {meta['tmdb_id']}")
    print(f"  IMDB ID    : {meta['imdb_id']}")
    print(f"  Poster     : {meta['poster']}")
    if meta["trailer"] != "N/A":
        print(f"  Trailer    : {meta['trailer']}")
    if meta["cast"]:
        print(f"  Cast       : {', '.join(meta['cast'])}")
    if meta["networks"]:
        print(f"  Networks   : {', '.join(meta['networks'])}")

    # TV extra info
    if meta["media_type"] == "tv":
        print(f"  Seasons    : {meta['total_seas']}")
        print(f"  Episodes   : {meta['total_eps']} total")
        if meta["seasons"] and season:
            print(f"  Streaming  : Season {season}, Episode {episode}")

    # Synopsis
    ov = meta["overview"]
    print(f"\n  Overview:")
    for i in range(0, min(len(ov), 500), 72):
        print(f"    {ov[i:i+72]}")

    # ── Stream links ──────────────────────────────────────────────────────────
    ep_label = f" — S{season:02}E{episode:02}" if season else ""
    print(f"\n{C.CYAN}  STREAMING LINKS{ep_label}  ({len(links)} providers){C.RESET}")
    print(f"  {sep2}")

    for i, item in enumerate(links, 1):
        print(f"\n  {C.BOLD}[{i}] {item['provider']}{C.RESET}")
        print(f"      {C.GREEN}{item['url']}{C.RESET}")

    # ── How to use ────────────────────────────────────────────────────────────
    print(f"\n  {sep2}")
    print(f"  {C.BOLD}💡  How to use these links:{C.RESET}")
    print(f"  1. Copy any URL above → paste into your browser → video plays")
    print(f"  2. If one provider is slow/broken, try the next one")
    print(f"  3. All links are iframe embed players (same as multimovies.autos)")
    print(f"  4. Best quality is usually VidSrc.me or VidLink.pro")
    print(f"  {SEP}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7 — Open in Browser
# ══════════════════════════════════════════════════════════════════════════════

def open_in_browser(links: list[dict]) -> None:
    """Let user pick a link to open directly in their default browser."""
    if not links:
        return

    print(f"  Open in browser?")
    raw = input(f"  Enter link number (1–{len(links)}), or Enter to skip: ").strip()

    if raw.isdigit() and 1 <= int(raw) <= len(links):
        url = links[int(raw) - 1]["url"]
        print(f"  Opening: {url}")
        webbrowser.open(url)
    else:
        print(f"  {C.DIM}Skipped.{C.RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 8 — Save to JSON
# ══════════════════════════════════════════════════════════════════════════════

def save_results(meta: dict, links: list[dict], season=None, episode=None) -> None:
    ep_tag = f"_S{season:02}E{episode:02}" if season else ""
    fname  = meta["title"].replace(" ", "_").replace("/", "-")[:35] + f"{ep_tag}_index.json"

    if meta["media_type"] == "movie":
        # ── Movie: flat structure compatible with db_insert.py ────────────────
        output = {
            "media_type": "movie",
            "metadata": {
                "tmdb_id"       : meta["tmdb_id"],
                "imdb_id"       : meta.get("imdb_id", "N/A"),
                "title"         : meta["title"],
                "overview"      : meta.get("overview"),
                "poster"        : meta.get("poster"),
                "year"          : meta.get("year"),
                "rating"        : meta.get("rating"),
                "status"        : meta.get("status"),
                "genres"        : meta.get("genres", []),
                "runtime"       : meta.get("runtime"),
                "tagline"       : meta.get("tagline", ""),
                "trailer"       : meta.get("trailer"),
                "cast"          : meta.get("cast", []),
            },
            "embed_links": links,   # flat list — movies have no seasons
        }
    else:
        # ── TV single episode: wrapped in seasons structure ────────────────────
        output = {
            "media_type": "tv",
            "metadata": {
                "tmdb_id"       : meta["tmdb_id"],
                "imdb_id"       : meta.get("imdb_id", "N/A"),
                "title"         : meta["title"],
                "overview"      : meta.get("overview"),
                "poster"        : meta.get("poster"),
                "year"          : meta.get("year"),
                "rating"        : meta.get("rating"),
                "status"        : meta.get("status"),
                "genres"        : meta.get("genres", []),
                "total_seasons" : meta.get("total_seas"),
                "total_episodes": meta.get("total_eps"),
                "networks"      : meta.get("networks", []),
                "first_aired"   : meta.get("year"),
            },
            "seasons": [
                {
                    "season"       : season,
                    "name"         : f"Season {season}",
                    "air_date"     : "N/A",
                    "poster"       : "N/A",
                    "episode_count": 1,
                    "episodes": [
                        {
                            "episode"    : episode,
                            "title"      : f"Episode {episode}",
                            "air_date"   : "N/A",
                            "rating"     : meta.get("rating"),
                            "overview"   : "",
                            "still_image": "N/A",
                            "embed_links": links,
                        }
                    ],
                }
            ],
        }

    with open(fname, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    ok(f"Saved → {fname}")
    size_kb = os.path.getsize(fname) / 1024
    print(f"  {C.DIM}Size: {size_kb:.1f} KB  |  Links: {len(links)}{C.RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"{C.BOLD}{C.MAG}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║   🎬  Movie & Series Scraper  —  TMDB + Embed Providers         ║")
    print("║   Movies • TV Series • Anime • K-Drama • Documentaries          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    # Validate TMDB key
    print("  Checking TMDB API key ...")
    if not validate_key():
        sys.exit(1)
    ok("TMDB API key valid")

    print(f"  {C.DIM}Embed providers loaded: {len(EMBED_PROVIDERS)}{C.RESET}")
    print(f"  {C.DIM}Type 'quit' to exit\n{C.RESET}")

    while True:
        query = input(f"{C.BOLD}🔎  Search movie / series / anime: {C.RESET}").strip()
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("👋  Goodbye!")
            break

        # 1 — Search
        item = search(query)
        if not item:
            continue

        # 2 — Full metadata
        meta = get_metadata(item)

        # 3 — Pick episode if TV
        ep_info = pick_episode(meta)
        season  = ep_info[0] if ep_info else None
        episode = ep_info[1] if ep_info else None

        # 4 — Build embed URLs
        head("🔗  Building embed URLs ...")
        links = build_embed_urls(meta, season, episode)
        ok(f"Built {len(links)} embed links")

        # 5 — Optional validation (can be slow)
        do_validate = input("\n  Validate links? (checks which are live) y/n [n]: ").strip().lower()
        if do_validate == "y":
            links = validate_links(links)

        # 6 — Print results
        print_results(meta, links, season, episode)

        # 7 — Open in browser
        open_in_browser(links)

        # 8 — Save
        if input("  Save to JSON? (y/n): ").strip().lower() == "y":
            save_results(meta, links, season, episode)

        if input("\n  Search again? (y/n): ").strip().lower() != "y":
            print("👋  Goodbye!")
            break
        print()


if __name__ == "__main__":
    main()
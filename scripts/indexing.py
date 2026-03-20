"""
series_indexer.py
═════════════════
Import this into main.py OR run standalone.

Given a series name it will:
  1. Search TMDB → pick the right show
  2. Fetch every season + every episode automatically
  3. Build embed URLs for EVERY episode across ALL providers
  4. Save one big JSON file like:
     {
       "metadata": { ... },
       "seasons": [
         {
           "season": 1,
           "name": "Season 1",
           "episodes": [
             {
               "episode": 1,
               "title": "Pilot",
               "air_date": "2008-01-20",
               "overview": "...",
               "embed_links": [
                 { "provider": "VidSrc.me", "url": "..." },
                 ...
               ]
             },
             ...
           ]
         },
         ...
       ]
     }

USAGE (standalone):
    python series_indexer.py

USAGE (imported into main.py):
    from series_indexer import build_series_index
    build_series_index()          # interactive
    # or
    build_series_index("Breaking Bad")
"""

import os
import sys
import json
import time
import requests

# ─── Shared config — reads same key as scraper.py ────────────────────────────
TMDB_API_KEY = "46aa19c9afc3d3d86b13366099cee99e"   # ← paste key here, OR set in main.py

def _get_key() -> str:
    """Read key at call-time so env vars set after import are picked up."""
    env = os.environ.get("TMDB_KEY", "")
    if env and env != "YOUR_TMDB_API_KEY_HERE":
        return env
    return TMDB_API_KEY
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w500"
REQ_TIMEOUT  = 12
DELAY        = 0.25   # seconds between TMDB calls (rate limit: 50 req/s)

EMBED_PROVIDERS = [
    ("VidSrc.me",      "https://vidsrc.me/embed/tv?tmdb={tmdb}&season={season}&episode={episode}"),
    ("VidSrc.cc (v2)", "https://vidsrc.cc/v2/embed/tv/{tmdb}/{season}/{episode}"),
    ("VidSrc.cc (v3)", "https://vidsrc.cc/v3/embed/tv/{tmdb}/{season}/{episode}"),
    ("VidLink.pro",    "https://vidlink.pro/tv/{tmdb}/{season}/{episode}"),
    ("AutoEmbed.cc",   "https://autoembed.cc/tv/tmdb/{tmdb}-{season}-{episode}"),
    ("Videasy",        "https://player.videasy.net/tv/{tmdb}/{season}/{episode}"),
    ("VidSrc.pro",     "https://vidsrc.pro/embed/tv/{tmdb}/{season}/{episode}"),
    ("2Embed.cc",      "https://www.2embed.cc/embedtv/{imdb}&s={season}&e={episode}"),
]

# ─── Colours ──────────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m";  BOLD  = "\033[1m"
    GREEN  = "\033[92m"; RED   = "\033[91m"
    CYAN   = "\033[96m"; DIM   = "\033[2m"
    YELLOW = "\033[93m"; MAG   = "\033[95m"

def ok(m):   print(f"{C.GREEN}✅  {m}{C.RESET}")
def warn(m): print(f"{C.YELLOW}⚠️   {m}{C.RESET}")
def err(m):  print(f"{C.RED}❌  {m}{C.RESET}")
def info(m): print(f"{C.CYAN}    {m}{C.RESET}")


# ─── TMDB auth helper ─────────────────────────────────────────────────────────

def _is_bearer(key: str) -> bool:
    return len(key) > 40

def tmdb_get(endpoint: str, params: dict = None, retries: int = 3) -> dict | None:
    key     = _get_key()
    params  = dict(params or {})
    headers = {
        "accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    if _is_bearer(key):
        headers["Authorization"] = f"Bearer {key}"
    else:
        params["api_key"] = key

    url = f"{TMDB_BASE}/{endpoint}"

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=REQ_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError:
            if r.status_code == 401:
                err("Invalid TMDB API key.")
                sys.exit(1)
            if r.status_code == 404:
                return None   # season/episode doesn't exist — not fatal
            if r.status_code == 429:
                wait = 2 ** attempt
                warn(f"Rate limited — waiting {wait}s ...")
                time.sleep(wait)
                continue
            err(f"TMDB HTTP {r.status_code} — {endpoint}")
            return None
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError) as e:
            if attempt < retries:
                wait = attempt * 1.5
                warn(f"Connection error (attempt {attempt}/{retries}) — retrying in {wait:.0f}s ...")
                time.sleep(wait)
                continue
            err(f"Connection failed after {retries} attempts — {endpoint}")
            err(f"Detail: {e}")
            return None
        except requests.exceptions.Timeout:
            if attempt < retries:
                warn(f"Timeout (attempt {attempt}/{retries}) — retrying ...")
                time.sleep(attempt)
                continue
            err(f"Timed out — {endpoint}")
            return None
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  1. Search
# ══════════════════════════════════════════════════════════════════════════════

def search_series(query: str) -> dict | None:
    """Search TMDB for TV shows only. Returns chosen show dict."""
    print(f"\n{C.BOLD}🔍  Searching: '{query}' ...{C.RESET}")

    data = tmdb_get("search/tv", params={"query": query, "page": 1})
    if not data or not data.get("results"):
        err("No results found.")
        return None

    results = sorted(data["results"], key=lambda x: x.get("popularity", 0), reverse=True)
    total   = min(len(results), 8)

    print(f"\n   {'#':<4} {'Title':<45} {'Year':<6} {'Rating'}")
    print(f"   {'─'*4} {'─'*45} {'─'*6} {'─'*6}")
    for i, r in enumerate(results[:total], 1):
        year  = (r.get("first_air_date") or "????")[:4]
        score = r.get("vote_average", 0)
        print(f"   {C.BOLD}{i:<4}{C.RESET} {r.get('name','?'):<45} {year:<6} {score:.1f}⭐")

    print()
    raw = input(f"   Pick (1–{total}), Enter = #1: ").strip()
    idx = (int(raw) - 1) if raw.isdigit() and 1 <= int(raw) <= total else 0
    chosen = results[idx]
    ok(f"Selected: {chosen['name']}  (TMDB ID: {chosen['id']})")
    return chosen


# ══════════════════════════════════════════════════════════════════════════════
#  2. Full Series Details
# ══════════════════════════════════════════════════════════════════════════════

def get_series_details(tmdb_id: int) -> dict | None:
    """Fetch full series details including season list and external IDs."""
    info(f"Fetching series details for TMDB ID {tmdb_id} ...")
    data = tmdb_get(f"tv/{tmdb_id}", params={"append_to_response": "external_ids"})
    if not data:
        err("Could not fetch series details.")
        return None
    return data


# ══════════════════════════════════════════════════════════════════════════════
#  3. Season Details (all episodes in one season)
# ══════════════════════════════════════════════════════════════════════════════

def get_season_episodes(tmdb_id: int, season_num: int) -> list[dict]:
    """
    Fetch all episodes for a given season.
    Returns list of episode dicts.
    """
    data = tmdb_get(f"tv/{tmdb_id}/season/{season_num}")
    if not data:
        return []
    return data.get("episodes", [])


# ══════════════════════════════════════════════════════════════════════════════
#  4. Build Embed URLs for one episode
# ══════════════════════════════════════════════════════════════════════════════

def build_episode_embeds(tmdb_id: int, imdb_id: str, season: int, episode: int) -> list[dict]:
    """Build all provider embed URLs for a single episode."""
    links = []
    for name, tpl in EMBED_PROVIDERS:
        # Skip 2embed if no imdb_id
        if "{imdb}" in tpl and (not imdb_id or imdb_id == "N/A"):
            continue
        url = tpl.format(
            tmdb    = tmdb_id,
            imdb    = imdb_id or "",
            season  = season,
            episode = episode,
        )
        links.append({"provider": name, "url": url})
    return links


# ══════════════════════════════════════════════════════════════════════════════
#  5. Full Index Builder
# ══════════════════════════════════════════════════════════════════════════════

def build_full_index(series_data: dict, search_result: dict) -> dict:
    """
    Core function: iterates every season → every episode,
    builds embed links for each, returns the full index dict.
    """
    tmdb_id = series_data["id"]
    imdb_id = series_data.get("external_ids", {}).get("imdb_id") or "N/A"
    title   = series_data.get("name", "Unknown")

    # Filter real seasons (skip season 0 = Specials unless desired)
    all_seasons = [
        s for s in series_data.get("seasons", [])
        if s.get("season_number", 0) > 0
    ]

    total_seasons  = len(all_seasons)
    total_episodes = sum(s.get("episode_count", 0) for s in all_seasons)

    print(f"\n{C.BOLD}{C.MAG}  Building full index for: {title}{C.RESET}")
    print(f"  Seasons  : {total_seasons}")
    print(f"  Episodes : ~{total_episodes} total")
    print(f"  TMDB ID  : {tmdb_id}")
    print(f"  IMDB ID  : {imdb_id}")
    print(f"  Providers: {len(EMBED_PROVIDERS)}\n")

    # Ask if user wants all seasons or specific range
    print(f"  Which seasons to index?")
    print(f"  [A] All seasons  (1–{total_seasons})")
    print(f"  [R] Range        (e.g. 1-3)")
    print(f"  [S] Single season")
    choice = input("  Choice (A/R/S), Enter = All: ").strip().upper()

    if choice == "R":
        raw = input(f"  Enter range (e.g. 1-3): ").strip()
        try:
            start, end = map(int, raw.split("-"))
            seasons_to_index = [s for s in all_seasons
                                if start <= s["season_number"] <= end]
        except Exception:
            warn("Invalid range — indexing all seasons.")
            seasons_to_index = all_seasons
    elif choice == "S":
        raw = input(f"  Season number (1–{total_seasons}): ").strip()
        n   = int(raw) if raw.isdigit() else 1
        seasons_to_index = [s for s in all_seasons if s["season_number"] == n]
    else:
        seasons_to_index = all_seasons

    print()

    # Build metadata block
    metadata = {
        "tmdb_id"      : tmdb_id,
        "imdb_id"      : imdb_id,
        "title"        : title,
        "original_name": series_data.get("original_name", title),
        "overview"     : series_data.get("overview", "N/A"),
        "status"       : series_data.get("status", "N/A"),
        "first_aired"  : series_data.get("first_air_date", "N/A"),
        "last_aired"   : series_data.get("last_air_date", "N/A"),
        "rating"       : series_data.get("vote_average", "N/A"),
        "votes"        : series_data.get("vote_count", 0),
        "genres"       : [g["name"] for g in series_data.get("genres", [])],
        "networks"     : [n["name"] for n in series_data.get("networks", [])],
        "languages"    : series_data.get("spoken_languages", []),
        "poster"       : f"{TMDB_IMG}{series_data['poster_path']}"
                         if series_data.get("poster_path") else "N/A",
        "total_seasons"  : series_data.get("number_of_seasons", "N/A"),
        "total_episodes" : series_data.get("number_of_episodes", "N/A"),
        "indexed_seasons": len(seasons_to_index),
        "embed_providers": [name for name, _ in EMBED_PROVIDERS],
    }

    # Build seasons block
    seasons_output = []
    indexed_ep_count = 0

    for s in seasons_to_index:
        s_num  = s["season_number"]
        s_name = s.get("name", f"Season {s_num}")
        ep_count_expected = s.get("episode_count", "?")

        print(f"  {C.BOLD}Season {s_num:<3}{C.RESET} — {s_name}  "
              f"{C.DIM}({ep_count_expected} eps){C.RESET}")

        # Fetch individual episode details
        episodes_raw = get_season_episodes(tmdb_id, s_num)
        time.sleep(DELAY)

        episodes_output = []
        for ep in episodes_raw:
            ep_num   = ep.get("episode_number", 0)
            ep_title = ep.get("name", f"Episode {ep_num}")
            ep_date  = ep.get("air_date", "N/A")
            ep_over  = ep.get("overview", "")
            ep_score = ep.get("vote_average", "N/A")
            ep_still = f"{TMDB_IMG}{ep['still_path']}" if ep.get("still_path") else "N/A"

            embeds = build_episode_embeds(tmdb_id, imdb_id, s_num, ep_num)

            episodes_output.append({
                "episode"    : ep_num,
                "title"      : ep_title,
                "air_date"   : ep_date,
                "rating"     : ep_score,
                "overview"   : ep_over,
                "still_image": ep_still,
                "embed_links": embeds,
            })

            indexed_ep_count += 1
            # Progress dot
            print(f"    Ep {ep_num:>3}  {C.DIM}{ep_title[:50]}{C.RESET}")

        seasons_output.append({
            "season"      : s_num,
            "name"        : s_name,
            "air_date"    : s.get("air_date", "N/A"),
            "poster"      : f"{TMDB_IMG}{s['poster_path']}" if s.get("poster_path") else "N/A",
            "episode_count": len(episodes_output),
            "episodes"    : episodes_output,
        })
        print()

    print(f"  {C.GREEN}✅  Indexed {indexed_ep_count} episodes across "
          f"{len(seasons_to_index)} season(s){C.RESET}")

    return {
        "metadata": metadata,
        "seasons" : seasons_output,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  6. Save JSON
# ══════════════════════════════════════════════════════════════════════════════

def save_index(index: dict, title: str) -> str:
    """Save the full index to a JSON file. Returns filename."""
    safe_title = title.replace(" ", "_").replace("/", "-")[:40]
    filename   = f"{safe_title}_full_index.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    ok(f"Saved → {filename}")
    size_kb = os.path.getsize(filename) / 1024
    info(f"File size: {size_kb:.1f} KB  |  "
         f"Seasons: {len(index['seasons'])}  |  "
         f"Episodes: {sum(len(s['episodes']) for s in index['seasons'])}")
    return filename


# ══════════════════════════════════════════════════════════════════════════════
#  7. Main entry point (importable + standalone)
# ══════════════════════════════════════════════════════════════════════════════

def build_series_index(query: str = None) -> dict | None:
    """
    Full pipeline: search → fetch → index → save.

    Args:
        query: Series name. If None, will prompt user.

    Returns:
        The full index dict (also saved to JSON).
    """
    # Key check — read lazily so env var from main.py is picked up
    if not _get_key() or _get_key() == "YOUR_TMDB_API_KEY_HERE":
        err("No TMDB API key set.")
        print("  Option A: edit series_indexer.py → paste key into TMDB_API_KEY")
        print("  Option B: edit main.py → paste key into os.environ.setdefault(\"TMDB_KEY\", \"your_key\")")
        return None

    # Get query
    if not query:
        query = input(f"{C.BOLD}🎬  Enter series / anime name: {C.RESET}").strip()
    if not query:
        return None

    # 1. Search
    result = search_series(query)
    if not result:
        return None

    # 2. Full details
    details = get_series_details(result["id"])
    if not details:
        return None

    # 3. Build full index
    index = build_full_index(details, result)

    # 4. Save
    filename = save_index(index, details.get("name", query))

    # 5. Quick summary
    print(f"\n{C.BOLD}{'═'*60}{C.RESET}")
    print(f"  📦  Index complete: {details.get('name')}")
    print(f"  Seasons indexed : {len(index['seasons'])}")
    total_ep = sum(len(s['episodes']) for s in index['seasons'])
    print(f"  Episodes indexed: {total_ep}")
    providers = len(EMBED_PROVIDERS)
    print(f"  Embed links     : {total_ep * providers} total  ({providers} providers × {total_ep} eps)")
    print(f"  Output file     : {filename}")
    print(f"{C.BOLD}{'═'*60}{C.RESET}\n")

    return index


# ══════════════════════════════════════════════════════════════════════════════
#  Standalone run
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"{C.BOLD}{C.MAG}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   📦  Series Full Indexer  —  All Seasons & Episodes     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(C.RESET)

    while True:
        index = build_series_index()
        if not index:
            print("Try again.\n")
            continue
        again = input("Index another series? (y/n): ").strip().lower()
        if again != "y":
            print("👋  Done!")
            break
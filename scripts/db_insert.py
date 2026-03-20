"""
db_insert.py
════════════
Reads the JSON produced by series_indexer.py and inserts
everything cleanly into your Supabase PostgreSQL database.

SETUP
─────
1.  pip install psycopg2-binary python-dotenv
2.  Copy .env.example → .env and fill in your DB URL
3.  Run schema.sql once in Supabase SQL Editor
4.  python db_insert.py

USAGE
─────
    python db_insert.py                          # interactive picker
    python db_insert.py Breaking_Bad_full_index.json  # specific file
"""

import os
import sys
import json
import glob
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# ─── Connection config ────────────────────────────────────────────────────────
#
#  Get your string from Supabase:
#  Dashboard → Connect (top of page) → Session Pooler tab → copy string
#  Replace [YOUR-PASSWORD] with your actual password (remove the brackets)
#
#  Format:
#  postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
#
DB_URL = os.environ.get("SUPABASE_DB_URL", "")


# ─── Colours ──────────────────────────────────────────────────────────────────
class C:
    RESET = "\033[0m";  BOLD  = "\033[1m"
    GREEN = "\033[92m"; RED   = "\033[91m"
    CYAN  = "\033[96m"; DIM   = "\033[2m"
    YEL   = "\033[93m"; MAG   = "\033[95m"

def ok(m):   print(f"{C.GREEN}✅  {m}{C.RESET}")
def warn(m): print(f"{C.YEL}⚠️   {m}{C.RESET}")
def err(m):  print(f"{C.RED}❌  {m}{C.RESET}")
def info(m): print(f"{C.CYAN}    {m}{C.RESET}")
def head(m): print(f"\n{C.BOLD}{C.MAG}{m}{C.RESET}")

def _safe_float(v):
    try:    return float(v) if v not in (None, "N/A", "") else None
    except: return None

def _safe_int(v):
    try:    return int(v) if v not in (None, "N/A", "") else None
    except: return None


# ─── Connect ──────────────────────────────────────────────────────────────────

def get_connection():
    if not DB_URL:
        err("SUPABASE_DB_URL is not set.")
        print("\n  Add to your .env file:")
        print("  SUPABASE_DB_URL=postgresql://postgres.xxxx:password@aws-0-xxxx.pooler.supabase.com:5432/postgres\n")
        print("  Get it from: Supabase Dashboard → Connect → Session Pooler tab")
        sys.exit(1)
    try:
        conn = psycopg2.connect(DB_URL, sslmode="require", connect_timeout=15)
        conn.autocommit = False
        return conn
    except psycopg2.OperationalError as e:
        err(f"Connection failed: {e}")
        print("\n  Tips:")
        print("  • Use the SESSION POOLER string (not Direct Connection)")
        print("  • Dashboard → Connect → Session Pooler tab")
        print("  • Make sure password has no [] brackets around it")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  Upsert helpers (ON CONFLICT = safe to re-run anytime)
# ══════════════════════════════════════════════════════════════════════════════

def upsert_series(cur, meta: dict) -> int:
    cur.execute("""
        INSERT INTO series
            (tmdb_id, title, overview, poster, year, rating,
             status, genres, total_seasons, total_episodes)
        VALUES
            (%(tmdb_id)s, %(title)s, %(overview)s, %(poster)s, %(year)s,
             %(rating)s, %(status)s, %(genres)s, %(total_seasons)s, %(total_episodes)s)
        ON CONFLICT (tmdb_id) DO UPDATE SET
            title           = EXCLUDED.title,
            overview        = EXCLUDED.overview,
            poster          = EXCLUDED.poster,
            year            = EXCLUDED.year,
            rating          = EXCLUDED.rating,
            status          = EXCLUDED.status,
            genres          = EXCLUDED.genres,
            total_seasons   = EXCLUDED.total_seasons,
            total_episodes  = EXCLUDED.total_episodes
        RETURNING id
    """, {
        "tmdb_id"       : meta["tmdb_id"],
        "title"         : meta["title"],
        "overview"      : meta.get("overview"),
        "poster"        : meta.get("poster") if meta.get("poster") != "N/A" else None,
        "year"          : (meta.get("first_aired") or "")[:4] or None,
        "rating"        : _safe_float(meta.get("rating")),
        "status"        : meta.get("status"),
        "genres"        : json.dumps(meta.get("genres", [])),
        "total_seasons" : _safe_int(meta.get("total_seasons")),
        "total_episodes": _safe_int(meta.get("total_episodes")),
    })
    return cur.fetchone()[0]


def upsert_season(cur, series_id: int, season: dict) -> int:
    cur.execute("""
        INSERT INTO seasons
            (series_id, season_number, name, air_date, poster, episode_count)
        VALUES
            (%(series_id)s, %(season_number)s, %(name)s,
             %(air_date)s, %(poster)s, %(episode_count)s)
        ON CONFLICT (series_id, season_number) DO UPDATE SET
            name          = EXCLUDED.name,
            air_date      = EXCLUDED.air_date,
            poster        = EXCLUDED.poster,
            episode_count = EXCLUDED.episode_count
        RETURNING id
    """, {
        "series_id"    : series_id,
        "season_number": season["season"],
        "name"         : season.get("name"),
        "air_date"     : season.get("air_date"),
        "poster"       : season.get("poster") if season.get("poster") != "N/A" else None,
        "episode_count": season.get("episode_count"),
    })
    return cur.fetchone()[0]


def upsert_episode(cur, series_id: int, season_id: int,
                   season_num: int, ep: dict) -> int:
    cur.execute("""
        INSERT INTO episodes
            (season_id, series_id, season_number, episode_number,
             title, air_date, still_image, rating)
        VALUES
            (%(season_id)s, %(series_id)s, %(season_number)s, %(episode_number)s,
             %(title)s, %(air_date)s, %(still_image)s, %(rating)s)
        ON CONFLICT (series_id, season_number, episode_number) DO UPDATE SET
            title       = EXCLUDED.title,
            air_date    = EXCLUDED.air_date,
            still_image = EXCLUDED.still_image,
            rating      = EXCLUDED.rating
        RETURNING id
    """, {
        "season_id"     : season_id,
        "series_id"     : series_id,
        "season_number" : season_num,
        "episode_number": ep["episode"],
        "title"         : ep.get("title"),
        "air_date"      : ep.get("air_date"),
        "still_image"   : ep.get("still_image") if ep.get("still_image") not in (None, "N/A") else None,
        "rating"        : _safe_float(ep.get("rating")),
    })
    return cur.fetchone()[0]


def upsert_embed_links_bulk(cur, episode_id: int, links: list) -> int:
    """Bulk insert all embed links for one episode."""
    rows = [
        {"episode_id": episode_id, "provider": l["provider"], "url": l["url"]}
        for l in links
        if l.get("provider") and l.get("url")
    ]
    if not rows:
        return 0
    psycopg2.extras.execute_batch(cur, """
        INSERT INTO embed_links (episode_id, provider, url)
        VALUES (%(episode_id)s, %(provider)s, %(url)s)
        ON CONFLICT (episode_id, provider) DO UPDATE SET url = EXCLUDED.url
    """, rows, page_size=200)
    return len(rows)


# ══════════════════════════════════════════════════════════════════════════════
#  Main loader
# ══════════════════════════════════════════════════════════════════════════════

def insert_movie_as_series(cur, meta: dict, links: list) -> tuple:
    """
    Store a movie in the series/seasons/episodes/embed_links tables.
    Uses season=1, episode=1 as a convention for movies.
    Returns (series_id, season_id, episode_id).
    """
    # 1. series row
    series_id = upsert_series(cur, {
        **meta,
        "total_seasons" : 1,
        "total_episodes": 1,
        "first_aired"   : meta.get("year"),
    })

    # 2. single season row
    season_id = upsert_season(cur, series_id, {
        "season"        : 1,
        "name"          : "Movie",
        "air_date"      : meta.get("year"),
        "poster"        : meta.get("poster"),
        "episode_count" : 1,
    })

    # 3. single episode row (the movie itself)
    episode_id = upsert_episode(cur, series_id, season_id, 1, {
        "episode"    : 1,
        "title"      : meta.get("title"),
        "air_date"   : meta.get("year"),
        "rating"     : meta.get("rating"),
        "overview"   : meta.get("overview", ""),
        "still_image": meta.get("poster"),   # use poster as still
    })

    # 4. embed links
    upsert_embed_links_bulk(cur, episode_id, links)

    return series_id, season_id, episode_id


def load_json_to_db(filepath: str) -> None:
    """
    Read JSON file → detect movie or TV → insert correctly → commit.
    Handles both:
      - Movie JSON  (media_type: "movie")
      - TV JSON     (media_type: "tv", has seasons/episodes)
    """
    head(f"📂  Loading: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        err(f"File not found: {filepath}")
        return
    except json.JSONDecodeError as e:
        err(f"Invalid JSON: {e}")
        return

    media_type = data.get("media_type", "tv")   # default tv for backward compat
    meta       = data.get("metadata", {})

    print(f"  Title      : {C.BOLD}{meta.get('title','?')}{C.RESET}")
    print(f"  Media type : {media_type.upper()}")

    head("🔌  Connecting ...")
    conn = get_connection()
    ok("Connected to Supabase")

    head("💾  Inserting ...")
    try:
        with conn.cursor() as cur:

            # ── MOVIE path — stored in series/seasons/episodes tables ──────
            if media_type == "movie":
                links = data.get("embed_links", [])
                series_id, season_id, episode_id = insert_movie_as_series(cur, meta, links)
                conn.commit()
                print(f"\n  {'─'*50}")
                ok("Done!")
                print(f"  Stored as  : series (id={series_id}) → season → episode")
                print(f"  Links      : {len(links)} embed providers stored")
                print(f"  {C.DIM}Movies use season=1, episode=1 convention{C.RESET}")
                print(f"  {'─'*50}")

            # ── TV / SERIES path ──────────────────────────────────────────────
            else:
                seasons = data.get("seasons", [])
                total_eps   = sum(len(s.get("episodes", [])) for s in seasons)
                total_links = sum(
                    len(ep.get("embed_links", []))
                    for s in seasons for ep in s.get("episodes", [])
                )
                print(f"  Seasons  : {len(seasons)}")
                print(f"  Episodes : {total_eps}")
                print(f"  Links    : {total_links}")

                series_id = upsert_series(cur, meta)
                ok(f"Series  →  id={series_id}  ({meta.get('title')})")

                ep_total  = 0
                lnk_total = 0

                for season in seasons:
                    s_num     = season["season"]
                    season_id = upsert_season(cur, series_id, season)
                    episodes  = season.get("episodes", [])

                    for ep in episodes:
                        ep_id  = upsert_episode(cur, series_id, season_id, s_num, ep)
                        n_lnk  = upsert_embed_links_bulk(cur, ep_id, ep.get("embed_links", []))
                        ep_total  += 1
                        lnk_total += n_lnk

                    info(f"S{s_num:02}  {season.get('name',''):<30}  {len(episodes)} eps")

                conn.commit()
                print(f"\n  {'─'*50}")
                ok("Done!  All data committed.")
                print(f"  Series   : 1 upserted")
                print(f"  Seasons  : {len(seasons)} upserted")
                print(f"  Episodes : {ep_total} upserted")
                print(f"  Links    : {lnk_total} upserted")
                print(f"  {C.DIM}Safe to re-run — uses ON CONFLICT DO UPDATE{C.RESET}")
                print(f"  {'─'*50}")

    except Exception as e:
        conn.rollback()
        err("Insert failed — rolled back.")
        err(str(e))
        import traceback; traceback.print_exc()
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  Interactive file picker
# ══════════════════════════════════════════════════════════════════════════════

def pick_json_file() -> str | None:
    # Collect ALL json files produced by any part of the toolkit:
    #   *_full_index.json  — series indexer (option 2)
    #   *_index.json       — scraper option 1 (movies + single episodes)
    #   *_results.json     — legacy name
    seen  = set()
    files = []
    for pattern in ("*_full_index.json", "*_index.json", "*_results.json"):
        for f in sorted(glob.glob(pattern)):
            if f not in seen:
                seen.add(f)
                files.append(f)

    if not files:
        err("No JSON index files found in current directory.")
        print("  Generate one first:")
        print("    Option 1 (movie/episode) → saves  <Title>_index.json")
        print("    Option 2 (full series)   → saves  <Title>_full_index.json")
        return None

    print(f"\n  {len(files)} file(s) found:\n")
    for i, f in enumerate(files, 1):
        size      = os.path.getsize(f) / 1024
        # Peek at media_type so user knows what each file is
        try:
            with open(f, "r", encoding="utf-8") as fh:
                peek = json.load(fh)
            mtype = peek.get("media_type", peek.get("metadata", {}).get("media_type", "?"))
            label = f"[{mtype.upper()}]" if mtype != "?" else ""
        except Exception:
            label = ""
        print(f"  {i:2}. {label:<8} {f:<50} {size:6.1f} KB")

    print()
    raw = input(f"  Pick (1–{len(files)}), Enter = #1: ").strip()
    idx = (int(raw) - 1) if raw.isdigit() and 1 <= int(raw) <= len(files) else 0
    return files[idx]


# ══════════════════════════════════════════════════════════════════════════════
#  Entry
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"{C.BOLD}{C.MAG}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   💾  Supabase Inserter  —  JSON → PostgreSQL            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(C.RESET)

    filepath = sys.argv[1] if len(sys.argv) > 1 else pick_json_file()
    if not filepath:
        sys.exit(1)

    load_json_to_db(filepath)

    while True:
        again = input("\n  Insert another file? (y/n): ").strip().lower()
        if again != "y":
            break
        filepath = pick_json_file()
        if filepath:
            load_json_to_db(filepath)

    print(f"\n{C.GREEN}👋  Done!{C.RESET}\n")


if __name__ == "__main__":
    main()
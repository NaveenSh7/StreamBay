"""
main.py
═══════
Entry point. Choose between:
  [1] Quick search  — find a movie/episode and get embed links
  [2] Series Indexer — full JSON of ALL seasons & episodes
  [3] DB Insert     — load a JSON index file into Supabase
"""

import os
import sys

# ─── Paste your TMDB API key here once ───────────────────────────────────────
# ← PASTE YOUR KEY HERE — this is the only place you need to set it
os.environ["TMDB_KEY"] = "YOUR_TMDB_API_KEY_HERE"

# ─── Colours ──────────────────────────────────────────────────────────────────
BOLD  = "\033[1m";  RESET = "\033[0m"
MAG   = "\033[95m"; GREEN = "\033[92m"
DIM   = "\033[2m";  RED   = "\033[91m"


def _load_indexer():
    """
    Import the series indexer regardless of what the file is named.
    Tries: indexing.py -> series_indexer.py
    Looks for the function: build_series_index
    """
    for module_name in ("indexing", "series_indexer"):
        try:
            mod = __import__(module_name)
            if hasattr(mod, "build_series_index"):
                return mod.build_series_index
            else:
                fns = [x for x in dir(mod) if not x.startswith("_") and callable(getattr(mod, x))]
                print(f"\n  {RED}Found '{module_name}.py' but no 'build_series_index' function.{RESET}")
                print(f"  Functions available: {', '.join(fns)}")
                print(f"\n  Fix: add this one line at the bottom of {module_name}.py:")
                print(f"  {DIM}build_series_index = <your_main_function_name>{RESET}\n")
                return None
        except ImportError:
            continue

    print(f"\n  {RED}Could not find indexing.py or series_indexer.py.{RESET}")
    print(f"  Make sure one of those files is in: {os.getcwd()}\n")
    return None


def main():
    print(f"{BOLD}{MAG}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║   🎬  Movie & Series Toolkit                                     ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║   [1]  Quick Search    — movie / single episode embed links      ║")
    print("║   [2]  Series Indexer  — full JSON  (all seasons & episodes)     ║")
    print("║   [3]  DB Insert       — load JSON index into Supabase           ║")
    print("║   [q]  Quit                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(RESET)

    while True:
        choice = input(f"{BOLD}Choose (1 / 2 / 3 / q): {RESET}").strip().lower()

        if choice == "1":
            try:
                from scraper import main as scraper_main
                scraper_main()
            except ImportError:
                print(f"  {RED}scraper.py not found in {os.getcwd()}{RESET}")
            break

        elif choice == "2":
            build_series_index = _load_indexer()
            if not build_series_index:
                continue
            while True:
                build_series_index()
                if input("Index another? (y/n): ").strip().lower() != "y":
                    break
            break

        elif choice == "3":
            try:
                from db_insert import main as db_main
                db_main()
            except ImportError:
                print(f"  {RED}db_insert.py not found in {os.getcwd()}{RESET}")
            break

        elif choice in ("q", "quit", "exit"):
            print("Goodbye!")
            break

        else:
            print(f"  {DIM}Enter 1, 2, 3, or q{RESET}")


if __name__ == "__main__":
    main()
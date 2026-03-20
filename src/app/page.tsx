"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { SeriesListItem } from "@/data/anime";

type SortKey = "alpha" | "popular" | "rating";
type CategoryKey = "series" | "movies" | "anime";

export default function Home() {
  const [sort, setSort] = useState<SortKey>("alpha");
  const [category, setCategory] = useState<CategoryKey>("series");
  const [items, setItems] = useState<SeriesListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [requestState, setRequestState] = useState<"idle" | "submitting" | "success" | "error">("idle");

  useEffect(() => {
    let cancelled = false;

    fetch(`/api/series?sort=${sort}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        setItems(Array.isArray(data?.items) ? (data.items as SeriesListItem[]) : []);
      })
      .catch(() => {
        if (cancelled) return;
        setItems([]);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [sort]);

  const sortLabel = useMemo(() => {
    if (sort === "alpha") return "Alphabetical";
    if (sort === "popular") return "Popular";
    return "Rating";
  }, [sort]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;

    return items.filter((s) => {
      const haystack = [
        s.title,
        s.overview,
        (s.genres ?? []).join(" "),
        s.year,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [items, query]);

  const categorize = useMemo(() => {
    const animeKeywords = ["anime", "animation", "japanese"];

    const isMovie = (s: SeriesListItem) => {
      const seasons = s.total_seasons ?? 0;
      const episodes = s.total_episodes ?? 0;
      // Heuristic: movies often have little/no season/episode indexing.
      return seasons <= 1 && episodes <= 1;
    };

    const isAnime = (s: SeriesListItem) => {
      const genres = (s.genres ?? []).map((g) => g.toLowerCase());
      return animeKeywords.some((k) => genres.some((g) => g.includes(k)));
    };

    const movies = filtered.filter((s) => isMovie(s));
    const anime = filtered.filter((s) => !isMovie(s) && isAnime(s));
    const series = filtered.filter((s) => !isMovie(s) && !isAnime(s));

    return { movies, anime, series };
  }, [filtered]);

  const activeCategory = useMemo(() => {
    if (category === "movies") {
      return { key: "movies" as const, title: "Movies", list: categorize.movies };
    }
    if (category === "anime") {
      return { key: "anime" as const, title: "Anime", list: categorize.anime };
    }
    return { key: "series" as const, title: "Series", list: categorize.series };
  }, [category, categorize]);

  const canRequest = query.trim().length > 0 && filtered.length === 0;

  async function handleRequestMissingTitle() {
    if (!canRequest || requestState === "submitting") return;

    setRequestState("submitting");
    try {
      const res = await fetch("/api/requests", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: query.trim() }),
      });

      if (!res.ok) throw new Error("Failed");
      setRequestState("success");
    } catch {
      setRequestState("error");
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-50">
      <header className="border-b border-zinc-800/80 bg-zinc-950/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:px-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded bg-gradient-to-br from-indigo-500 via-sky-500 to-cyan-400 shadow-lg shadow-indigo-500/40" />
            <div className="flex flex-col leading-tight">
              <span className="text-lg font-semibold tracking-tight">
                StreamBay
              </span>
              <span className="text-xs text-zinc-400">
                Watch TV Shows Online
              </span>
            </div>
          </Link>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-6 md:px-6 md:py-10">
        <section className="flex flex-col gap-6">
          <div className="relative overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-6 shadow-lg md:p-7">
            <div className="relative flex flex-col gap-4 md:gap-5">
              <p className="text-xs font-medium uppercase tracking-[0.3em] text-sky-400/80">
                StreamBay
              </p>
              <h2 className="text-3xl font-semibold tracking-tight md:text-4xl">
                Watch Series & Movies
                <span className="text-sky-400"> anytime, anywhere.</span>
              </h2>

              <div className="mt-2 flex flex-col gap-3">
                <div className="flex items-center gap-3 rounded-full border border-zinc-700/80 bg-zinc-900/80 px-4 py-2.5">
                  <span className="text-sm text-zinc-500">Search</span>
                  <input
                    type="text"
                    value={query}
                    placeholder="Search titles, genres, year..."
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setRequestState("idle");
                    }}
                    className="w-full bg-transparent text-sm outline-none placeholder:text-zinc-500"
                  />
                  {query ? (
                    <button
                      onClick={() => {
                        setQuery("");
                        setRequestState("idle");
                      }}
                      className="rounded-full bg-zinc-950 px-3 py-1 text-xs text-zinc-200 hover:bg-zinc-800"
                      aria-label="Clear search"
                    >
                      Clear
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3 rounded-2xl border border-zinc-800/80 bg-zinc-950/90 px-4 py-3">
            <div className="text-sm text-zinc-300">
              Sort: <span className="text-sky-300">{sortLabel}</span>
            </div>
            <select
              value={sort}
              onChange={(e) => {
                setLoading(true);
                setSort(e.target.value as SortKey);
              }}
              className="rounded-full border border-zinc-700 bg-zinc-900/40 px-3 py-2 text-sm text-zinc-200 outline-none"
            >
              <option value="alpha">Alphabetical (A-Z)</option>
              <option value="popular">Popular</option>
              <option value="rating">Rating</option>
            </select>
          </div>

          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold tracking-tight md:text-xl">
              Discover
            </h2>
            <span className="text-xs text-zinc-500">
              {loading ? "Loading..." : `Showing ${filtered.length} results`}
            </span>
          </div>

          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-2">
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { key: "series", title: "Series", count: categorize.series.length },
                  { key: "movies", title: "Movies", count: categorize.movies.length },
                  { key: "anime", title: "Anime", count: categorize.anime.length },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setCategory(tab.key)}
                  className={`rounded-xl border px-3 py-2 text-sm transition ${
                    category === tab.key
                      ? "border-sky-500 bg-sky-500/20 text-sky-200"
                      : "border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:border-sky-500/70"
                  }`}
                >
                  {tab.title} ({tab.count})
                </button>
              ))}
            </div>
          </div>

          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-md font-semibold tracking-tight text-zinc-50">
                {activeCategory.title}
              </h3>
              <span className="text-xs text-zinc-500">{activeCategory.list.length}</span>
            </div>

            {activeCategory.list.length ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {activeCategory.list.map((s) => (
                  <Link
                    key={s.tmdb_id}
                    href={`/anime/${s.tmdb_id}`}
                    className="group relative overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-3 shadow-sm transition duration-150 hover:-translate-y-0.5 hover:border-sky-500/70"
                  >
                    <div className="relative mb-3 h-52 overflow-hidden rounded-xl bg-zinc-900">
                      {s.poster ? (
                        <img
                          src={s.poster}
                          alt={s.title}
                          className="h-full w-full object-cover opacity-80 transition duration-300 group-hover:scale-[1.02]"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-zinc-900 text-sm text-zinc-500">
                          No poster
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/50 to-transparent" />
                      <div className="absolute bottom-2 left-2 flex flex-col gap-1 text-xs">
                        <span className="max-w-[85%] truncate rounded-full bg-black/60 px-2 py-0.5 text-[11px] font-medium text-zinc-50 backdrop-blur">
                          {(s.genres ?? []).slice(0, 3).join(" • ") || "Unknown genre"}
                        </span>
                        <span className="inline-flex items-center gap-1 rounded-full bg-black/60 px-2 py-0.5 text-[11px] text-zinc-300 backdrop-blur">
                          {(s.total_seasons ?? 0) as number} seasons • {(s.total_episodes ?? 0) as number} episodes
                        </span>
                      </div>
                      {s.rating != null ? (
                        <div className="absolute right-2 top-2 rounded-full bg-black/70 px-1.5 py-0.5 text-[11px] text-amber-300 backdrop-blur">
                          ★ {s.rating.toFixed(1)}
                        </div>
                      ) : null}
                    </div>

                    <div className="space-y-2">
                      <h3 className="line-clamp-2 text-lg font-semibold tracking-tight text-zinc-50 group-hover:text-sky-400">
                        {s.title}
                      </h3>
                      <p className="line-clamp-3 text-sm text-zinc-400">
                        {s.overview ?? "No overview available."}
                      </p>
                    </div>

                    <div className="mt-3 flex items-center justify-end text-[11px] text-zinc-400">
                      <span className="rounded-full bg-zinc-900/80 px-2 py-0.5 text-[11px] text-sky-300 group-hover:bg-sky-600/20 group-hover:text-sky-200">
                        ▶ Watch now
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/70 p-4 text-sm text-zinc-500">
                No {activeCategory.title.toLowerCase()} found.

                {canRequest ? (
                  <div className="mt-3 flex flex-col gap-2 justify-center items-center">
                    <button
                      onClick={handleRequestMissingTitle}
                      disabled={requestState === "submitting" || requestState === "success"}
                      className="w-fit rounded-full border border-sky-500 bg-sky-500/20 px-5 py-2 text-xl cursor-pointer text-sky-200 transition hover:bg-sky-500/30 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {requestState === "submitting"
                        ? "Requesting..."
                        : requestState === "success"
                          ? "Requested"
                          : "Request captain to add this"}
                    </button>

                    {requestState === "error" ? (
                      <p className="text-xs text-red-400">
                        Could not submit request. Please try again.
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            )}
          </section>
        </section>
      </main>

      <footer className="border-t border-zinc-900/80 bg-zinc-950/90">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-4 text-[11px] text-zinc-500 md:flex-row md:px-6">
          <p>© {new Date().getFullYear()} StreamBay. All rights reserved.</p>
          <p className="text-[10px] text-zinc-600">
            Data is fetched from your Supabase Postgres tables.
          </p>
        </div>
      </footer>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ShowPlayer from "@/components/show-player";
import type { ShowData } from "@/data/anime";

export default function AnimeDetailInner({ slug }: { slug: string }) {
  const [show, setShow] = useState<ShowData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetch(`/api/series/${slug}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        setShow(data as ShowData);
      })
      .catch(() => {
        if (cancelled) return;
        setShow(null);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-50">
        <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 md:px-6 md:py-8">
          <header className="flex items-center justify-between gap-3">
            <span className="rounded-full bg-zinc-900/80 px-2 py-1 text-[11px]">
              Loading...
            </span>
          </header>
          <section className="rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4 md:p-6">
            <div className="h-48 w-full animate-pulse rounded-xl bg-zinc-900/60" />
          </section>
        </div>
      </div>
    );
  }

  if (!show) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-50">
        <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 md:px-6 md:py-8">
          <header className="flex items-center justify-between gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-xs text-zinc-400 hover:text-sky-400"
            >
              <span className="rounded-full bg-zinc-900/80 px-2 py-1 text-[11px]">
                ← Back to home
              </span>
            </Link>
          </header>
          <section className="rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4 md:p-6">
            <h1 className="text-xl font-semibold">Series not found</h1>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-50">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 md:px-6 md:py-8">
        <header className="flex items-center justify-between gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs text-zinc-400 hover:text-sky-400"
          >
            <span className="rounded-full bg-zinc-900/80 px-2 py-1 text-[11px]">
              ← Back to home
            </span>
          </Link>
          <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-[11px] font-medium text-emerald-400">
            {show.metadata.status ?? "Series"} •{" "}
            {(show.metadata.total_seasons ?? show.seasons.length) as number}{" "}
            seasons
          </span>
        </header>

        <section className="flex flex-col gap-4 rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4 md:p-6">
          <div className="flex flex-col gap-4 md:flex-row">
            {show.metadata.poster ? (
              <img
                src={show.metadata.poster}
                alt={show.metadata.title}
                className="h-56 w-40 rounded-xl object-cover"
              />
            ) : (
              <div className="flex h-56 w-full items-center justify-center rounded-xl bg-zinc-900/60 text-sm text-zinc-500 md:w-40">
                No poster
              </div>
            )}
            <div className="flex flex-1 flex-col gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">
                {show.metadata.title}
              </h1>
              <p className="text-sm text-zinc-300">
                {show.metadata.overview ?? "No overview available."}
              </p>
              <div className="flex flex-wrap gap-2 text-xs text-zinc-300">
                {show.metadata.genres.map((genre) => (
                  <span
                    key={genre}
                    className="rounded-full border border-zinc-700 bg-zinc-900/60 px-2 py-1"
                  >
                    {genre}
                  </span>
                ))}
              </div>
              <div className="mt-1 text-xs text-zinc-500">
                {show.metadata.rating != null
                  ? `Rating: ${show.metadata.rating.toFixed(1)} / 10 • `
                  : ""}
                Episodes:{" "}
                {show.metadata.total_episodes ??
                  show.seasons.reduce(
                    (acc, s) => acc + s.episodes.length,
                    0,
                  )}
              </div>
            </div>
          </div>
        </section>

        <ShowPlayer show={show} />
      </div>
    </div>
  );
}


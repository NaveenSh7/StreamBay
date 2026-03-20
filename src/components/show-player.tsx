"use client";

import { useMemo, useState } from "react";
import type { ShowData } from "@/data/anime";

type ShowPlayerProps = {
  show: ShowData;
};

export default function ShowPlayer({ show }: ShowPlayerProps) {
  const pickDefaultProvider = (embedLinks: ShowData["seasons"][number]["episodes"][number]["embed_links"]) => {
    return embedLinks.find((l) => l.provider === "Videasy")?.provider ?? embedLinks[0]?.provider ?? "";
  };

  const playableSeasons = useMemo(
    () => show.seasons.filter((season) => season.episodes.length > 0),
    [show.seasons],
  );
  const [selectedSeason, setSelectedSeason] = useState<number | undefined>(
    playableSeasons[0]?.season,
  );
  const selectedSeasonData = useMemo(
    () =>
      playableSeasons.find((season) => season.season === selectedSeason) ??
      playableSeasons[0],
    [playableSeasons, selectedSeason],
  );

  const [selectedEpisode, setSelectedEpisode] = useState(
    selectedSeasonData?.episodes[0]?.episode ?? 1,
  );

  const selectedEpisodeData = useMemo(
    () =>
      selectedSeasonData?.episodes.find(
        (episode) => episode.episode === selectedEpisode,
      ) ?? selectedSeasonData?.episodes[0],
    [selectedEpisode, selectedSeasonData],
  );

  const [selectedProvider, setSelectedProvider] = useState(
    selectedEpisodeData?.embed_links
      ? pickDefaultProvider(selectedEpisodeData.embed_links)
      : "",
  );

  const providerUrl = useMemo(() => {
    if (!selectedEpisodeData) return "";
    const selected = selectedEpisodeData.embed_links.find(
      (link) => link.provider === selectedProvider,
    );
    return selected?.url ?? selectedEpisodeData.embed_links[0]?.url ?? "";
  }, [selectedEpisodeData, selectedProvider]);

  if (playableSeasons.length === 0) {
    return (
      <main className="grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <section className="flex flex-col gap-2 rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4 md:p-6">
          <h2 className="text-lg font-semibold tracking-tight">
            No episodes available
          </h2>
          <p className="text-sm text-zinc-400">
            This series exists in the database, but has no indexed episodes yet.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <section className="flex flex-col gap-4 rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4 md:p-6">
        <h2 className="text-lg font-semibold tracking-tight">
          Season {selectedSeasonData?.season} • Episode {selectedEpisodeData?.episode}
        </h2>
        <p className="text-sm text-zinc-300">
          {selectedEpisodeData?.title ?? "Untitled Episode"}
        </p>
        <div className="text-xs text-zinc-500">
          {selectedEpisodeData?.air_date ? `Aired: ${selectedEpisodeData.air_date}` : null}
          {selectedEpisodeData?.rating != null ? (
            <span>{selectedEpisodeData?.air_date ? " • " : null}Rating: {selectedEpisodeData.rating.toFixed(1)}</span>
          ) : null}
        </div>

        <div className="overflow-hidden rounded-xl border border-zinc-800 bg-black">
          {providerUrl ? (
            <iframe
              key={providerUrl}
              src={providerUrl}
              title={`${show.metadata.title} player`}
              allowFullScreen
              className="aspect-video w-full"
            />
          ) : (
            <div className="flex aspect-video items-center justify-center text-sm text-zinc-500">
              No playable source available.
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {selectedEpisodeData?.embed_links.map((provider) => (
            <button
              key={provider.provider}
              onClick={() => setSelectedProvider(provider.provider)}
              className={`rounded-full border px-3 py-1 text-xs transition ${
                selectedProvider === provider.provider
                  ? "border-sky-500 bg-sky-500/20 text-sky-200"
                  : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-sky-500"
              }`}
            >
              {provider.provider}
            </button>
          ))}
        </div>
      </section>

      <aside className="flex flex-col gap-4 rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4 md:p-5">
        <h2 className="text-sm font-semibold tracking-tight">Seasons & Episodes</h2>

        <div className="space-y-2">
          <p className="text-[11px] uppercase tracking-[0.15em] text-zinc-500">
            Seasons
          </p>
          <div className="flex flex-wrap gap-2">
            {playableSeasons.map((season) => (
              <button
                key={season.season}
                onClick={() => {
                  setSelectedSeason(season.season);
                  setSelectedEpisode(season.episodes[0].episode);
                  setSelectedProvider(
                    pickDefaultProvider(season.episodes[0].embed_links),
                  );
                }}
                className={`rounded-full border px-3 py-1 text-xs transition ${
                  selectedSeasonData?.season === season.season
                    ? "border-sky-500 bg-sky-500/20 text-sky-200"
                    : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-sky-500"
                }`}
              >
                S{season.season}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-[11px] uppercase tracking-[0.15em] text-zinc-500">
            Episodes
          </p>
          <div className="max-h-[60vh] space-y-1 overflow-y-auto pr-1">
            {selectedSeasonData?.episodes.map((episode) => (
              <button
                key={episode.episode}
                onClick={() => {
                  setSelectedEpisode(episode.episode);
                  setSelectedProvider(pickDefaultProvider(episode.embed_links));
                }}
                className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-xs transition ${
                  selectedEpisodeData?.episode === episode.episode
                    ? "border-sky-500 bg-sky-500/10 text-sky-200"
                    : "border-zinc-800 bg-zinc-900/50 text-zinc-300 hover:border-sky-500/70"
                }`}
              >
                <span className="truncate">
                  Ep {episode.episode}: {episode.title ?? "Untitled Episode"}
                </span>
                <span className="text-[10px]">▶</span>
              </button>
            ))}
          </div>
        </div>
      </aside>
    </main>
  );
}

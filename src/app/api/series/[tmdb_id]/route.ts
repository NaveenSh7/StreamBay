import { NextResponse } from "next/server";
import { getPgPool } from "@/lib/db";
import type { EmbedLink, Episode, Season, ShowData, ShowMetadata } from "@/data/anime";

function parseGenres(genres: unknown): string[] {
  if (!genres) return [];
  if (Array.isArray(genres)) return genres.filter(Boolean) as string[];
  if (typeof genres === "string") {
    try {
      const parsed = JSON.parse(genres);
      if (Array.isArray(parsed)) return parsed.filter(Boolean) as string[];
    } catch {
      // ignore
    }
  }
  return [];
}

function parseNullableNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "number") return value;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function parseNullableString(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  const s = String(value);
  return s.length ? s : null;
}

export async function GET(
  req: Request,
  {
    params,
  }: {
    params: Promise<{
      tmdb_id: string;
    }>;
  },
) {
  const resolvedParams = await params;
  const tmdbIdNum = Number(resolvedParams.tmdb_id);
  if (!Number.isFinite(tmdbIdNum)) {
    return NextResponse.json({ error: "Invalid tmdb_id" }, { status: 400 });
  }

  const pool = getPgPool();

  const seriesRes = await pool.query(
    `
    SELECT
      id,
      tmdb_id,
      title,
      overview,
      poster,
      year,
      rating,
      status,
      genres,
      total_seasons,
      total_episodes
    FROM series
    WHERE tmdb_id = $1
    LIMIT 1
  `,
    [tmdbIdNum],
  );

  const seriesRow = seriesRes.rows[0];
  if (!seriesRow) {
    return NextResponse.json({ error: "Series not found" }, { status: 404 });
  }

  const seriesId = Number(seriesRow.id);

  const seasonsRes = await pool.query(
    `
    SELECT
      season_number,
      name,
      air_date,
      poster,
      episode_count
    FROM seasons
    WHERE series_id = $1
    ORDER BY season_number ASC
  `,
    [seriesId],
  );

  const episodesRes = await pool.query(
    `
    SELECT
      id,
      season_id,
      season_number,
      episode_number,
      title,
      air_date,
      still_image,
      rating
    FROM episodes
    WHERE series_id = $1
    ORDER BY season_number ASC, episode_number ASC
  `,
    [seriesId],
  );

  const episodeIds = episodesRes.rows
    .map((r: Record<string, unknown>) => Number(r.id))
    .filter(Boolean);

  const embedLinksRes =
    episodeIds.length > 0
      ? await pool.query(
          `
          SELECT
            episode_id,
            provider,
            url
          FROM embed_links
          WHERE episode_id = ANY($1::bigint[])
          ORDER BY provider ASC
        `,
          [episodeIds],
        )
      : { rows: [] as Array<{ episode_id: number; provider: string; url: string }> };

  const embedsByEpisode = new Map<number, EmbedLink[]>();
  for (const row of embedLinksRes.rows) {
    const episodeId = Number(row.episode_id);
    if (!embedsByEpisode.has(episodeId)) embedsByEpisode.set(episodeId, []);
    embedsByEpisode.get(episodeId)!.push({
      provider: String(row.provider),
      url: String(row.url),
    });
  }

  const metadata: ShowMetadata = {
    tmdb_id: Number(seriesRow.tmdb_id),
    title: String(seriesRow.title),
    overview: parseNullableString(seriesRow.overview),
    poster: seriesRow.poster ?? null,
    year: parseNullableString(seriesRow.year),
    rating: parseNullableNumber(seriesRow.rating),
    status: parseNullableString(seriesRow.status),
    genres: parseGenres(seriesRow.genres),
    total_seasons: seriesRow.total_seasons ?? null,
    total_episodes: seriesRow.total_episodes ?? null,
  };

  const seasonByNumber = new Map<number, Season>();
  for (const s of seasonsRes.rows) {
    const seasonNum = Number(s.season_number);
    seasonByNumber.set(seasonNum, {
      season: seasonNum,
      name: s.name ?? null,
      air_date: s.air_date ?? null,
      poster: s.poster ?? null,
      episode_count: s.episode_count ?? null,
      episodes: [],
    });
  }

  for (const e of episodesRes.rows) {
    const seasonNum = Number(e.season_number);
    const episodeNum = Number(e.episode_number);
    const season = seasonByNumber.get(seasonNum);
    if (!season) continue;

    const episodeId = Number(e.id);
    const episode: Episode = {
      episode: episodeNum,
      title: e.title ?? null,
      air_date: e.air_date ?? null,
      rating: parseNullableNumber(e.rating),
      still_image: e.still_image ?? null,
      embed_links: embedsByEpisode.get(episodeId) ?? [],
    };

    season.episodes.push(episode);
  }

  const show: ShowData = {
    metadata,
    seasons: Array.from(seasonByNumber.values()).sort(
      (a, b) => a.season - b.season,
    ),
  };

  return NextResponse.json(show);
}


import { NextResponse } from "next/server";
import { getPgPool } from "@/lib/db";
import type { SeriesListItem } from "@/data/anime";

type SortKey = "alpha" | "popular" | "rating";

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

type SeriesRow = {
  tmdb_id: number | string;
  title: string;
  overview: string | null;
  poster: string | null;
  year: string | null;
  rating: number | string | null;
  status: string | null;
  genres: unknown;
  total_seasons: number | null;
  total_episodes: number | null;
};

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const sort = (searchParams.get("sort") ?? "alpha") as SortKey;

  const sortExpr =
    sort === "rating"
      ? "rating DESC NULLS LAST, title ASC"
      : sort === "popular"
        ? "total_episodes DESC NULLS LAST, rating DESC NULLS LAST, title ASC"
        : "title ASC";

  const pool = getPgPool();
  const result = await pool.query(
    `
    SELECT
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
    ORDER BY ${sortExpr}
  `,
  );

  const items: SeriesListItem[] = (result.rows as SeriesRow[]).map((row) => ({
    tmdb_id: Number(row.tmdb_id),
    title: String(row.title),
    overview: row.overview ?? null,
    poster: row.poster ?? null,
    year: row.year ?? null,
    rating: parseNullableNumber(row.rating),
    status: row.status ?? null,
    genres: parseGenres(row.genres),
    total_seasons: row.total_seasons ?? null,
    total_episodes: row.total_episodes ?? null,
  }));

  return NextResponse.json({ items });
}


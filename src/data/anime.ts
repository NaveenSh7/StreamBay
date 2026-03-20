export type EmbedLink = {
  provider: string;
  url: string;
};

export type Episode = {
  episode: number;
  title: string | null;
  air_date: string | null;
  rating: number | null;
  still_image: string | null;
  embed_links: EmbedLink[];
};

export type Season = {
  season: number;
  name: string | null;
  air_date: string | null;
  poster: string | null;
  episode_count: number | null;
  episodes: Episode[];
};

export type ShowMetadata = {
  tmdb_id: number;
  title: string;
  overview: string | null;
  year: string | null;
  status: string | null;
  rating: number | null;
  genres: string[];
  poster: string | null;
  total_seasons: number | null;
  total_episodes: number | null;
};

export type ShowData = {
  metadata: ShowMetadata;
  seasons: Season[];
};

export type SeriesListItem = {
  tmdb_id: number;
  title: string;
  overview: string | null;
  poster: string | null;
  year: string | null;
  rating: number | null;
  status: string | null;
  genres: string[];
  total_seasons: number | null;
  total_episodes: number | null;
};


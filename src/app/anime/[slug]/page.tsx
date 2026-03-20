import AnimeDetailInner from "./AnimeDetailInner";

type PageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function AnimeDetailPage({ params }: PageProps) {
  const { slug } = await params;
  return <AnimeDetailInner key={slug} slug={slug} />;
}


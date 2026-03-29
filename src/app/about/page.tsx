"use client";

import Link from "next/link";

export default function About() {
  return (
    <div className="min-h-screen bg-linear-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-50">
      {/* Header/Navbar */}
      <header className="border-b border-zinc-800/80 bg-zinc-950/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:px-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded bg-linear-to-br from-indigo-500 via-sky-500 to-cyan-400 shadow-lg shadow-indigo-500/40" />
            <div className="flex flex-col leading-tight">
              <span className="text-lg font-semibold tracking-tight">
                StreamBay
              </span>
              <span className="text-xs text-zinc-400">
                Watch TV Shows Online
              </span>
            </div>
          </Link>
          <Link 
            href="/about" 
            className="rounded-lg border border-sky-500/50 bg-sky-950/20 px-3 py-2 text-sm font-medium text-sky-300 transition hover:bg-sky-950/40 hover:border-sky-500/70"
          >
            About
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-6 md:px-6 md:py-10">
        {/* Developer Section */}
        <section className="flex flex-col gap-6">
          <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-6 backdrop-blur md:p-8">
            {/* Developed By Header */}
            <div className="mb-8 text-center">
              <p className="mb-2 text-xs font-medium uppercase tracking-[0.3em] text-sky-400/80">
                But you have heard of me
              </p>
              <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
                Developed by <span className="text-sky-300">Captain Jack Sparrow</span>
              </h2>
            </div>

            {/* Main Content - Image and Info */}
            <div className="flex flex-col items-center gap-8">
              {/* Jack Sparrow Image */}
              <div className="relative">
                <div className="pointer-events-none absolute -inset-3 rounded-full bg-sky-500/15 blur-xl" />
                <div className="relative h-64 w-64 overflow-hidden rounded-full border-2 border-sky-400/70 shadow-[0_0_40px_rgba(56,189,248,0.35)]">
                  <img
                    src="https://static0.colliderimages.com/wordpress/wp-content/uploads/2024/05/johnny-depp-as-jack-sparrow-and-orlando-bloom-as-will-turner-in-the-curse-of-the-black-pearl.jpg?q=49&fit=crop&w=825&dpr=2"
                    alt="Captain Jack Sparrow"
                    className="h-full w-full object-cover object-center"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent" />
                </div>
              </div>

              {/* Info Section */}
              <div className="w-full max-w-2xl space-y-6">
                {/* Quote */}
                <div className="rounded-xl border border-sky-500/30 bg-sky-950/20 p-4 backdrop-blur">
                  <p className="text-sm leading-relaxed italic text-sky-100">
                    "One word love: curiosity. You long for freedom. You long to do what you want to do because you want it. To act on selfish impulse. You want to see what it's like. One day you won't be able to resist."
                  </p>
                  <p className="mt-3 text-right text-xs font-semibold text-sky-300">
                    — Captain Jack Sparrow
                  </p>
                </div>

                {/* GitHub Link */}
                <a
                  href="https://github.com/NaveenSh7"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-3 rounded-xl border border-zinc-700/80 bg-zinc-900/70 px-5 py-3 transition hover:border-sky-500/70 hover:bg-zinc-900/90 hover:shadow-lg hover:shadow-sky-500/20"
                >
                  <div className="rounded-md bg-white/95 px-2 py-1">
                    <img
                      src="data:image/png;base64,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"
                      alt="GitHub"
                      referrerPolicy="no-referrer"
                      className="h-8 w-8"
                    />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-semibold text-zinc-100">GitHub</span>
                
                  </div>
                </a>

                {/* Disclaimer */}
                <div className="rounded-xl border border-sky-500/30 bg-sky-950/20 p-4 backdrop-blur">
                  <p className="text-xs leading-relaxed text-sky-100">
                    <span className="font-semibold text-sky-300">⚠️ Educational Purpose:</span> This project is for <span className="font-semibold">fun and educational purposes only</span>. We do not host pirated content, and we do not promote piracy in any manner. All content is sourced from legitimate providers already available on the internet.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-900/80 bg-zinc-950/90">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-4 text-[11px] text-zinc-500 md:px-6">
          <p>© {new Date().getFullYear()} StreamBay. All rights reserved.</p>
          <Link href="/admin" className="text-[11px] text-sky-400 hover:text-sky-300">
            Admin panel
          </Link>
          <p className="text-[10px] text-zinc-600">
            Data is fetched from your Supabase Postgres tables.
          </p>
        </div>
      </footer>
    </div>
  );
}

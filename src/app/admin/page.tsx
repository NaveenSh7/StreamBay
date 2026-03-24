"use client";

import { useState } from "react";

type RequestItem = {
  id: number;
  requestedItem: string;
  requesterName: string;
  createdAt: string;
};

export default function AdminRequestsPage() {
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "unauthorized" | "error" | "success">("idle");
  const [items, setItems] = useState<RequestItem[]>([]);

  async function handleOpenPanel() {
    if (!password.trim() || status === "loading") return;

    setStatus("loading");
    try {
      const res = await fetch("/api/requests", {
        method: "GET",
        headers: {
          "x-admin-password": password.trim(),
        },
      });

      if (res.status === 401) {
        setStatus("unauthorized");
        return;
      }

      if (!res.ok) {
        setStatus("error");
        return;
      }

      const data = (await res.json()) as { items?: RequestItem[] };
      setItems(Array.isArray(data.items) ? data.items : []);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="min-h-screen bg-linear-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-50">
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-4 px-4 py-8 md:px-6 md:py-10">
        <h1 className="text-2xl font-semibold tracking-tight">Admin Panel</h1>
        <p className="text-sm text-zinc-400">
          Enter admin password to view user requests.
        </p>

        <div className="flex flex-col gap-2 rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Admin password"
            className="w-full rounded-xl border border-zinc-700 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
          />
          <button
            onClick={handleOpenPanel}
            disabled={status === "loading" || !password.trim()}
            className="w-fit rounded-full border border-sky-500 bg-sky-500/20 px-4 py-2 text-sm text-sky-200 transition hover:bg-sky-500/30 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {status === "loading" ? "Opening..." : "Open admin panel"}
          </button>

          {status === "unauthorized" ? (
            <p className="text-xs text-red-400">Wrong password.</p>
          ) : null}
          {status === "error" ? (
            <p className="text-xs text-red-400">Could not load requests.</p>
          ) : null}
        </div>

        {status === "success" ? (
          <section className="rounded-2xl border border-zinc-800/80 bg-zinc-950/90 p-4">
            <h2 className="mb-3 text-lg font-semibold">Requested Additions</h2>

            {items.length === 0 ? (
              <p className="text-sm text-zinc-500">No requests yet.</p>
            ) : (
              <div className="space-y-2">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3"
                  >
                    <p className="text-sm text-zinc-200">
                      <span className="font-medium text-sky-300">Want to add:</span>{" "}
                      {item.requestedItem}
                    </p>
                    <p className="text-sm text-zinc-300">
                      <span className="font-medium text-zinc-100">Name:</span>{" "}
                      {item.requesterName}
                    </p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {new Date(item.createdAt).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>
        ) : null}
      </main>
    </div>
  );
}

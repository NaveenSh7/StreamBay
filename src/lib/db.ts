import fs from "node:fs";
import path from "node:path";
import { Pool } from "pg";

let cachedPool: Pool | null = null;

function loadEnvVar(key: string): string | undefined {
  // Prefer real environment variables (recommended for production).
  if (process.env[key]) return process.env[key];

  // Local dev convenience: fall back to scripts/.env if Next env isn't set.
  try {
    const envPath = path.join(process.cwd(), "scripts", ".env");
    if (!fs.existsSync(envPath)) return undefined;
    const contents = fs.readFileSync(envPath, "utf8");
    for (const line of contents.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const idx = trimmed.indexOf("=");
      if (idx === -1) continue;
      const envKey = trimmed.slice(0, idx).trim();
      const envVal = trimmed.slice(idx + 1).trim();
      if (envKey === key) return envVal;
    }
  } catch {
    // Ignore and return undefined.
  }

  return undefined;
}

export function getPgPool(): Pool {
  if (cachedPool) return cachedPool;

  const connectionString =
    loadEnvVar("SUPABASE_DB_URL") || loadEnvVar("DATABASE_URL");

  if (!connectionString) {
    throw new Error(
      "Missing database connection string. Set SUPABASE_DB_URL (recommended) in your Next env.",
    );
  }

  cachedPool = new Pool({
    connectionString,
    ssl: false, // Supabase pooler connection string may already handle SSL requirements.
  });

  return cachedPool;
}


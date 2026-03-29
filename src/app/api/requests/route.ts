import { NextResponse } from "next/server";
import { getPgPool } from "@/lib/db";

type RequestBody = {
  requestedItem?: unknown;
  requesterName?: unknown;
};

function normalizeText(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.trim();
}

async function ensureRequestsSchema() {
  const pool = getPgPool();

  await pool.query(`
    CREATE TABLE IF NOT EXISTS requests (
      id BIGSERIAL PRIMARY KEY,
      requested_item TEXT,
      requester_name TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);

  await pool.query(`
    ALTER TABLE requests
    ADD COLUMN IF NOT EXISTS requested_item TEXT,
    ADD COLUMN IF NOT EXISTS requester_name TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()
  `);
}

function getAdminPassword(req: Request): string {
  const headerPassword = req.headers.get("x-admin-password") ?? "";
  if (headerPassword.trim()) return headerPassword.trim();

  const authHeader = req.headers.get("authorization") ?? "";
  if (authHeader.startsWith("Bearer ")) {
    return authHeader.slice("Bearer ".length).trim();
  }

  return "";
}

function escapeDiscordMarkdown(value: string): string {
  return value.replace(/[\\*_`~|>]/g, "\\$&");
}

async function sendRequestNotificationDiscordWebhook(
  requestedItem: string,
  requesterName: string,
) {
  const webhookUrl = process.env.REQUEST_NOTIFY_DISCORD_WEBHOOK_URL?.trim() ?? "";

  if (!webhookUrl) return;

  const safeRequestedItem = escapeDiscordMarkdown(requestedItem);
  const safeRequesterName = escapeDiscordMarkdown(requesterName);

  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      content: [
        "**New StreamBay Request**",
        `Requested item: **${safeRequestedItem}**`,
        `Requester name: **${safeRequesterName}**`,
      ].join("\n"),
    }),
  });

  if (!response.ok) {
    throw new Error(`Discord webhook failed with status ${response.status}`);
  }
}

export async function GET(req: Request) {
  const configuredPassword = process.env.ADMIN_PANEL_PASSWORD?.trim() ?? "";

  if (!configuredPassword) {
    return NextResponse.json(
      { error: "ADMIN_PANEL_PASSWORD is not configured" },
      { status: 500 },
    );
  }

  const providedPassword = getAdminPassword(req);
  if (!providedPassword || providedPassword !== configuredPassword) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  await ensureRequestsSchema();

  const pool = getPgPool();
  const result = await pool.query<{
    id: number;
    requested_item: string | null;
    requester_name: string | null;
    created_at: string;
  }>(
    `
      SELECT id, requested_item, requester_name, created_at
      FROM requests
      ORDER BY created_at DESC
      LIMIT 500
    `,
  );

  return NextResponse.json({
    items: result.rows.map((row) => ({
      id: row.id,
      requestedItem: row.requested_item ?? "",
      requesterName: row.requester_name ?? "",
      createdAt: row.created_at,
    })),
  });
}

export async function POST(req: Request) {
  let payload: RequestBody;

  try {
    payload = (await req.json()) as RequestBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const requestedItem = normalizeText(payload.requestedItem);
  const requesterName = normalizeText(payload.requesterName);

  if (!requestedItem) {
    return NextResponse.json(
      { error: "Requested item is required" },
      { status: 400 },
    );
  }

  if (!requesterName) {
    return NextResponse.json({ error: "Your name is required" }, { status: 400 });
  }

  if (requestedItem.length > 255) {
    return NextResponse.json(
      { error: "Requested item is too long" },
      { status: 400 },
    );
  }

  if (requesterName.length > 255) {
    return NextResponse.json({ error: "Name is too long" }, { status: 400 });
  }

  await ensureRequestsSchema();

  const pool = getPgPool();

  await pool.query(
    `
      INSERT INTO requests (requested_item, requester_name)
      VALUES ($1, $2)
    `,
    [requestedItem, requesterName],
  );

  try {
    await sendRequestNotificationDiscordWebhook(requestedItem, requesterName);
  } catch (error) {
    console.error("Request notification Discord webhook failed", error);
  }

  return NextResponse.json({ ok: true });
}

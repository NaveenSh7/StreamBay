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

async function sendRequestNotificationEmail(
  requestedItem: string,
  requesterName: string,
) {
  const apiKey = process.env.RESEND_API_KEY?.trim() ?? "";
  const to = process.env.REQUEST_NOTIFY_TO_EMAIL?.trim() ?? "";

  if (!apiKey || !to) return;

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: "StreamBay <onboarding@resend.dev>",
      to: [to],
      subject: `New StreamBay request: ${requestedItem}`,
      html: `
        <div style="font-family: Arial, sans-serif; line-height: 1.5;">
          <h2>New StreamBay Request</h2>
          <p><strong>Requested item:</strong> ${requestedItem}</p>
          <p><strong>Requester name:</strong> ${requesterName}</p>
        </div>
      `,
      text: `A new content request was submitted.\n\nRequested item: ${requestedItem}\nRequester name: ${requesterName}`,
    }),
  });

  if (!response.ok) {
    throw new Error(`Resend API failed with status ${response.status}`);
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
    await sendRequestNotificationEmail(requestedItem, requesterName);
  } catch (error) {
    console.error("Request notification email failed", error);
  }

  return NextResponse.json({ ok: true });
}

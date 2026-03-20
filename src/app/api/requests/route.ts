import { NextResponse } from "next/server";
import { getPgPool } from "@/lib/db";

type RequestBody = {
  name?: unknown;
};

function normalizeName(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.trim();
}

export async function POST(req: Request) {
  let payload: RequestBody;

  try {
    payload = (await req.json()) as RequestBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const name = normalizeName(payload.name);
  if (!name) {
    return NextResponse.json({ error: "Name is required" }, { status: 400 });
  }

  if (name.length > 255) {
    return NextResponse.json({ error: "Name is too long" }, { status: 400 });
  }

  const pool = getPgPool();

  try {
    await pool.query(
      `
      INSERT INTO requests (name )
      VALUES ($1)
    `,
      [name],
    );
  } catch {
    await pool.query(
      `
      INSERT INTO requests (name)
      VALUES ($1)
    `,
      [name],
    );
  }

  return NextResponse.json({ ok: true });
}

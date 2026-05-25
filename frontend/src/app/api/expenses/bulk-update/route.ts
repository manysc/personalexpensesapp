import { NextRequest, NextResponse } from "next/server";

const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const res = await fetch(`${backendUrl()}/expenses/bulk-update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

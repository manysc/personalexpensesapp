import { NextResponse } from "next/server";

const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

export async function POST() {
  const res = await fetch(`${backendUrl()}/categories/seed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

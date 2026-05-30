import { NextRequest } from "next/server";

const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const res = await fetch(`${backendUrl()}/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return new Response(res.body, {
    status: res.status,
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}

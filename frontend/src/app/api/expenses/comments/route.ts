import { NextRequest, NextResponse } from "next/server";

const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const upstream = `${backendUrl()}/expenses/comments?${searchParams.toString()}`;

  const res = await fetch(upstream, { cache: "no-store" });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

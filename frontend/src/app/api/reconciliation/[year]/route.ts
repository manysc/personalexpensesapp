import { NextRequest, NextResponse } from "next/server";

const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

type Params = { params: Promise<{ year: string }> };

// GET only reports; POST also updates the dashboard's action items.
async function proxy(method: "GET" | "POST", request: NextRequest, { params }: Params) {
  const { year } = await params;
  const query = request.nextUrl.searchParams.toString();
  const res = await fetch(`${backendUrl()}/reconciliation/${year}${query ? `?${query}` : ""}`, {
    method,
    cache: "no-store",
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function GET(request: NextRequest, context: Params) {
  return proxy("GET", request, context);
}

export async function POST(request: NextRequest, context: Params) {
  return proxy("POST", request, context);
}

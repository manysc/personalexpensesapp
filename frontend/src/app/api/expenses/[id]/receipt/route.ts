import { NextRequest, NextResponse } from "next/server";

const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const inline = request.nextUrl.searchParams.get("inline") === "true";
  const res = await fetch(
    `${backendUrl()}/expenses/${id}/receipt?inline=${inline}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    return NextResponse.json(data, { status: res.status });
  }
  const contentType = res.headers.get("content-type") ?? "application/octet-stream";
  const contentDisposition = res.headers.get("content-disposition") ?? "";
  const body = await res.arrayBuffer();
  return new NextResponse(body, {
    status: 200,
    headers: {
      "Content-Type": contentType,
      "Content-Disposition": contentDisposition,
    },
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const formData = await request.formData();
  const res = await fetch(`${backendUrl()}/expenses/${id}/receipt`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const res = await fetch(`${backendUrl()}/expenses/${id}/receipt`, {
    method: "DELETE",
  });
  if (res.status === 204) {
    return new NextResponse(null, { status: 204 });
  }
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  return NextResponse.json(data, { status: res.status });
}

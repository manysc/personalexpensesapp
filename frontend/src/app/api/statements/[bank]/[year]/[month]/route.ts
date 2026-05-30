import { NextRequest, NextResponse } from "next/server";

const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ bank: string; year: string; month: string }> }
) {
  const { bank, year, month } = await params;
  const inline = request.nextUrl.searchParams.get("view") === "1";
  const res = await fetch(
    `${backendUrl()}/statements/${bank}/${year}/${month}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Not found" }));
    return NextResponse.json(data, { status: res.status });
  }
  const disposition = inline
    ? `inline; filename="${bank}-${month}-${year}.pdf"`
    : `attachment; filename="${bank}-${month}-${year}.pdf"`;
  return new Response(res.body, {
    status: res.status,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": disposition,
    },
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ bank: string; year: string; month: string }> }
) {
  const { bank, year, month } = await params;
  const formData = await request.formData();
  const res = await fetch(
    `${backendUrl()}/statements/${bank}/${year}/${month}`,
    { method: "POST", body: formData }
  );
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

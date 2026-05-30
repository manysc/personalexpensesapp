import { NextRequest } from "next/server";

const ollamaUrl = () => process.env.OLLAMA_BASE_URL ?? "http://localhost:11434";
const ollamaModel = () => process.env.OLLAMA_MODEL ?? "llama3.2";
const backendUrl = () => process.env.API_URL ?? "http://localhost:8000";

type SummaryRow = { month: string; category: string; total: number };
type ExpenseItem = {
  id: number;
  date: string;
  bank: string;
  description: string;
  debit: number | null;
  credit: number | null;
  category: string | null;
  comments: string | null;
};
type Category = { id: number; name: string };

async function buildContext(): Promise<string> {
  const base = backendUrl();
  const now = new Date();
  const sixMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 5, 1)
    .toISOString()
    .slice(0, 10);
  const today = now.toISOString().slice(0, 10);

  const [summaryRes, categoriesRes, recentRes] = await Promise.allSettled([
    fetch(`${base}/expenses/summary?date_from=${sixMonthsAgo}&date_to=${today}`, {
      cache: "no-store",
    }),
    fetch(`${base}/categories`, { cache: "no-store" }),
    fetch(`${base}/expenses?limit=25&date_from=${sixMonthsAgo}`, { cache: "no-store" }),
  ]);

  const parts: string[] = [];

  if (summaryRes.status === "fulfilled" && summaryRes.value.ok) {
    const rows: SummaryRow[] = await summaryRes.value.json();
    const byMonth = new Map<string, SummaryRow[]>();
    for (const row of rows) {
      if (!byMonth.has(row.month)) byMonth.set(row.month, []);
      byMonth.get(row.month)!.push(row);
    }
    const lines = ["## Monthly Spending (last 6 months)"];
    for (const [month, cats] of [...byMonth.entries()].sort()) {
      lines.push(`\n**${month}**`);
      for (const c of cats.sort((a, b) => b.total - a.total)) {
        const label = c.total >= 0 ? "expense" : "income";
        lines.push(`  ${c.category}: $${Math.abs(c.total).toFixed(2)} ${label}`);
      }
    }
    parts.push(lines.join("\n"));
  }

  if (categoriesRes.status === "fulfilled" && categoriesRes.value.ok) {
    const cats: Category[] = await categoriesRes.value.json();
    parts.push(`## Available Categories\n${cats.map((c) => c.name).join(", ")}`);
  }

  if (recentRes.status === "fulfilled" && recentRes.value.ok) {
    const payload = await recentRes.value.json();
    const items: ExpenseItem[] = payload.items ?? [];
    const lines = ["## Recent Transactions (last 25)"];
    for (const e of items) {
      const amount =
        e.debit != null
          ? `-$${Number(e.debit).toFixed(2)}`
          : e.credit != null
          ? `+$${Number(e.credit).toFixed(2)}`
          : "$0.00";
      const comment = e.comments ? ` [${e.comments}]` : "";
      lines.push(
        `  ${e.date} | ${e.bank} | ${e.description} | ${
          e.category ?? "uncategorized"
        } | ${amount}${comment}`
      );
    }
    parts.push(lines.join("\n"));
  }

  return parts.join("\n\n") || "No expense data available.";
}

interface ChatMessage {
  role: string;
  content: string;
}

function getSystemPrompt(context: string): string {
  const today = new Date().toISOString().slice(0, 10);
  return `You are a personal finance assistant. Today is ${today}.

Here is the user's current expense data:

${context}

Guidelines:
- Be concise and helpful.
- Format dollar amounts with $ and 2 decimal places.
- In the monthly summary, total = debit minus credit. Positive = net expense; negative = net income or refund.
- If asked about data outside the context above, say it is outside the current 6-month view.`;
}

export async function POST(request: NextRequest) {
  const { messages } = (await request.json()) as { messages: ChatMessage[] };

  const context = await buildContext();
  const systemPrompt = getSystemPrompt(context);
  const encoder = new TextEncoder();
  const model = ollamaModel();

  const responseStream = new ReadableStream({
    async start(controller) {
      try {
        const res = await fetch(`${ollamaUrl()}/v1/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model,
            messages: [{ role: "system", content: systemPrompt }, ...messages],
            stream: true,
          }),
        });

        if (!res.ok || !res.body) {
          const msg =
            res.status === 404
              ? `Model "${model}" not found. Pull it first: ollama pull ${model}`
              : "Could not connect to Ollama. Make sure it is running (ollama serve)."
          controller.enqueue(encoder.encode(msg));
          controller.close();
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = line.slice(6).trim();
            if (payload === "[DONE]") continue;
            try {
              const chunk = JSON.parse(payload);
              const text = chunk.choices?.[0]?.delta?.content;
              if (text) controller.enqueue(encoder.encode(text));
            } catch {
              // skip malformed SSE lines
            }
          }
        }
        controller.close();
      } catch {
        controller.enqueue(
          encoder.encode(
            "Error: Could not reach Ollama. Is `ollama serve` running on this machine?"
          )
        );
        controller.close();
      }
    },
  });

  return new Response(responseStream, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}

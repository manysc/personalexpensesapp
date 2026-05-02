import CategoryEditor from "@/components/CategoryEditor";
import CommentsEditor from "@/components/CommentsEditor";
import type { Expense } from "@/types/expense";
import Link from "next/link";
import { notFound } from "next/navigation";

async function getExpense(id: string): Promise<Expense> {
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const res = await fetch(`${apiUrl}/expenses/${id}`, { cache: "no-store" });
  if (res.status === 404) notFound();
  if (!res.ok)
    throw new Error(`Failed to fetch expense: ${res.statusText}`);
  return res.json() as Promise<Expense>;
}

interface PageProps {
  params: Promise<{ id: string }>;
}

function formatAmount(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export default async function ExpenseDetailPage({ params }: PageProps) {
  const { id } = await params;
  const expense = await getExpense(id);

  const staticFields = [
    { label: "Date", value: expense.date },
    { label: "Bank", value: expense.bank },
    { label: "Description", value: expense.description },
    { label: "Debit", value: formatAmount(expense.debit) },
    { label: "Credit", value: formatAmount(expense.credit) },
  ];

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 hover:underline"
        >
          ← Back to expenses
        </Link>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-xl font-semibold text-gray-900">
            Expense Details
          </h1>
          <p className="mt-1 text-sm text-gray-500">ID #{expense.id}</p>
        </div>

        <dl className="divide-y divide-gray-100">
          {staticFields.map(({ label, value }) => (
            <div key={label} className="px-6 py-4 grid grid-cols-3 gap-4">
              <dt className="text-sm font-medium text-gray-500">{label}</dt>
              <dd className="text-sm text-gray-900 col-span-2 break-words">
                {value}
              </dd>
            </div>
          ))}
          <div className="px-6 py-4 grid grid-cols-3 gap-4 items-center">
            <dt className="text-sm font-medium text-gray-500">Category</dt>
            <dd className="col-span-2">
              <CategoryEditor expense={expense} />
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4 items-start">
            <dt className="text-sm font-medium text-gray-500">Comments</dt>
            <dd className="col-span-2">
              <CommentsEditor expense={expense} />
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}


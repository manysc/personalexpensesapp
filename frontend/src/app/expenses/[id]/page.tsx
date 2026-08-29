import BackButton from "@/components/BackButton";
import ExpenseDetailCard from "@/components/ExpenseDetailCard";
import type { Expense } from "@/types/expense";
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

export default async function ExpenseDetailPage({ params }: PageProps) {
  const { id } = await params;
  const expense = await getExpense(id);

  const staticFields = [
    { label: "Date", value: expense.date },
    { label: "Bank", value: expense.bank },
    { label: "Description", value: expense.description },
  ];

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <BackButton />
      </div>
      <ExpenseDetailCard expense={expense} staticFields={staticFields} />
    </div>
  );
}


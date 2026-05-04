"use client";

import { useRouter } from "next/navigation";

export default function BackButton() {
  const router = useRouter();
  return (
    <button
      onClick={() => router.back()}
      className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 hover:underline"
    >
      ← Back to expenses
    </button>
  );
}

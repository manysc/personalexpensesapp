"use client";

interface Props {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const btnClass =
  "rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40 transition-colors";

export default function Pagination({ page, totalPages, onPageChange }: Props) {
  return (
    <div className="flex items-center justify-center gap-4">
      <button
        className={btnClass}
        onClick={() => onPageChange(page - 1)}
        disabled={page === 0}
      >
        ← Previous
      </button>
      <span className="text-sm text-gray-600">
        Page {page + 1} of {totalPages}
      </span>
      <button
        className={btnClass}
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages - 1}
      >
        Next →
      </button>
    </div>
  );
}

export interface Expense {
  id: number;
  date: string;
  bank: string;
  description: string;
  debit: number | null;
  credit: number | null;
  category: string | null;
  overridden: boolean;
  comments: string | null;
}

export interface ExpenseListResponse {
  total: number;
  limit: number;
  offset: number;
  items: Expense[];
}

export interface ExpenseFilters {
  bank: string;
  category: string;
  date_from: string;
  date_to: string;
}

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

export interface RentalProperty {
  id: number;
  alias: string;
  address: string;
  tenant: string | null;
  lease_renewal_date: string | null;
  payment_day: number | null;
}

export interface RentalPropertyRequest {
  alias: string;
  address: string;
  tenant: string | null;
  lease_renewal_date: string | null;
  payment_day: number | null;
}

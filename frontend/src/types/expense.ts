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
  property_id: number | null;
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
  description: string;
  comments: string;
  property_id: string;
  overridden_only: boolean;
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

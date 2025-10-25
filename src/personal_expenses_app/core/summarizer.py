class Summarizer:
    @staticmethod
    def summarize_by_category(expenses):
        # Group by category and sum both Debit and Credit columns
        summary = expenses.groupby("Category")[["Debit", "Credit"]].sum().reset_index()
        # Fill NaN values with 0 and calculate net amount (Debit - Credit)
        summary["Debit"] = summary["Debit"].fillna(0)
        summary["Credit"] = summary["Credit"].fillna(0)
        summary["Net"] = summary["Debit"] + summary["Credit"]
        # Sort by net amount descending
        summary = summary.sort_values(by="Net", ascending=False)
        return summary

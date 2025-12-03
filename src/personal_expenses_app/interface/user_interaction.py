class UserInteraction:
    def __init__(self):
        super().__init__()


    @staticmethod
    def ask_user_correction(row, pred_cat):
        print(f"\nExpense: {row['Description']} | Predicted Category (low acc): {pred_cat}")
        return input("Type correct category (or Enter to confirm): ").strip()


    @staticmethod
    def print_summary(summary):
        month = summary['Month'].iloc[0] if 'Month' in summary.columns else "Unknown"
        year = summary['Year'].iloc[0] if 'Year' in summary.columns else "Unknown"
        print(f"\n===== Expense Summary for {month}/{year} by Category =====")
        # don't print month/year columns
        summary = summary.drop(columns=['Month', 'Year'], errors='ignore')
        print(summary)
        print("")


    @staticmethod
    def print_total(summary):
        # drop Transfers if exists
        summary = summary[summary['Category'] != 'Transfers'] if 'Category' in summary.columns else summary
        total_debit = summary['Debit'].sum()
        total_credit = summary['Credit'].sum()
        net = total_credit - total_debit
        print(f"\n===== Total Summary =====")
        print(f"Total Debit: ${total_debit:,.2f}")
        print(f"Total Credit: ${total_credit:,.2f}")
        print(f"Net Amount (Credit - Debit): ${net:,.2f}\n")
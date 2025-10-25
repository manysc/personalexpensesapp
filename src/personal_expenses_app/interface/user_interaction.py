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
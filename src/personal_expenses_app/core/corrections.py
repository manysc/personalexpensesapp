import pandas as pd


class Corrections:
    def __init__(self):
        super().__init__()

    @staticmethod
    def apply_corrections(expenses, corrections_df, all_labeled_expenses):
        """
        Apply category corrections using substring matching or historical labels:
        1. If a substring in corrections exists, assign its category.
        2. Else, if a substring in all_labeled_expenses exists, assign its category.
        3. Else, keep the current category.
        """
        corrections_list = [
            (str(corr_desc).lower(), cat)
            for corr_desc, cat in zip(
                corrections_df["Description"], corrections_df["Category"]
            )
        ]
        labeled_list = [
            (str(desc).lower(), cat)
            for desc, cat in zip(
                all_labeled_expenses["Description"], all_labeled_expenses["Category"]
            )
        ]

        def find_correction(row):
            desc_lower = str(row["Description"]).lower()
            old_cat = row["Category"]
            # 1. Correction substring
            for corr_desc, cat in corrections_list:
                if corr_desc in desc_lower:
                    if old_cat != cat:
                        print(
                            f"File Correction: {row['Description']} | Old: {old_cat} -> New: {cat}"
                        )
                    return cat
            # 2. Historical label substring
            for labeled_desc, cat in labeled_list:
                if labeled_desc in desc_lower:
                    if old_cat != cat:
                        amount = (
                            row["Debit"] if pd.notnull(row["Debit"]) else row["Credit"]
                        )
                        print(
                            f"Labeled Correction: {row['Description']} | Amount: {amount} | Old: {old_cat} -> New: {cat}"
                        )
                    return cat
            # 3. No match; keep current
            return old_cat

        expenses["Category"] = expenses.apply(find_correction, axis=1)
        return expenses

    @staticmethod
    def collect_low_acc_corrections(
        expenses,
        corrections_df,
        cat_acc,
        all_labeled_expenses,
        user_prompt_fn,
        threshold=0.8,
    ):
        # Precompute corrections substrings
        corrections_list = [
            str(corr_desc).lower() for corr_desc in corrections_df["Description"]
        ]
        new_corrections = []

        # Build mapping for all_labeled_expenses for quick lookup: description -> category
        labeled_map = {
            str(desc).lower(): cat
            for desc, cat in zip(
                all_labeled_expenses["Description"], all_labeled_expenses["Category"]
            )
        }

        for idx, row in expenses.iterrows():
            desc = str(row["Description"]).lower()
            pred_cat = row["Category"]

            # 1. Check if any correction substring is in desc
            already_corrected = any(corr_desc in desc for corr_desc in corrections_list)
            if already_corrected:
                print(f"Skipping already corrected: {row['Description']}")
                continue  # Correction already exists

            # 2. Check if any substring in all_labeled_expenses['Description'] matches
            auto_category = None
            for labeled_desc, labeled_cat in labeled_map.items():
                if labeled_desc in desc:
                    auto_category = labeled_cat
                    break

            if auto_category:
                if pred_cat != auto_category:
                    print(
                        f"Auto Correction: {row['Description']} | Old: {pred_cat} -> New: {auto_category}"
                    )
                # Assign this auto-found category (no prompt)
                expenses.at[idx, "Category"] = auto_category
                continue

            # 3. If not, and category is low-accuracy, prompt user
            if cat_acc.get(pred_cat, 1) < threshold:
                user_input = user_prompt_fn(
                    description=row["Description"], predicted_category=pred_cat
                )
                if user_input:
                    new_corrections.append(
                        {"Description": row["Description"], "Category": user_input}
                    )

        if new_corrections:
            return pd.DataFrame(new_corrections)
        else:
            return pd.DataFrame(columns=["Description", "Category"])

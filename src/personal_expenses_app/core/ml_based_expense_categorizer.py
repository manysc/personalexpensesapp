from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


class MLBasedExpenseCategorizer:
    def __init__(self):
        super().__init__()

    @staticmethod
    def prepare_training_data(df):
        """
        Takes a list of expense dicts or a DataFrame, returns DataFrame with just Description & Category.
        """
        df = df[df["Category"] != "Other"]
        df = df[["Description", "Category"]].dropna()
        df["Description"] = df["Description"].str.upper()
        return df

    @staticmethod
    def split_train_test(training_data, test_size=0.2, random_state=42):
        X = training_data["Description"]
        y = training_data["Category"]

        # Check if stratification is possible (all classes need at least 2 samples)
        value_counts = y.value_counts()
        can_stratify = (value_counts >= 2).all()

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            stratify=y if can_stratify else None,
            test_size=test_size,
            random_state=random_state,
        )
        return X_train, X_test, y_train, y_test

    @staticmethod
    def evaluate_model(model, X_test, y_test):
        """
        Returns classification_report and category accuracy dict.
        """
        y_pred = model.predict(X_test)
        report = classification_report(
            y_test, y_pred, digits=3, output_dict=True, zero_division=0
        )
        print("\n=== Per-Category Classification Report ===")
        print(classification_report(y_test, y_pred, digits=3, zero_division=0))
        cat_acc = {
            cat: values["f1-score"]
            for cat, values in report.items()
            if isinstance(values, dict) and "f1-score" in values
        }
        return cat_acc

    @staticmethod
    def train_categorization_model(df):
        input_data = df["Description"]
        output_data = df["Category"]
        model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(max_features=1000)),
                ("clf", LogisticRegression(max_iter=1000)),
            ]
        )
        model.fit(input_data, output_data)
        return model

    @staticmethod
    def ml_categorize_expenses(df, model):
        df["Category"] = model.predict(df["Description"].astype(str).str.upper())
        return df

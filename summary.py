import pandas as pd

def normalize_statement(filepath):
    df = pd.read_excel(filepath, header=None)

    header_row_index = None
    date_keywords = ["date", "trans date", "value date", "posting date"]
    credit_keywords = ["credit", "cr", "deposit", "inflow", "amount in"]

    for i in range(min(30, len(df))):
        row = df.iloc[i].astype(str).str.lower().tolist()
        if any(any(k in cell for k in date_keywords) for cell in row) and \
           any(any(k in cell for k in credit_keywords) for cell in row):
            header_row_index = i
            break

    if header_row_index is None:
        raise ValueError("Could not detect header row with both date and credit-like columns")

    df = pd.read_excel(filepath, header=header_row_index)
    df.columns = df.columns.str.strip().str.lower()
    return df


def summarize_monthly(df):
    date_col = next((col for col in df.columns if "date" in col), None)
    if not date_col:
        raise ValueError(f"No date column found. Available: {df.columns.tolist()}")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    credit_keywords = ["credit", "cr", "deposit", "inflow", "amount in"]
    credit_col = next((col for col in df.columns if any(k in col for k in credit_keywords)), None)

    if not credit_col:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            credit_col = numeric_cols[0]
        else:
            raise ValueError(f"No credit column found. Available: {df.columns.tolist()}")

    df[credit_col] = pd.to_numeric(df[credit_col], errors="coerce").fillna(0)

    df["month"] = df[date_col].dt.to_period("M")
    summary = df.groupby("month").agg(
        credit_count=(credit_col, lambda x: (x > 0).sum()),
        total_credits=(credit_col, "sum")
    ).reset_index()

    summary["month"] = summary["month"].astype(str)
    return summary.to_dict(orient="records")

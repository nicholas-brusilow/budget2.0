import html
import os
import glob
import re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWDATA = os.path.join(ROOT, "rawdata")
OUTPUT = os.path.join(ROOT, "expenditures.csv")
VISUAL_OUTPUT = os.path.join(ROOT, "visual_expenditures.csv")

OUTPUT_COLUMNS = [
    "date", "amount", "description", "account",
    "category", "subcategory", "necessity_level",
    "timescale", "timescale_end", "ignore",
]


def _parse_alliant_amount(raw: str) -> float:
    # Alliant: plain $1.23 = money in (deposit/payment), ($1.23) = money out (purchase/withdrawal).
    # Returns positive for money in, negative for money out.
    s = raw.strip()
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(",", "")
    val = float(s)
    return -val if negative else val


def load_alliant_cc(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    # _parse_alliant_amount returns positive for payments, negative for purchases — correct as-is.
    out["amount"] = df["Amount"].apply(_parse_alliant_amount)
    out["description"] = df["Description"].str.strip().apply(html.unescape)
    out["account"] = "alliant_cc"
    return out


def load_alliant_checking(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    # _parse_alliant_amount returns positive for deposits, negative for withdrawals — correct as-is.
    out["amount"] = df["Amount"].apply(_parse_alliant_amount)
    out["description"] = df["Description"].str.strip().apply(html.unescape)
    out["account"] = "alliant_checking"
    return out


def load_chase_cc(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["Transaction Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    # Chase CC: negative = purchase (money out), positive = payment (money in) — correct as-is.
    out["amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    out["description"] = df["Description"].str.strip()
    out["account"] = "chase_cc"
    return out


def load_chase_checking(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["Posting Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    # Chase checking: negative = debit (money out), positive = credit (money in) — correct as-is.
    out["amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    out["description"] = df["Description"].str.strip()
    out["account"] = "chase_checking"
    return out


def load_discover_cc(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["Trans. Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    # Discover: positive = purchase (money out), negative = payment — negate to match convention.
    out["amount"] = pd.to_numeric(df["Amount"], errors="coerce") * -1
    out["description"] = df["Description"].str.strip()
    out["account"] = "discover_cc"
    return out


LOADERS = {
    "alliant_cc":       (load_alliant_cc,       ["*.csv"]),
    "alliant_checking": (load_alliant_checking,  ["*.csv"]),
    "chase_cc":         (load_chase_cc,          ["*.CSV", "*.csv"]),
    "chase_checking":   (load_chase_checking,    ["*.CSV", "*.csv"]),
    "discover_cc":      (load_discover_cc,       ["*.csv"]),
}


def load_all_raw() -> pd.DataFrame:
    frames = []
    for account, (loader, patterns) in LOADERS.items():
        folder = os.path.join(RAWDATA, account)
        if not os.path.isdir(folder):
            continue
        files = []
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(folder, pattern)))
        for path in sorted(set(files)):
            try:
                df = loader(path)
                frames.append(df)
            except Exception as e:
                print(f"Warning: could not parse {path}: {e}")
    if not frames:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    combined = pd.concat(frames, ignore_index=True)
    combined["category"] = ""
    combined["subcategory"] = ""
    combined["necessity_level"] = ""
    combined["timescale"] = combined["date"]
    combined["timescale_end"] = combined["date"]
    combined["ignore"] = False
    return combined[OUTPUT_COLUMNS]


VISUAL_COLUMNS = ["date", "amount", "category", "subcategory", "necessity_level"]


def generate_visual_expenditures(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["ignore"] = df["ignore"].astype(str).str.strip().str.lower() == "true"

    def _resolve(row, col):
        val = str(row.get(col, "")).strip()
        return val if val and val.lower() not in ("nan", "nat") else row["date"]

    rows = []
    for _, row in df.iterrows():
        if row["ignore"] or pd.isna(row["amount"]):
            continue
        try:
            start = pd.to_datetime(_resolve(row, "timescale"))
            end = pd.to_datetime(_resolve(row, "timescale_end"))
        except Exception:
            start = end = pd.to_datetime(row["date"])
        n_days = max((end - start).days + 1, 1)
        daily = row["amount"] / n_days
        for i in range(n_days):
            rows.append({
                "date": (start + pd.Timedelta(days=i)).strftime("%Y-%m-%d"),
                "amount": daily,
                "category": row.get("category", ""),
                "subcategory": row.get("subcategory", ""),
                "necessity_level": row.get("necessity_level", ""),
            })

    if not rows:
        return pd.DataFrame(columns=VISUAL_COLUMNS)
    return pd.DataFrame(rows, columns=VISUAL_COLUMNS)


def run():
    new_data = load_all_raw()

    if os.path.exists(OUTPUT):
        existing = pd.read_csv(OUTPUT, dtype=str)
        if "ignore" not in existing.columns:
            existing["ignore"] = "False"
        existing["amount"] = pd.to_numeric(existing["amount"], errors="coerce")
        existing_keys = set(
            zip(existing["date"], existing["amount"].round(2), existing["description"])
        )
        is_new = [
            (row["date"], round(row["amount"], 2), row["description"]) not in existing_keys
            for _, row in new_data.iterrows()
        ]
        new_rows = new_data[is_new]
        if new_rows.empty:
            print("No new transactions found.")
            combined = existing
        else:
            combined = pd.concat([existing, new_rows], ignore_index=True)
            combined.to_csv(OUTPUT, index=False)
            print(f"Added {len(new_rows)} new transactions. expenditures.csv now has {len(combined)} total rows.")
    else:
        combined = new_data
        combined.to_csv(OUTPUT, index=False)
        print(f"Added {len(combined)} new transactions. expenditures.csv now has {len(combined)} total rows.")

    visual = generate_visual_expenditures(combined)
    visual.to_csv(VISUAL_OUTPUT, index=False)
    print(f"Generated visual_expenditures.csv with {len(visual)} rows.")


if __name__ == "__main__":
    run()

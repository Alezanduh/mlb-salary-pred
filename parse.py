import re
import pandas as pd

_SEG = re.compile(r"(\d+)\s*yrs?\s*/\s*\$([\d.,]+)\s*([KMB]?)", re.I)
_MULT = {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}

def parse_contract(text):
    """Sum guaranteed years and dollars across comma-separated segments; options after '&' are ignored."""
    years = total = 0.0
    for seg in str(text).split(","):
        m = _SEG.search(seg.split("&")[0])
        if m:
            years += int(m.group(1))
            total += float(m.group(2).replace(",", "")) * _MULT[m.group(3).upper()]
    if years == 0:
        return pd.Series({"Total On Contract": float("nan"), "Total Average Salary": float("nan")})
    return pd.Series({"Total On Contract": total, "Total Average Salary": round(total / years, 3)})

SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}

def standardize_names(df, col="name"):
    """Standardizes naming conventions to a 'First Last' context"""
    def _fix(name):
        if pd.isna(name):
            return name
        name = re.sub(r"\s+", " ", str(name)).strip() # collapse stray whitespace
        if "," not in name:
            return name                                  
        parts = [p.strip() for p in name.split(",")]
        last, first = parts[0], parts[1]
        suffix = " ".join(p for p in parts[2:] if p)     
        # 'Last Jr., First' → move the suffix to the end
        last_tokens = last.split()
        if len(last_tokens) > 1 and last_tokens[-1].lower() in SUFFIXES:
            suffix = (last_tokens[-1] + " " + suffix).strip()
            last = " ".join(last_tokens[:-1])
        return " ".join(p for p in (first, last, suffix) if p)

    df = df.copy()
    df[col] = df[col].apply(_fix)
    return df

_ROUNDS = [
    ("World Series", 4),
    ("Championship Series", 3),
    ("Division Series", 2),
    ("Wild Card", 1),
]

def parse_postseason(text):
    """Highest round reached: 0 none, 1 Wild Card, 2 Division Series, 3 LCS, 4 World Series, 5 won World Series."""
    if not isinstance(text, str) or not text.strip():
        return 0
    reached = 0
    for series in text.split(";"):
        series = series.strip()
        for label, level in _ROUNDS:
            if label in series:
                if level == 4 and series.startswith("Won"):
                    level = 5
                reached = max(reached, level)
                break
    return reached

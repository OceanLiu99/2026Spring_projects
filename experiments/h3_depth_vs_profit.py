"""
H3: pool H1 + H2 results and dedup by seed for the depth-profit correlation.

Output: outputs/data/h3_pooled.csv
"""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "outputs" / "data"


def main():
    h1 = pd.read_csv(DATA / "h1_luck_vs_bomb.csv")
    h2 = pd.read_csv(DATA / "h2_profit_distributions.csv")
    pooled = pd.concat([h1, h2], ignore_index=True)
    before = len(pooled)
    pooled = pooled.drop_duplicates(subset=["seed", "cell_id"])
    after = len(pooled)
    print(f"[H3] pooled {before} -> {after} after dedup by (seed, cell_id)")
    pooled.to_csv(DATA / "h3_pooled.csv", index=False)


if __name__ == "__main__":
    main()
"""
H2: 4 strategy cells x 500 runs = 2000 runs at neutral luck.

Output: outputs/data/h2_profit_distributions.csv
"""
import time
import pandas as pd

from experiments.runner import run_cell, write_csv, assert_equipment_present

EXPERIMENT_ID = 2
RUNS_PER_CELL = 500
LUCK_NEUTRAL = 4  # representative value 0.035 (closest to 0)


def main():
    assert_equipment_present()
    started = time.time()
    cells = []
    cell_ids = ["pickaxe_nofood", "pickaxe_food", "bomb_nofood", "bomb_food"]
    for cell_idx in range(len(cell_ids)):
        cell_id = cell_ids[cell_idx]
        print(f"[H2] cell={cell_id} ({cell_idx + 1}/4)")
        df = run_cell(EXPERIMENT_ID, cell_idx, cell_id, LUCK_NEUTRAL, RUNS_PER_CELL)
        cells.append(df)
    full = pd.concat(cells, ignore_index=True)
    out = write_csv(full, "h2_profit_distributions.csv")
    print(f"[H2] wrote {len(full)} rows to {out} in {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
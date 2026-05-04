"""
H2: 4 strategy cells x 500 runs = 2000 runs at neutral luck.
RUNS_PER_CELL comes from Phase2 real-engine validation, especially the noisy
net_profit cells checked in the targeted extension.

Output: outputs/data/h2_profit_distributions.csv
"""
import time
import pandas as pd

from experiments.runner import run_cell, write_csv, assert_equipment_present

# Phase2 real-engine validation selected this as the final run count.
# See outputs/data/validation_n_final.csv and
# outputs/data/validation_n_extension_summary_real.csv.
RUNS_PER_CELL = 2000
# keeps H2 seeds separate from H1 runs
EXPERIMENT_ID = 2
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
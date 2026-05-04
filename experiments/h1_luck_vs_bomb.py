"""
H1: 6 luck levels x 2 bomb strategies x 500 runs = 6000 runs.
RUNS_PER_CELL comes from Phase2 real-engine validation, not from the earlier
testing default.

Food strategy fixed to no-food to isolate luck-vs-bomb axis.
Output: outputs/data/h1_luck_vs_bomb.csv
"""
import time
import pandas as pd

from experiments.runner import run_cell, write_csv, assert_equipment_present

# Phase2 real-engine validation selected this as the final run count.
# See outputs/data/validation_n_final.csv and
# outputs/data/validation_n_extension_summary_real.csv.
RUNS_PER_CELL = 2000
# keeps H1 seeds separate from H2 runs
EXPERIMENT_ID = 1

def main():
    assert_equipment_present()
    started = time.time()
    cells = []
    cell_idx = 0
    for luck_level in (1, 2, 3, 4, 5, 6):
        for cell_id in ("pickaxe_nofood", "bomb_nofood"):
            print(f"[H1] cell={cell_id} luck={luck_level} ({cell_idx + 1}/12)")
            df = run_cell(EXPERIMENT_ID, cell_idx, cell_id, luck_level, RUNS_PER_CELL)
            cells.append(df)
            cell_idx += 1
    full = pd.concat(cells, ignore_index=True)
    out = write_csv(full, "h1_luck_vs_bomb.csv")
    print(f"[H1] wrote {len(full)} rows to {out} in {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
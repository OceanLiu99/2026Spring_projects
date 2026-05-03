"""
H1: 6 luck levels x 2 bomb strategies x 500 runs = 6000 runs.

Food strategy fixed to no-food to isolate luck-vs-bomb axis.
Output: outputs/data/h1_luck_vs_bomb.csv
"""
import time
import pandas as pd

from experiments.runner import run_cell, write_csv, assert_equipment_present

EXPERIMENT_ID = 1
RUNS_PER_CELL = 500


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
import csv
from pathlib import Path

from validation.run_phase2 import run_phase2_validation


def read_rows(csv_path):
    with csv_path.open(newline="", encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def remove_test_output(output_dir):
    if output_dir.exists():
        for csv_path in output_dir.glob("*.csv"):
            csv_path.unlink()
        output_dir.rmdir()


def test_run_phase2_writes_four_csvs():
    output_dir = Path("outputs") / "data" / "_test_phase2"
    remove_test_output(output_dir)

    try:
        summary = run_phase2_validation(
            output_dir=output_dir,
            n_runs=60,
            sample_n_grid=(10, 20),
            sample_replicates=3,
            sensitivity_n=10,
        )

        expected_names = (
            "validation_convergence.csv",
            "validation_sample_size.csv",
            "validation_sensitivity.csv",
            "validation_n_final.csv",
        )

        for file_name in expected_names:
            assert (output_dir / file_name).exists()

        convergence_rows = read_rows(summary["convergence_path"])
        sample_size_rows = read_rows(summary["sample_size_path"])
        sensitivity_rows = read_rows(summary["sensitivity_path"])
        n_final_rows = read_rows(summary["n_final_path"])

        assert len(convergence_rows) > 0
        assert len(sample_size_rows) == 2
        assert len(sensitivity_rows) == 2
        assert len(n_final_rows) == 1

        assert "cell_id" in convergence_rows[0]
        assert "converged" in convergence_rows[0]
        assert "relative_half_width" in sample_size_rows[0]
        assert "monotonic_passed" in sensitivity_rows[0]
        assert "evidence" in n_final_rows[0]
    finally:
        remove_test_output(output_dir)

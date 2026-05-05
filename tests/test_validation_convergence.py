from validation.convergence import processing_mean
from validation.convergence import convergence_test
from validation.convergence import assess_engine
from validation.simple_mock import simple_mock_run

def test_processing_mean_returns_cumulative_average():
    assert processing_mean([10, 20, 30]) == [10.0, 15.0, 20.0]

def test_processing_mean_empty_list_returns_empty_list():
    assert processing_mean([]) == []

def test_convergence_test_returns_true_for_constant_function():
    result = convergence_test([10.0] * 100, window=10, rel_tol=0.01, min_n=50)

    assert result["converged"] is True
    assert result["n_required"] >= 50
    assert result["final_mean"] == 10.0

def test_convergence_test_returns_fails_when_not_enough_values():
    result = convergence_test([10, 10, 10], window=20, rel_tol=0.01, min_n=50)

    assert result["converged"] is False
    assert result["n_required"] is None
    assert result["final_mean"] == 10.0

def test_convergence_test_fails_for_drift_sequence():
    result = convergence_test(list(range(200)), window=20, rel_tol=0.01, min_n=50)

    assert result["converged"] is False
    assert result["n_required"] is None

def test_assess_engine_collects_samples():
    result = assess_engine(
        # call simple_mock_engine to simulate 30 runs, checking convergence on the "max_depth" metric each time
        simple_mock_run,
        {"cell_id": "bomb_food", "luck_level": 6, "use_bombs": True},
        "max_depth",
        n_runs=30,
        window=10,
        min_n=10,
    )

    assert result["metric"] == "max_depth"
    assert len(result["samples"]) == 30
    #cant guarantee its converged since random noise involved
    assert "converged" in result
    assert "final_mean" in result

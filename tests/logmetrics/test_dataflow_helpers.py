import pytest
from datetime import datetime, timezone
from logmetrics.dataflow_helpers import (
    acc_builder,
    Accumulator,
    LogEvent,
    calculate_stats,
)


def test_acc_builder_returns_expected_intial_dict():
    assert acc_builder() == Accumulator(
        date=None,
        customer_id=None,
        count=0,
        errors=0,
        avg_duration=0,
        median_duration=0,
        p99_duration=0,
        durations=[],
    )


@pytest.mark.parametrize(
    "durations, expected_avg, expected_p50, expected_p99",
    [
        pytest.param([0.5], 0.5, 0.5, 0.5, id="Single value"),
        pytest.param([0.5, 1.5], 1.0, 1.0, 1.5, id="Two values"),
        pytest.param(
            [0.1, 0.2, 0.3],
            0.2,
            0.2,
            0.3,
            id="Odd number of values for median",
        ),
        pytest.param(
            [0.1, 0.2, 0.3, 0.4],
            0.25,
            0.25,
            0.4,
            id="Even number of values for median",
        ),
        pytest.param(
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            0.55,  # avg
            0.55,  # median (mean of 0.5 and 0.6)
            1.0,  # p99
            id="Large sample for p99",
        ),
        pytest.param(
            [0.1, 0.1, 0.1, 0.2, 0.2], 0.14, 0.1, 0.2, id="Repeated values"
        ),
        pytest.param([0.3, 0.1, 0.2], 0.2, 0.2, 0.3, id="Unsorted input"),
    ],
)
def test_calculate_stats_calculates_correct_durations(
    durations, expected_avg, expected_p50, expected_p99
):
    """
    Test that calculate_stats correctly computes average, median, and p99 durations.
    """
    snapshot = acc_builder()

    # Create test events and apply calculate_stats
    for duration in durations:
        event = LogEvent(
            customer_id="test_customer",
            resource="/test",
            status_code=200,
            duration=duration,
            timestamp=datetime.now(timezone.utc),
        )
        snapshot = calculate_stats(snapshot, event)

    # Assert results with small tolerance for floating point arithmetic
    assert abs(snapshot.avg_duration - expected_avg) < 0.0001
    assert abs(snapshot.median_duration - expected_p50) < 0.0001
    assert abs(snapshot.p99_duration - expected_p99) < 0.0001


@pytest.mark.parametrize(
    "status_codes, expected_count, expected_error_count",
    [
        pytest.param([200], 1, 0, id="Single success"),
        pytest.param([500], 1, 1, id="Single error"),
        pytest.param([200, 400, 500], 3, 2, id="Mixed success and errors"),
        pytest.param([200, 201, 202, 204], 4, 0, id="All success codes"),
        pytest.param(
            [400, 401, 403, 404, 500, 502, 503], 7, 7, id="All_error_types"
        ),
        pytest.param([], 0, 0, id="Empty input"),
        pytest.param(
            [200, 201, 301, 302, 400, 404, 500],
            7,
            3,
            id="Mixed all status types",
        ),
        pytest.param([399, 400], 2, 1, id="Error boundary case"),
        pytest.param(
            [200, 200, 200, 404, 200, 500],
            6,
            2,
            id="Common production scenario",
        ),
    ],
)
def test_calculate_stats_calculates_accurate_counts(
    status_codes, expected_count, expected_error_count
):
    """
    Test that calculate_stats correctly counts total requests and errors.
    """
    # Initialize empty snapshot
    snapshot = acc_builder()

    # Create test events and apply calculate_stats
    for status_code in status_codes:
        event = LogEvent(
            customer_id="test_customer",
            resource="/test",
            status_code=status_code,
            duration=0.1,  # dummy duration
            timestamp=datetime.now(timezone.utc),
        )
        snapshot = calculate_stats(snapshot, event)

    # Assert counts match expected values
    assert snapshot.count == expected_count
    assert snapshot.errors == expected_error_count

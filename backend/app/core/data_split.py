"""
SkyGuard AI - Train / Evaluation Split for Real Station Data

Single source of truth for which real observations any component is allowed to
LEARN from, so that no model is ever fitted on rows it will later be scored on.

Why this module exists: the real-data benchmark evaluates on the first
`EVAL_HOLDOUT_ROWS` rows of each station file, while the isolation forest, the
autoencoder, and the hourly climatology all originally trained on the *entire*
file -- so 100% of the evaluation set sat inside the training set (for the
coastal station, the evaluation window was ~56% of everything that station
contributed to training). The learned components are unsupervised and the
injected faults are added at scoring time, so they never memorized a fault
label; but they had already seen the exact clean background readings they were
later asked to judge as normal, which inflates precision and depresses the
false-positive rate -- the two headline claims of the real-data benchmark.

Every consumer of the real CSVs must therefore take its training rows through
`training_rows()`. The benchmark keeps using the leading rows, and the two
sets are disjoint by construction.
"""

from typing import List, TypeVar

# Must match benchmark/run_real_data_benchmark.py's WARMUP_STEPS +
# MAX_STEPS_PER_STATION (30 + 1500). That file asserts this at import time so
# the two cannot silently drift apart.
EVAL_HOLDOUT_ROWS = 1530

T = TypeVar("T")


def training_rows(all_rows: List[T]) -> List[T]:
    """
    The portion of one station's chronological observations that models may
    train on: everything AFTER the evaluation holdout window.

    If a station has too few rows to leave a usable training remainder, returns
    an empty list rather than silently leaking -- a component with no clean
    training data for a station should fall back to its synthetic baseline, not
    quietly train on the evaluation set.
    """
    if len(all_rows) <= EVAL_HOLDOUT_ROWS:
        return []
    return all_rows[EVAL_HOLDOUT_ROWS:]

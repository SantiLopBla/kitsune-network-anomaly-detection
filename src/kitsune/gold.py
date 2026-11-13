# Transformations for the gold layer.

from pyspark.sql import DataFrame, functions as F

from .feature_names import LAMBDAS

# EDA found leaked Unix timestamps in these two stats of the jitter block.
# The weight stat is clean, so it stays in gold
LEAKED_JITTER_STATS = ["mean", "variance"]


def add_split(packets: DataFrame, train_end_row: int, validation_end_row: int) -> DataFrame:
    """Tag each packet as train, validation or test by its position in the capture."""
    # Rows are in arrival order, so splitting by row number is a chronological split.
    # A random split would put future packets in train and near-identical neighbors in both sets
    split = (
        # Conditions are checked in order, like if / elif / else
        F.when(F.col("_row_number") <= train_end_row, "train")
        # Only reached if the row is past train_end_row, so no lower bound is needed
        .when(F.col("_row_number") <= validation_end_row, "validation")
        # Everything after the normal prefix, where the attacks are
        .otherwise("test")
    )
    # The boundaries come from the notebook, so the same function works with other limits
    return packets.withColumn("split", split)


def leaked_jitter_columns() -> list[str]:
    """Return the 10 hh_jit columns with leaked timestamps (mean and variance of every window)."""
    # Built from LAMBDAS instead of typed by hand, so the names always match silver.
    # A wrong name would be dangerous: df.drop() ignores columns that don't exist
    names = []
    for lam in LAMBDAS:
        # Same naming rule as feature_names(): 0.1 becomes 0_1
        lam_text = lam.replace(".", "_")
        for stat in LEAKED_JITTER_STATS:
            # e.g. hh_jit_l5_mean, hh_jit_l0_1_variance
            names.append(f"hh_jit_l{lam_text}_{stat}")
    return names
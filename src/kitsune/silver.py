from pyspark.sql import DataFrame, functions as F

from .feature_names import feature_names


def clean_features(features_raw: DataFrame) -> DataFrame:
    """Cast the 115 bronze feature columns to double and give them their real names."""
    names = feature_names()

    # _c0 -> mi_l5_weight, _c1 -> mi_l5_mean, ... (all as double)
    feature_cols = []
    for i in range(len(names)):
        feature_cols.append(F.col(f"_c{i}").cast("double").alias(names[i]))

    # Keep the row number (to join with labels later) + the 115 clean columns
    return features_raw.select("_row_number", *feature_cols)


def clean_labels(labels_raw: DataFrame) -> DataFrame:
    """Cast the bronze labels: row number to bigint and x to an int label."""
    return labels_raw.select(
        F.col("_c0").cast("bigint").alias("_row_number"),  # same name/type as features, to join
        F.col("x").cast("int").alias("label"),             # 1 = attack, 0 = benign   
    )


def join_features_labels(features: DataFrame, labels: DataFrame) -> DataFrame:
    """Attach each packet's label to its features, matching by row number."""
    return features.join(labels, on="_row_number", how="inner")


def validate_silver(packets: DataFrame, expected_rows: int) -> None:
    """Raise an error if the silver data breaks any quality rule."""
    # Rule 1: the join must not lose or add rows
    actual_rows = packets.count()
    if actual_rows != expected_rows:
        raise ValueError(f"Row count changed in join: expected {expected_rows}, got {actual_rows}")

    # Rule 2: no nulls in any column (one pass over the data)
    null_exprs = []
    for c in packets.columns:
        null_exprs.append(F.count_if(F.col(c).isNull()).alias(c))
    null_row = packets.agg(*null_exprs).first()

    cols_with_nulls = []
    for c in packets.columns:
        if null_row[c] > 0:
            cols_with_nulls.append(c)

    if cols_with_nulls:
        raise ValueError(f"Columns with nulls: {cols_with_nulls}")

    # Rule 3: no NaN or infinite values in the features (one more pass)
    bad_exprs = []
    for c in feature_names():
        value = F.col(c)
        is_bad = F.isnan(value) | (value == float("inf")) | (value == float("-inf"))
        bad_exprs.append(F.count_if(is_bad).alias(c))
    bad_row = packets.agg(*bad_exprs).first()

    cols_with_bad_values = []
    for c in feature_names():
        if bad_row[c] > 0:
            cols_with_bad_values.append(c)

    if cols_with_bad_values:
        raise ValueError(f"Columns with NaN or infinite values: {cols_with_bad_values}")

    # Rule 4: label must be 0 (benign) or 1 (attack)
    invalid_labels = packets.filter(~F.col("label").isin(0, 1)).count()
    if invalid_labels > 0:
        raise ValueError(f"{invalid_labels} rows have a label other than 0 or 1")
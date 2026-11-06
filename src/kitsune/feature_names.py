# Names and descriptions of the 115 Kitsune features.
# Column layout checked in Notebooks/Exploration/feature_layout_check

# Decay factors (λ) of the time windows.
# A bigger λ forgets old packets faster, so it looks at a shorter window.
LAMBDAS = ["5", "3", "1", "0.1", "0.01"]

# Stats for a single stream of packets
STATS_1D = ["weight", "mean", "variance"]

# Stats for a conversation: the same 3 plus 4 that compare both directions
STATS_2D = ["weight", "mean", "variance", "radius", "magnitude", "cov", "pcc"]

# Feature blocks in the same order as the CSV columns
BLOCKS = [
    ("mi", STATS_1D),      # traffic sent by this device (MAC + IP)
    ("h", STATS_1D),       # traffic sent by this IP
    ("hh", STATS_2D),      # conversation between two IPs
    ("hh_jit", STATS_1D),  # time gaps between packets in that conversation
    ("hphp", STATS_2D),    # conversation between two sockets (IP + port)
]

# Texts used to build the column comments in Unity Catalog
BLOCK_DESCRIPTIONS = {
    "mi": "packet sizes sent by this host (MAC + IP)",
    "h": "packet sizes sent by this IP",
    "hh": "packet sizes in the conversation between two IPs",
    "hh_jit": "time gaps between packets in the conversation between two IPs",
    "hphp": "packet sizes in the conversation between two sockets (IP + port)",
}

STAT_DESCRIPTIONS = {
    "weight": "decayed packet count (recent packets count more)",
    "mean": "decayed mean",
    "variance": "decayed variance",
    "radius": "combined spread of both directions (from their variances)",
    "magnitude": "combined size of both directions (from their means)",
    "cov": "covariance between both directions",
    "pcc": "Pearson correlation between both directions",
}


def feature_names():
    """Return the 115 feature names in column order."""
    names = []
    # block -> window -> stat, same order as the CSV (mi_l5_weight, mi_l5_mean, ...)
    for block, stats in BLOCKS:
        for lam in LAMBDAS:
            # Spark column names can't have dots, so 0.1 becomes 0_1
            lam_text = lam.replace(".", "_")
            for stat in stats:
                names.append(f"{block}_l{lam_text}_{stat}")
    return names


def feature_comments():
    """Return a dict {feature name: comment} for the 115 features."""
    comments = {}
    # Same loop as feature_names(), so every name gets its own comment
    for block, stats in BLOCKS:
        for lam in LAMBDAS:
            lam_text = lam.replace(".", "_")
            for stat in stats:
                name = f"{block}_l{lam_text}_{stat}"
                # The comment can keep the dot: 0.1 instead of 0_1
                comments[name] = f"{BLOCK_DESCRIPTIONS[block]}: {STAT_DESCRIPTIONS[stat]} (decay factor λ = {lam})"
    return comments
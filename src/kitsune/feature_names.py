# Kitsune feature layout (verified in Notebooks/exploration/feature_layout_check)

# Time windows (decay factor λ): bigger = forgets faster = shorter memory
LAMBDAS = ["5", "3", "1", "0.1", "0.01"]

# Stats for one traffic stream
STATS_1D = ["weight", "mean", "variance"]

# Stats for two streams compared (both directions of a conversation)
STATS_2D = ["weight", "mean", "variance", "radius", "magnitude", "cov", "pcc"]

# Blocks in column order: (name, stats computed in each window)
BLOCKS = [
    ("mi", STATS_1D),      # traffic sent by this device (MAC + IP)
    ("h", STATS_1D),       # traffic sent by this IP
    ("hh", STATS_2D),      # conversation between two IPs
    ("hh_jit", STATS_1D),  # time gaps between packets in that conversation
    ("hphp", STATS_2D),    # conversation between two sockets (IP + port)
]


def feature_names():
    """Return the 115 Kitsune feature names in column order."""
    names = []
    for block, stats in BLOCKS:
        for lam in LAMBDAS:
            lam_text = lam.replace(".", "_")  # "0.1" -> "0_1", dots break Spark column names
            for stat in stats:
                names.append(f"{block}_l{lam_text}_{stat}")  # e.g. hh_l5_pcc
    return names
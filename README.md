# Kitsune Network Anomaly Detection

> **🚧 Status: rebuilding.** The pipeline is being rebuilt with Unity Catalog, data quality checks and production practices. Done so far: setup, landing, bronze and silver layers (notebooks 00–03) and the exploratory analysis (EDA). Next: the gold layer (model-ready train/validation/test sets), designed from the EDA findings.

## What is this project?

Imagine a security camera connected to the internet. Most of the time it
just sends normal data back and forth — but sometimes an attacker floods it
with fake connection requests to knock it offline. This is a **SYN DoS
attack**.

This project analyzes almost **2.8 million network packets** and asks: can
we tell, just from the data, which ones are normal and which are part of an
attack? It's being built as a full pipeline — raw data to model-ready
dataset — using Databricks, Spark, and Delta Lake. The core challenge
(finding rare suspicious events hidden in a huge amount of normal activity)
is the same one behind fraud and risk detection.

## The dataset

- **Source:** [Kitsune Network Attack Dataset](https://archive.ics.uci.edu/dataset/516/kitsune+network+attack+dataset) (UCI ML Repository), SYN DoS subset
- **2,771,276 packets**, 115 numeric measurements each
- **Label:** `0` = normal, `1` = attack
- **Severely imbalanced:** 99.75% normal vs. 0.25% attack
- The 115 measurements have no names in the source file. The silver layer
  gives them descriptive names (see [Finding the real column names](#finding-the-real-column-names)).

## Architecture

```
UCI files (CSV.gz)
      │
      ▼
kitsune_dev.raw.landing            ← volume: source files, unchanged
      │
      ▼
kitsune_dev.bronze                 ← Delta tables: raw data (all text) + ingestion metadata
  ├── syn_dos_features_raw
  └── syn_dos_labels_raw
      │
      ▼
kitsune_dev.silver                 ← Delta table: typed, named, validated, one row per packet
  └── syn_dos_packets  ──────────►  EDA (Exploration/eda_syn_dos): findings → gold design
      │
      ▼
kitsune_dev.gold                   ← next: model-ready dataset
```

All data lives in a dedicated Unity Catalog catalog (`kitsune_dev`), with
one schema per layer, kept separate from a future production catalog.

## Repository structure

```
Notebooks/
  00_setup_catalog            catalog, schemas, volume, tags
  01_land_source_files        copy source files into the landing volume
  02_bronze_ingestion         raw files → bronze Delta tables
  03_silver_transformation    bronze → silver (orchestration only)
  Exploration/
    feature_layout_check      evidence for the column names used in silver
    eda_syn_dos               exploratory analysis of the silver table
src/kitsune/
  feature_names.py            generates the 115 feature names
  silver.py                   silver transformations and quality checks
```

The notebooks **orchestrate**; the transformation logic lives in Python
modules under `src/kitsune/`. This keeps the notebooks short, lets the same
functions be reused, and makes them testable with `pytest` later.

Notebooks under `Exploration/` are **not pipeline steps**: they answer
questions about the data, and their outputs are committed as evidence.

## Pipeline

| Step | Notebook | What happens |
|---|---|---|
| Setup | `00_setup_catalog` | Creates the catalog, schemas (`raw`, `bronze`, `silver`, `gold`), the landing volume and layer tags |
| Landing | `01_land_source_files` | Copies the source files into the landing volume, skipping files already there |
| Bronze | `02_bronze_ingestion` | Loads features and labels as managed Delta tables, unchanged, plus `_source_file` and `_ingested_at` |
| Silver | `03_silver_transformation` | Casts the 115 features to numbers, gives them real names, joins them with the labels, validates and writes `syn_dos_packets` |

### Design decisions

- **Bronze keeps the data exactly as received.** All columns stay as
  strings; typing and cleaning happen in silver. If something goes wrong
  later, the original data is always available.
- **The pipeline fails loudly instead of printing warnings.** Each notebook
  raises an error if a check fails, so later steps never run on bad data:
  - Landing: every expected file is present with its exact size in bytes
  - Bronze: the features file has 115 columns, features and labels have the
    same number of rows, and row numbers in both tables go from 1 to n with
    no gaps or repeats
  - Silver (before writing): the join doesn't lose or add rows, no column
    has nulls, no feature has NaN or infinite values, and every label is 0 or 1
  - Silver (after writing): the saved table has the expected number of rows
- **Silver validates before it writes.** Bad data is stopped before it
  reaches the table, not discovered afterwards.
- **Strict type casting in the pipeline.** Silver uses `cast`, which stops
  with an error if a value isn't a number (ANSI mode, on by default in
  serverless); the exploration notebook uses `try_cast`, which returns null
  instead, because it only profiles data.
- **Every notebook is idempotent.** Re-running it produces the same result
  (silver uses `overwrite`), so it's safe to retry after a failure.
- **Liquid clustering on `_row_number` in silver.** The data is in time
  order (verified in the EDA), and later steps select ranges of packets (for
  example, the first part of the capture for training), so clustering by row
  number speeds up those filters.
- **Tables are documented in Unity Catalog** with table comments and tags
  (`layer`, `source`, `dataset`, `contains_pii`), so anyone can understand
  them from the Catalog Explorer. Bronze also has column comments; silver
  column comments are planned.

## Finding the real column names

The 115 features come without names, and the two official sources disagree
on their order: the Kitsune source code and Table II of the Kitsune paper
list two of the five feature groups in opposite order.

Instead of picking one, I checked both against the data
(`Notebooks/Exploration/feature_layout_check`):

1. Computed the minimum and maximum of all 115 columns in a single Spark pass.
2. Checked rules that can't be broken: counts, means and variances are never
   negative, and correlations are always between -1 and 1.
3. **Result:** the paper's order would put a correlation in a column whose
   maximum is 5,609, which is impossible. The source code's order passes
   every rule, so silver uses it.

Each feature is named `{group}_l{window}_{statistic}`, for example
`hh_l5_pcc` = correlation between the two directions of a conversation
between two IPs, over the shortest time window (λ = 5).

The five groups summarize recent traffic from different points of view:

| Group | Groups packets by | Columns |
|---|---|---|
| MI | same sender (MAC + IP) | 15 |
| H | same source IP | 15 |
| HH | same pair of IPs (A ↔ B) | 35 |
| HH_jit | same pair of IPs, time between packets (jitter) | 15 |
| HpHp | same pair of IP + port | 35 |

## What the EDA found

Before building gold, I explored the silver table
(`Notebooks/Exploration/eda_syn_dos`) with one question in mind: **what in
this data could mislead a model?** Every finding below is backed by an output
in the notebook.

### 1. Where the attack is

- The first **2,682,349 packets (96.8%) are 100% normal**. The attack starts
  at row 2,682,350 and lasts until the end of the file (7,038 attack packets).
- The attack never takes over the traffic: at most about 37% of the packets
  in any 1,000-packet window are attacks. There is a **sustained flood**
  (about 20% attack share), followed by **short bursts**.
- **Why it matters:** the model will learn what "normal" looks like from the
  clean prefix only (like the original Kitsune). Normal packets inside the
  attack zone are left out of training, because their features summarize
  recent traffic that includes the attack. The model should also be
  evaluated per phase, since the short bursts are harder to detect.

### 2. A bug in the dataset that would let a model cheat

- The HH_jit columns should hold **seconds between packets**, but 537 rows
  contain values of about **1.49 billion seconds (47 years)**. Converted to a
  date, they give **2017-02-25**, the day the dataset was recorded: the
  feature extractor leaked the **Unix timestamp** instead of the time gap,
  on the first packet of each new conversation.
- The leak spreads to the following packets through the running averages:
  from 1,577 rows (fastest-forgetting window) to 10,427 rows
  (slowest-forgetting window).
- **490 of the 492 leaked rows in the attack zone are attack packets
  (99.6%).** A SYN flood opens many new conversations, so the bug lands
  almost only on attacks. A model would learn to spot the bug instead of the
  attack: inflated metrics that wouldn't hold on a real network.
- I checked every HH_jit statistic: `mean` and `variance` carry the leak,
  `weight` (a packet count) is clean.
- **Bonus:** the leaked timestamps work as a hidden clock. They never go
  backwards (checked with a window function), which proves the file is
  stored in **arrival order** and supports a chronological train/test split.
  The capture lasts about 53 minutes.

### 3. The other feature groups carry real signals

I compared the average of every column in normal vs attack packets, group by
group, looking for anything as suspicious as the HH_jit leak:

| Group | Result | Action for gold |
|---|---|---|
| MI | Real signal: attack packets come from senders with larger, more uniform packet sizes | Keep |
| H | Almost identical to MI (each device uses one IP) | Keep, note redundancy |
| HH | Real signal, physically possible values | Keep |
| HH_jit | **Leaked timestamps** in `mean` and `variance` | **Drop 10 columns**, keep 5 `weight` |
| HpHp | Real signal: attacks hit a single port pair, normal traffic uses many | Keep |

### Decisions for the gold layer

- **Train only on the normal prefix** (rows 1 to 2,682,349).
- **Drop the 10 HH_jit `mean` and `variance` columns**, keep the 5 `weight`
  columns.
- **Keep silver unchanged** (all 115 columns), so a model trained with and
  without the HH_jit columns can be compared to show how much the bug
  inflates the results.

## How to run

Requires a Databricks workspace with Unity Catalog (works on Free Edition).

1. Clone this repo into a Databricks Git folder.
2. Run `00_setup_catalog` once to create the catalog structure.
3. Download `SYN DoS_dataset.csv.gz` and `SYN DoS_labels.csv.gz` from the
   [UCI ML Repository](https://archive.ics.uci.edu/dataset/516/kitsune+network+attack+dataset)
   and upload them to `/Volumes/kitsune_dev/raw/landing/`.
4. Run `02_bronze_ingestion` (about 4 min).
5. Run `03_silver_transformation`.
6. *(Optional)* Run `Exploration/eda_syn_dos` to reproduce the EDA findings.

`01_land_source_files` copies the files from a previous volume in the
author's workspace; skip it if you uploaded the files manually in step 3.

## Known limitations

- **Full reload, not incremental.** The dataset is a fixed file, so each run
  rebuilds the tables. With new files arriving, ingestion would switch to
  Auto Loader.
- **Environment is set in a config cell.** `CATALOG = "kitsune_dev"` is a
  constant at the top of the notebook; it will become a job parameter when
  the pipeline is orchestrated with Lakeflow Jobs.
- **Silver validation reads the data several times.** The quality rules could
  be merged into a single aggregation to make the check faster.
- **No automated tests yet.** The functions in `src/kitsune/` are written to
  be tested; `pytest` tests are planned.
- **The EDA feature comparison uses averages.** Averages can hide a few
  extreme values; the maximum was only checked for the HH_jit group.
- **No IP or MAC addresses in the dataset.** Some patterns (for example, why
  attack senders have larger packets) can be described but not fully explained.

## Findings from the previous version

**Bronze:** caught a subtle bug early — the features and labels files didn't
line up by one row, traced to a hidden header in the labels file. Fixed it,
then verified every row was correctly matched, not just assumed. The rebuilt
bronze layer keeps the labels file's own row number (`_c0`) and validates it
(exactly 1 to n, no gaps or repeats), so the join in silver can't silently
misalign packets and labels.

## Tools used

Databricks (Free Edition) · PySpark · Spark SQL · Delta Lake · Unity Catalog · matplotlib · Git / GitHub

## Dataset citation

Kitsune Network Attack [Dataset]. (2019). UCI Machine Learning Repository.
https://doi.org/10.24432/C5D90Q

Y. Mirsky, T. Doitshman, Y. Elovici, and A. Shabtai, "Kitsune: An Ensemble
of Autoencoders for Online Network Intrusion Detection," Network and
Distributed System Security Symposium (NDSS), 2018.

## Author

**Santiago López Blanco** — Data Science Engineering student, Universidad
Fidélitas, Costa Rica
[LinkedIn](https://www.linkedin.com/in/santiago-lopez-blanco-ds) ·
[GitHub](https://github.com/SantiLopBla)
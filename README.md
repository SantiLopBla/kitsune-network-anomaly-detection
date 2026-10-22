# Kitsune Network Anomaly Detection

> **🚧 Status: rebuilding.** The pipeline is being rebuilt with Unity Catalog, data quality checks and production practices. Done so far: setup, landing and bronze layer (notebooks 00–02). 

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
- The 115 measurements have no descriptive names in the source file

## Architecture

```
UCI files (CSV.gz)
      │
      ▼
kitsune_dev.raw.landing            ← volume: source files, unchanged
      │
      ▼
kitsune_dev.bronze                 ← Delta tables: raw data + ingestion metadata
  ├── syn_dos_features_raw
  └── syn_dos_labels_raw
      │
      ▼
kitsune_dev.silver / gold          ← next
```

All data lives in a dedicated Unity Catalog catalog (`kitsune_dev`), with
one schema per layer, kept separate from a future production catalog.

## Pipeline

| Step | Notebook | What happens |
|---|---|---|
| Setup | `00_setup_catalog` | Creates the catalog, schemas (`raw`, `bronze`, `silver`, `gold`), the landing volume and layer tags |
| Landing | `01_land_source_files` | Copies the source files into the landing volume, skipping files already there |
| Bronze | `02_bronze_ingestion` | Loads features and labels as managed Delta tables, unchanged, plus `_source_file` and `_ingested_at` |

### Design decisions

- **Bronze keeps the data exactly as received.** All columns stay as
  strings; typing and cleaning happen in silver. If something goes wrong
  later, the original data is always available.
- **The pipeline fails loudly instead of printing warnings.** Each notebook
  raises an error if a check fails, so later steps never run on bad data:
  - Landing: every expected file is present with its exact size in bytes
  - Bronze: the features file has 115 columns, features and labels have the
    same number of rows, and row numbers go from 1 to n with no gaps
- **Every notebook is idempotent.** Re-running it produces the same result,
  so it's safe to retry after a failure.
- **Tables are documented in Unity Catalog** with table and column comments
  and tags (`layer`, `source`, `dataset`, `contains_pii`), so anyone can
  understand them from the Catalog Explorer.

## How to run

Requires a Databricks workspace with Unity Catalog (works on Free Edition).

1. Clone this repo into a Databricks Git folder.
2. Run `00_setup_catalog` once to create the catalog structure.
3. Download `SYN DoS_dataset.csv.gz` and `SYN DoS_labels.csv.gz` from the
   [UCI ML Repository](https://archive.ics.uci.edu/dataset/516/kitsune+network+attack+dataset)
   and upload them to `/Volumes/kitsune_dev/raw/landing/`.
4. Run `02_bronze_ingestion` (~4 min).

`01_land_source_files` copies the files from a previous volume in the
author's workspace; skip it if you uploaded the files manually in step 3.

## Findings from the previous version

**Bronze:** caught a subtle bug early — the features and labels files didn't
line up by one row, traced to a hidden header in the labels file. Fixed it,
then verified every row was correctly matched, not just assumed. The rebuilt
bronze layer keeps the labels file's own row number (`_c0`) so the join in
silver can be checked explicitly.

## Tools used

Databricks (Free Edition) · PySpark · Spark SQL · Delta Lake · Unity Catalog · Git / GitHub

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
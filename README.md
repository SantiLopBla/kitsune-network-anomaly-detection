# Kitsune Network Anomaly Detection

End-to-end data engineering and machine learning pipeline for detecting network
intrusions, built on Databricks using the Medallion Architecture (Bronze →
Silver → Gold).

## Project overview

This project processes the **SYN DoS** subset of the [Kitsune Network Attack
Dataset](https://archive.ics.uci.edu/dataset/516/kitsune+network+attack+dataset)
(UCI Machine Learning Repository), a real network capture where an attacker
performs a SYN flood denial-of-service attack against an IoT camera. The goal
is to build a reliable data pipeline and, eventually, a classification model
capable of distinguishing normal network traffic from attack traffic.

The project was built to reinforce hands-on skills in Databricks, Spark, and
Delta Lake ahead of the **Microsoft Azure Databricks Data Engineer Associate
(DP-750)** certification, and to demonstrate a data engineering + ML workflow
relevant to fraud/risk detection roles (a domain that shares the same core
challenge: detecting rare anomalous events in a sea of normal activity).

## Dataset

- **Source:** Kitsune Network Attack Dataset (UCI ML Repository), SYN DoS subset
- **Size:** 2,771,276 rows (network packets), 115 numeric features per packet
- **Features:** 23 base traffic statistics computed over 5 time windows
  (~100ms, ~500ms, ~1.5s, ~10s, ~1min), giving 115 total columns. Column names
  are not semantically labeled in the public dataset.
- **Label:** binary — `0` (normal traffic) / `1` (SYN DoS attack traffic)
- **Class balance:** severely imbalanced — 99.75% normal, 0.25% attack
  (2,764,238 vs. 7,038 rows)

## Pipeline architecture

Built on Databricks Free Edition using Unity Catalog, Delta Lake, and PySpark,
following the Medallion Architecture:

| Layer | Notebook | Purpose |
|---|---|---|
| Bronze | `01_bronze_ingestion.ipynb` | Raw ingestion, schema validation, row alignment audit |
| Silver | `02_silver_transformation.ipynb` | Type casting, null validation, data quality checks |
| EDA | `03_EDA.ipynb` | Feature ranking, distribution analysis |
| Gold | `04_gold_layer.ipynb` *(in progress)* | Class imbalance handling, model-ready dataset |

### Bronze layer
- Ingested two raw source files (features + labels) into Unity Catalog Volumes.
- Diagnosed and resolved a row-count mismatch caused by an unexpected header
  row in the labels file.
- Joined features and labels using `monotonically_increasing_id()`, then
  **audited the join for silent misalignment risk** by verifying both source
  DataFrames were read into a single Spark partition.

### Silver layer
- Cast all 115 feature columns from `string` to `double`, and `label` from
  `string` to `int`, applying an explicit scope rule: type correction belongs
  in Silver, model-specific encoding (e.g. one-hot) belongs in Gold.
- Validated null counts before/after casting (0 nulls introduced), verified
  `label` domain (`{0, 1}` only), and confirmed no duplicate row IDs.

### Exploratory Data Analysis
- Since none of the 115 features have public semantic names, feature
  importance was assessed statistically rather than by domain intuition:
  ranked all 115 features by a normalized mean-difference score between the
  normal and attack classes (`[mean(attack) − mean(normal)] / stddev(normal)`).
- Identified a small cluster of highly discriminative features
  (`feature_67`, `feature_70`, `feature_73`, `feature_74`, `feature_76`,
  `feature_77`, `feature_79`, `feature_80`) with scores far above the rest —
  clustered together in the 115-feature vector, suggesting one specific time
  window carries most of the signal for this attack type.
- Visualized distributions (log scale, due to extreme value ranges) and found
  that normal and attack traffic overlap heavily near zero for most features,
  with attack-only outliers forming a separate tail — meaning a simple
  threshold rule would not reliably separate the two classes.

### Gold layer (in progress)
Next steps: address the severe class imbalance (resampling or class weighting),
finalize `label` encoding based on the chosen model, and prepare a model-ready
dataset for training and evaluation.

## Tech stack

- **Platform:** Databricks (Free Edition), Unity Catalog
- **Processing:** PySpark, Apache Spark
- **Storage:** Delta Lake
- **Analysis:** pandas, matplotlib
- **Version control:** Git integration via Databricks

## Repository structure

```
├── Notebooks/
│   ├── 01_bronze_ingestion.ipynb
│   ├── 02_silver_transformation.ipynb
│   ├── 03_EDA.ipynb
│   └── 04_gold_layer.ipynb        (in progress)
└── README.md
```

## Author

**Santiago López Blanco** — Data Science Engineering student, Universidad
Fidélitas, Costa Rica
[LinkedIn](https://www.linkedin.com/in/santiago-lopez-blanco-ds) ·
[GitHub](https://github.com/SantiLopBla)
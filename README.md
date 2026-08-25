# Kitsune Network Anomaly Detection

## What is this project?

Imagine a security camera connected to the internet. Most of the time it
just sends normal data back and forth — but sometimes an attacker floods it
with fake connection requests to knock it offline. This is a **SYN DoS
attack**.

This project analyzes almost **2.8 million network packets** and asks: can
we tell, just from the data, which ones are normal and which are part of an
attack? It's built as a full pipeline — raw data to model-ready dataset —
using Databricks, Spark, and Delta Lake. The core challenge (finding rare
suspicious events hidden in a huge amount of normal activity) is the same
one behind fraud and risk detection.

## The dataset

- **Source:** [Kitsune Network Attack Dataset](https://archive.ics.uci.edu/dataset/516/kitsune+network+attack+dataset) (UCI ML Repository), SYN DoS subset
- **2,771,276 packets**, 115 numeric measurements each
- **Label:** `0` = normal, `1` = attack
- **Severely imbalanced:** 99.75% normal vs. 0.25% attack
- The 115 measurements have no descriptive names — feature relevance is
  decided with statistics, not guesswork

## Pipeline (Medallion Architecture)

| Stage | Notebook | What happens |
|---|---|---|
| Bronze | `01_bronze_ingestion.ipynb` | Load raw data, validate it's complete and correctly matched |
| Silver | `02_silver_transformation.ipynb` | Fix data types, validate for errors and missing values |
| EDA | `03_EDA.ipynb` | Explore the data, rank which measurements matter most |
| Gold | `04_gold_feature_engineering.ipynb` | Build the model-ready train/cv/test datasets |

**Bronze:** loaded the raw files and caught a subtle bug early — the
measurements and labels files didn't line up by one row, traced to a hidden
header. Fixed it, then verified every row was correctly matched, not just
assumed.

**Silver:** converted every column to the right type and validated: zero
missing values, no duplicate rows, label domain confirmed.

**EDA:** ranked the 115 unnamed features by how differently they behave
between normal and attack traffic. Found 8 that stand out — but also found
they cluster into 3 correlated groups, carrying overlapping signal rather
than being 8 independent ones.

**Gold:** located the attack window in time and found it's front-loaded,
then built a chronological train/cv/test split (splitting randomly would
leak future data into training). Recomputing the EDA feature score on train
only revealed it had leakage — the score collapsed and no longer separated
the classes cleanly. Feature selection by score was dropped; all 115
features are kept, with selection deferred to the baseline model's own
feature importances. Also found the three splits end up with very different
class balances (train 0.13%, cv 15.0%, test 1.8%), a side effect of where
attack density concentrates in time — documented as a caveat for reading
future model metrics.

## Tools used

Databricks (Free Edition) · PySpark · Delta Lake · Unity Catalog · pandas ·
matplotlib

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
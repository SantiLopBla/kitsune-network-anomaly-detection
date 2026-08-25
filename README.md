# Kitsune Network Anomaly Detection

## What is this project?

Imagine a security camera connected to the internet. Most of the time, it just
sends normal data back and forth. But sometimes, an attacker tries to shut it
down by flooding it with fake connection requests — this is called a **SYN DoS
attack**.

This project analyzes almost **2.8 million network packets** (each one a tiny
piece of data sent over the network) and tries to figure out: *can we tell,
just by looking at the data, which packets are normal and which ones are part
of an attack?*

It's built as a full data pipeline — from messy raw data to a clean, analyzed
dataset — using Databricks, Spark, and Delta Lake. It also connects to a
real-world problem: detecting fraud or risk is the same kind of challenge —
finding rare, suspicious events hidden inside a huge amount of normal activity.

## The dataset

- **Source:** [Kitsune Network Attack Dataset](https://archive.ics.uci.edu/dataset/516/kitsune+network+attack+dataset) (UCI ML Repository), SYN DoS subset
- **2,771,276 packets**, each described by 115 numeric measurements
- **Label:** `0` = normal traffic, `1` = attack traffic
- **Very imbalanced:** 99.75% normal vs. 0.25% attack — attacks are rare

The 115 measurements don't have descriptive names (just `feature_1` to
`feature_115`), so this project relies on statistics — not guesswork — to
figure out which ones actually matter.

## How the project is organized

Following the **Medallion Architecture**, a common way of organizing data
pipelines in three quality stages:

| Stage | Notebook | What happens |
|---|---|---|
| Bronze | `01_bronze_ingestion.ipynb` | Load the raw data, check it's complete and correctly matched |
| Silver | `02_silver_transformation.ipynb` | Fix data types, check for errors and missing values |
| EDA | `03_EDA.ipynb` | Explore the data, find which measurements matter most |
| Gold | `04_gold_layer.ipynb` *(in progress)* | Prepare the final dataset for building a model |

### Bronze — getting the raw data right
Loaded the raw files and caught a subtle bug early: the two source files
(measurements and labels) didn't line up by one row. Traced it to a hidden
header row, fixed it, and then double-checked that every measurement was
correctly matched to its label — not just assumed.

### Silver — cleaning the data
Converted every column to the right data type and validated the result: zero
missing values, no duplicate rows, and the label only contains valid values.

### EDA — finding what matters
Since the 115 measurements have no descriptive names, ranked them purely by
how differently they behave during an attack versus normal traffic. Found 8
measurements that stand out clearly above the rest — and discovered that
several of them are highly correlated with each other, meaning they carry
overlapping information rather than being 8 independent signals.

### Gold — building the model-ready dataset (in progress)
Next: decide how to handle the severe class imbalance, choose which of the
8 key features to keep given their overlap, and prepare the final dataset for
model training.

## Tools used

Databricks (Free Edition) · PySpark · Delta Lake · Unity Catalog · pandas ·
matplotlib

## Author

**Santiago López Blanco** — Data Science Engineering student, Universidad
Fidélitas, Costa Rica
[LinkedIn](https://www.linkedin.com/in/santiago-lopez-blanco-ds) ·
[GitHub](https://github.com/SantiLopBla)
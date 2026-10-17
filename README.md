# PharmaLens AI 💊
## Drug Safety Intelligence & Signal Exploration Platform

PharmaLens AI is a data-driven pharmacovigilance research platform built with Python and Streamlit. It analyzes adverse-event reports to help users explore medicine-related reporting patterns, screen potential drug–reaction signals, investigate reported events, and understand the limitations of safety-report data.

The project also includes a personal wellness check-in that generates practical, general lifestyle suggestions based on user responses.

**The main goal:** Turn complex adverse-event report data into understandable charts, screening statistics, evidence tables, and investigation workflows.

> **Important:** PharmaLens AI is an educational research prototype. Adverse-event reports do not prove that a medicine caused a reaction. The application is not intended for diagnosis, treatment decisions, or regulatory decision-making.

---

## 1. Project Overview

PharmaLens AI combines two main areas:

1. **Health and wellness:** A lifestyle questionnaire that provides general suggestions about sleep, physical activity, nutrition, stress, hydration, screen habits, tobacco/nicotine, and preventive health check-ups.
2. **Drug safety intelligence:** An interactive analytics workspace for examining adverse-event reports, exploring medicines and reactions, screening potential reporting signals, and documenting investigations.

The application is designed to make safety-report analysis easier to explore and explain without presenting statistical associations as confirmed medical conclusions.

### What makes the project useful?

- Interactive analytics rather than static reports.
- Drug–reaction screening using reporting odds ratios (ROR) and confidence intervals.
- Investigation tracking with locally stored records.
- A dataset-backed Safety Copilot using predefined, transparent analysis rules.
- Data-quality checks to expose missing information and limitations.
- CSV exports for further analysis and documentation.
- A dark, responsive-style interface with a dedicated landing page and separate analytical modules.

---

## 2. Dataset Used

### Dataset: FDA Adverse Event Reporting System (FAERS)

The project uses a prepared CSV file of adverse-event reports associated with the FDA Adverse Event Reporting System (FAERS).

FAERS contains reports of suspected adverse events and medication errors submitted to the US Food and Drug Administration. Such reports are useful for pharmacovigilance research, but they do not independently establish causation.

**Dataset file expected by the application:**

`data/adverse_events.csv`

The current application reads this local CSV file and attempts to identify common column names automatically.

### Dataset information

| Item | Details |
|---|---|
| Dataset family | FDA Adverse Event Reporting System (FAERS) |
| File format | CSV |
| Expected filename | `adverse_events.csv` |
| Required location | `data/adverse_events.csv` |
| Main analytical entities | Medicines and reported reactions |
| Other supported fields | Report dates, country, seriousness, death flags, age, sex, report identifiers |
| Data processing | Python, Pandas, NumPy |
| Visual exploration | Plotly charts in Streamlit |

The exact source download, extraction date, reporting period, and dataset release should be documented from the original data acquisition records. They are not specified in the current README or application code, so this repository does not claim a particular release date.

### Important dataset considerations

- A reported reaction is not necessarily caused by the medicine mentioned in the report.
- Reporting counts are not incidence rates or absolute patient risk.
- Reports may be incomplete, duplicated, under-reported, or influenced by publicity and reporting practices.
- Missing fields can affect the accuracy of some summaries.
- Results depend on the coverage and composition of the supplied CSV.

The app's Overview page displays statistics calculated from the loaded dataset, rather than relying on fixed report-count values.

---

## 3. Features and Modules

### 3.1 Home Page and Project Overview

The home page provides an introduction to PharmaLens AI and displays dataset-derived summary statistics.

It includes:

- Total reports loaded.
- Number of identified medicines.
- Number of distinct reported reactions.
- A personal wellness check-in.
- Navigation cards for the drug-safety workspace.

### 3.2 Personal Wellness Check-In

Users can answer optional questions about:

- Typical sleep duration.
- Physical activity.
- Eating patterns.
- Stress.
- Hydration.
- Screen-free time before sleep.
- Tobacco or nicotine use.
- Preventive health check-ups.

After submission, the application generates general suggestions based on the selected answers.

**How it works:** The recommendations are produced by predefined Python rules. This module does not calculate biological age, predict disease, or provide a medical diagnosis. Responses are kept in the current application session and are not saved to the drug-safety database.

### 3.3 Overview Dashboard

The Overview module summarizes the loaded dataset using metrics, charts, and tables.

Features include:

- Total reports, identified medicines, and reported reactions.
- Counts of reports with serious and death flags.
- Most frequently reported medicines.
- Most common reported reactions.
- Report seriousness visualization.
- Potential drug–reaction screening leads.
- Monthly report trends when usable date information is available.
- Dataset snapshot and detected-column information.

These visualizations describe the supplied reports, not the true frequency of adverse events among all patients.

### 3.4 Signal Lab

The Signal Lab screens medicine–reaction pairs using reporting counts and the Reporting Odds Ratio (ROR).

Users can:

- Set a minimum report count.
- Set a minimum ROR threshold.
- Filter for elevated screening leads.
- Review pair-level report counts.
- Inspect 95% confidence intervals.
- Explore a scatter plot of report volume and ROR.
- View supporting report records.
- Export screening results to CSV.
- Add a selected pair to the Investigation Queue.

#### Reporting Odds Ratio

The app constructs a report-level contingency table for each medicine–reaction pair:

- **a:** Reports containing both the selected medicine and reaction.
- **b:** Reports containing the selected medicine with other reactions.
- **c:** Reports containing other medicines with the selected reaction.
- **d:** Reports containing other medicines with other reactions.

The ROR is calculated as:

`ROR = (a × d) / (b × c)`

A 0.5 continuity correction is added to each cell to handle zero counts.

The approximate 95% confidence interval is calculated using:

`95% CI = exp(ln(ROR) ± 1.96 × SE)`

where:

`SE = sqrt(1/a + 1/b + 1/c + 1/d)`

The application labels a pair as an elevated reporting lead when it has at least three pair reports, an ROR greater than 1, and a lower 95% confidence bound greater than 1.

**Interpretation:** These are exploratory screening criteria implemented in the code, not a validated regulatory signal-detection method. An elevated ROR does not establish causation or patient-level risk.

### 3.5 Drug Explorer

The Drug Explorer focuses on one selected medicine.

Features include:

- Total reports associated with the selected medicine.
- Number of distinct reported reactions.
- Serious-flag and death-flag counts.
- Most frequently reported reactions.
- Report counts by country.
- A report timeline when dates are available.
- Drug–reaction pair screening results.
- Supporting report records.
- CSV export of the selected medicine's reports.

This module helps users inspect the reporting context of an individual medicine.

### 3.6 Reaction Explorer

The Reaction Explorer starts with a selected reported reaction and examines its reporting patterns.

Features include:

- Total reports containing the selected reaction.
- Number of medicines associated with those reports.
- Serious-flag report counts.
- Medicines most frequently reported with that reaction.
- Pair-level screening statistics.
- Matching report records.
- CSV export of reaction evidence.

The associations displayed are based on the loaded reports and do not prove that any listed medicine caused the reaction.

### 3.7 Time & Geography

This module explores when and where reports appear in the dataset.

Features include:

- Report volume over time.
- Monthly, quarterly, or yearly aggregation.
- Most represented reporting countries.
- A country-by-medicine report-count matrix.

The charts describe reporting patterns. They should not be interpreted as geographic disease prevalence, medicine usage, or comparative safety risk.

### 3.8 Investigation Queue

The Investigation Queue supports a basic, local investigation workflow.

Users can:

- Create an investigation manually.
- Add an investigation directly from the Signal Lab.
- Associate a medicine and reported reaction.
- Assign High, Medium, or Low priority.
- Record analyst notes and next steps.
- Track Open, In review, and Closed statuses.
- Edit or delete investigation records.
- Export the investigation list to CSV.

Investigation records are stored in a local SQLite database:

`data/pharmalens_investigations.db`

This database is created automatically when needed. It is separate from the adverse-event CSV.

### 3.9 Safety Copilot

The Safety Copilot answers supported questions using the currently loaded dataset and predefined Python rules.

Supported question areas include:

- Which medicines have the most reports?
- What are the most frequently reported reactions?
- How many reports have serious or death flags?
- Which drug–reaction pairs are the strongest screening leads?
- Which countries have the most reports?
- How do report counts change over time?
- What reactions are reported with a selected medicine?
- Which medicines are reported with a selected reaction?
- How ROR and confidence intervals work.
- What the dataset can and cannot tell us.

The Copilot can display tables, statistics, explanations, and charts for supported questions.

**Technical clarification:** This is a rule-based, dataset-backed assistant, not a general-purpose generative AI model. It does not browse medical literature, independently verify clinical evidence, or determine whether a medicine caused an adverse event.

### 3.10 Data Quality & Coverage

This module helps users understand the structure and completeness of the loaded dataset.

Features include:

- Total CSV rows.
- Field completeness percentages.
- Missing or blank field counts.
- Detected source-column mappings.
- Duplicate report-ID checks when a recognized identifier exists.
- A preview of the loaded data.
- CSV export of cleaned analysis fields.

The application attempts to recognize common aliases for medicine names, reactions, dates, countries, seriousness indicators, death indicators, age, sex, and report identifiers.

If required medicine or reaction columns cannot be identified, the application displays an error instead of continuing with invalid analysis.

### 3.11 Methods and Limitations

The application includes a Methods & Limitations module explaining the analytical approach and interpretation constraints.

Refer to this module when reviewing the assumptions behind the charts and screening results.

---

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and data processing |
| Streamlit | Web interface, navigation, forms, and interactive controls |
| Pandas | CSV loading, cleaning, grouping, and tabular analysis |
| NumPy | Numerical operations and statistical calculations |
| Plotly Express | Interactive charts and visualizations |
| Plotly Graph Objects | Additional chart customization |
| SQLite | Local persistence for investigation records |
| HTML and CSS | Custom dark theme, layout, spacing, and styling |
| Git and GitHub | Version control and project hosting |

No separate React frontend or FastAPI backend is required for this current Streamlit version.

The wellness recommendations and Safety Copilot logic are implemented using Python rules. The project does not require a hosted language model API to run these features.

---

## 5. Project Folder Structure

The repository should use the following structure:

```text
PharmaLens-AI/
│
├── app.py
│   └── Main Streamlit application.
│
├── requirements.txt
│   └── Python package dependencies.
│
├── README.md
│   └── Project documentation and setup instructions.
│
├── .gitignore
│   └── Excludes virtual environments, secrets,
│       generated files, and local database files.
│
└── data/
    ├── adverse_events.csv
    │   └── Input adverse-event dataset.
    │
    └── pharmalens_investigations.db
        └── Local SQLite database created by the app.
```

The SQLite database is generated at runtime and does not need to be committed to GitHub.

---

## 6. Installation and Setup on macOS

### Prerequisites

Install Python 3 and Git. The project also requires an internet connection during the initial package installation.

### Step 1: Clone the repository

Replace the example URL with the URL of your actual GitHub repository.

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd PharmaLens-AI
```

### Step 2: Check the project files

```bash
ls
```

Confirm that `app.py`, `requirements.txt`, `README.md`, and the `data` directory are present.

### Step 3: Place the dataset

The required location is:

```text
PharmaLens-AI/data/adverse_events.csv
```

If you already have the prepared CSV elsewhere, copy it into the `data` folder.

For example, if the existing file is in your earlier project directory:

```bash
mkdir -p data
cp ~/Desktop/Projects/PharmaLens-AI/data/adverse_events.csv data/adverse_events.csv
```

Adjust the source path if your existing project is stored elsewhere.

### Step 4: Create a virtual environment

```bash
python3 -m venv .venv
```

### Step 5: Activate the environment

```bash
source .venv/bin/activate
```

### Step 6: Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 7: Run the application

```bash
python -m streamlit run app.py
```

Streamlit will print a local URL in the terminal, normally:

`http://localhost:8501`

Open that URL in your browser.

To stop the application, press `Control + C` in the terminal.

### Running the project again later

Open Terminal, navigate to the repository, activate the existing environment, and start Streamlit:

```bash
cd PharmaLens-AI
source .venv/bin/activate
python -m streamlit run app.py
```

Do not recreate the virtual environment every time.

---

## 7. Dependencies

The current `requirements.txt` contains:

```text
streamlit>=1.39
pandas>=2.2
numpy>=1.26
plotly>=5.24
```

These packages support the Streamlit interface, data processing, numerical calculations, and interactive visualizations.

---

## 8. Data Processing Workflow

The application's main workflow is:

1. Load `data/adverse_events.csv`.
2. Normalize column names and detect recognized column aliases.
3. Create standardized analysis fields for medicine, reaction, date, country, seriousness, death, age, sex, and report ID where available.
4. Identify rows containing both a recognized medicine and reaction.
5. Calculate summary statistics and report-count distributions.
6. Construct medicine–reaction contingency tables.
7. Calculate exploratory ROR values, confidence intervals, and screening labels.
8. Display interactive dashboards, tables, and charts.
9. Allow users to inspect supporting records and export selected results.
10. Store investigation notes and workflow status in SQLite.

The code preserves loaded rows for data-quality inspection, while some analytics exclude rows without an identifiable medicine or reaction.

---

## 9. Known Limitations and Responsible Use

PharmaLens AI is a research and learning project. Its outputs must be interpreted carefully.

- **No causal proof:** A report cannot independently establish that a medicine caused a reaction.
- **No incidence calculation:** The number of exposed patients is not available from report counts alone.
- **No absolute-risk estimate:** ROR is a reporting disproportionality statistic, not the probability that a patient will experience an event.
- **Exploratory screening only:** The implemented ROR thresholds are not a validated regulatory signal-detection system.
- **Data quality matters:** Missing fields, duplicates, inconsistent values, and source coverage can affect results.
- **Seriousness flags depend on the input:** If the CSV lacks suitable seriousness or outcome fields, the app cannot reliably reconstruct them.
- **Rule-based Copilot:** It answers supported question types using predefined logic, not independent clinical reasoning or live medical literature.
- **General wellness only:** Lifestyle recommendations are not diagnoses, biological-age calculations, or individualized medical treatment.
- **Local persistence:** Investigation records are stored in a local SQLite database. They are not automatically synchronized across different computers.

Do not use this application as a substitute for medical advice, clinical assessment, or formal pharmacovigilance review.

---

## 10. Future Improvements

Potential future enhancements include:

- More robust duplicate-case handling and data validation.
- Clearer dataset provenance and release tracking.
- Additional statistical screening methods with documented assumptions.
- Improved filtering and report-level search.
- Investigation export formats suitable for research documentation.
- Automated tests for data parsing, statistical calculations, and navigation.
- Deployment with appropriate privacy, access-control, and data-governance safeguards.

These are possible future enhancements, not claims that they are already implemented.

---

## 11. Author and Project Purpose

**Project:** PharmaLens AI  
**Category:** Data Analytics, Python, Health Intelligence, and Pharmacovigilance  
**Interface:** Streamlit  
**Purpose:** Educational research and exploratory adverse-event report analysis

This project demonstrates how data processing, statistical screening, interactive visualization, and simple workflow management can be combined to explore medicine-related safety-report patterns transparently.

---

## Disclaimer

PharmaLens AI is an educational research prototype. It is not a medical device, does not provide medical advice, and is not validated for clinical or regulatory decisions. All findings require appropriate interpretation and independent expert review.

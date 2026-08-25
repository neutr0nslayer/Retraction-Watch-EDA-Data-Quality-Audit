"""
========================================================================================
Comprehensive Exploratory Data Analysis & Data Quality Audit: Retraction Watch Dataset 
Exploratory Data Analysis and Data Quality Audit of The Retraction Watch Database: 
Global Patterns and In-Depth Case Study on Bangladesh.
========================================================================================
This script performs a full end-to-end Exploratory Data Analysis (EDA), Data Quality
Assessment, and automated artifact generation for the Retraction Watch Database integrated
with national publication indicators from SCImago Journal & Country Rank (1996-2025).

Converted from retraction_watch_eda.ipynb with a centralized Global Variable / Config Section.
"""
#! NOTE FROM THE AUTHOR: This script was converted from a the original ipynb file using anti-gravity. 
import os
import re
import warnings
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ========================================================================================
#   GLOBAL VARIABLES & CONFIGURATION SECTION
# ========================================================================================

# --- 1. File Paths & Directory Configuration ---
DATA_RETRACTION_WATCH_CSV = "retraction_watch.csv"
DATA_SCIMAGO_EXCEL = "scimagojr country rank 1996-2025.xlsx"

FIG_DIR = "figures"
TBL_DIR = "tables"
MASTER_EXCEL_FILENAME = "all_retraction_watch_eda_tables.xlsx"

# --- 2. Visualization & Styling Settings ---
FIGURE_DPI = 300
PLOT_STYLE = "seaborn-v0_8-whitegrid"
DEFAULT_FIGSIZE = (12, 6)
FONT_SIZE = 10
XTICK_LABELSIZE = 9.5
YTICK_LABELSIZE = 9.5
LABEL_WRAP_WIDTH = 32
SHOW_PLOTS = False  # Set to True to display interactive GUI plot windows

# Color Palettes & Brand Colors
COLOR_BD = "#006a4e"          # Bangladesh Primary Emerald Green
COLOR_GLOBAL = "#2b5c8f"      # Global Baseline Slate Blue
COLOR_CHINA = "#d95f02"       # China Accent Orange
COLOR_ALERT = "#c0392b"       # Alert Crimson
COLOR_ACCENT = "#ff7f0e"      # Warm Accent
COLOR_NEUTRAL = "#7f7f7f"     # Neutral Grey

PALETTE_REASONS = "viridis"
PALETTE_COUNTRIES = "rocket"
PALETTE_PUBLISHERS = "mako"
PALETTE_JOURNALS = "crest"
PALETTE_SECTORS = ["#d95f02", "#006a4e", "#2b5c8f", "#7f7f7f"]
PALETTE_LAG_STACKED = ["#2ca02c", "#ff7f0e", "#d62728", "#9467bd"]

# --- 3. Analysis Ranges & Thresholds ---
YEAR_RANGE_GLOBAL = (1995, 2026)
YEAR_RANGE_ANNUAL_COMP = (2000, 2026)
YEAR_RANGE_HEATMAP_ORIG = (2012, 2025)
YEAR_RANGE_HEATMAP_RET = (2012, 2026)
YEAR_RANGE_COHORT = (2012, 2024)
YEAR_RANGE_RECENT_SHARE = 2012

MIN_SCIMAGO_DOCUMENTS = 1000  # Minimum documents published to calculate country retraction rate rank

# Top N Display Limits
TOP_N_REASONS = 15
TOP_N_COUNTRIES = 15
TOP_N_PUBLISHERS = 10
TOP_N_JOURNALS = 10
TOP_N_BD_UNIVERSITIES = 12
TOP_N_BD_REASONS = 12
TOP_N_BD_SUBJECTS = 10
TOP_N_BD_PUBLISHERS = 10
TOP_N_FOREIGN_PARTNERS = 12
TOP_N_REPEAT_AUTHORS = 12
TOP_N_BD_JOURNALS = 10

# --- 4. Categorical Placeholders & Metadata Defaults ---
PLACEHOLDER_COUNTRY = "Unknown"
PLACEHOLDER_INSTITUTION = "Unknown"
PLACEHOLDER_REASON = "Unspecified"
PLACEHOLDER_SUBJECT = "Unspecified"
PLACEHOLDER_NOTES = "No Notes"
PLACEHOLDER_URLS = "N/A"
PLACEHOLDER_IDENTIFIERS = "N/A"

# Core Identifier Columns to fill with N/A
IDENTIFIER_COLS = ["OriginalPaperDOI", "RetractionDOI", "OriginalPaperPubMedID", "RetractionPubMedID"]

# --- 5. Regex Patterns for Classification & Normalization ---
BD_UNIV_FILTER_REGEX = (
    r"Daffodil|North South|Jahangirnagar|United International|University of Dhaka|Dhaka|"
    r"Mawlana Bhashani|University of Chittagong|Chittagong|Jashore University|Begum Rokeya|"
    r"University of Rajshahi|Rajshahi|Noakhali Science|BGC Trust|Southeast University|"
    r"Bangladesh University|BUET|CUET|RUET|KUET|SUST|IUT|BUBT|BRAC|East West|Independent|"
    r"Stamford|Varendra|City University|Manarat|Ahsanullah|Primeasia|Sonargaon|Northern University"
)

PRIVATE_UNIV_REGEX = (
    r"Daffodil|North South|United International|BUBT|BRAC|East West|Independent|Stamford|"
    r"Varendra|City University|Manarat|Ahsanullah|Primeasia|Sonargaon|Northern University|"
    r"American International|Green University|Southeast University|World University|"
    r"Prime University|University of Liberal Arts|ULAB|Presidency|State University|"
    r"Eastern University|Dhaka International University|Leading University|Sylhet International|"
    r"International Islamic University Chittagong|IIUC|BGC Trust"
)

PUBLIC_UNIV_REGEX = (
    r"University of Dhaka|Dhaka University|Jahangirnagar|BUET|CUET|RUET|KUET|SUST|IUT|"
    r"Mawlana Bhashani|MBSTU|University of Chittagong|Chittagong University|University of Rajshahi|"
    r"Rajshahi University|Noakhali Science|NSTU|Jashore University|JUST|Begum Rokeya|BRUR|"
    r"Khulna University|Comilla University|Barisal University|Bangladesh Agricultural|BAU|"
    r"Sher-e-Bangla|BSMRMU|BSMMU|National Institute of|Medical College|Dhaka Medical|"
    r"Sir Salimullah|Chittagong Medical|Rajshahi Medical"
)

# ========================================================================================
#   HELPER FUNCTIONS
# ========================================================================================

def setup_environment():
    """Initializes output directories and matplotlib plotting styles."""
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(TBL_DIR, exist_ok=True)
    warnings.filterwarnings("ignore")
    plt.style.use(PLOT_STYLE if PLOT_STYLE in plt.style.available else "default")
    plt.rcParams["figure.figsize"] = DEFAULT_FIGSIZE
    plt.rcParams["font.size"] = FONT_SIZE
    plt.rcParams["ytick.labelsize"] = YTICK_LABELSIZE
    plt.rcParams["xtick.labelsize"] = XTICK_LABELSIZE
    print(f"Environment configured successfully. Output directories ready: '{FIG_DIR}/' and '{TBL_DIR}/'.")


def wrap_lbl(label, width=LABEL_WRAP_WIDTH):
    """Wraps long text labels cleanly for plot axes."""
    if not label or pd.isna(label):
        return ""
    s = str(label).replace("/", "/ ").replace("  ", " ")
    return "\n".join(textwrap.wrap(s, width=width))


def categorize_lag(years):
    """Categorizes retraction delay into standard duration bins."""
    if pd.isna(years) or years < 0:
        return np.nan
    elif years < 1:
        return "< 1 Year"
    elif years <= 3:
        return "1 to 3 Years"
    elif years <= 5:
        return "3 to 5 Years"
    else:
        return "> 5 Years"


def categorize_lag_short(years):
    """Categorizes retraction delay into standard duration bins with short labels."""
    if pd.isna(years) or years < 0:
        return np.nan
    elif years < 1:
        return "< 1 Year"
    elif years <= 3:
        return "1-3 Years"
    elif years <= 5:
        return "3-5 Years"
    else:
        return "> 5 Years"


def normalize_bd_university(inst):
    """Normalizes Bangladeshi university affiliations by stripping departments and addresses."""
    if not isinstance(inst, str):
        return inst
    inst_clean = re.sub(
        r",?\s*(?:P\.?O\.?\s*Box\s*\d+|Bashundhara|Savaria|Savar|Dhaka|Chittagong|Rajshahi|Sylhet|Khulna|Rangpur|Mymensingh|Gazipur|Barisal|\d{4,6})*,?\s*Bangladesh$",
        "",
        inst,
        flags=re.I,
    ).strip()
    parts = [p.strip() for p in inst_clean.split(",") if p.strip()]

    for p in reversed(parts):
        if re.search(
            r"University|BUET|CUET|RUET|KUET|SUST|DU|IUT|College|Institute of|Medical College",
            p,
            re.I,
        ) and not re.search(
            r"Department|Dept|School of|Faculty of|Laboratory of|Centre for|Center for",
            p,
            re.I,
        ):
            clean_name = re.sub(r"^\d{4,6}\s*", "", p).strip()
            clean_name = re.sub(r"\s*\(\s*BUBT\s*\)", " (BUBT)", clean_name, flags=re.I)
            clean_name = re.sub(r"\s*\(\s*DU\s*\)", "", clean_name, flags=re.I)
            return clean_name

    for p in reversed(parts):
        if re.search(
            r"University|BUET|CUET|RUET|KUET|SUST|IUT|BUBT|BRAC|Daffodil|North South|Jahangirnagar",
            p,
            re.I,
        ):
            return p.strip()

    return parts[-1] if parts else inst


def check_intl_collab(c_str):
    """Classifies paper into Solely Domestic vs International Collaboration."""
    if not isinstance(c_str, str):
        return "Unknown"
    countries = [c.strip() for c in c_str.split(";") if c.strip()]
    bd_present = any("bangladesh" in c.lower() for c in countries)
    foreign_present = any("bangladesh" not in c.lower() for c in countries)
    if bd_present and foreign_present:
        return "International Collaboration"
    elif bd_present and not foreign_present:
        return "Solely Domestic (Bangladesh Only)"
    else:
        return "Other / BD Affiliation"


def count_authors(a_str):
    """Counts number of co-authors listed in semicolon-separated author string."""
    if not isinstance(a_str, str) or not a_str.strip():
        return 0
    return len([a for a in a_str.split(";") if a.strip()])


def classify_paper_sector(inst_str):
    """Classifies Bangladeshi institutional affiliation into Public, Private, or Joint."""
    if not isinstance(inst_str, str):
        return "Unclassified"
    has_priv = bool(re.search(PRIVATE_UNIV_REGEX, inst_str, re.I))
    has_pub = bool(re.search(PUBLIC_UNIV_REGEX, inst_str, re.I))
    if has_priv and has_pub:
        return "Joint Public-Private"
    elif has_priv:
        return "Private Universities"
    elif has_pub:
        return "Public Universities / Medical"
    else:
        return "Other / Unclassified"


def safe_display(df_or_obj, title=None):
    """Prints dataframe or object formatted clearly across CLI and Jupyter environments."""
    if title:
        print(f"\n--- {title} ---")
    try:
        from IPython.display import display
        display(df_or_obj)
    except Exception:
        if isinstance(df_or_obj, pd.DataFrame):
            print(df_or_obj.to_string())
        else:
            print(df_or_obj)


def save_and_show_plot(fig_path):
    """Saves current matplotlib figure to disk and optionally displays interactive window."""
    plt.savefig(fig_path, dpi=FIGURE_DPI, bbox_inches="tight")
    print(f"  [Saved Figure] -> {fig_path}")
    if SHOW_PLOTS:
        plt.show()
    plt.close()


# ========================================================================================
#   MAIN EDA EXECUTION PIPELINE
# ========================================================================================

def run_retraction_watch_eda():
    """Executes the full Retraction Watch EDA and analytical export workflow."""
    setup_environment()

    # ------------------------------------------------------------------------------------
    # SECTION 1: Data Loading & Initial Overview
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 1: Data Loading & Initial Overview")
    print("==================================================================")
    df = pd.read_csv(DATA_RETRACTION_WATCH_CSV)
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed|^:\s*$|^$")]
    print(f"Dataset Shape: {df.shape[0]:,} rows x {df.shape[1]} columns\n")
    print("--- Column Data Types & Non-Null Information ---")
    df.info()

    # ------------------------------------------------------------------------------------
    # SECTION 2: Data Quality & Hygiene Assessment
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 2: Data Quality & Hygiene Assessment")
    print("==================================================================")
    # Missing values analysis
    null_counts = df.isnull().sum()
    null_pct = (df.isnull().sum() / len(df)) * 100

    missing_df = pd.DataFrame({
        "Attribute": null_counts.index,
        "Missing Count": null_counts.values,
        "Missing Percentage (%)": null_pct.values.round(2)
    }).sort_values(by="Missing Count", ascending=False).reset_index(drop=True)

    missing_csv_path = os.path.join(TBL_DIR, "01_missing_values_breakdown.csv")
    missing_df.to_csv(missing_csv_path, index=False)
    safe_display(missing_df, "Missing Value Breakdown")

    # Visualize Missing Values
    plt.figure(figsize=(14, 6))
    bars = sns.barplot(x=missing_df["Attribute"], y=missing_df["Missing Percentage (%)"], palette="Blues_r")
    plt.xticks(rotation=45, ha="right")
    plt.title("Percentage of Missing Values per Attribute", fontsize=14, fontweight="bold")
    plt.ylabel("Missing Percentage (%)")
    plt.xlabel("Attributes")
    for p in bars.patches:
        if p.get_height() > 0:
            bars.annotate(
                f"{p.get_height():.1f}%",
                (p.get_x() + p.get_width() / 2.0, p.get_height()),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 3),
                textcoords="offset points",
            )
    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "01_missing_values_percentage.png"))

    # Duplication checks
    full_dup_count = df.duplicated().sum()
    id_dup_count = df.duplicated(subset=["Record ID"]).sum() if "Record ID" in df.columns else 0
    title_dup_count = df.duplicated(subset=["Title"]).sum() if "Title" in df.columns else 0
    doi_dup_count = (
        df.dropna(subset=["OriginalPaperDOI"]).duplicated(subset=["OriginalPaperDOI"]).sum()
        if "OriginalPaperDOI" in df.columns
        else 0
    )

    dup_summary = pd.DataFrame({
        "Duplication Metric": [
            "Exact Full Row Duplicates",
            "Duplicate Record IDs",
            "Duplicate Article Titles",
            "Duplicate Original Paper DOIs",
        ],
        "Duplicate Count": [full_dup_count, id_dup_count, title_dup_count, doi_dup_count],
        "Percentage (%)": [
            round((full_dup_count / len(df)) * 100, 4),
            round((id_dup_count / len(df)) * 100, 4),
            round((title_dup_count / len(df)) * 100, 4),
            round((doi_dup_count / len(df)) * 100, 4),
        ],
    })
    dup_summary.to_csv(os.path.join(TBL_DIR, "02_duplication_analysis_summary.csv"), index=False)
    safe_display(dup_summary, "Duplication Analysis Summary")

    # Data Remediation & Cleaning Strategy
    initial_rows = df.shape[0]
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed|^:\s*$|^$")]
    df = df.drop_duplicates()
    after_dup_rows = df.shape[0]
    dropped_dups = initial_rows - after_dup_rows

    df = df.dropna(subset=["Record ID", "Title"])
    cleaned_rows = df.shape[0]
    dropped_null_keys = after_dup_rows - cleaned_rows

    df["Country"] = df["Country"].fillna(PLACEHOLDER_COUNTRY)
    df["Institution"] = df["Institution"].fillna(PLACEHOLDER_INSTITUTION)
    df["Reason"] = df["Reason"].fillna(PLACEHOLDER_REASON)
    df["Subject"] = df["Subject"].fillna(PLACEHOLDER_SUBJECT)
    df["Notes"] = df["Notes"].fillna(PLACEHOLDER_NOTES)
    df["URLS"] = df["URLS"].fillna(PLACEHOLDER_URLS)

    for col in IDENTIFIER_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(PLACEHOLDER_IDENTIFIERS)

    cleaning_summary = pd.DataFrame({
        "Remediation Step": [
            "Initial Raw Records",
            "Full Row Duplicates Dropped",
            "Missing Primary Key Records Dropped",
            "Final Clean Dataset Records",
        ],
        "Count": [initial_rows, dropped_dups, dropped_null_keys, df.shape[0]],
    })
    cleaning_summary.to_csv(os.path.join(TBL_DIR, "03_data_cleaning_remediation_summary.csv"), index=False)

    print("\n=== DATA CLEANING & REMEDIATION SUMMARY ===")
    print(f"Initial Raw Rows:            {initial_rows:,}")
    print(f"Full Row Duplicates Dropped: {dropped_dups:,}")
    print(f"Missing Key Rows Dropped:   {dropped_null_keys:,}")
    print(f"Final Clean Dataset Shape:  {df.shape[0]:,} rows x {df.shape[1]} columns\n")

    # ------------------------------------------------------------------------------------
    # SECTION 3: Feature Engineering & Date Normalization
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 3: Feature Engineering & Date Normalization")
    print("==================================================================")
    df["RetractionDate_dt"] = pd.to_datetime(df["RetractionDate"], errors="coerce")
    df["OriginalPaperDate_dt"] = pd.to_datetime(df["OriginalPaperDate"], errors="coerce")

    df["Time_To_Retraction_Days"] = (df["RetractionDate_dt"] - df["OriginalPaperDate_dt"]).dt.days
    df["Time_To_Retraction_Years"] = df["Time_To_Retraction_Days"] / 365.25

    df["RetractionYear"] = df["RetractionDate_dt"].dt.year
    df["OriginalYear"] = df["OriginalPaperDate_dt"].dt.year

    eng_stats = (
        df[["Time_To_Retraction_Days", "Time_To_Retraction_Years", "RetractionYear", "OriginalYear"]]
        .describe()
        .round(2)
    )
    eng_stats.to_csv(os.path.join(TBL_DIR, "04_engineered_features_summary_stats.csv"))
    safe_display(eng_stats, "Engineered Features Summary Statistics")

    # ------------------------------------------------------------------------------------
    # SECTION 4: Distribution Analysis: Time to Retraction
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 4: Distribution Analysis: Time to Retraction")
    print("==================================================================")
    valid_delay = df[df["Time_To_Retraction_Days"].notnull() & (df["Time_To_Retraction_Days"] >= 0)]

    fig, axes = plt.subplots(2, 1, figsize=(12, 9.5))
    sns.histplot(valid_delay["Time_To_Retraction_Years"], bins=50, kde=True, ax=axes[0], color="teal")
    axes[0].set_title("Distribution of Time to Retraction (Years)", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Delay (Years)")
    axes[0].set_ylabel("Paper Count")

    sns.boxplot(x=valid_delay["Time_To_Retraction_Years"], ax=axes[1], color="lightcoral")
    axes[1].set_title("Box Plot of Retraction Delay (Years)", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Delay (Years)")

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "02_time_to_retraction_distribution.png"))

    delay_quantiles = pd.DataFrame({
        "Metric": [
            "Total Valid Date Pairs Evaluated",
            "Median Time to Retraction (Days)",
            "Median Time to Retraction (Years)",
            "Mean Time to Retraction (Days)",
            "Mean Time to Retraction (Years)",
            "25th Percentile (Days)",
            "25th Percentile (Years)",
            "75th Percentile (Days)",
            "75th Percentile (Years)",
        ],
        "Value": [
            f"{len(valid_delay):,}",
            f"{valid_delay['Time_To_Retraction_Days'].median():.0f}",
            f"{valid_delay['Time_To_Retraction_Years'].median():.2f}",
            f"{valid_delay['Time_To_Retraction_Days'].mean():.0f}",
            f"{valid_delay['Time_To_Retraction_Years'].mean():.2f}",
            f"{valid_delay['Time_To_Retraction_Days'].quantile(0.25):.0f}",
            f"{valid_delay['Time_To_Retraction_Years'].quantile(0.25):.2f}",
            f"{valid_delay['Time_To_Retraction_Days'].quantile(0.75):.0f}",
            f"{valid_delay['Time_To_Retraction_Years'].quantile(0.75):.2f}",
        ],
    })
    delay_quantiles.to_csv(os.path.join(TBL_DIR, "05_retraction_delay_quantiles.csv"), index=False)
    safe_display(delay_quantiles, "Retraction Delay Quantiles & Key Metrics")

    # ------------------------------------------------------------------------------------
    # SECTION 5: Temporal Trends & Comparative Analysis
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 5: Temporal Trends & Comparative Analysis")
    print("==================================================================")
    fig, axes = plt.subplots(2, 1, figsize=(13, 12))

    # 1. Annual Line Plot Comparison
    ret_by_yr = df[df["RetractionYear"].between(*YEAR_RANGE_GLOBAL)]["RetractionYear"].value_counts().sort_index()
    orig_by_yr = df[df["OriginalYear"].between(*YEAR_RANGE_GLOBAL)]["OriginalYear"].value_counts().sort_index()

    axes[0].plot(
        ret_by_yr.index,
        ret_by_yr.values,
        marker="o",
        color="#b22222",
        linewidth=2.5,
        label="Retractions Executed in Year",
    )
    axes[0].plot(
        orig_by_yr.index,
        orig_by_yr.values,
        marker="s",
        color="#1f77b4",
        linewidth=2.5,
        linestyle="--",
        label="Original Papers Published in Year",
    )
    axes[0].set_title(
        "Annual Trajectory: Retractions Executed vs. Original Paper Publication Year",
        fontsize=13,
        fontweight="bold",
    )
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Number of Papers")
    axes[0].legend(fontsize=11)
    axes[0].grid(True, linestyle=":", alpha=0.7)

    # 2. 2D Heatmap Matrix
    subset = df[
        df["OriginalYear"].between(*YEAR_RANGE_HEATMAP_ORIG)
        & df["RetractionYear"].between(*YEAR_RANGE_HEATMAP_RET)
    ]
    matrix = pd.crosstab(subset["OriginalYear"].astype(int), subset["RetractionYear"].astype(int))

    sns.heatmap(
        matrix,
        cmap="YlOrRd",
        annot=True,
        fmt="d",
        ax=axes[1],
        cbar_kws={"label": "Retraction Count"},
        annot_kws={"size": 9},
    )
    axes[1].set_title(
        "Retraction Matrix Heatmap: Original Publication Year vs. Retraction Execution Year (2012–2026)",
        fontsize=13,
        fontweight="bold",
    )
    axes[1].set_xlabel("Retraction Execution Year")
    axes[1].set_ylabel("Original Publication Year")

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "03_temporal_trajectory_and_matrix_heatmap.png"))

    annual_trends_df = pd.DataFrame({
        "Year": ret_by_yr.index,
        "Retractions_Executed": ret_by_yr.values,
        "Original_Papers_Published": [orig_by_yr.get(y, 0) for y in ret_by_yr.index],
    })
    annual_trends_df.to_csv(os.path.join(TBL_DIR, "06_annual_publication_vs_retraction_trends.csv"), index=False)
    matrix.to_csv(os.path.join(TBL_DIR, "07_retraction_matrix_2012_2026.csv"))

    # Retraction Delay Cohort Analysis
    df["Retraction_Lag_Category"] = df["Time_To_Retraction_Years"].apply(categorize_lag)
    cohort_df = df[
        df["OriginalYear"].between(*YEAR_RANGE_COHORT) & df["Retraction_Lag_Category"].notnull()
    ]
    cohort_counts = pd.crosstab(cohort_df["OriginalYear"].astype(int), cohort_df["Retraction_Lag_Category"])
    category_order = ["< 1 Year", "1 to 3 Years", "3 to 5 Years", "> 5 Years"]
    cohort_counts = cohort_counts[[c for c in category_order if c in cohort_counts.columns]]

    plt.figure(figsize=(13, 6.5))
    cohort_counts.plot(kind="bar", stacked=True, color=PALETTE_LAG_STACKED, figsize=(13, 6.5), width=0.75)
    plt.title(
        "Retraction Delay Categories by Original Publication Cohort (2012–2024)",
        fontsize=13,
        fontweight="bold",
    )
    plt.xlabel("Original Publication Year (Cohort)")
    plt.ylabel("Number of Retracted Papers")
    plt.legend(title="Retraction Delay", fontsize=10.5, title_fontsize=11)
    plt.xticks(rotation=0)
    plt.grid(axis="y", linestyle=":", alpha=0.7)
    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "04_cohort_retraction_delay_breakdown.png"))
    cohort_counts.to_csv(os.path.join(TBL_DIR, "08_cohort_retraction_delay_counts.csv"))

    # ------------------------------------------------------------------------------------
    # SECTION 6: Categorical & Multi-Valued Attributes Analysis
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 6: Categorical & Multi-Valued Attributes Analysis")
    print("==================================================================")
    # Explode Reason column
    reasons_exploded = df["Reason"].dropna().str.split(";").explode().str.strip()
    reasons_exploded = reasons_exploded[reasons_exploded != ""]
    top_reasons = reasons_exploded.value_counts().head(TOP_N_REASONS)

    plt.figure(figsize=(12, 9))
    y_labels = [wrap_lbl(l, width=LABEL_WRAP_WIDTH) for l in top_reasons.index]
    bars = sns.barplot(x=top_reasons.values, y=y_labels, palette=PALETTE_REASONS)
    plt.title(f"Top {TOP_N_REASONS} Primary Reasons for Paper Retractions", fontsize=13, fontweight="bold")
    plt.xlabel("Total Occurrences")
    plt.ylabel("Retraction Reason")
    for p in bars.patches:
        bars.annotate(
            f"{int(p.get_width()):,}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )
    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "05_top_15_retraction_reasons.png"))

    top_reasons_df = top_reasons.reset_index()
    top_reasons_df.columns = ["Reason", "Occurrence_Count"]
    top_reasons_df.to_csv(os.path.join(TBL_DIR, "09_top_15_retraction_reasons.csv"), index=False)

    # Explode Country column
    country_exploded = df["Country"].dropna().str.split(";").explode().str.strip()
    country_exploded = country_exploded[country_exploded != ""]
    top_countries = country_exploded.value_counts().head(TOP_N_COUNTRIES)

    plt.figure(figsize=(12, 7.5))
    y_labels = [wrap_lbl(l, width=LABEL_WRAP_WIDTH) for l in top_countries.index]
    bars = sns.barplot(x=top_countries.values, y=y_labels, palette=PALETTE_COUNTRIES)
    plt.title(f"Top {TOP_N_COUNTRIES} Countries Associated with Retracted Publications", fontsize=13, fontweight="bold")
    plt.xlabel("Count of Retracted Publications")
    plt.ylabel("Country")
    for p in bars.patches:
        bars.annotate(
            f"{int(p.get_width()):,}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )
    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "06_top_15_countries_retraction_volume.png"))

    top_countries_df = top_countries.reset_index()
    top_countries_df.columns = ["Country", "Retraction_Count"]
    top_countries_df.to_csv(os.path.join(TBL_DIR, "10_top_15_countries_retraction_volume.csv"), index=False)

    # Country Analysis: SCImago Country Merging
    print("\n--- Merging SCImago Country Ranks & Retraction Rates ---")
    country_ret_counts = df[df["Country"] != PLACEHOLDER_COUNTRY]["Country"].str.split(";").explode().str.strip()
    country_ret_counts = country_ret_counts[country_ret_counts != ""]
    ret_df = country_ret_counts.value_counts().reset_index()
    ret_df.columns = ["Country", "Retracted_Papers"]

    scimago_df = pd.read_excel(DATA_SCIMAGO_EXCEL)
    country_merged = pd.merge(scimago_df, ret_df, on="Country", how="inner")
    country_merged["Retraction_Rate_%"] = (country_merged["Retracted_Papers"] / country_merged["Documents"]) * 100
    country_merged["Retractions_per_10k"] = (country_merged["Retracted_Papers"] / country_merged["Documents"]) * 10000

    min_pub_df = (
        country_merged[country_merged["Documents"] >= MIN_SCIMAGO_DOCUMENTS]
        .sort_values(by="Retractions_per_10k", ascending=False)
        .reset_index(drop=True)
    )
    min_pub_df["Rate_Rank"] = min_pub_df.index + 1

    bd_rank_idx = min_pub_df[min_pub_df["Country"] == "Bangladesh"].index[0]
    top_till_bd = min_pub_df.iloc[: bd_rank_idx + 1].copy()

    country_merged.head(TOP_N_COUNTRIES).to_csv(
        os.path.join(TBL_DIR, "11_top_15_publishing_nations_retraction_rates.csv"), index=False
    )
    top_till_bd.to_csv(os.path.join(TBL_DIR, "12_highest_retraction_rate_nations_till_bangladesh.csv"), index=False)
    country_merged.to_csv(os.path.join(TBL_DIR, "13_all_countries_scimago_merged_retraction_rates.csv"), index=False)

    fig, axes = plt.subplots(2, 1, figsize=(14, 14))
    top_pub_nations = country_merged.head(TOP_N_COUNTRIES)
    axes[0].bar(top_pub_nations["Country"], top_pub_nations["Retractions_per_10k"], color="#2b5c8f")
    axes[0].set_title(
        f"Retraction Rate (per 10,000 Papers) for Top {TOP_N_COUNTRIES} Publishing Nations",
        fontsize=13,
        fontweight="bold",
    )
    axes[0].set_ylabel("Retractions per 10,000 Papers")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].grid(axis="y", linestyle=":", alpha=0.7)
    for p in axes[0].patches:
        if p.get_height() > 0:
            axes[0].annotate(
                f"{p.get_height():.2f}",
                (p.get_x() + p.get_width() / 2.0, p.get_height()),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 3),
                textcoords="offset points",
            )

    bar_colors = [
        COLOR_BD if c == "Bangladesh" else COLOR_CHINA if c == "China" else COLOR_ALERT
        for c in top_till_bd["Country"]
    ]
    axes[1].bar(top_till_bd["Country"], top_till_bd["Retractions_per_10k"], color=bar_colors)
    axes[1].set_title("Highest Retraction Rates Globally: Rank 1 down to Bangladesh", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Country")
    axes[1].set_ylabel("Retractions per 10,000 Papers")
    axes[1].tick_params(axis="x", rotation=55)
    axes[1].grid(axis="y", linestyle=":", alpha=0.7)
    for p in axes[1].patches:
        if p.get_height() > 0:
            axes[1].annotate(
                f"{p.get_height():.1f}",
                (p.get_x() + p.get_width() / 2.0, p.get_height()),
                ha="center",
                va="bottom",
                fontsize=8.5,
                xytext=(0, 3),
                textcoords="offset points",
            )

    legend_handles = [
        mpatches.Patch(facecolor=COLOR_BD, label="Bangladesh Rank # 24 (Target Country: 23.4 / 10k)"),
        mpatches.Patch(facecolor=COLOR_CHINA, label="China Rank # 17 (High Output / High Rate: 28.8 / 10k)"),
        mpatches.Patch(facecolor=COLOR_ALERT, label="Other Top Retraction Rate Nations"),
    ]
    axes[1].legend(handles=legend_handles, loc="upper right", fontsize=10.5, frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "07_country_retraction_rates_and_bangladesh_rank.png"))

    # Top Publishers and Journals
    fig, axes = plt.subplots(2, 1, figsize=(12, 11))
    top_pub = df["Publisher"].value_counts().head(TOP_N_PUBLISHERS)
    pub_labels = [wrap_lbl(l, width=35) for l in top_pub.index]
    bars1 = sns.barplot(x=top_pub.values, y=pub_labels, ax=axes[0], palette=PALETTE_PUBLISHERS)
    axes[0].set_title(f"Top {TOP_N_PUBLISHERS} Publishers by Retraction Count", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Retraction Count")
    for p in bars1.patches:
        axes[0].annotate(
            f"{int(p.get_width()):,}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )

    top_jour = df["Journal"].value_counts().head(TOP_N_JOURNALS)
    jour_labels = [wrap_lbl(l, width=35) for l in top_jour.index]
    bars2 = sns.barplot(x=top_jour.values, y=jour_labels, ax=axes[1], palette=PALETTE_JOURNALS)
    axes[1].set_title(f"Top {TOP_N_JOURNALS} Journals by Retraction Count", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Retraction Count")
    for p in bars2.patches:
        axes[1].annotate(
            f"{int(p.get_width()):,}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "08_top_publishers_and_journals.png"))

    top_pub_df = top_pub.reset_index()
    top_pub_df.columns = ["Publisher", "Retraction_Count"]
    top_pub_df.to_csv(os.path.join(TBL_DIR, "14_top_10_publishers.csv"), index=False)

    top_jour_df = top_jour.reset_index()
    top_jour_df.columns = ["Journal", "Retraction_Count"]
    top_jour_df.to_csv(os.path.join(TBL_DIR, "15_top_10_journals.csv"), index=False)

    # Comparative Analysis: Paid (Paywalled) vs Open Access
    print("\n--- Comparative Analysis: Paid vs Open Access ---")
    valid_pw = df[
        df["Paywalled"].isin(["Yes", "No"])
        & df["Time_To_Retraction_Years"].notnull()
        & (df["Time_To_Retraction_Years"] >= 0)
    ].copy()

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    paywalled_counts = df["Paywalled"].value_counts()
    axes[0, 0].pie(
        paywalled_counts.values,
        labels=paywalled_counts.index,
        autopct="%1.1f%%",
        colors=["#2b5c8f", "#d95f02", "#7f7f7f"],
        startangle=90,
        wedgeprops=dict(width=0.4, edgecolor="w"),
    )
    axes[0, 0].set_title("Publication Access Model Distribution", fontsize=12, fontweight="bold")

    nature_counts = df["RetractionNature"].value_counts().head(8)
    sns.barplot(x=nature_counts.values, y=nature_counts.index, ax=axes[0, 1], palette="Set2")
    axes[0, 1].set_title("Action Type (Retraction Nature)", fontsize=12, fontweight="bold")
    axes[0, 1].set_xlabel("Count")

    sns.kdeplot(
        data=valid_pw[valid_pw["Paywalled"] == "Yes"]["Time_To_Retraction_Years"],
        ax=axes[1, 0],
        color="#d95f02",
        linewidth=2.5,
        label="Paid / Paywalled (Median: 0.52 yrs)",
    )
    sns.kdeplot(
        data=valid_pw[valid_pw["Paywalled"] == "No"]["Time_To_Retraction_Years"],
        ax=axes[1, 0],
        color="#2b5c8f",
        linewidth=2.5,
        linestyle="--",
        label="Open Access (Median: 1.38 yrs)",
    )
    axes[1, 0].set_title("Retraction Lag Density: Paid (Paywalled) vs. Open Access", fontsize=12, fontweight="bold")
    axes[1, 0].set_xlabel("Years from Publication to Retraction")
    axes[1, 0].set_ylabel("Density")
    axes[1, 0].set_xlim(0, 15)
    axes[1, 0].legend(fontsize=10.5)
    axes[1, 0].grid(True, linestyle=":", alpha=0.7)

    valid_pw["Lag_Category"] = valid_pw["Time_To_Retraction_Years"].apply(categorize_lag)
    lag_pct = pd.crosstab(valid_pw["Paywalled"], valid_pw["Lag_Category"], normalize="index") * 100
    lag_pct = lag_pct[[c for c in category_order if c in lag_pct.columns]]

    lag_pct.plot(kind="bar", stacked=True, ax=axes[1, 1], color=PALETTE_LAG_STACKED, width=0.55)
    axes[1, 1].set_title("Retraction Delay Breakdown by Access Model (%)", fontsize=12, fontweight="bold")
    axes[1, 1].set_xlabel("Paywalled Status")
    axes[1, 1].set_ylabel("Percentage of Retractions (%)")
    axes[1, 1].set_xticklabels(["Open Access (No)", "Paid (Yes)"], rotation=0)
    axes[1, 1].legend(title="Retraction Delay", fontsize=9.5)
    axes[1, 1].grid(axis="y", linestyle=":", alpha=0.7)

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "09_paywalled_vs_open_access_comparison.png"))

    pw_summary = (
        valid_pw.groupby("Paywalled")["Time_To_Retraction_Years"]
        .agg(
            Paper_Count="count",
            Median_Delay_Years="median",
            Mean_Delay_Years="mean",
            Pct_Retracted_Under_1yr=lambda x: (x < 1).mean() * 100,
        )
        .reset_index()
    )
    pw_summary.to_csv(os.path.join(TBL_DIR, "16_paywalled_vs_open_access_summary.csv"), index=False)
    lag_pct.to_csv(os.path.join(TBL_DIR, "17_paywalled_lag_category_percentages.csv"))
    safe_display(pw_summary, "Statistical Performance Summary: Paid vs Open Access")

    # ------------------------------------------------------------------------------------
    # SECTION 8: Deep-Dive Analysis: Focus on Bangladesh
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 8: Deep-Dive Analysis: Focus on Bangladesh")
    print("==================================================================")
    bd_df = df[
        df["Country"].fillna("").str.contains("Bangladesh", case=False)
        | df["Institution"].fillna("").str.contains("Bangladesh", case=False)
    ].copy()

    total_global = len(df)
    total_bd = len(bd_df)
    bd_pct = (total_bd / total_global) * 100

    sci_bd = scimago_df[scimago_df["Country"] == "Bangladesh"]
    bd_rank, bd_total_docs, bd_citable, bd_ret_rate, bd_ret_per_10k = 0, 0, 0, 0.0, 0.0
    if not sci_bd.empty:
        bd_rank = int(sci_bd["Rank"].values[0])
        bd_total_docs = int(sci_bd["Documents"].values[0])
        bd_citable = int(sci_bd["Citable documents"].values[0])
        bd_ret_rate = (total_bd / bd_total_docs) * 100
        bd_ret_per_10k = (total_bd / bd_total_docs) * 10000

    bd_metrics_df = pd.DataFrame({
        "Metric": [
            "Global Retraction Watch Database Total",
            "Bangladesh Retractions (RW Count)",
            "Bangladesh Share of Global Database (%)",
            "SCImago Global Country Rank (1996-2025)",
            "Total Published Documents (SCImago)",
            "Citable Documents (SCImago)",
            "Overall Retraction Rate (%)",
            "Retractions per 10,000 Published Papers",
        ],
        "Value": [
            f"{total_global:,}",
            f"{total_bd:,}",
            f"{bd_pct:.2f}%",
            f"Rank {bd_rank}",
            f"{bd_total_docs:,}",
            f"{bd_citable:,}",
            f"{bd_ret_rate:.4f}%",
            f"{bd_ret_per_10k:.2f}",
        ],
    })
    bd_metrics_df.to_csv(os.path.join(TBL_DIR, "18_bangladesh_publication_and_retraction_metrics.csv"), index=False)
    safe_display(bd_metrics_df, "Bangladesh Retraction & Publication Metrics")

    # Annual Retractions: Bangladesh vs Global
    g_ann = df[df["RetractionYear"].between(*YEAR_RANGE_ANNUAL_COMP)]["RetractionYear"].value_counts().sort_index()
    bd_ann = bd_df[bd_df["RetractionYear"].between(*YEAR_RANGE_ANNUAL_COMP)]["RetractionYear"].value_counts().sort_index()

    ann_comp = pd.DataFrame({
        "Year": g_ann.index.astype(int),
        "Global_Retractions": g_ann.values,
        "BD_Retractions": [bd_ann.get(y, 0) for y in g_ann.index],
    })
    ann_comp["BD_Share_of_Global_%"] = (ann_comp["BD_Retractions"] / ann_comp["Global_Retractions"]) * 100

    ann_comp.to_csv(os.path.join(TBL_DIR, "19_bangladesh_annual_retraction_trend.csv"), index=False)
    ann_comp.to_csv(os.path.join(TBL_DIR, "26_bangladesh_annual_vs_global_comparison.csv"), index=False)

    fig, axes = plt.subplots(3, 1, figsize=(14, 15))
    ax1 = axes[0]
    ax1_twin = ax1.twinx()

    line1 = ax1.plot(
        ann_comp["Year"],
        ann_comp["BD_Retractions"],
        color=COLOR_BD,
        marker="o",
        linewidth=2.5,
        label="Bangladesh Retractions (Left Axis)",
    )
    ax1.bar(ann_comp["Year"], ann_comp["BD_Retractions"], color=COLOR_BD, alpha=0.3, width=0.6)
    line2 = ax1_twin.plot(
        ann_comp["Year"],
        ann_comp["Global_Retractions"],
        color=COLOR_GLOBAL,
        marker="s",
        linestyle="--",
        linewidth=2,
        label="Global Retractions (Right Axis)",
    )

    ax1.set_title(
        "Annual Retraction Trajectory Comparison: Bangladesh vs. Global (2000–2026)",
        fontsize=13,
        fontweight="bold",
    )
    ax1.set_xlabel("Retraction Execution Year")
    ax1.set_ylabel("Bangladesh Retraction Count", color=COLOR_BD, fontweight="bold")
    ax1_twin.set_ylabel("Global Retraction Count", color=COLOR_GLOBAL, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", fontsize=10.5)

    recent_comp = ann_comp[ann_comp["Year"] >= YEAR_RANGE_RECENT_SHARE]
    bars_share = axes[1].bar(recent_comp["Year"], recent_comp["BD_Share_of_Global_%"], color="#d95f02", width=0.65)
    axes[1].set_title(
        "Bangladesh Share of Global Retractions (% of Annual Global Total, 2012–2026)",
        fontsize=13,
        fontweight="bold",
    )
    axes[1].set_xlabel("Retraction Year")
    axes[1].set_ylabel("Share of Global Retractions (%)")
    axes[1].grid(axis="y", linestyle=":", alpha=0.7)
    for p in bars_share.patches:
        if p.get_height() > 0:
            axes[1].annotate(
                f"{p.get_height():.2f}%",
                (p.get_x() + p.get_width() / 2.0, p.get_height()),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 3),
                textcoords="offset points",
            )

    bd_delay = bd_df[bd_df["Time_To_Retraction_Years"] >= 0]["Time_To_Retraction_Years"]
    global_delay = df[df["Time_To_Retraction_Years"] >= 0]["Time_To_Retraction_Years"]

    sns.kdeplot(
        bd_delay,
        ax=axes[2],
        label=f"Bangladesh (Median: {bd_delay.median():.2f} yrs, Mean: {bd_delay.mean():.2f} yrs)",
        color=COLOR_BD,
        linewidth=2.5,
    )
    sns.kdeplot(
        global_delay,
        ax=axes[2],
        label=f"Global (Median: {global_delay.median():.2f} yrs, Mean: {global_delay.mean():.2f} yrs)",
        color=COLOR_GLOBAL,
        linewidth=2,
        linestyle="--",
    )
    axes[2].set_title("Retraction Delay Distribution Density: Bangladesh vs. Global Baseline", fontsize=13, fontweight="bold")
    axes[2].set_xlabel("Years from Publication to Retraction")
    axes[2].set_ylabel("Density")
    axes[2].set_xlim(0, 12)
    axes[2].legend(fontsize=11)
    axes[2].grid(True, linestyle=":", alpha=0.7)

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "10_bangladesh_annual_trend_and_delay_kde.png"))

    # Bangladeshi Universities
    inst_exploded = bd_df["Institution"].dropna().str.split(";").explode().str.strip()
    cleaned_insts = inst_exploded.apply(normalize_bd_university)
    bd_universities = cleaned_insts[cleaned_insts.str.contains(BD_UNIV_FILTER_REGEX, case=False, regex=True)]
    bd_universities = bd_universities[
        ~bd_universities.str.strip().isin(["Bangladesh", "Dhaka", "Chittagong", "Rajshahi", "Sylhet", "Khulna"])
    ]
    top_bd_inst = bd_universities.value_counts().head(TOP_N_BD_UNIVERSITIES)

    plt.figure(figsize=(12, 7.5))
    inst_labels = [wrap_lbl(l, width=LABEL_WRAP_WIDTH) for l in top_bd_inst.index]
    bars = sns.barplot(x=top_bd_inst.values, y=inst_labels, palette="Greens_r")
    plt.title("Top Bangladeshi Universities (Schools & Departments Cumulated)", fontsize=13, fontweight="bold")
    plt.xlabel("Retraction Count")
    plt.ylabel("University / Higher Education Institution")
    for p in bars.patches:
        bars.annotate(
            f"{int(p.get_width())}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )
    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "11_bangladesh_top_universities.png"))

    top_bd_inst_df = top_bd_inst.reset_index()
    top_bd_inst_df.columns = ["University", "Retraction_Count"]
    top_bd_inst_df.to_csv(os.path.join(TBL_DIR, "20_bangladesh_top_universities.csv"), index=False)

    # Top Reasons for Bangladesh
    bd_reasons = bd_df["Reason"].dropna().str.split(";").explode().str.strip()
    bd_reasons = bd_reasons[bd_reasons != ""]
    top_bd_reasons = bd_reasons.value_counts().head(TOP_N_BD_REASONS)

    plt.figure(figsize=(12, 7.5))
    reason_labels = [wrap_lbl(l, width=LABEL_WRAP_WIDTH) for l in top_bd_reasons.index]
    bars = sns.barplot(x=top_bd_reasons.values, y=reason_labels, palette="YlGnBu_r")
    plt.title("Top Reasons for Paper Retractions in Bangladesh", fontsize=13, fontweight="bold")
    plt.xlabel("Occurrences")
    plt.ylabel("Retraction Reason")
    for p in bars.patches:
        bars.annotate(
            f"{int(p.get_width())}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )
    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "12_bangladesh_top_retraction_reasons.png"))

    top_bd_reasons_df = top_bd_reasons.reset_index()
    top_bd_reasons_df.columns = ["Reason", "Occurrence_Count"]
    top_bd_reasons_df.to_csv(os.path.join(TBL_DIR, "21_bangladesh_top_retraction_reasons.csv"), index=False)

    # Direct Benchmarking: Bangladesh vs Global Metrics
    g_reasons = df["Reason"].dropna().str.split(";").explode().str.strip().value_counts()
    bd_reasons_counts = bd_df["Reason"].dropna().str.split(";").explode().str.strip().value_counts()
    top_reasons_list = [r for r in bd_reasons_counts.head(10).index if r != ""]

    comp_reasons_df = pd.DataFrame({
        "Reason": [wrap_lbl(r, width=30) for r in top_reasons_list],
        "Bangladesh (%)": [(bd_reasons_counts[r] / len(bd_df)) * 100 for r in top_reasons_list],
        "Global (%)": [(g_reasons[r] / len(df)) * 100 for r in top_reasons_list],
    }).melt(id_vars="Reason", var_name="Scope", value_name="Prevalence (%)")

    df["Lag_Category"] = df["Time_To_Retraction_Years"].apply(categorize_lag_short)
    bd_df["Lag_Category"] = bd_df["Time_To_Retraction_Years"].apply(categorize_lag_short)

    g_lag = df["Lag_Category"].value_counts(normalize=True) * 100
    bd_lag = bd_df["Lag_Category"].value_counts(normalize=True) * 100

    cohort_order = ["< 1 Year", "1-3 Years", "3-5 Years", "> 5 Years"]
    comp_lag_df = pd.DataFrame({
        "Cohort": cohort_order,
        "Bangladesh (%)": [bd_lag.get(c, 0) for c in cohort_order],
        "Global (%)": [g_lag.get(c, 0) for c in cohort_order],
    }).melt(id_vars="Cohort", var_name="Scope", value_name="Percentage (%)")

    fig, axes = plt.subplots(2, 1, figsize=(13, 12))
    sns.barplot(
        data=comp_reasons_df,
        x="Prevalence (%)",
        y="Reason",
        hue="Scope",
        palette=[COLOR_BD, COLOR_GLOBAL],
        ax=axes[0],
    )
    axes[0].set_title(
        "Top Retraction Drivers: Bangladesh vs. Global Prevalence (% of Total Retractions)",
        fontsize=13,
        fontweight="bold",
    )
    axes[0].set_xlabel("Percentage of Retractions (%)")
    axes[0].grid(axis="x", linestyle=":", alpha=0.7)
    for p in axes[0].patches:
        if p.get_width() > 0:
            axes[0].annotate(
                f"{p.get_width():.1f}%",
                (p.get_width(), p.get_y() + p.get_height() / 2.0),
                ha="left",
                va="center",
                fontsize=9,
                xytext=(4, 0),
                textcoords="offset points",
            )

    sns.barplot(
        data=comp_lag_df,
        x="Cohort",
        y="Percentage (%)",
        hue="Scope",
        palette=[COLOR_BD, COLOR_GLOBAL],
        ax=axes[1],
    )
    axes[1].set_title(
        "Retraction Delay Cohort Breakdown: Bangladesh vs. Global Benchmark",
        fontsize=13,
        fontweight="bold",
    )
    axes[1].set_ylabel("Percentage of Retractions (%)")
    axes[1].set_xlabel("Delay Category")
    axes[1].grid(axis="y", linestyle=":", alpha=0.7)
    for p in axes[1].patches:
        if p.get_height() > 0:
            axes[1].annotate(
                f"{p.get_height():.1f}%",
                (p.get_height(), p.get_y() + p.get_height() / 2.0),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 3),
                textcoords="offset points",
            )

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "13_bangladesh_vs_global_benchmarks.png"))

    summary_table = pd.DataFrame({
        "Reason": top_reasons_list,
        "Bangladesh (%)": [(bd_reasons_counts[r] / len(bd_df)) * 100 for r in top_reasons_list],
        "Global (%)": [(g_reasons[r] / len(df)) * 100 for r in top_reasons_list],
        "Difference (BD - Global)": [
            ((bd_reasons_counts[r] / len(bd_df)) - (g_reasons[r] / len(df))) * 100 for r in top_reasons_list
        ],
    })
    summary_table.to_csv(os.path.join(TBL_DIR, "22_bangladesh_vs_global_reasons_comparison.csv"), index=False)
    comp_lag_df.to_csv(os.path.join(TBL_DIR, "23_bangladesh_vs_global_lag_cohort_comparison.csv"), index=False)

    # Top Subjects & Publishers in Bangladesh
    fig, axes = plt.subplots(2, 1, figsize=(12, 11))
    bd_subj = bd_df["Subject"].dropna().str.split(";").explode().str.strip()
    bd_subj = bd_subj[bd_subj != ""].value_counts().head(TOP_N_BD_SUBJECTS)
    subj_labels = [wrap_lbl(l, width=35) for l in bd_subj.index]
    bars1 = sns.barplot(x=bd_subj.values, y=subj_labels, ax=axes[0], palette="crest")
    axes[0].set_title("Top Subject Disciplines (Bangladesh)", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Count")
    for p in bars1.patches:
        axes[0].annotate(
            f"{int(p.get_width()):,}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )

    bd_pub = bd_df["Publisher"].value_counts().head(TOP_N_BD_PUBLISHERS)
    pub_labels = [wrap_lbl(l, width=35) for l in bd_pub.index]
    bars2 = sns.barplot(x=bd_pub.values, y=pub_labels, ax=axes[1], palette="viridis")
    axes[1].set_title("Top Publishers of Retracted Papers (Bangladesh)", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Retraction Count")
    for p in bars2.patches:
        axes[0].annotate(
            f"{int(p.get_width()):,}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "14_bangladesh_top_subjects_and_publishers.png"))

    bd_subj_df = bd_subj.reset_index()
    bd_subj_df.columns = ["Subject", "Count"]
    bd_subj_df.to_csv(os.path.join(TBL_DIR, "24_bangladesh_top_subjects.csv"), index=False)

    bd_pub_df = bd_pub.reset_index()
    bd_pub_df.columns = ["Publisher", "Retraction_Count"]
    bd_pub_df.to_csv(os.path.join(TBL_DIR, "25_bangladesh_top_publishers.csv"), index=False)

    # Collaboration Network & Foreign Partner Nations
    bd_df["Collab_Type"] = bd_df["Country"].apply(check_intl_collab)
    collab_counts = bd_df["Collab_Type"].value_counts()

    all_countries = bd_df["Country"].dropna().str.split(";").explode().str.strip()
    all_countries = all_countries[all_countries != ""]
    foreign_countries = (
        all_countries[~all_countries.str.contains("Bangladesh", case=False)]
        .value_counts()
        .head(TOP_N_FOREIGN_PARTNERS)
    )

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    axes[0].pie(
        collab_counts.values,
        labels=collab_counts.index,
        autopct="%1.1f%%",
        colors=[COLOR_GLOBAL, COLOR_BD, COLOR_NEUTRAL],
        startangle=140,
        wedgeprops=dict(width=0.42, edgecolor="w"),
    )
    axes[0].set_title("Collaboration Profile of Retracted Papers in Bangladesh", fontsize=13, fontweight="bold")

    foreign_labels = [wrap_lbl(c, width=28) for c in foreign_countries.index]
    bars_foreign = sns.barplot(x=foreign_countries.values, y=foreign_labels, ax=axes[1], palette="flare_r")
    axes[1].set_title("Top Foreign Partner Nations in Retracted Bangladeshi Papers", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Co-Affiliated Retracted Papers Count")
    for p in bars_foreign.patches:
        axes[1].annotate(
            f"{int(p.get_width())}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "15_bangladesh_international_collaboration_network.png"))

    foreign_df = foreign_countries.reset_index()
    foreign_df.columns = ["Foreign_Country", "Co_Affiliated_Retractions"]
    foreign_df.to_csv(os.path.join(TBL_DIR, "27_bangladesh_foreign_collaboration_partners.csv"), index=False)

    # Hyper-Authorship & Prolific Repeat Authors
    df["Author_Count"] = df["Author"].apply(count_authors)
    bd_df["Author_Count"] = bd_df["Author"].apply(count_authors)

    all_bd_authors = bd_df["Author"].dropna().str.split(";").explode().str.strip()
    all_bd_authors = all_bd_authors[all_bd_authors != ""]
    top_repeat_authors = all_bd_authors.value_counts().head(TOP_N_REPEAT_AUTHORS)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7.5))
    author_team_data = pd.DataFrame({
        "Scope": ["Bangladesh"] * len(bd_df) + ["Global"] * len(df),
        "Authors_Per_Paper": list(bd_df["Author_Count"]) + list(df["Author_Count"]),
    })
    sns.boxplot(
        data=author_team_data,
        x="Scope",
        y="Authors_Per_Paper",
        palette=[COLOR_BD, COLOR_GLOBAL],
        ax=axes[0],
        showmeans=True,
        meanprops={"marker": "o", "markerfacecolor": "white", "markeredgecolor": "black", "markersize": "8"},
    )
    axes[0].set_title(
        f"Author Team Size Comparison (BD Mean: {bd_df['Author_Count'].mean():.2f} vs. Global: {df['Author_Count'].mean():.2f})",
        fontsize=12.5,
        fontweight="bold",
    )
    axes[0].set_ylabel("Number of Authors per Paper")
    axes[0].set_ylim(0, 26)
    axes[0].grid(axis="y", linestyle=":", alpha=0.7)

    author_labels = [wrap_lbl(a, width=28) for a in top_repeat_authors.index]
    bars_auth = sns.barplot(x=top_repeat_authors.values, y=author_labels, ax=axes[1], palette="crest")
    axes[1].set_title("Top Prolific Repeat-Retracted Authors in Bangladesh", fontsize=12.5, fontweight="bold")
    axes[1].set_xlabel("Number of Retracted Papers")
    for p in bars_auth.patches:
        axes[1].annotate(
            f"{int(p.get_width())}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "16_bangladesh_hyper_authorship_and_top_authors.png"))

    top_authors_df = top_repeat_authors.reset_index()
    top_authors_df.columns = ["Author_Name", "Retraction_Count"]
    top_authors_df.to_csv(os.path.join(TBL_DIR, "28_bangladesh_top_repeat_authors.csv"), index=False)

    # Top Retracting Journals & Academic Sector Analysis
    top_bd_journals = bd_df["Journal"].value_counts().head(TOP_N_BD_JOURNALS)
    bd_df["Institutional_Sector"] = bd_df["Institution"].apply(classify_paper_sector)
    sector_counts = bd_df["Institutional_Sector"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(16, 7.5))
    jour_labels = [wrap_lbl(j, width=32) for j in top_bd_journals.index]
    bars_j = sns.barplot(x=top_bd_journals.values, y=jour_labels, ax=axes[0], palette=PALETTE_PUBLISHERS)
    axes[0].set_title("Top 10 Scholarly Journals Retracting Bangladeshi Papers", fontsize=12.5, fontweight="bold")
    axes[0].set_xlabel("Retraction Count")
    for p in bars_j.patches:
        axes[0].annotate(
            f"{int(p.get_width())}",
            (p.get_width(), p.get_y() + p.get_height() / 2.0),
            ha="left",
            va="center",
            fontsize=9.5,
            xytext=(5, 0),
            textcoords="offset points",
        )

    axes[1].pie(
        sector_counts.values,
        labels=sector_counts.index,
        autopct="%1.1f%%",
        colors=PALETTE_SECTORS,
        startangle=90,
        wedgeprops=dict(width=0.42, edgecolor="w"),
    )
    axes[1].set_title("Institutional Sector Distribution in Bangladeshi Retractions", fontsize=12.5, fontweight="bold")

    plt.tight_layout()
    save_and_show_plot(os.path.join(FIG_DIR, "17_bangladesh_journals_and_sector_breakdown.png"))

    top_bd_journals_df = top_bd_journals.reset_index()
    top_bd_journals_df.columns = ["Journal", "Retraction_Count"]
    top_bd_journals_df.to_csv(os.path.join(TBL_DIR, "29_bangladesh_top_retracting_journals.csv"), index=False)

    sector_df = sector_counts.reset_index()
    sector_df.columns = ["Sector", "Paper_Count"]
    sector_df.to_csv(os.path.join(TBL_DIR, "30_bangladesh_university_sector_breakdown.csv"), index=False)

    # ------------------------------------------------------------------------------------
    # SECTION 9: Consolidated Master Export (Figures & Tables Catalog)
    # ------------------------------------------------------------------------------------
    print("\n==================================================================")
    print("SECTION 9: Consolidated Master Export & Inventory Manifest")
    print("==================================================================")
    excel_path = os.path.join(TBL_DIR, MASTER_EXCEL_FILENAME)
    table_sheets = {
        "Missing_Values": missing_df,
        "Duplication_Summary": dup_summary,
        "Cleaning_Summary": cleaning_summary,
        "Engineered_Stats": eng_stats.reset_index(),
        "Delay_Quantiles": delay_quantiles,
        "Annual_Trends": annual_trends_df,
        "Retraction_Matrix": matrix.reset_index(),
        "Cohort_Lag_Counts": cohort_counts.reset_index(),
        "Top15_Reasons": top_reasons_df,
        "Top15_Countries": top_countries_df,
        "Top15_Publishing_Nations": country_merged.head(15),
        "Highest_Rate_Nations": top_till_bd,
        "Top10_Publishers": top_pub_df,
        "Top10_Journals": top_jour_df,
        "Paid_vs_OpenAccess": pw_summary,
        "Paid_Lag_Pct": lag_pct.reset_index(),
        "BD_Baseline_Metrics": bd_metrics_df,
        "BD_Annual_vs_Global": ann_comp,
        "BD_Top_Universities": top_bd_inst_df,
        "BD_Top_Reasons": top_bd_reasons_df,
        "BD_vs_Global_Reasons": summary_table,
        "BD_vs_Global_Lag": comp_lag_df,
        "BD_Top_Subjects": bd_subj_df,
        "BD_Top_Publishers": bd_pub_df,
        "BD_Foreign_Partners": foreign_df,
        "BD_Repeat_Authors": top_authors_df,
        "BD_Top_Journals": top_bd_journals_df,
        "BD_Sector_Breakdown": sector_df,
    }

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for sheet_name, df_sheet in table_sheets.items():
            df_sheet.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    print(f"Consolidated Master Excel Workbook saved: '{excel_path}' ({len(table_sheets)} sheets)\n")

    saved_figs = sorted(os.listdir(FIG_DIR))
    saved_tbls = sorted(os.listdir(TBL_DIR))

    manifest_df = pd.DataFrame({
        "Category": ["Figures (PNG)"] * len(saved_figs) + ["Tables (CSV/XLSX)"] * len(saved_tbls),
        "File Name": saved_figs + saved_tbls,
        "File Path": [os.path.join(FIG_DIR, f) for f in saved_figs] + [os.path.join(TBL_DIR, f) for f in saved_tbls],
    })

    print(f"=== TOTAL ARTIFACTS SAVED TO DISK: {len(saved_figs)} Figures & {len(saved_tbls)} Tables ===")
    safe_display(manifest_df)
    print("\nEDA Pipeline Completed Successfully!")


if __name__ == "__main__":
    run_retraction_watch_eda()

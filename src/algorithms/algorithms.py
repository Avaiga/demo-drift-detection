"""
This file is designed to contain the various Python functions used to configure tasks.

The functions will be imported by the __init__.py file in this folder.
"""

import pandas as pd
import scipy.stats as stats


def detect_categorical(dataset: pd.DataFrame) -> list:
    """
    Detect the names of categorical columns in a dataframe.

    Args:
        dataset: The dataframe to detect categorical columns from.

    Returns:
        A list of categorical column names.
    """
    categorical = []
    for col in dataset.columns:
        if dataset[col].dtype == "object":
            categorical.append(col)
    return categorical


def detect_numerical(dataset: pd.DataFrame) -> list:
    """
    Detect the names of numerical columns in a dataframe.

    Args:
        dataset: The dataframe to detect numerical columns from.

    Returns:
        A list of numerical column names.
    """
    numerical = []
    for col in dataset.columns:
        if dataset[col].dtype != "object":
            numerical.append(col)
    return numerical


def ks_2samp(series_1: pd.Series, series_2: pd.Series) -> float:
    """
    Runs the two-sample Kolmogorov-Smirnov test on two series.

    Args:
        series_1: The first series.
        series_2: The second series.

    Returns:
        The p-value of the test.
    """
    analysis = stats.ks_2samp(series_1, series_2)
    return int(analysis[1] * 100) / 100


def kolmogorov(
    dataset: pd.DataFrame, ref_dataset: pd.DataFrame, num_cols: list
) -> dict:
    """
    Runs the two-sample Kolmogorov-Smirnov test on all numerical columns in a dataframe.

    Args:
        dataset: The dataframe to run the test on.
        ref_dataset: The reference dataframe to compare against.
        num_cols: The list of numerical column names.

    Returns:
        A dictionary of test statistics.
    """
    ks_dict = {}
    for col in num_cols:
        ks_dict[col] = ks_2samp(dataset[col], ref_dataset[col])
    return ks_dict


def chi_squared_2samp(series_1: pd.Series, series_2: pd.Series) -> float:
    """
    Runs the two-sample chi-squared test on two series.

    Args:
        series_1: The first series.
        series_2: The second series.

    Returns:
        The p-value of the test.
    """
    # Get the unique values
    series_1_unique = series_1.unique()
    series_2_unique = series_2.unique()
    # Get the frequencies
    series_1_freq = series_1.value_counts()
    series_2_freq = series_2.value_counts()
    # Get the expected frequencies
    series_1_exp_freq = []
    series_2_exp_freq = []
    for i, _ in enumerate(series_1_unique):
        series_1_exp_freq.append(
            series_1_freq[series_1_unique[i]] * len(series_2) / len(series_1)
        )
    for i, _ in enumerate(series_2_unique):
        series_2_exp_freq.append(
            series_2_freq[series_2_unique[i]] * len(series_1) / len(series_2)
        )
    analysis = stats.chisquare(series_1_exp_freq, series_2_exp_freq)
    return int(analysis[1] * 100) / 100


def chi_squared(
    dataset: pd.DataFrame, ref_dataset: pd.DataFrame, cat_cols: list
) -> dict:
    """
    Runs the chi-squared test on all categorical columns in a dataframe.

    Args:
        dataset: The dataframe to run the test on.
        ref_dataset: The reference dataframe to compare against.
        cat_cols: The list of categorical column names.

    Returns:
        A dictionary of test statistics.
    """
    chi_dict = {}
    for col in cat_cols:
        chi_dict[col] = chi_squared_2samp(dataset[col], ref_dataset[col])
    return chi_dict


def collect_results(num_results: dict, cat_results: dict) -> pd.DataFrame:
    """
    Collects the results of the two tests into a single dictionary.

    Args:
        num_results: The dictionary of numerical test results.
        cat_results: The dictionary of categorical test results.

    Returns:
        A dataframe of the results.
    """
    columns = []
    tests = []
    values = []
    detected = []
    for col in cat_results:
        columns.append(col)
        tests.append("Chi-Squared")
        values.append(cat_results[col])
        if cat_results[col] < 0.05:
            detected.append(True)
        else:
            detected.append(False)
    for col in num_results:
        columns.append(col)
        tests.append("Kolmogorov-Smirnov")
        values.append(num_results[col])
        if num_results[col] < 0.05:
            detected.append(True)
        else:
            detected.append(False)
    results = pd.DataFrame(
        {"Column": columns, "Test": tests, "p-value": values, "Drift": detected}
    )
    return results


def merge_data(ref_data: pd.DataFrame, compare_data: pd.DataFrame):
    """
    Merges the reference and comparison data into a single dataframe.
    The Dataframe is prepared for plotting.

    Args:
        ref_data: The reference data.
        compare_data: The comparison data.

    Returns:
        plot_data: The dataset for other columns.
        sex_data: The dataset for sex distribution.
    """
    bp_data = [
        {"Blood Pressure": list(ref_data["blood_pressure"])},
        {"Blood Pressure": list(compare_data["blood_pressure"])},
    ]
    # Count the Male and Female rows in ref and compare
    male_ref = ref_data[ref_data["sex"] == "Male"].shape[0]
    male_compare = compare_data[compare_data["sex"] == "Male"].shape[0]
    female_ref = ref_data[ref_data["sex"] == "Female"].shape[0]
    female_compare = compare_data[compare_data["sex"] == "Female"].shape[0]
    sex_data = pd.DataFrame(
        {
            "Dataset": ["Ref", "Compare"],
            "Male": [male_ref, male_compare],
            "Female": [female_ref, female_compare],
        }
    )
    return bp_data, sex_data

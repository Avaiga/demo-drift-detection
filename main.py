import taipy as tp
from taipy import Gui, Config
from taipy.gui import notify
import numpy as np
import pandas as pd
import scipy.stats as stats


def detect_categorical(df: pd.DataFrame) -> list:
    """
    Detect the names of categorical columns in a dataframe.

    Args:
        df: The dataframe to detect categorical columns from.

    Returns:
        A list of categorical column names.
    """
    categorical = []
    for col in df.columns:
        if df[col].dtype == "object":
            categorical.append(col)
    return categorical


def detect_numerical(df: pd.DataFrame) -> list:
    """
    Detect the names of numerical columns in a dataframe.

    Args:
        df: The dataframe to detect numerical columns from.

    Returns:
        A list of numerical column names.
    """
    numerical = []
    for col in df.columns:
        if df[col].dtype != "object":
            numerical.append(col)
    return numerical


def ks_2samp(x1: pd.Series, x2: pd.Series) -> float:
    """
    Runs the two-sample Kolmogorov-Smirnov test on two series.

    Args:
        x1: The first series.
        x2: The second series.

    Returns:
        The p-value of the test.
    """
    analysis = stats.ks_2samp(x1, x2)
    return int(analysis[1] * 100) / 100


def kolmogorov(df: pd.DataFrame, ref_df: pd.DataFrame, num_cols: list) -> dict:
    """
    Runs the two-sample Kolmogorov-Smirnov test on all numerical columns in a dataframe.

    Args:
        df: The dataframe to run the test on.
        ref_df: The reference dataframe to compare against.
        num_cols: The list of numerical column names.

    Returns:
        A dictionary of test statistics.
    """
    ks_dict = {}
    for col in num_cols:
        ks_dict[col] = ks_2samp(df[col], ref_df[col])
    return ks_dict


def chi_squared_2samp(x1: pd.Series, x2: pd.Series) -> float:
    """
    Runs the two-sample chi-squared test on two series.

    Args:
        x1: The first series.
        x2: The second series.

    Returns:
        The p-value of the test.
    """
    # Get the unique values
    x1_unique = x1.unique()
    x2_unique = x2.unique()
    # Get the frequencies
    x1_freq = x1.value_counts()
    x2_freq = x2.value_counts()
    # Get the expected frequencies
    x1_exp_freq = []
    x2_exp_freq = []
    for i in range(len(x1_unique)):
        x1_exp_freq.append(x1_freq[x1_unique[i]] * len(x2) / len(x1))
    for i in range(len(x2_unique)):
        x2_exp_freq.append(x2_freq[x2_unique[i]] * len(x1) / len(x2))
    analysis = stats.chisquare(x1_exp_freq, x2_exp_freq)
    return int(analysis[1] * 100) / 100


def chi_squared(df: pd.DataFrame, ref_df: pd.DataFrame, cat_cols: list) -> dict:
    """
    Runs the chi-squared test on all categorical columns in a dataframe.

    Args:
        df: The dataframe to run the test on.
        ref_df: The reference dataframe to compare against.
        cat_cols: The list of categorical column names.

    Returns:
        A dictionary of test statistics.
    """
    chi_dict = {}
    for col in cat_cols:
        chi_dict[col] = chi_squared_2samp(df[col], ref_df[col])
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


Config.load("config.toml")
scenario_cfg = Config.scenarios["drift_scenario"]
scenario = tp.Core().run()

scenario = tp.create_scenario(scenario_cfg)
scenario.compare_data.write(pd.read_csv("data_ref.csv"))
tp.submit(scenario)
results = scenario.results.read()

data_ref = pd.read_csv("data_ref.csv")
compare_path = "data_ref"
compare_data = pd.read_csv(compare_path + ".csv")


def merge_data(ref_data: pd.DataFrame, compare_data: pd.DataFrame) -> pd.DataFrame:
    plot_data = pd.DataFrame()
    # Add data_ref to the plot_data dataframe while adding _ref to the column names
    for col in ref_data.columns:
        plot_data[col + "_ref"] = ref_data[col]
    # Add the comparison data to the plot_data dataframe
    for col in compare_data.columns:
        plot_data[col + "_compare"] = compare_data[col]
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
    return plot_data, sex_data


plot_data, sex_data = merge_data(data_ref, compare_data)


def on_button(state):
    scenario = tp.create_scenario(scenario_cfg)
    state.compare_data = pd.read_csv(state.compare_path + ".csv")
    scenario.compare_data.write(state.compare_data)
    tp.submit(scenario)
    state.results = scenario.results.read()
    # If the Drift column has any True values, notify the user
    if state.results["Drift"].any():
        notify(state, "info", "Potential Drift Detected")
    else:
        notify(state, "success", "No Drift Detected")
    state.plot_data, state.sex_data = merge_data(data_ref, state.compare_data)


page = """
# **Drift Detection**{: .color-primary} in Diabetes Dataset

<|layout|columns=1 3|
<|part|class_name=card|
### Select Comparison Data<br/>
<|{compare_path}|selector|lov=data_ref;data_noisy;data_female;data_big|dropdown|>
<|Run|button|on_action=on_button|>
|>

<|part|class_name=card|
<|{results}|table|show_all=True|>
|>
|>

<br/>

<|layout|columns=1 1|
<|part|class_name=card|
<|{sex_data}|chart|type=bar|x=Dataset|y[1]=Male|y[2]=Female|title=Sex Distribution|>
|>

<|part|class_name=card|
<|{plot_data}|chart|type=histogram|y[1]=bp_ref|y[2]=bp_compare|title=Blood Pressure Distribution|>
|>
|>

"""

gui = Gui(page)
gui.run(use_reloader=True)

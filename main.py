"""
Drift Detection Taipy Demo

Please refer to https://docs.taipy.io/en/latest/manuals/gui/ for more details.
"""

from taipy.gui import Gui, notify


import taipy as tp
from taipy import Config
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
    for i in range(len(series_1_unique)):
        series_1_exp_freq.append(
            series_1_freq[series_1_unique[i]] * len(series_2) / len(series_1)
        )
    for i in range(len(series_2_unique)):
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


Config.load("config.toml")
scenario_cfg = Config.scenarios["drift_scenario"]
scenario = tp.Core().run()

scenario = tp.create_scenario(scenario_cfg)
scenario.compare_data.write(pd.read_csv("data/data_ref.csv"))
tp.submit(scenario)
results = scenario.drift_results.read()

data_ref = pd.read_csv("data/data_ref.csv")
compare_path = "data_ref"
compare_data = pd.read_csv("data/" + compare_path + ".csv")


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


bp_data, sex_data = merge_data(data_ref, compare_data)


def on_button(state):
    """
    Runs the drift detection scenario and displays the results when the button is clicked.
    """
    scenario = tp.create_scenario(scenario_cfg)
    state.compare_data = pd.read_csv("data/" + state.compare_path + ".csv")
    scenario.compare_data.write(state.compare_data)
    tp.submit(scenario)
    state.results = scenario.drift_results.read()
    # If the Drift column has any True values, notify the user
    if state.results["Drift"].any():
        notify(state, "info", "Potential Drift Detected")
    else:
        notify(state, "success", "No Drift Detected")
    state.bp_data, state.sex_data = merge_data(data_ref, state.compare_data)


bp_options = [
    # First data set displayed as green-ish, and 5 bins
    {
        "marker": {"color": "#4A4", "opacity": 0.8},
        "nbinsx": 10,
    },
    # Second data set displayed as red-ish, and 25 bins
    {
        "marker": {"color": "#A33", "opacity": 0.8, "text": "Compare Data"},
        "nbinsx": 10,
    },
]

bp_layout = {
    # Overlay the two histograms
    "barmode": "overlay",
    "title": "Blood Pressure Distribution (Green = Reference, Red = Compare)",
    "showlegend": False,
}


page = """
<center>
<|navbar|lov={[("page1", "Homepage"), ("https://docs.taipy.io/en/latest/manuals/about/", "Taipy Docs"), ("https://docs.taipy.io/en/latest/getting_started/", "Getting Started")]}|>
</center>

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

<|Reference Dataset and Compare Dataset|expandable|expanded=False|
<|layout|columns=1 1|
<|{data_ref}|table|page_size=5|>

<|{compare_data}|table|page_size=5|>
|>
|>

<|layout|columns=1 1|
<|part|class_name=card|
<|{sex_data}|chart|type=bar|x=Dataset|y[1]=Male|y[2]=Female|title=Sex Distribution|>
|>

<|part|class_name=card|
<|{bp_data}|chart|type=histogram|options={bp_options}|layout={bp_layout}|>
|>
|>

"""

if __name__ == "__main__":
    gui = Gui(page=page)
    gui.run(title="Drift Detection", use_reloader=True)

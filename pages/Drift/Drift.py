"""
A page of the application.
Page content is imported from the Drift.md file.

Please refer to https://docs.taipy.io/en/latest/manuals/gui/pages for more details.
"""

import taipy as tp
from taipy.gui import Markdown
import pandas as pd
from taipy.gui import notify

from configuration.config import scenario_cfg

Drift = Markdown("pages/Drift/Drift.md")


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


def on_ref_change(state):
    state.ref_data = pd.read_csv("data/" + state.ref_selected + ".csv")
    state.scenario.reference_data.write(state.ref_data)
    state.bp_data, state.sex_data = merge_data(state.ref_data, state.compare_data)


def on_compare_change(state):
    state.compare_data = pd.read_csv("data/" + state.compare_selected + ".csv")
    state.scenario.compare_data.write(state.compare_data)
    state.bp_data, state.sex_data = merge_data(state.ref_data, state.compare_data)


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


def on_submission_status_change(state, submittable, details):
    submission_status = details.get("submission_status")

    if submission_status == "COMPLETED":
        notify(state, "success", "Drift Detection Completed")
        state.refresh("scenario")

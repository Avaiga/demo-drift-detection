"""
This page/script is not used in the application. Its only purpose is educationnal.
How to create the same drift page but with the Python API instead of the Markdown syntax.
"""

"""
A page of the application.
Page content is imported from the Drift.md file.

Please refer to https://docs.taipy.io/en/latest/manuals/gui/pages for more details.
"""

import taipy as tp
import pandas as pd
from taipy.gui import notify
import taipy.gui.builder as tgb

from configuration.config import scenario_cfg


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


with tgb.Page() as Drift:
    tgb.toggle(theme=True)

    with tgb.layout("1 1"):
        with tgb.part("card"):
            tgb.text("### Select Reference Data", mode="md")
            tgb.selector(
                "{ref_selected}",
                lov=["data_ref", "data_noisy", "data_female", "data_big"],
                dropdown=True,
                on_change=on_ref_change,
            )

        with tgb.part("card"):
            tgb.text("### Select Comparison Data", mode="md")
            tgb.selector(
                "{compare_selected}",
                lov=["data_ref", "data_noisy", "data_female", "data_big"],
                dropdown=True,
                on_change=on_compare_change,
            )

    with tgb.expandable("Reference Dataset and Compare Dataset", expanded=True):
        with tgb.layout("1 1"):
            tgb.table("{ref_data}", page_size=5)

            tgb.table("{compare_data}", page_size=5)

    with tgb.layout("1 1"):
        with tgb.part("card"):
            tgb.chart(
                "{sex_data}",
                type="bar",
                x="Dataset",
                y=["Male", "Female"],
                title="Sex Distribution",
            )

        with tgb.part("card"):
            tgb.chart(
                "{bp_data}", type="histogram", options=bp_options, layout=bp_layout
            )

    tgb.html("br")

    tgb.text("### Run the scenario:", mode="md")

    tgb.scenario(
        "{scenario}",
        expandable=False,
        on_submission_status_change=on_submission_status_change,
    )

    tgb.scenario_dag("{scenario}")

    tgb.html("br")

    tgb.text("### View the results:", mode="md")
    tgb.data_node(lambda scenario: scenario.drift_results if scenario else None)

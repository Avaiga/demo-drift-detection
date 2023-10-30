import taipy as tp
from taipy.gui import Gui
import pandas as pd

from configuration.config import scenario_cfg
from pages import *
from pages.Drift.Drift import merge_data


if __name__ == "__main__":
    ref_data = pd.read_csv("data/data_ref.csv")

    tp.Core().run()
    scenario = tp.create_scenario(scenario_cfg)

    ref_selected = "data_ref"
    compare_selected = "data_noisy"

    ref_data = pd.read_csv("data/" + ref_selected + ".csv")
    scenario.reference_data.write(ref_data)

    compare_data = pd.read_csv("data/" + compare_selected + ".csv")
    scenario.compare_data.write(compare_data)

    bp_data, sex_data = merge_data(ref_data, compare_data)

    gui = Gui(page=Drift)
    gui.run(title="Drift Detection")

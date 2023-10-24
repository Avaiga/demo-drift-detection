"""
Contain the application's configuration including the scenario configurations.

The configuration is run by the Core service.
"""

from algorithms.algorithms import *

from taipy import Config

reference_data_cfg = Config.configure_data_node("reference_data", "csv")
compare_data_cfg = Config.configure_data_node("compare_data", "csv")
num_cols_cfg = Config.configure_data_node("num_cols")
cat_cols_cfg = Config.configure_data_node("cat_cols")
num_results_cfg = Config.configure_data_node("num_results")
cat_results_cfg = Config.configure_data_node("cat_results")
drift_results_cfg = Config.configure_data_node("drift_results")

detect_numerical_cfg = Config.configure_task(
    id="detect_numerical",
    function=detect_numerical,
    input=[reference_data_cfg],
    output=num_cols_cfg,
)
detect_categorical_cfg = Config.configure_task(
    id="detect_categorical",
    function=detect_categorical,
    input=[reference_data_cfg],
    output=cat_cols_cfg,
)
kolmogorov_cfg = Config.configure_task(
    id="kolmogorov",
    function=kolmogorov,
    input=[compare_data_cfg, reference_data_cfg, num_cols_cfg],
    output=num_results_cfg,
)
chi_squared_cfg = Config.configure_task(
    id="chi_squared",
    function=chi_squared,
    input=[compare_data_cfg, reference_data_cfg, cat_cols_cfg],
    output=cat_results_cfg,
)
collect_results_cfg = Config.configure_task(
    id="collect_results",
    function=collect_results,
    input=[num_results_cfg, cat_results_cfg],
    output=drift_results_cfg,
)

scenario_cfg = Config.configure_scenario(
    id="drift_detection",
    task_configs=[
        detect_numerical_cfg,
        detect_categorical_cfg,
        kolmogorov_cfg,
        chi_squared_cfg,
        collect_results_cfg,
    ],
)

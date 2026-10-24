"""Streamlit rendering regressions for the targeted audit follow-up."""
import json
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

from utils.sensor import SensorService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"


class FrontendRegressionTests(unittest.TestCase):
    def app_test(self):
        # Prevent AppTest from ever opening a host serial device during discovery.
        self.auto_connect_patch = patch.object(
            SensorService, "auto_connect_unique", return_value=False
        )
        self.auto_connect_patch.start()
        self.addCleanup(self.auto_connect_patch.stop)
        return AppTest.from_file(str(APP_PATH), default_timeout=30).run()

    def test_all_six_pages_render_without_exceptions(self):
        app = self.app_test()
        self.assertFalse(app.exception)
        for page in (
            "pages/1_Executive_Overview.py",
            "pages/2_Inventory_Digital_Twin.py",
            "pages/3_AI_Demand_Forecast.py",
            "pages/4_Scenario_Simulator.py",
            "pages/5_Replenishment_Alerts.py",
            "pages/6_System_Health.py",
        ):
            with self.subTest(page=page):
                app.switch_page(page).run()
                self.assertFalse(app.exception)

    def test_scenario_charts_use_distinct_units_and_preserve_comparisons(self):
        app = self.app_test()
        app.switch_page("pages/4_Scenario_Simulator.py").run()
        self.assertFalse(app.exception)

        charts = app.get("plotly_chart")
        self.assertEqual(len(charts), 2)
        demand_spec, inventory_spec = [json.loads(chart.proto.spec) for chart in charts]
        self.assertEqual(
            demand_spec["layout"]["yaxis"]["title"]["text"],
            "Demand (units/day)",
        )
        self.assertEqual(
            inventory_spec["layout"]["yaxis"]["title"]["text"],
            "Inventory (units)",
        )
        self.assertEqual(demand_spec["data"][0]["x"], ["Baseline", "Scenario"])
        self.assertEqual(
            inventory_spec["data"][0]["x"], ["Reorder point", "Current stock"]
        )
        self.assertEqual(
            [trace["name"] for trace in inventory_spec["data"]],
            ["Baseline", "Scenario"],
        )

    def test_forecast_identifies_notebook_reported_benchmark_values(self):
        app = self.app_test()
        app.switch_page("pages/3_AI_Demand_Forecast.py").run()
        self.assertFalse(app.exception)
        headings = [element.value for element in app.subheader]
        self.assertIn("Notebook-reported benchmark MAE (synthetic holdout)", headings)
        messages = [element.value for element in app.info]
        self.assertTrue(any("does not evaluate artifacts at runtime" in x for x in messages))
        self.assertTrue(any("not evidence of real-world warehouse forecasting accuracy" in x for x in messages))

    def test_download_csv_matches_the_visible_replenishment_table(self):
        captured = {}
        original_download_button = st.download_button

        def capture_download(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return original_download_button(*args, **kwargs)

        app = self.app_test()
        with patch.object(st, "download_button", side_effect=capture_download):
            app.switch_page("pages/5_Replenishment_Alerts.py").run()

        self.assertFalse(app.exception)
        self.assertEqual(captured["args"][0], "Download recommendation CSV")
        self.assertEqual(
            captured["kwargs"]["file_name"], "replenishment_recommendation.csv"
        )
        exported = pd.read_csv(BytesIO(captured["args"][1]))
        visible = app.dataframe[0].value
        pd.testing.assert_frame_equal(exported, visible, check_dtype=False)


if __name__ == "__main__":
    unittest.main()

import unittest

import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import widgets
from nwbwidgets.timeseries import (
    BaseGroupedTraceWidget,
    show_ts_fields,
    show_timeseries,
    plot_traces,
    show_indexed_timeseries_mpl,
)
from pynwb import TimeSeries


def test_timeseries_widget():
    ts = TimeSeries(
        name="name",
        description="no description",
        data=np.array([[1.0, 2.0, 3.0, 4.0], [11.0, 12.0, 13.0, 14.0]]),
        rate=100.0,
    )

    BaseGroupedTraceWidget(ts)


class ShowTimeSeriesTestCase(unittest.TestCase):
    def setUp(self):
        data = np.random.rand(160, 3)
        self.ts = TimeSeries(
            name="test_timeseries", data=data, unit="m", starting_time=0.0, rate=1.0
        )

    def test_show_ts_fields(self):
        assert isinstance(show_ts_fields(self.ts), widgets.Widget)

    def test_show_timeseries(self):
        assert isinstance(show_timeseries(self.ts, istart=5, istop=56), widgets.Widget)

    def test_show_indexed_timeseries_mpl(self):
        ax = show_indexed_timeseries_mpl(
            self.ts, zero_start=True, title="Test show_indexed_timeseries_mpl"
        )
        assert isinstance(ax, plt.Subplot)


class PlotTracesTestCase(unittest.TestCase):
    def setUp(self):
        self.data = np.random.rand(160, 3)

    def test_plot_traces(self):
        ts = TimeSeries(
            name="test_timeseries",
            data=self.data,
            unit="m",
            starting_time=0.0,
            rate=20.0,
        )
        plot_traces(ts)

    def test_plot_traces_fix(self):
        ts = TimeSeries(
            name="test_timeseries",
            data=self.data.T,
            unit="m",
            starting_time=0.0,
            rate=20.0,
        )
        plot_traces(ts)

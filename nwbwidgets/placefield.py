import numpy as np
from scipy.ndimage import label
from scipy.ndimage.filters import gaussian_filter, maximum_filter

import matplotlib.pyplot as plt

import pynwb
from ipywidgets import widgets, BoundedFloatText, Dropdown, Checkbox, fixed

from .analysis.placefields import compute_2d_firing_rate, compute_linear_firing_rate

from .utils.widgets import interactive_output
from .utils.units import get_spike_times
from .utils.timeseries import get_timeseries_in_units, get_timeseries_tt
from .base import vis2widget
from .controllers import  GroupAndSortController


## To-do
# [X] Create PlaceFieldWidget class
    # [X] Refactor place field calculation code to deal with nwb data type
        # [X] Incorporate place field fxns into class
        # [X] Change all internal attributes references
        # [X]Change all internal method references

    # [X] Get pos
    # [X] Get time
    # [X] Get spikes
    # [] Get trials / epochs

# [X] Submit draft PR

    # [] 1D Place Field Widget
        # [X] Incorporate nelpy package into widget
        # [X] Speed threshold implementation
        # [X] Add foreign group and sort controller to pick unit groups and ranges?
        # [X] Normalized firing rate figure?
        # [X] Add collapsed unit vizualization?
        # [] Scale bar?
        # [] Sort place cell tuning curves by peak firing rate position?
        # [] Color palette control?

# [] Dropdown that controls which unit

# [x] Work in buttons / dropdowns / sliders to modify following parameters in place field calculation:
# [] Different epochs
# [x] Gaussian SD
# [x] Speed threshold
# [] Minimum firing rate
# [] Place field thresh (% of local max)

def route_placefield(spatial_series: pynwb.behavior.SpatialSeries):
    print(spatial_series.data.shape)
    if spatial_series.data.shape[1] == 2:
        return PlaceFieldWidget(spatial_series)
    elif spatial_series.data.shape[1] == 1:
        return PlaceField_1D_Widget(spatial_series)
    else:
        print('Spatial series exceeds dimensionality for visualization')
        return


# Put widget rendering here
class PlaceFieldWidget(widgets.HBox):

    def __init__(self, spatial_series: pynwb.behavior.SpatialSeries, **kwargs):
        super().__init__()


        if hasattr(spatial_series.get_ancestor('NWBFile'),'velocity'):
            velocity = spatial_series.get_ancestor('NWBFile').velocity
        else:
            velocity = []

        self.units = spatial_series.get_ancestor('NWBFile').units
        self.pos_tt = get_timeseries_tt(spatial_series)

        istart = 0
        istop = None

        self.pos, self.unit = get_timeseries_in_units(spatial_series, istart, istop)

        self.pixel_width = (np.nanmax(self.pos) - np.nanmin(self.pos)) / 1000

        # Put widget controls here:
        # - Minimum firing rate
        # - Place field thresh (% of local max)

        bft_gaussian = BoundedFloatText(value=0.0184, min=0, max=99999, description='gaussian sd (cm)')
        bft_speed = BoundedFloatText(value=0.03, min=0, max=99999, description='speed threshold (cm/s)')
        dd_unit_select = Dropdown(options=np.arange(len(self.units)), description='unit')
        cb_velocity = Checkbox(value=False, description='use velocity', indent=False)

        self.controls = dict(
            gaussian_sd=bft_gaussian,
            speed_thresh=bft_speed,
            index=dd_unit_select,
            use_velocity=cb_velocity,
            velocity=fixed(velocity)
        )

        out_fig = interactive_output(self.do_rate_map, self.controls)

        self.children = [
            widgets.VBox([
                bft_gaussian,
                bft_speed,
                dd_unit_select,
                cb_velocity
            ]),
            vis2widget(out_fig)
        ]

    def do_rate_map(self, index=0, speed_thresh=0.03, gaussian_sd=0.0184, use_velocity=False, velocity=[]):
        tmin = min(self.pos_tt)
        tmax = max(self.pos_tt)

        spikes = get_spike_times(self.units, index, [tmin, tmax])
        if use_velocity == False:
            occupancy, filtered_firing_rate, [edges_x, edges_y] = compute_2d_firing_rate(
                self.pos, self.pos_tt, spikes, self.pixel_width, speed_thresh=speed_thresh, gaussian_sd=gaussian_sd)
        else:
            occupancy, filtered_firing_rate, [edges_x, edges_y] = compute_2d_firing_rate(
                self.pos, self.pos_tt, spikes, self.pixel_width, speed_thresh=speed_thresh, gaussian_sd=gaussian_sd,
                velocity=velocity)

        fig, ax = plt.subplots()

        im = ax.imshow(filtered_firing_rate,
                       extent=[edges_x[0], edges_x[-1], edges_y[0], edges_y[-1]],
                       aspect='equal')
        ax.set_xlabel('x ({})'.format(self.unit))
        ax.set_ylabel('y ({})'.format(self.unit))

        cbar = plt.colorbar(im)
        cbar.ax.set_ylabel('firing rate (Hz)')

        return fig


class PlaceField_1D_Widget(widgets.HBox):

    def __init__(self, spatial_series: pynwb.behavior.SpatialSeries,
                 foreign_group_and_sort_controller: GroupAndSortController = None,
                 group_by=None, **kwargs):

        super().__init__()

        self.units = spatial_series.get_ancestor('NWBFile').units

        self.pos_tt = get_timeseries_tt(spatial_series)

        if foreign_group_and_sort_controller:
            self.gas = foreign_group_and_sort_controller
        else:
            self.gas = self.make_group_and_sort(group_by=group_by, control_order=False)

        istart = 0
        istop = None
        self.pos, self.unit = get_timeseries_in_units(spatial_series, istart, istop)

        self.pixel_width = (np.nanmax(self.pos) - np.nanmin(self.pos)) / 1000

        # Put widget controls here:
        # - Minimum firing rate
        # - Place field thresh (% of local max)

        bft_gaussian = BoundedFloatText(value=0.0557, min=0, max=99999, description='gaussian sd (m)')
        bft_spatial_bin_len = BoundedFloatText(value=0.0168, min=0, max=99999, description='spatial bin length (m)')
        cb_normalize_select = Checkbox(value=False, description='normalize', indent=False)
        cb_collapsed_select = Checkbox(value=False, description='collapsed', indent=False)

        self.controls = dict(
            gas=self.gas,
            gaussian_sd=bft_gaussian,
            spatial_bin_len=bft_spatial_bin_len,
            normalize=cb_normalize_select,
            collapsed=cb_collapsed_select
        )

        out_fig = interactive_output(self.do_1d_rate_map, self.controls)
        checkboxes = widgets.HBox([cb_normalize_select, cb_collapsed_select])
        self.children = [
            widgets.VBox([
                bft_gaussian,
                bft_spatial_bin_len,
                checkboxes,
                self.gas,
            ]),
            vis2widget(out_fig)
        ]

    def make_group_and_sort(self, group_by=None, control_order=True):
        return GroupAndSortController(self.units, group_by=group_by, control_order=control_order)

    def do_1d_rate_map(self, units_window=None, order=None, group_inds=None, labels=None, normalize=False,
                       collapsed=False, gaussian_sd=0.0557, spatial_bin_len=0.0168, **kwargs):
        tmin = min(self.pos_tt)
        tmax = max(self.pos_tt)

        print('Order is {}'.format(order))
        print('Units_window is {}'.format(units_window))
        print('Group_inds is {}'.format(group_inds))
        print('Labels is {}'.format(labels))
        if order.any() == None:
            index = np.arange(0, len(self.units))
        else:
            index = order

        spikes = get_spike_times(self.units, index[0], [tmin, tmax])
        xx, occupancy, filtered_firing_rate = compute_linear_firing_rate(
            self.pos, self.pos_tt, spikes, gaussian_sd=gaussian_sd, spatial_bin_len=spatial_bin_len)

        all_unit_firing_rate = np.zeros([len(index), len(xx)])
        all_unit_firing_rate[0] = filtered_firing_rate
        firing_rate_ind = 0
        for ind in index[1:]:
            spikes = get_spike_times(self.units, ind, [tmin, tmax])
            _, _, all_unit_firing_rate[firing_rate_ind] = compute_linear_firing_rate(
                self.pos, self.pos_tt, spikes, gaussian_sd=gaussian_sd, spatial_bin_len=spatial_bin_len)
            firing_rate_ind += 1

        # npl.set_palette(npl.colors.rainbow)
        # with npl.FigureManager(show=True, figsize=(8, 8)) as (fig, ax):
        #     npl.utils.skip_if_no_output(fig)
        fig, ax = plt.subplots()
        plot_tuning_curves1D(all_unit_firing_rate, xx, ax=ax, unit_labels=index, normalize=normalize,
                             collapsed=collapsed)

        # fig = ax.plot(xx, filtered_firing_rate, '-')
        # ax.set_xlabel('x ({})'.format(self.unit))
        # ax.set_ylabel('firing rate (Hz)')

        return fig

def plot_tuning_curves1D(ratemap, bin_pos, ax=None, normalize=False, pad=10, unit_labels=None, fill=True, color=None,
                         collapsed=False):
    """

    Parameters
    ----------
    ratemap: array-like
        An array of dim: [number of units, bin positions] with the spike rates for a unit, at every pos, in each row
    bin_pos: array-like
        An array representing the bin positions of ratemap for each column
    ax: matplotlib.pyplot.ax
        Axes object for the figure on which the ratemaps will be plotted
    normalize: bool
        default = False
        Input to determine whether or not to normalize firing rates
    pad: int
        default = 10
        Changes to 0 if 'collapsed' is true
        Amount of space to put between each unit (i.e. row) in the figure
    unit_labels: array-like
        Unit ids for each unit in ratemap
    collapsed: bool
        default = False
        Determines whether to plot the ratemaps with zero padding, i.e. at the same y coordinate, on the ratemap
    fill: bool, optional

    Returns
    -------
    matplotlib.pyplot.ax

    """
    xmin = bin_pos[0]
    xmax = bin_pos[-1]
    xvals = bin_pos

    n_units, n_ext = ratemap.shape

    if normalize:
        peak_firing_rates = ratemap.max(axis=1)
        ratemap = (ratemap.T / peak_firing_rates).T
        pad = 1
    # # determine max firing rate
    # max_firing_rate = ratemap.max()
    if collapsed:
        pad = 0

    if xvals is None:
        xvals = np.arange(n_ext)
    if xmin is None:
        xmin = xvals[0]
    if xmax is None:
        xmax = xvals[-1]

    for unit, curve in enumerate(ratemap):
        if color is None:
            line = ax.plot(xvals, unit*pad + curve, zorder=int(10+2*n_units-2*unit))
        else:
            line = ax.plot(xvals, unit*pad + curve, zorder=int(10+2*n_units-2*unit), color=color)
        if fill:
            # Get the color from the current curve
            fillcolor = line[0].get_color()
            ax.fill_between(xvals, unit*pad, unit*pad + curve, alpha=0.3, color=fillcolor, zorder=int(10+2*n_units-2*unit-1))

    ax.set_xlim(xmin, xmax)
    if pad != 0:
        yticks = np.arange(n_units)*pad + 0.5*pad
        ax.set_yticks(yticks)
        ax.set_yticklabels(unit_labels)
        ax.set_xlabel('external variable')
        ax.set_ylabel('unit')
        ax.tick_params(axis=u'y', which=u'both', length=0)
        ax.spines['left'].set_color('none')
        ax.yaxis.set_ticks_position('right')
    else:
        if normalize:
            ax.set_ylabel('normalized firing rate')
        else:
            ax.set_ylabel('firing rate [Hz]')
        ax.set_ylim(0)

    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.spines['right'].set_color('none')
    ax.yaxis.set_ticks_position('left')

    return ax

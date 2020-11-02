from ndx_spectrum import Spectrum
import warnings
import matplotlib.pyplot as plt
from ipywidgets import widgets
import numpy as np


def show_spectrum(node: Spectrum, **kwargs) -> widgets.Widget:
    if isinstance(node, Spectrum):
        data = node.power if 'power' in node.fields else node.phase
        if len(data.shape)==2:
            no_channels = data.shape[1]
        else:
            no_channels = 1
        freqs_all = np.asarray(node.frequencies)
        channel_slider = widgets.IntRangeSlider(
            min=1,
            max=no_channels,
            step=1,
            description='Channel Range:',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
        )
        freq_slider = widgets.IntRangeSlider(
            min=0,
            max=freqs_all[-1],
            step=1,
            description='Frequency Range:',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
        )
        out = widgets.Output()
        with out:
            widgets.interact(
                lambda channel_no, frequency_range: get_spectrum_figure(node, channel_no, frequency_range),
                channel_no=channel_slider,
                frequency_range=freq_slider)
        return out
    else:
        warnings.warn('neurodatatype not of type: Spectrum')


def get_spectrum_figure(spectrum,channel_no, freqs):
    all_freqs = np.asarray(spectrum.frequencies)
    start_id = (np.abs(freqs[0]-all_freqs)).argmin()
    end_id = (np.abs(freqs[1] - all_freqs)).argmin()
    if channel_no[0] != channel_no[1]:
        range_ = range(channel_no[0] - 1, channel_no[1] - 1)
    else:
        range_ = channel_no[0]-1
    if 'power' in spectrum.fields and 'phase' in spectrum.fields:
        power_data = np.asarray(spectrum.power)
        if len(power_data.shape)==1:
            power_data = power_data[:, np.newaxis]
        phase_data = np.asarray(spectrum.phase)
        if len(phase_data.shape)==1:
            phase_data = phase_data[:, np.newaxis]
        fig, axs = plt.subplots(2, 1, sharex=True)
        axs[0].semilogy(all_freqs[start_id:end_id],
                        power_data[start_id:end_id,range_])
        axs[0].set_ylabel('Power')
        axs[1].plot(all_freqs[start_id:end_id],
                    phase_data[start_id:end_id,range_])
        axs[1].set_ylabel('phase')
    elif 'power' in spectrum.fields:
        power_data = np.asarray(spectrum.power)
        if len(power_data.shape) == 1:
            power_data = power_data[:, np.newaxis]
        fig, ax = plt.subplots()
        ax.set_xlabel('frequency')
        ax.semilogy(all_freqs[start_id:end_id],
                    power_data[start_id:end_id,range_])
        ax.set_ylabel('Power')
    elif 'phase' in spectrum.fields:
        phase_data = np.asarray(spectrum.phase)
        if len(phase_data.shape) == 1:
            phase_data = phase_data[:, np.newaxis]
        fig, ax = plt.subplots()
        ax.plot(all_freqs[start_id:end_id],
                phase_data[start_id:end_id,range_])
        ax.set_ylabel('phase')
        ax.set_xlabel('frequency')
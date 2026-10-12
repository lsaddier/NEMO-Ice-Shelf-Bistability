"""plotting_utils.py
Utility functions to configure matplotlib and colormaps for notebooks.

Usage:
    import setup_plotting

This file extracts the plotting-related code from `resolution.ipynb` cell 3 so it can be reused across notebooks.
"""
import numpy as np
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt


matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'

SMALL_SIZE = 8
MEDIUM_SIZE = 9
BIGGER_SIZE = 10

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

# optional dependency: cmcrameri provides perceptually uniform colormaps
try:
    from cmcrameri import cm as cmcra # type: ignore
except Exception:
    cmcra = None



def mk_binary_alpha():
    """Make the binary alpha colormap."""

    try:
        # register a binary colormap with alpha ramp if not present
        cmap = matplotlib.colormaps['binary_alpha']
    except Exception:
        ncolors = 256
        color_array = plt.get_cmap('binary')(range(ncolors))
        color_array[:, -1] = np.linspace(0.0, 1.0, ncolors)
        map_object = LinearSegmentedColormap.from_list(name='binary_alpha', colors=color_array)
        try:
            plt.colormaps.register(cmap=map_object)
        except Exception:
            # older matplotlib versions
            matplotlib.cm.register_cmap(name='binary_alpha', cmap=map_object)
        cmap = matplotlib.colormaps['binary_alpha']
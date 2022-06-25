
from matplotlib.axis import Axis
from .._base import ChartExtension
from ...helpers.metaclasses.vispm import Presentor
from ...static.dotted import StaticDottedChartPresentor

from typing import Any, Tuple, List
from enum import Enum, auto

import numpy as np

from matplotlib.axes import Axes
from matplotlib.transforms import Affine2D


class DottedColourHistogramExtension(ChartExtension):
    """
    Adds a histogram showing the density of a given colour per segement of the choosen axis.\n

    Call Sequence:
    ----
    To use this extension call the following methods, finally attach to presentor:
    ```
    extension = DottedColourHistogramExtension()
    presentor.add_extension(extension)
    presentor.plot()
    ```
    Parameters:
    ----
    direction:`ChartExtension.Direction`\n
    [Optional] Sets what direction to build axes in for extension \n
    \n
    plot_axes:`DottedColourHistogramExtension.PlotAxes=PlotAxes.X"\n
    [Optional] Sets what axes to plot. X plots the colour of the events 
    \n
    debug:`bool=True`\n
    [Optional] Sets whether debug messages are printed.\n
    """

    class PlotAxes(Enum):
            Y=auto()
            X=auto()

    _compatable = StaticDottedChartPresentor


    def __init__(self, 
        direction:ChartExtension.Direction=ChartExtension.Direction.SOUTH, 
        plot_axes:PlotAxes=PlotAxes.Y,
        debug: bool = True) -> None:
        super().__init__(debug)
        # setup 
        self._direction = direction
        self._plot_axes = plot_axes
        self._axes = None
        self._size = (1.0,1.0)

    def compatable_with(self, presentor:Presentor) -> bool:
        return self._compatable is presentor.__class__

    def get_update_state(self) -> ChartExtension.UpdateState:
        return ChartExtension.UpdateState.PLOTTING

    def set_axes(self, axes: Axes):
        self._axes = axes

    def get_direction(self) -> ChartExtension.Direction:
        return self._direction
    
    def get_size(self) -> Tuple[float, float]:
        return self._size

    def _find_scale(self, seconds:float) -> Tuple[str,float]:
        if seconds < (60 * 3):
            return ("min" , 60)
        elif seconds < (  60 * 60 * 20):
            return ("hr", ( 60 * 60))
        elif seconds < (  60 * 60 * 24 * 183):
            return ("d", ( 60 * 60 * 24))
        else: 
            return ("yr", ( 60 * 60 * 24 * 365))

    def draw(self, x_data:List[float], y_data:List[float], colors:List[Tuple[float,float,float,float]], *args, **kwags) -> Axes:
        # set plot axis 
        self._debug("ploting histogram...")
        plot_axis = x_data if self._plot_axes == self.PlotAxes.X else y_data
        # bin_space = np.linspace(min(plot_axis), max(plot_axis), 100)
        # bins = [ () for start,end in zip(bin_space[:-1],bin_space[1:])]
        x_rects = [] 
        uni_colors = set(colors)
        for color in  uni_colors:
            x_subset = [ x for x,c in zip(plot_axis, colors) if c.__eq__(color)]
            x_rects.append(x_subset)

        if self._direction == self.Direction.EAST or self._direction == self.Direction.WEST:
            orientation = 'horizontal'
        else:
            orientation = 'vertical'

        # plot
        self._axes.hist(x_rects,stacked=True, histtype='barstacked', bins=100, color=uni_colors, orientation=orientation)

        # add labels 
        if self._plot_axes == self.PlotAxes.Y:
            if orientation == 'horizontal':
                self._axes.set_ylabel("trace identifier")
                self._axes.set_xlabel("No. events")
            else:
                self._axes.set_xlabel("trace identifier")
                self._axes.set_ylabel("No. events")
        else:
            if orientation == 'horizontal':
                self._axes.set_ylabel("time of event")
                self._axes.set_xlabel("No. events")
            else:
                self._axes.set_xlabel("time of event")
                self._axes.set_ylabel("No. events")
        
        # adjust xticks for timestamp
        if  self._plot_axes == self.PlotAxes.X:

            if orientation == 'horizontal':
                min_x = min(plot_axis)
                suffix, scale = self._find_scale(max(plot_axis) - min_x)
                self._axes.set_yticklabels(
                    [ 
                        f"{(tick - min_x) / scale:.1f}{suffix}"
                        for tick 
                        in self._axes.get_yticks()
                    ],
                    rotation=-45
                )    
            else :
                min_x = min(plot_axis)
                suffix, scale = self._find_scale(max(plot_axis) - min_x)
                self._axes.set_xticklabels(
                    [ 
                        f"{(tick - min_x) / scale:.1f}{suffix}"
                        for tick 
                        in self._axes.get_xticks()
                    ],
                    rotation=-45
                )    

        # clean up axes
        
        self._axes.set_frame_on(False)
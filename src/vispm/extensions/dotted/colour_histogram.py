from .._base import ChartExtension
from ...helpers.metaclasses.vispm import Presentor
from ...static.dotted import StaticDottedChartPresentor
from ...helpers.imputers.colour_imputers import ColourImputer

from typing import Any, Tuple, List
from enum import Enum, auto

import numpy as np

from matplotlib.axes import Axes
from matplotlib.colors import Colormap


class DottedColourHistogramExtension(ChartExtension):
    """
    Adds a histogram showing the density of a given colour per segment of the choosen axis.\n

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
    bin_axes:`DottedColourHistogramExtension.PlotAxes=PlotAxes.X`\n
    [Optional] Sets what axes to use to generate bins. X will use the relative timestamp from start of event log, while Y will use the trace number. 
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
        bin_axes:PlotAxes=PlotAxes.Y,
        colourmap:Colormap=None,
        debug: bool = True) -> None:
        super().__init__(debug)
        # setup 
        self._direction = direction
        self._bin_axes = bin_axes
        self._axes = None
        self._size = (1.0,1.0)
        self._colormap = colourmap

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

    def draw(self, x_data:List[float], y_data:List[float], colors:List[Tuple[float,float,float,float]], colour_imputer:ColourImputer, *args, **kwags) -> Axes:
        # set plot axis 
        self._debug("ploting histogram...")
        plot_axis = x_data if self._bin_axes == self.PlotAxes.X else y_data

        x_rects = [] 
        seen_colors = colour_imputer.get_seen_order()
        for color in  seen_colors:
            x_subset = [ x for x,c in zip(plot_axis, colors) if c.__eq__(color)]
            x_rects.append(x_subset)

        if self._direction == self.Direction.EAST or self._direction == self.Direction.WEST:
            orientation = 'horizontal'
        else:
            orientation = 'vertical'

        # plot
        n,bins,_ = self._axes.hist(x_rects, histtype='barstacked', bins=100, color=seen_colors, orientation=orientation)

        tops = [ 
            max([ stack[i] for stack in n ])
            for i 
            in range(len(n[0]))  
        ]
        count_max = np.max(tops)
        count_mid = np.floor(count_max/2.0)


        # add labels 
        if self._bin_axes == self.PlotAxes.Y:
            if orientation == 'horizontal':
                self._axes.set_ylabel("trace identifier")
                self._axes.set_xlabel("No. events")
                self._axes.set_xticks([0, count_mid, count_max])
                self._axes.set_xlim(0, count_max)
            else:
                self._axes.set_xlabel("trace identifier")
                self._axes.set_ylabel("No. events")
                self._axes.set_yticks([0, count_mid, count_max])
                self._axes.set_ylim(0, count_max)
        else:
            if orientation == 'horizontal':
                self._axes.set_ylabel("time of event")
                self._axes.set_xlabel("No. events")
                self._axes.set_xticks([0, count_mid, count_max])
                self._axes.set_xlim(0, count_max)
            else:
                self._axes.set_xlabel("time of event")
                self._axes.set_ylabel("No. events")
                self._axes.set_yticks([0, count_mid, count_max])
                self._axes.set_ylim(0, count_max)
        
        min_x = min(plot_axis)
        max_x = max(plot_axis)
        # adjust xticks for timestamp
        if  self._bin_axes == self.PlotAxes.X:
            if orientation == 'horizontal':
                portion = (max_x - min_x) / 8.0
                suffix, scale = self._find_scale(max_x - min_x)
                ticks = [min_x] + [min_x + (i*portion) for i in range(1,8)] + [max_x]
                self._axes.set_yticks(ticks)
                self._axes.set_yticklabels(
                    [ 
                        f"{(tick - min_x) / scale:.1f}{suffix}"
                        for tick 
                        in ticks
                    ],
                    rotation=-13,
                    fontdict={'fontsize' : 6}
                )
                self._axes.set_ylim([min_x,max_x])
            else :
                portion = (max_x - min_x) / 8.0
                suffix, scale = self._find_scale(max_x - min_x)
                ticks = [min_x] + [(min_x + (i*portion)) for i in range(1,8)] + [max_x]
                self._axes.set_xticks(ticks)
                self._axes.set_xticklabels(
                    [ 
                        f"{(tick - min_x) / scale:.1f}{suffix}"
                        for tick 
                        in ticks
                    ],
                    rotation=-13,
                    fontdict={'fontsize' : 6}
                )    
                self._axes.set_xlim([min_x,max_x])
        else:
            portion = (max_x - min_x) / 8.0
            ticks = [min_x] + [int(np.floor((min_x + (i*portion)))) for i in range(1,8)] + [max_x]
            if orientation == 'horizontal':
                self._axes.set_ylim([min_x,max_x]) 
                self._axes.set_yticks(ticks)
                self._axes.set_yticklabels(
                    ticks,
                    rotation=-13,
                    fontdict={'fontsize' : 6}
                )    
            else:
                self._axes.set_xlim([min_x,max_x])
                self._axes.set_xticks(ticks)
                self._axes.set_xticklabels(
                    ticks,
                    rotation=-13,
                    fontdict={'fontsize' : 6}
                )    

        # clean up axes
        self._axes.set_frame_on(False)
        return self._axes
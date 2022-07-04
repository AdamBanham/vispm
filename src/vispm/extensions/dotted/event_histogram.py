from vispm.helpers.imputers.event_imputers import EventLabelImputer
from .._base import ChartExtension
from ...helpers.data.log_data import SequenceData
from ...helpers.metaclasses.vispm import Presentor
from ...static.dotted import StaticDottedChartPresentor
from ...helpers.imputers.colour_imputers import EventLabelColourer
from ...helpers.colours.colourmaps import HIGH_CONTRAST_WARM

from typing import Any, Tuple, List
from enum import Enum, auto

import numpy as np

from matplotlib.axes import Axes
from matplotlib.cm import get_cmap, ScalarMappable
from matplotlib.colors import Colormap,ListedColormap,Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable

DEFAULT_COLORMAP = get_cmap('rainbow')

class DottedEventHistogramExtension(ChartExtension):
    """
    Adds a histogram showing the breakdown of event labels per segment of the choosen axis.\n

    Call Sequence:
    ----
    To use this extension call the following methods, finally attach to presentor:
    ```
    extension = DottedEventHistogramExtension()
    presentor.add_extension(extension)
    presentor.plot()
    ```

    Parameters:
    ----
    colourmap:`ListedColormap=HIGH_CONTRAST_WARM`\n
    [Optional] \n
    \n
    direction:`ChartExtension.Direction=ChartExtension.Direction.SOUTH`\n
    [Optional] Sets what direction to build axes in for extension \n
    \n
    bin_axes:`DottedEventHistogramExtension.PlotAxes=PlotAxes.X`\n
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
        colourmap:Colormap=DEFAULT_COLORMAP,
        direction:ChartExtension.Direction=ChartExtension.Direction.SOUTH, 
        bin_axes:PlotAxes=PlotAxes.Y,
        debug: bool = True) -> None:
        super().__init__(debug)
        # setup 
        self._colourer = EventLabelColourer()
        self._event_mapper = EventLabelImputer()
        self._colourmap = colourmap
        self._direction = direction
        self._bin_axes = bin_axes
        self._axes = None
        self._size = (1.5,1.5)

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

    def draw(self,x_data:List[float], y_data:List[float],sequences:List[List[SequenceData]], *args, **kwags) -> Axes:
        # set plot axis 
        self._debug("ploting histogram...")
        plot_axis = x_data if self._bin_axes == self.PlotAxes.X else y_data
        copy_sequences = [ s for seq in sequences for s in seq]

        seen_activities = []
        for seq in sequences:
            activities = [ sa['act'] for sa in seen_activities]
            seq_acts = [ s.label for s in seq ]
            unique_acts =set(seq_acts)
            for act in unique_acts:
                places = [ i for i,s in enumerate(seq_acts) if s == act]
                count = len(places)
                if act not in activities:
                    seen_activities.append({'act': act, 'count': count, 'place': sum(places)})
                else:
                    counter = [sa for sa in seen_activities if sa['act'] == act ][0]
                    counter['count'] += count
                    counter['place'] += sum(places)

        x_rects = []
        colours = []
        seen_activities = sorted(seen_activities, key=lambda x: (x['place']/x['count'],x['count']) )
        
        # try looking up the cmap and resetting length otherwise use as is.
        try:
            self._colourer._set_cm(get_cmap(self._colourmap, len(seen_activities))) 
        except:
            self._colourer._set_cm(self._colourmap)
        
        for sa in seen_activities:
            label = sa["act"]
            x_subset = [ (x,c) for x,c in zip(plot_axis, copy_sequences) if c.label == label ]
            x_rects.append([ x for x,c in x_subset])
            colours.append(self._colourer([x_subset[0][1]])[0])
            self._event_mapper.add_label(label)
            sa['act'] = self._event_mapper.get_label(label)

        if self._direction == self.Direction.EAST or self._direction == self.Direction.WEST:
            orientation = 'horizontal'
        else:
            orientation = 'vertical'

        # plot
        n,bins,_ = self._axes.hist(x_rects, histtype='barstacked', bins=100, color=colours, orientation=orientation)
        
        # handle colour bar for event labels
        divider = make_axes_locatable(self._axes)
        if self._direction == self.Direction.NORTH or self._direction == self.Direction.SOUTH:
            cbar_orientation = 'horizontal'
            cax = divider.append_axes('top', size='10%', pad=0.2)
        else:
            cbar_orientation = 'vertical'
            cax = divider.append_axes('right', size='10%', pad=0.2)
        
        # add colourbar to axes
        tickers = list(range(0,len(seen_activities)))
        norm = Normalize(vmin=0, vmax=max(tickers))
        cbar = self._axes.get_figure().colorbar(ScalarMappable(cmap=ListedColormap(colours), norm=norm), ticks=tickers, orientation=cbar_orientation, cax=cax)
        tickers = cbar.get_ticks()
        cbar.set_ticks(tickers, labels=[ sa['act'] for sa in seen_activities], fontsize=6)
        # adjust tick position if needed
        if self._direction == self.Direction.NORTH:
            cbar.ax.get_xaxis().set_ticks_position('top')

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
            # adjust ticks for trace identifiers
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
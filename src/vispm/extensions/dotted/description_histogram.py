from .._base import ChartExtension
from ...static.dotted import StaticDottedChartPresentor
from ...helpers.metaclasses.vispm import Presentor
from ...helpers.data.log_data import SequenceData
from vispm.helpers.imputers.event_imputers import EventLabelImputer
from ...helpers.colours.colourmaps import HIGH_CONTRAST_COOL

DEFAULT_CM = HIGH_CONTRAST_COOL

from typing import Any, Tuple, List
from enum import Enum, auto

import numpy as np

from matplotlib.axes import Axes
from matplotlib.cm import get_cmap, ScalarMappable
from matplotlib.colors import Colormap,ListedColormap,Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable

class DescriptionHistogramExtension(ChartExtension):
    """
    Adds a histogram showing varitey of values seen for a aspect of events, binned over trace (has an event with aspect) or by event.\n

    Call Sequence:
    ----
    To use this extension call the following methods, finally attach to presentor:
    ```
    extension = DescriptionHistogramExtension(
        describe=DescriptionHistogramExtension.Describe.EventLabel,
        density=DescriptionHistogramExtension.Density.Trace
    )
    presentor.add_extension(extension)
    presentor.plot()
    ```
    Parameters:
    ----
    direction: `ChartExtension.Direction=ChartExtension.Direction.NORTH`\n
    [Optional] Sets what direction to build axes in for extension \n
    \n
    describe: `Density=Density.Event`\n
    [Optional]  How to count for the bins in the histogram, e.g. count total events or traces. \n 
    \n
    describe: `Describe=Describe.EventLabel`\n
    [Optional]  The aspect to describe, such as event's acitvity label, trace duration, weekday, monthday, or trace length.\n 
    \n
    colormap: `matplotlib.colors.Colormap=HIGH_CONTRAST_COOL`\n
    [Optional]  The colourmap used for the colorbar (if needed) and colours for bins in histogram. Colourmap will be resampled.\n 
    \n
    debug:`bool=True`\n
    [Optional] Sets whether debug messages are printed.\n
    """

    class Density(Enum):
            Event=auto()
            Trace=auto()

    class Describe(Enum):
            EventLabel=auto()
            Weekday=auto()
            Monthday=auto()
            Hourly=auto()
            TraceDuration=auto()
            TraceLength=auto()

    _compatable = StaticDottedChartPresentor

    def __init__(self, 
        direction:ChartExtension.Direction=ChartExtension.Direction.NORTH,
        describe:Describe=Describe.EventLabel,
        density:Density=Density.Event,
        colormap:Colormap=DEFAULT_CM,
        imputer_type:str="ascii",
        debug: bool = True) -> None:
           super().__init__(debug)
           #setup
           self._direction = direction 
           self._describe = describe
           self._counter = density
           self._axes = None 
           self._size = (1.3,1.3)
           self._colormap = colormap
           self._imputer_type = imputer_type
    
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

    def _create_bins(self, sequences:List[List[SequenceData]]) -> Tuple[List[List[float]], List[Tuple[float,float,float,float]], List[float], List[str]]:
        if self._describe == self.Describe.EventLabel:
            return self._create_label_bins(sequences)
        elif self._describe == self.Describe.Monthday:
            return self._create_monthday_bins(sequences)
        elif self._describe == self.Describe.Weekday:
            return self._create_weekday_bins(sequences)
        elif self._describe == self.Describe.TraceDuration:
            return self._create_tdur_bins(sequences)
        elif self._describe == self.Describe.TraceLength:
            return self._create_tlen_bins(sequences)
        elif self._describe == self.Describe.Hourly:
            return self._create_hourly_bins(sequences)
        else:
            raise ValueError(f"Description type not support :: {self._describe}")

    def _create_hourly_bins(self, sequences:List[List[SequenceData]]) -> Tuple[List[List[float]], List[Tuple[float,float,float,float]], List[float], List[str]]:
        bin_values= []
        bin_edges= list(range(0,25))
        bin_labels=[]
        colours = []
        colour_maximun = 24

        self._colourmap = get_cmap(self._colormap, colour_maximun)
        for hourly,label in zip(range(0,colour_maximun), range(0,colour_maximun)):
            if self._counter == self.Density.Event:
                x_subset = [ hourly+0.5 for seq in sequences for s in seq if s.hour == hourly ]
            elif self._counter ==self.Density.Trace:
                x_subset = [ hourly+0.5 for seq in sequences if hourly in [ s.hour for s in seq] ]
            bin_values = bin_values + x_subset
            colours.append(self._colormap(hourly/colour_maximun))
            bin_labels.append(label)

        return bin_values, colours, bin_edges, bin_labels, colour_maximun 

    def _create_tlen_bins(self, sequences:List[List[SequenceData]]) -> Tuple[List[List[float]], List[Tuple[float,float,float,float]], List[float], List[str]]:
        bin_values= []
        bin_labels=[]
        colours = []

        durs = [ len(seq) for seq in sequences ]
        min_edge = int(np.floor(min(durs)))
        max_edge = int(np.ceil(max(durs)))
        edge_dist = ((max_edge - min_edge)) /100
        bin_edges = [min_edge] + [min_edge + (edge_dist * i) for i in range(1,100)] + [max_edge]
        self._colormap = get_cmap(self._colormap, len(bin_edges))
        colour_maximun = (min_edge,max_edge)

        for seq,dur in zip(sequences,durs):
            if self._counter == self.Density.Event:
                x_subset = [ dur for s in seq ]
            else:
                x_subset = [ dur ]
            bin_values = bin_values + x_subset

        return bin_values, colours, bin_edges, bin_labels, colour_maximun 

    def _create_label_bins(self, sequences:List[List[SequenceData]]) -> Tuple[List[List[float]], List[Tuple[float,float,float,float]], List[float], List[str]]:
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

        bin_values= []
        bin_edges= []
        bin_labels=[]
        colours = []
        seen_activities = sorted(seen_activities, key=lambda x: (x['place']/x['count'],x['count']) )
        max_spot = np.ceil(max([ sa['place'] / sa["count"] for sa in seen_activities ]))
        labeler = EventLabelImputer(type=EventLabelImputer.IMPUTER_TYPE.find(self._imputer_type))
        self._colourmap = get_cmap(self._colormap, max_spot)
        for index,sa in enumerate(seen_activities):
            label = sa["act"]
            bin_edges.append(index)
            if self._counter == self.Density.Event:
                x_subset = [ index+0.5 for seq in sequences for s in seq if s.label == label ]
            elif self._counter ==self.Density.Trace:
                x_subset = [ index+0.5 for seq in sequences if label in [ s.label for s in seq] ]
            likely_place = sa['place'] / sa["count"]
            colours.append(self._colormap(likely_place/max_spot))
            bin_values = bin_values + x_subset
            labeler.add_label(label)
            bin_labels.append(labeler.get_label(label))
        bin_edges.append(len(seen_activities))
        self._debug(f"Event labels are imputed as :: {labeler._lookup}")
        return bin_values, colours, bin_edges, bin_labels, max_spot

    def _create_monthday_bins(self, sequences:List[List[SequenceData]]) -> Tuple[List[List[float]], List[Tuple[float,float,float,float]]]:
        bin_values= []
        bin_edges= list(range(1,33))
        bin_labels=[]
        colours = []
        colour_maximun = 31

        self._colourmap = get_cmap(self._colormap, colour_maximun)
        for monthday in range(1,32):
            if self._counter == self.Density.Event:
                x_subset = [ monthday+0.5 for seq in sequences for s in seq if s.monthday == monthday ]
            elif self._counter ==self.Density.Trace:
                x_subset = [ monthday+0.5 for seq in sequences if monthday in [ s.monthday for s in seq] ]
            bin_values = bin_values + x_subset
            colours.append(self._colormap(monthday/colour_maximun))
            bin_labels.append(monthday)

        return bin_values, colours, bin_edges, bin_labels, colour_maximun 

    def _create_weekday_bins(self, sequences:List[List[SequenceData]]) -> Tuple[List[List[float]], List[Tuple[float,float,float,float]]]:
        bin_values= []
        bin_edges= list(range(0,8))
        bin_labels=[]
        colours = []
        colour_maximun = 7

        self._colourmap = get_cmap(self._colormap, colour_maximun)
        for day,label in zip(range(0,7), ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]):
            if self._counter == self.Density.Event:
                x_subset = [ day+0.5 for seq in sequences for s in seq if s.weekday == day ]
            elif self._counter ==self.Density.Trace:
                x_subset = [ day+0.5 for seq in sequences if day in [ s.weekday for s in seq] ]
            bin_values = bin_values + x_subset
            colours.append(self._colormap(day/colour_maximun))
            bin_labels.append(label)


        return bin_values, colours, bin_edges, bin_labels, colour_maximun 

    def _create_tdur_bins(self, sequences:List[List[SequenceData]]) -> Tuple[List[List[float]], List[Tuple[float,float,float,float]]]:
        bin_values= []

        durs = [ seq[-1].time - seq[0].time for seq in sequences ]
        min_edge = int(np.floor(min(durs)))
        max_edge = int(np.ceil(max(durs)))
        scale_unit,scale = self._find_scale(max_edge - min_edge)
        edge_dist = ((max_edge - min_edge)/scale) /100
        min_edge = min_edge/scale 
        max_edge = max_edge/scale
        bin_edges = [min_edge] + [min_edge + (edge_dist * i) for i in range(1,100)] + [max_edge]
        colour_maximun = bin_edges[-1]
        self._colormap = get_cmap(self._colormap, len(bin_edges))

        for seq,dur in zip(sequences,durs):
            if self._counter == self.Density.Event:
                x_subset = [ dur/scale for s in seq ]
            else:
                x_subset = [ dur/scale ]
            bin_values = bin_values + x_subset
            
        return bin_values, scale, bin_edges, scale_unit, colour_maximun 

    def _find_scale(self, seconds:float) -> Tuple[str,float]:
        if seconds < (60 * 3):
            return ("minutes" , 60)
        elif seconds < (  60 * 60 * 20):
            return ("hours", ( 60 * 60))
        elif seconds < (  60 * 60 * 24 * 183):
            return ("days", ( 60 * 60 * 24))
        else: 
            return ("years", ( 60 * 60 * 24 * 365))

    def draw(self, sequences:List[List[SequenceData]], *args, **kwags) -> Axes:
        self._debug("plotting histogram")

        # compute bin edges
        if self._describe == self.Describe.TraceDuration:
            bin_values, scale, bin_edges, scale_unit, colour_maximun = self._create_bins(sequences)
        else:
            bin_values, bin_colours, bin_edges, bin_labels, max_spot = self._create_bins(sequences)

        #decide on orientation of histogram
        if self._direction == self.Direction.EAST or self._direction == self.Direction.WEST:
            orientation = 'horizontal'
        else:
            orientation = 'vertical'

        # determine rwidth
        rwidth = 0.85


        # plot histogram
        n,_,rects = self._axes.hist(bin_values, bins=bin_edges, orientation=orientation,rwidth=rwidth)
        # adjust bars to match colours
        if self._describe in [self.Describe.TraceLength,self.Describe.TraceDuration]:
            norm = Normalize(vmin=min(n),vmax=max(n))
            for rect,v in zip(rects,n):
                rect.set(color=self._colormap(norm(v)))
        else:
            for rect, c in zip(rects, bin_colours):
                rect.set(color=c)
        # adjust ticks 
        xticks = [ ed+0.5 for ed in bin_edges[:-1]]
        if self._direction == self.Direction.NORTH or self._direction == self.Direction.SOUTH:
            if self._describe == self.Describe.TraceDuration:
                self._axes.set_xlabel(f"Duration in {scale_unit}")
            elif self._describe == self.Describe.TraceLength:
                mids = xticks[1:-1]
                if len(mids) > 8:
                    new_mids = []
                    step = len(mids)/8
                    curr = 0
                    for i in range(1,8):
                        curr = (i * step)
                        new_mids.append(mids[int(curr)])
                    mids = new_mids
                xticks = [xticks[0]] + mids + [xticks[-1]]
                xlabels = [ f"{int(t):d}" for t in xticks ]
                self._axes.set_xticks(xticks)
                self._axes.set_xticklabels(xlabels, 
                    fontdict={"fontsize": 5, 'rotation': -13})
            else:
                self._axes.set_xticks(xticks)
                self._axes.set_xticklabels(bin_labels, 
                    fontdict={"fontsize": 5, 'rotation': -13})
            self._axes.set_xlim([min(bin_edges), max(bin_edges)])
        else:
            if self._describe == self.Describe.TraceDuration:
                self._axes.set_ylabel(f"Duration in {scale_unit}")
            elif self._describe == self.Describe.TraceLength:
                mids = xticks[1:-1]
                if len(mids) > 8:
                    new_mids = []
                    step = len(mids)/8
                    curr = 0
                    for i in range(1,8):
                        curr = (i * step)
                        new_mids.append(mids[int(curr)])
                    mids = new_mids
                xticks = [xticks[0]] + mids + [xticks[-1]]
                xlabels = [ f"{int(t):d}" for t in xticks ]
                self._axes.set_yticks(xticks)
                self._axes.set_yticklabels(xlabels, fontdict={"fontsize": 5})
            else:
                self._axes.set_yticks(xticks)
                self._axes.set_yticklabels(bin_labels, fontdict={"fontsize": 5})
            self._axes.set_ylim([min(bin_edges), max(bin_edges)])
        
        if  self._describe in [self.Describe.EventLabel, self.Describe.TraceDuration, self.Describe.TraceLength]:
            # add colour bar to show where activties are likely to occur
            divider = make_axes_locatable(self._axes)
            if self._direction == self.Direction.NORTH or self._direction == self.Direction.SOUTH:
                cbar_orientation = 'horizontal'
                if self._direction == self.Direction.NORTH:
                    cax = divider.append_axes('top', size='10%', pad=0.15)
                else:
                    cax = divider.append_axes('bottom', size='10%', pad=0.45)
            else:
                cbar_orientation = 'vertical'
                if self._direction == self.Direction.EAST:
                    cax = divider.append_axes('right', size='10%', pad=0.15)
                else: 
                    cax = divider.append_axes('left', size='10%', pad=0.55)

            # add colourbar to axes
            if self._describe == self.Describe.EventLabel:
                dist = max_spot - 1
                portion = dist / 10 
                tickers = [1] + [int(1 + portion*i) for i in range(1,10) ] + [int(max_spot)]
                norm = Normalize(vmin=min(tickers), vmax=max(tickers))
                cbar = self._axes.get_figure().colorbar(ScalarMappable(cmap=self._colormap, norm=norm), ticks=tickers, orientation=cbar_orientation, cax=cax)
                tickers = cbar.get_ticks()
                cbar.set_ticks(tickers, labels=tickers, fontsize=6)
                cbar.set_label("likely position in traces")
            else:
                dist = max(n) - min(n)
                portion = dist / 10 
                tickers = [int(min(n))] + [int(1 + portion*i) for i in range(1,10) ] + [int(max(n))]
                cbar = self._axes.get_figure().colorbar(ScalarMappable(cmap=self._colormap, norm=norm), ticks=tickers, orientation=cbar_orientation, cax=cax)
                cbar.set_ticks(tickers, labels=tickers, fontsize=6)
                cbar.set_label("Count")

            # adjust tick position for colorbar if needed
            if self._direction == self.Direction.NORTH:
                cbar.ax.get_xaxis().set_ticks_position('top')
                cbar.ax.get_xaxis().set_label_position('top')
            if self._direction == self.Direction.WEST:
                cbar.ax.get_yaxis().set_ticks_position('left')
                cbar.ax.get_yaxis().set_label_position('left')
        
        # add height label to histogram 
        if self._counter == self.Density.Event:
            height_label = "No. of events"
        else:
            height_label = "No. of traces"

        #add bin label
        bin_label = ""
        if self._describe == self.Describe.Monthday:
            bin_label = "day of month"
        elif self._describe == self.Describe.EventLabel:
            bin_label = "activity"
        elif self._describe == self.Describe.TraceLength:
            bin_label = "trace length"
        elif self._describe == self.Describe.TraceDuration:
            bin_label = f"Duration in {scale_unit}"
        
        if self._direction in [self.Direction.NORTH, self.Direction.SOUTH]:
            self._axes.set_xlabel(bin_label)
        else:
            self._axes.set_ylabel (bin_label)

        # add a suitable height ticks for histogram
        if self._direction in [self.Direction.NORTH, self.Direction.SOUTH]:
            self._axes.set_ylabel(height_label)
            top = max(n)
            ticks = [0, int(top/2), int(top)]
            self._axes.set_yticks(ticks)
            self._axes.set_yticklabels(ticks, fontdict={'fontsize' : 6, 'rotation': -13})
        else:
            self._axes.set_xlabel(height_label)
            top = max(n)
            ticks = [0, int(top/2), int(top)]
            self._axes.set_xticks(ticks)
            self._axes.set_xticklabels(ticks, fontdict={'fontsize' : 6, 'rotation': -13})


        # clean up axes
        self._axes.set_frame_on(False)
        return self._axes
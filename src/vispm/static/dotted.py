from enum import Enum
from ..helpers.data.log_data import SequenceData
from ..helpers.metaclasses.pm4py import EventLog
from ..helpers.handlers.log_runners import SequenceDataExtractor
from ..helpers.imputers.colour_imputers import ColourImputer, TraceColourer, EventLabelColourer
from ..helpers.colours.colourmaps import CATEGORICAL
from ..helpers.iters.tools import iter_chunker
from ..extensions._base import ChartExtension
from ._base import StaticPresentor

from typing import List, Tuple, Any
from datetime import datetime
from math import ceil, floor

from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle

PLOT_STATE = ChartExtension.UpdateState

class StaticDottedChartPresentor(StaticPresentor):
    """
    Presentor for generating a static dotted chart for a given log. Should 
    be used in a one shot manner.

    Call sequence:
    ---
    To use presentor call the following methods:
    ``` 
    presentor = StaticDottedChartPresentor(log)
    presentor.plot()
    ```

    Parameters:
    ----
    event_log:`EventLog`\n
    [Required] A python object, where sequence behaviour (i.e. log[1:5] 
    returns a list of traces) and mapping behaviour (i.e log["attr"]) return 
    attributes attached to the event log.\n
    Currently assumes that the given log, is very similar to the pm4py 
    implementation.\n
    \n
    dpi:`int=96`\n
    [Optional] The dpi of the figure, if generating one.\n
    \n
    figsize:`Tuple[float,float]=(8,8)`\n
    [Optional] The size of the figure in inches (WxH), if generating one.\n
    \n
    markersize:`float=0.5`\n
    [Optional] The relevative size of each circle drawn for each event.\n
    \n
    ax:`matplotlib.axes.Axes=None`\n
    [Optional] Instead of generating a figure and axes, use the given axes 
    as is to plot.\n
    \n
    starting_time:`datetime.datetime=None`\n
    [Optional] Instead of inferring the starting time of the event log, 
    use the given timstamp as the starting point for extracting data.\n
    \n
    trace_sorting:`StaticDottedChartPresentor.TraceSorting=firstevent`\n
    [Optional] Decides how traces are sorted on the y-axis for plotting,
    default value sorts traces by the timestamp of their first event.
    \n
    time_transform:`StaticDottedChartPresentor.TimeTransform=relative_to_log`\n
    [Optional] Decides how the timestamp for events are handled for plotting 
    and for the axis labels. Defaults to making all timetamps relative to the
    first event seen in the log.
    \n
    colormap:`matplotlib.colors.ListedColormap=vispm.helpers.colours.colourmaps.CATEGORICAL`\n
    [Optional] The colourmap to be passed to the colourer, some examples 
    of coloursmaps can be found in vispm.helpers.colours.colourmaps.\n
    \n
    event_colour_scheme:`vispm.helpers.imputers.colour_imputers.ColourImputer=StaticDottedChartPresentor.EventColourScheme.Trace`\n
    [Optional] The colourer to be used for deciding how a event is coloured, 
    will be passed the colourmap at init.\n
    For ease of use, this parameter can be controlled via a parameter enum, 
    which passes a class to use via `StaticDottedChartPresentor.EventColourScheme`\n
    For more advance use, a instance of a subclass from ColourImputer can be 
    passed instead.\n
    \n
    debug:`bool=True`\n
    [Optional] Sets whether debug messages are printed.\n

    """

    _fig = None
    _ax = None 
    _extractor = SequenceDataExtractor()
    _sequences = None
    _log_name = "Unknown EventLog"
    _colour_schemer = None
    _show_debug = True
    _marksize =0.5

    TraceSorting = SequenceDataExtractor.TraceSorting
    TimeTransform = SequenceDataExtractor.TimestampTransform

    class EventColourScheme(Enum):
        """
        Parameter Enum for event_colour_scheme of StaticDottedChartPresentor. Sets how events are coloured when plotting.

        Selection
        -----
        `EventColourScheme.Trace`\n
        \t Events will be colour via trace identifier.\n
        `EventColourScheme.EventLabel`\n
        \t Events will be coloured via event label, in a FIFO manner.
        """
        Trace:ColourImputer=TraceColourer
        EventLabel:ColourImputer=EventLabelColourer    

        def __call__(self,*args, **kwags) -> ColourImputer:
            return self.value(*args,**kwags)

    def __init__(self, event_log:EventLog, dpi:int=96, 
                 figsize:Tuple[float,float]=(8,8), ax:Axes=None,
                 markersize:float=0.5, 
                 starting_time=None,
                 trace_sorting:TraceSorting=TraceSorting.firstevent,
                 time_transform:TimeTransform=TimeTransform.relative_to_log,
                 colormap:ListedColormap=CATEGORICAL,debug:bool=True,
                 event_colour_scheme:EventColourScheme=EventColourScheme.Trace
                 ) -> None:
        super().__init__(debug=debug)
        self._sorting = trace_sorting
        self._time_transform = time_transform
        # set default values
        self._marksize = markersize
        # so turns out its painful to not show a figure and still show it when needed.
        reset_it = plt.isinteractive()
        if reset_it:
            plt.ioff()
        if ax == None:
            self._fig = plt.figure(figsize=figsize,dpi=dpi,constrained_layout=True)
            self._ax = self._fig.subplots(1,1)
        else:
            self._fig = ax.get_figure()
            self._ax = ax
        if reset_it:
            plt.ion()
        # adjust markersize
        # radius in data coordinates:
        self._marker_raidus = 2 # units
        # radius in display coordinates:
        # r_ = self._ax.transData.transform([self._marker_raidus,0])[0] - self._ax.transData.transform([0,0])[0] # points
        # marker size as the area of a circle
        # self._markersize = (2*r_)**2
        # self._marker_raidus = r_
        # process event data
        self._debug("Processing event data...")
        self._sequences = self._extractor(event_log, 
                                          start_time=starting_time,
                                          sorting=trace_sorting,
                                          time_transform=time_transform
                                          )
        # handle colourer input
        if isinstance(event_colour_scheme, self.EventColourScheme):
            self._colour_schemer = event_colour_scheme(cm=colormap)
        else:
            if issubclass(event_colour_scheme.__class__, ColourImputer):
                self._colour_schemer = event_colour_scheme
            else:
                self._debug(f"Unknown ColourImputer passed, unsafe to continue : passed {event_colour_scheme.__class__.__name__} which is not a subclass of vispm.helpers.imputers.colour_imputers.ColourImputer.")
                raise AttributeError("Given event colourer is not a subclass of ColourImputer.")
        #try to find event log name in attributes
        try:
            from pmkoalas.complex import ComplexEventLog
            if (isinstance(event_log, ComplexEventLog)):
                self._log_name = event_log.name
            else:
                raise ValueError("not a pmkoalas data structure")
        except:
            try :
                self._log_name = event_log.attributes['concept:name'] 
            except:
                self._debug("Cannot find concept:name in eventlog attributes.")
        self._debug("Ready to plot...")

    def _create_dotted_frame(self,sequences:List[List[SequenceData]], ax:Axes) -> List[Artist]:
        self.update_plot_state(PLOT_STATE.PLOTTING)
        self._debug("Compiling plot data...             ", end="\r")
        all_artists = []
        # preallocate mem space for speed
        x_data = [  0.0 for trace in sequences for ev in trace ]
        y_data = [ 0.0 for trace in sequences for ev in trace]
        colors = [ (0.0,0.0,0.0,0.0) for trace in sequences for ev in trace ]
        #collect markers
        total_seqs = len(sequences)
        percentile = ceil(total_seqs * 0.01)
        start_idx = 0
        for y,sequence in enumerate(sequences):
            end_idx = start_idx + len(sequence)
            new_colors = self._colour_schemer(trace_id=y,seq_data=sequence)
            for idx,seq in enumerate(sequence): 
                colors[start_idx+idx] = new_colors[idx]
                x_data[start_idx+idx] = seq.time
                y_data[start_idx+idx] = (y * (self._marker_raidus * 4))
            if y > 0 and y % percentile == 0:
                self._debug(f" {(y/total_seqs)*100:03.1f}% compiled...        ",end="\r")
            start_idx = end_idx
        # plot markers
        self._debug("Compiling finished...        ")
        self._debug("Plotting data...")
        self.update_extensions(x_data=x_data, y_data=y_data, colors=colors, colour_imputer=self._colour_schemer,sequences=sequences)
        for xers,yers,cers in zip(iter_chunker(x_data,500),iter_chunker(y_data,500),iter_chunker(colors,500)):
            patches = []
            for x,y,c in zip(xers,yers,cers):
                patches.append(
                    Circle(
                        (x,y),
                        radius=self._marker_raidus,
                        color=c,
                        alpha=0.66
                    )
                )
            # artists = ax.scatter(
            #     x=xers,
            #     y=yers,
            #     edgecolors=None,
            #     s = self._marksize,
            #     color=cers,
            #     alpha=0.66
            # )
            pc = PatchCollection(
                patches,
                match_original=True
            )
            ax.add_artist(pc)
            all_artists.append(pc)
            
        # handle y ticks using y_data
        max_y = max(y_data)+self._marker_raidus * 3
        self._ax.set_ylim(-self._marker_raidus * 3, max_y)
        self._ax.set_yticks([])
        self._ax.set_yticks([0,max_y])
        self._ax.set_yticklabels([ "1",f"{int(len(sequences))}"])
        return all_artists

    def plot(self) -> Figure:
        self._ax = self._adjust_for_extensions(self._fig)
        self.update_plot_state(PLOT_STATE.DRAWING)
        self._debug("setting up axis for plot...")
        #clean up plot
        # self._ax.set_ylim([0,len(self._sequences) * self._marker_raidus])
        if self._sorting == self.TraceSorting.tracelength and \
            self._time_transform == self.TimeTransform.constant_per_event:
            min_x = len(self._sequences[0]) * SequenceDataExtractor._constant_time_per_event
            max_x = len(self._sequences[-1]) * SequenceDataExtractor._constant_time_per_event
            self._ax.set_xlim([
                min_x , 
                max_x 
            ])
            # add suitable xticks 
            diff_x = max_x - min_x 
            tickers = [ min_x] + \
                        [ min_x + (portion/100) * diff_x 
                            for portion in range(10,100,10) ] + \
                        [ max_x ]
            self._ax.set_xticks(
                tickers
            )
            self._ax.set_xticklabels(
                [ 
                    f"{(tick) / SequenceDataExtractor._constant_time_per_event}"
                    for tick 
                    in self._ax.get_xticks()
                ],
                rotation=-90
            )    
            self._ax.set_xlabel("Event Number")
        else:
            min_x = self._sequences[0][0].time
            max_x = max([ seq[-1].time for seq in self._sequences if len(seq) > 0])
            self._ax.set_xlim([min_x, max_x ])
            # add suitable xticks 
            diff_x = max_x - min_x 
            tickers = [ min_x] + \
                        [ min_x + (portion/100) * diff_x 
                            for portion in range(10,100,10) ] + \
                        [ max_x ]
            suffix, scale = self._find_scale(diff_x)
            self._ax.set_xticks(
                tickers
            )
            if self._time_transform != self.TimeTransform.raw:
                self._ax.set_xticklabels(
                    [ 
                        f"{(tick - min_x) / scale:.2f}{suffix}"
                        for tick 
                        in self._ax.get_xticks()
                    ],
                    rotation=-90
                )    
            else:
                self._ax.set_xticklabels(
                    [ 
                        f"{datetime.fromtimestamp(tick).strftime('%d/%m/%Y')}"
                        for tick 
                        in self._ax.get_xticks()
                    ],
                    rotation=-90,
                    fontdict={
                        'fontsize' : 6
                    }
                )    
            self._ax.set_xlabel("Time")
        #add labels
        self._ax.set_ylabel("Trace")
        self._ax.set_title(f"Dotted Chart of\n {self._log_name}")
        self._ax.grid(True,color="grey",alpha=0.33)
        self.update_extensions(sequences=self._sequences)
        self._create_dotted_frame(self._sequences,self._ax)
        self._debug("Plot is ready to show...")
        return self._fig

    def get_axes(self) -> Axes:
        return self._ax

    def get_figure(self) -> Figure:
        return self._fig 

    def _find_scale(self, seconds:float) -> Tuple[str,float]:
        if seconds < (60 * 3):
            return ("min" , 60)
        elif seconds < (  60 * 60 * 20):
            return ("hr", ( 60 * 60))
        elif seconds < (  60 * 60 * 24 * 183):
            return ("d", ( 60 * 60 * 24))
        else: 
            return ("yr", ( 60 * 60 * 24 * 365))
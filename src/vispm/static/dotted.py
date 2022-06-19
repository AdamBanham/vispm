from enum import Enum
from ..helpers.data.log_data import SequenceData
from ..helpers.metaclasses.pm4py import EventLog
from ..helpers.handlers.log_runners import SequenceDataExtractor
from ..helpers.imputers.colour_imputers import ColourImputer, TraceColourer, EventLabelColourer
from ..helpers.colours.colourmaps import CATEGORICAL
from ..helpers.iters.tools import iter_chunker

from typing import List,Tuple
from math import ceil, floor

from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap

class StaticDottedChartPresentor():
    """
    Presentor for generating a static dotted chart for a given log. Should be used in a one shot manner.

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
    [Required] A python object, where sequence behaviour (i.e. log[1:5] returns a list of traces) and mapping behaviour (i.e log["attr"]) return attributes attached to the event log.\n
    Currently assumes that the given log, is very similar to the pm4py implementation.\n
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
    [Optional] Instead of generating a figure and axes, use the given axes as is to plot.\n
    \n
    starting_time:`datetime.datetime=None`\n
    [Optional] Instead of inferring the starting time of the event log, use the given timstamp as the starting point for extracting data.\n
    \n
    colormap:`matplotlib.colors.ListedColormap=vispm.helpers.colours.colourmaps.CATEGORICAL`\n
    [Optional] The colourmap to be passed to the colourer, some examples of coloursmaps can be found in vispm.helpers.colours.colourmaps.\n
    \n
    event_colour_scheme:`vispm.helpers.imputers.colour_imputers.ColourImputer=StaticDottedChartPresentor.EventColourScheme.Trace`\n
    [Optional] The colourer to be used for deciding how a event is coloured, will be passed the colourmap at init.\n
    For ease of use, this parameter can be controlled via a parameter enum, which passes a class to use via `StaticDottedChartPresentor.EventColourScheme`\n
    For more advance use, a instance of a subclass from ColourImputer can be passed instead.\n
    \n
    debug:`bool=True`\n
    [Optional] Sets whether debug messages are printed as class generates chart.\n

    """

    _fig = None
    _ax = None 
    _extractor = SequenceDataExtractor()
    _sequences = None
    _log_name = "Unknown EventLog"
    _colour_schemer = None
    _show_debug = True
    _marksize =0.5

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


    def __init__(self, event_log:EventLog, dpi:int=96, figsize:Tuple[float,float]=(8,8), ax:Axes=None,
        markersize:float=0.5, starting_time=None,
        colormap:ListedColormap=CATEGORICAL,debug:bool=True,
        event_colour_scheme:EventColourScheme=EventColourScheme.Trace) -> None:
        # set default values
        self._show_debug = debug
        self._marksize = markersize
        # so turns out its painful to not show a figure and still show it when needed.
        reset_it = plt.isinteractive()
        if reset_it:
            plt.ioff()
        if ax == None:
            self._fig = plt.figure(figsize=figsize,dpi=dpi,)
            self._ax = self._fig.subplots(1,1)
        else:
            self._fig = ax.get_figure()
            self._ax = ax
        if reset_it:
            plt.ion()
        # process event data
        self._debug("Processing event data...")
        self._sequences = self._extractor(event_log, start_time=starting_time)
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
        try :
            self._log_name = event_log.attributes['concept:name'] 
        except:
            self._debug("Cannot find concept:name in eventlog attributes.")
        self._debug("Ready to plot...")

    def _debug(self, message:str, end="\n"):
        if self._show_debug:
            print(f"[{self.__class__.__name__}] {message} ",end=end)

    def _create_dotted_frame(self,sequences:List[List[SequenceData]], ax:Axes) -> List[Artist]:
        self._debug("Compiling plot data...             ", end="\r")
        all_artists = []
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
            colors[start_idx:end_idx] = new_colors
            x_data[start_idx:end_idx] = [ seq.time for seq in sequence ]
            y_data[start_idx:end_idx] = [ y for _ in  range(len(sequence)) ]
            if y > 0 and y % percentile == 0:
                self._debug(f" {(y/total_seqs)*100:03.1f}% compiled...        ",end="\r")
            start_idx = end_idx
        # plot markers
        self._debug("Compiling finished...        ")
        self._debug("Plotting data...")
        for xers,yers,cers in zip(iter_chunker(x_data,500),iter_chunker(y_data,500),iter_chunker(colors,500)):
            artists = ax.scatter(
                x=xers,
                y=yers,
                s = self._marksize,
                color=cers,
                alpha=0.66
            )
            all_artists.append(artists)
        return all_artists

    def plot(self) -> Figure:
        self._create_dotted_frame(self._sequences,self._ax)
        self._debug("Cleaning up plot...")
        #clean up plot
        self._ax.set_ylim([0,len(self._sequences)])
        min_x = self._sequences[0][0].time
        max_x = max([ seq[-1].time for seq in self._sequences if len(seq) > 0])
        self._ax.set_xlim([min_x, max_x ])
        self._ax.set_yticks([])
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
        self._ax.set_xticklabels(
            [ 
                f"{(tick - min_x) / scale:.2f}{suffix}"
                for tick 
                in self._ax.get_xticks()
            ],
            rotation=-90
        )    
        #add labels
        self._ax.set_ylabel("Trace")
        self._ax.set_xlabel("Time")
        self._ax.set_title(f"Dotted Chart of\n {self._log_name}")
        self._ax.grid(True,color="grey",alpha=0.33)
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